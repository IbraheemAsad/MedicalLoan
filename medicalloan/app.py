"""``MedicalEquipmentApp`` orchestrator.

Phase 3 of the improvement plan slimmed this class down from a
~2,900-line god object that owned every screen into a thin
orchestrator that:

* opens the database connection (and runs the on-launch backup),
* loads ``config.ini`` + per-language icons,
* configures ttk styles via :mod:`medicalloan.ui.styles`,
* owns the persistent ``StringVar`` state shared between views
  (search boxes that survive language toggles, the in-flight new-loan
  form, etc.),
* exposes ``show_<view>`` methods that simply forward to the matching
  module under :mod:`medicalloan.ui.views`,
* delegates Excel export/import to :mod:`medicalloan.ui.views.data_io`.

The ``main()`` function at the bottom configures logging next to the
DB (B9), installs an excepthook that pops a "Critical Error" message
on uncaught exceptions, then enters the Tk mainloop.

Behaviour is intentionally identical to the legacy ``main.py``; this
PR is pure restructuring. Sub-views read state via ``app.<attr>`` and
navigate via ``app.show_<other>()`` so the dispatch graph stays
explicit.
"""

from __future__ import annotations

import configparser
import logging
import os
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from database import Database
from medicalloan.i18n import I18N_STRINGS
from medicalloan.ui import styles, validators
from medicalloan.ui.views import (
    borrowers as borrowers_view,
)
from medicalloan.ui.views import (
    dashboard as dashboard_view,
)
from medicalloan.ui.views import (
    data_io,
)
from medicalloan.ui.views import (
    inventory as inventory_view,
)
from medicalloan.ui.views import (
    new_loan as new_loan_view,
)
from medicalloan.ui.views import (
    process_return as process_return_view,
)
from medicalloan.ui.views import (
    reports as reports_view,
)
from reports import ReportGenerator

log = logging.getLogger(__name__)

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    print("Warning: Pillow library not found. Icon resizing will be basic.")
    print("For better icon resizing, please install Pillow: pip install Pillow")
    PIL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Resource path helper
# ---------------------------------------------------------------------------

def resource_path(relative_path: str) -> str:
    """Return an absolute path to a bundled resource.

    Works in both dev mode (running ``python main.py`` from the repo
    root) and PyInstaller-packaged builds (where ``sys._MEIPASS``
    points at the unpacked temp dir).
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ---------------------------------------------------------------------------
# MedicalEquipmentApp
# ---------------------------------------------------------------------------

# Resolution order for the dashboard "Excel Export / Import" button stays
# hardcoded -- the legacy main.py never localised it. We could move it
# into i18n in a follow-up, but that's out of scope for this PR.

# Bounds for the global font-size +/- controls.
_MIN_FONT_SIZE = 9
_MAX_FONT_SIZE = 24
_DEFAULT_FONT_SIZE = 14
_DEFAULT_LANG = 'he'


class MedicalEquipmentApp:
    """Top-level Tk application.

    The class is small on purpose. Per-screen rendering lives in
    :mod:`medicalloan.ui.views.*`; the dispatch methods on this class
    are deliberately one-liners so the navigation graph reads at a
    glance.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root

        # --- Data layer + reports ---------------------------------------
        self.db = Database()
        self.perform_backup()
        self.load_configuration()
        self.reports = ReportGenerator(config=self.config)

        # --- Theme + persistent UI state --------------------------------
        self.current_theme: str = 'light'

        # Persistent ``StringVar``s so search/form text survives
        # language and font-size changes (each of which destroys and
        # rebuilds the whole view tree).
        self.search_vars: dict[str, tk.StringVar] = {
            'inventory': tk.StringVar(),
            'loan_step1': tk.StringVar(),
            'loan_step2': tk.StringVar(),
            'return': tk.StringVar(),
            'borrowers': tk.StringVar(),
        }
        self.form_vars: dict[str, tk.StringVar] = {
            'name': tk.StringVar(),
            'id': tk.StringVar(),
            'phone1': tk.StringVar(),
            'phone2': tk.StringVar(),
            'address': tk.StringVar(),
            'deposit': tk.StringVar(),
            'donation': tk.StringVar(),
        }

        # --- Live font objects (font-size controls mutate these in
        # place so all widgets follow without rebuilding styles).
        self.base_font_size: int = _DEFAULT_FONT_SIZE
        self.ui_font = tkfont.Font(family="Helvetica", size=self.base_font_size)
        self.input_font = tkfont.Font(
            family="Helvetica", size=self.base_font_size + 2,
        )

        # --- Language settings ------------------------------------------
        self.lang: str = _DEFAULT_LANG
        self.is_rtl: bool = self.lang in ('he', 'ar')
        # Views still read ``app.i18n[app.lang][key]``; keep that
        # access pattern working unchanged.
        self.i18n: dict = I18N_STRINGS

        self.root.title(self.i18n[self.lang]['window_title'])
        try:
            icon_path = resource_path(os.path.join('Icons', 'app_icon.ico'))
            self.root.iconbitmap(icon_path)
        except tk.TclError:
            pass  # Use the default Tk icon if the .ico isn't present.
        self.root.geometry("1200x700")

        # --- Icons + styles --------------------------------------------
        self.load_icons()
        self.setup_styles(self.base_font_size)

        # --- Main frame + first view -----------------------------------
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True)
        self.show_dashboard()

        # --- Validators (registered once per app) ----------------------
        self.vcmd_numbers = (
            self.root.register(validators.numbers_only), '%P',
        )
        self.vcmd_id = (
            self.root.register(validators.id_input), '%P',
        )

        # --- Clean shutdown (B15) --------------------------------------
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _on_close(self) -> None:
        """Close the DB cleanly (WAL checkpoint included) on quit."""
        try:
            self.db.close()
        except Exception:
            log.exception("Error closing database on shutdown")
        self.root.destroy()

    def perform_backup(self) -> None:
        """Run the on-launch backup. Phase 2 (B8) added cadence + retention."""
        from services.backup_service import perform_backup as _do_backup
        try:
            _do_backup(self.db.db_path)
        except Exception:
            log.exception("Database backup failed")

    def load_configuration(self) -> None:
        """Load ``config.ini`` (next to the DB), seeding a default if absent."""
        self.config = configparser.ConfigParser()

        config_path = os.path.join(os.path.dirname(self.db.db_path), 'config.ini')

        if not os.path.exists(config_path):
            self.config['General'] = {
                'institution_name': 'Medical Loan Center',
            }
            self.config['PDF_Terms'] = {
                'term1': '1. The borrower agrees to return the equipment in good condition.',
                'term2': '2. The deposit will be refunded upon return.',
                'term3': '3. The borrower is responsible for damages.',
                'term4': '4. Equipment must be returned on time.',
            }
            with open(config_path, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        else:
            self.config.read(config_path, encoding='utf-8')

    # ------------------------------------------------------------------
    # Icons
    # ------------------------------------------------------------------
    def load_icons(self) -> None:
        """(Re)load every PNG icon, applying dark-mode inversion if needed.

        Each icon is stored as ``self.icon_<key>`` so view modules can
        reference them directly (e.g. ``app.icon_new_loan``). On a
        load failure the corresponding attribute is set to ``None`` so
        ``ttk.Button(image=None, ...)`` still renders (just without an
        image).
        """
        icon_path = resource_path('Icons')

        icon_map = {
            'new_loan': 'NewLoan.png',
            'process_return': 'ReturnProcess.png',
            'search_inventory': 'SearchInventory.png',
            'manage_borrowers': 'ManageBorrowers.png',
            'generate_reports': 'GenerateReports.png',
            'flag_en': 'flag_en.png',
            'flag_he': 'flag_he.png',
            'flag_ar': 'flag_ar.png',
        }

        main_icon_size = (24, 24)
        flag_icon_size = (24, 16)

        try:
            from PIL import ImageOps
        except ImportError:
            ImageOps = None  # type: ignore[assignment]

        for icon_attr, filename in icon_map.items():
            full_path = os.path.join(icon_path, filename)
            try:
                if PIL_AVAILABLE:
                    img = Image.open(full_path)
                    if 'flag' in icon_attr:
                        img = img.resize(flag_icon_size, Image.Resampling.LANCZOS)
                    else:
                        img = img.resize(main_icon_size, Image.Resampling.LANCZOS)
                        # Invert non-flag icons in dark mode so dark
                        # glyphs stay visible against the dark
                        # background.
                        if self.current_theme == 'dark' and ImageOps:
                            if img.mode == 'RGBA':
                                r, g, b, a = img.split()
                                rgb_image = Image.merge('RGB', (r, g, b))
                                inverted_image = ImageOps.invert(rgb_image)
                                r2, g2, b2 = inverted_image.split()
                                img = Image.merge('RGBA', (r2, g2, b2, a))
                            else:
                                img = ImageOps.invert(img)

                    tk_image = ImageTk.PhotoImage(img)
                    setattr(self, f'icon_{icon_attr}', tk_image)
                else:
                    img = tk.PhotoImage(file=full_path)
                    setattr(self, f'icon_{icon_attr}', img)
            except Exception as e:
                log.warning("Error loading icon %s: %s", filename, e)
                setattr(self, f'icon_{icon_attr}', None)

    # ------------------------------------------------------------------
    # Styles + theme
    # ------------------------------------------------------------------
    def setup_styles(self, base_size: int = _DEFAULT_FONT_SIZE) -> None:
        """Apply the current theme via :mod:`medicalloan.ui.styles`."""
        styles.apply_theme(
            self.root,
            self.current_theme,
            ui_font=self.ui_font,
            input_font=self.input_font,
            base_size=base_size,
        )

    def toggle_theme(self, current_view_callback) -> None:
        """Flip light <-> dark, reload icons + styles, refresh the view."""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.load_icons()
        self.setup_styles(self.base_font_size)
        current_view_callback()

    # ------------------------------------------------------------------
    # Window helpers
    # ------------------------------------------------------------------
    def clear_window(self) -> None:
        """Destroy every widget inside ``main_frame``. Used by every view."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_global_controls(self, parent_frame, current_view_callback) -> None:
        """Render the per-screen language / font-size / theme bar at the top.

        ``current_view_callback`` is the no-arg function the bar uses
        to redraw the current screen after a setting changes -- views
        pass ``lambda: show(app)`` so the same screen rebuilds.
        """
        is_rtl = self.is_rtl

        controls_frame = ttk.Frame(parent_frame)
        controls_frame.pack(fill='x', pady=5, padx=10)

        # --- Language selector ------------------------------------------
        lang_frame = ttk.Frame(controls_frame)
        lang_frame.pack(side='right' if not is_rtl else 'left')

        def set_lang(new_lang: str) -> None:
            self.lang = new_lang
            self.is_rtl = self.lang in ('he', 'ar')
            self.root.title(self.i18n[self.lang]['window_title'])
            self.setup_styles(self.base_font_size)
            current_view_callback()

        ttk.Button(
            lang_frame, text="EN", image=self.icon_flag_en,
            command=lambda: set_lang('en'),
        ).pack(side='left', padx=3)
        ttk.Button(
            lang_frame, text="HE", image=self.icon_flag_he,
            command=lambda: set_lang('he'),
        ).pack(side='left', padx=3)
        ttk.Button(
            lang_frame, text="AR", image=self.icon_flag_ar,
            command=lambda: set_lang('ar'),
        ).pack(side='left', padx=3)

        # --- Left-side controls (font-size + theme) ---------------------
        left_controls = ttk.Frame(controls_frame)
        left_controls.pack(side='left' if not is_rtl else 'right')

        ttk.Label(
            left_controls,
            text=f"{self.i18n[self.lang]['font_size']}:",
        ).pack(side='left', padx=2)

        ttk.Button(
            left_controls, text="-", style='Font.TButton', width=2,
            command=lambda: self.adjust_font_size(-1, current_view_callback),
        ).pack(side='left', padx=1)
        ttk.Button(
            left_controls, text="+", style='Font.TButton', width=2,
            command=lambda: self.adjust_font_size(1, current_view_callback),
        ).pack(side='left', padx=1)

        ttk.Label(left_controls, text="|").pack(side='left', padx=10)

        # Theme toggle. The trailing space on "🌙  Dark Mode" lines the
        # text up with the wider sun emoji; preserved verbatim.
        if self.current_theme == 'light':
            theme_text = "🌙  Dark Mode"
        else:
            theme_text = "☀️  Light Mode"

        ttk.Button(
            left_controls, text=theme_text, style='Font.TButton',
            command=lambda: self.toggle_theme(current_view_callback),
        ).pack(side='left', padx=5)

    def adjust_font_size(self, amount: int, current_view_callback) -> None:
        """Bump the live font objects by ``amount``, clamp, redraw view.

        Mutating the existing :class:`tkfont.Font` objects in place
        causes every widget that uses them to resize without us
        rebuilding the style table; we only re-run :func:`setup_styles`
        afterwards so the *padding* recomputes (it scales with
        ``base_size``).
        """
        new_size = max(_MIN_FONT_SIZE, min(_MAX_FONT_SIZE, self.base_font_size + amount))

        if new_size == self.base_font_size:
            return

        self.base_font_size = new_size
        self.ui_font.configure(size=new_size)
        self.input_font.configure(size=new_size + 2)
        self.setup_styles(self.base_font_size)
        current_view_callback()

    # ------------------------------------------------------------------
    # Navigation -- thin wrappers around the per-view ``show(app)`` fns
    # ------------------------------------------------------------------
    def show_dashboard(self) -> None:
        dashboard_view.show(self)

    def show_inventory(self) -> None:
        inventory_view.show(self)

    def show_new_loan(self) -> None:
        new_loan_view.show(self)

    def show_process_return(self) -> None:
        process_return_view.show(self)

    def show_borrowers(self) -> None:
        borrowers_view.show(self)

    def show_reports(self) -> None:
        reports_view.show(self)

    # ------------------------------------------------------------------
    # Data IO -- delegate to the views.data_io module
    # ------------------------------------------------------------------
    def export_to_excel(self) -> None:
        data_io.export_to_excel(self)

    def import_from_excel(self) -> None:
        data_io.import_from_excel(self)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Launch the Tk application.

    Configures logging next to the database (B9 fix), installs an
    ``excepthook`` that surfaces uncaught exceptions to both the log
    *and* a "Critical Error" message box, then runs the mainloop.
    """
    from paths import default_db_path, log_file_path

    log_path = log_file_path(default_db_path())
    logging.basicConfig(
        filename=log_path,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback),
        )
        messagebox.showerror(
            "Critical Error",
            f"An error occurred. See {log_path}.\n\n{exc_value}",
        )

    sys.excepthook = handle_exception

    root = tk.Tk()
    MedicalEquipmentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
