"""ttk theme palette and style configuration.

Phase 3 of the improvement plan extracted this module out of the
``MedicalEquipmentApp.setup_styles`` method. The styles produced here
are byte-identical to what the original method produced -- only the
plumbing changed (palette dicts pulled out as module constants,
``apply_theme`` takes ``root``/``ui_font``/``input_font``/``base_size``
as explicit arguments instead of reading them off ``self``).

Two themes are exposed: ``"light"`` (standard enterprise blue/grey)
and ``"dark"`` (Google-style neutral black/grey).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# --- Theme palettes ---------------------------------------------------------

LIGHT_THEME: dict[str, str] = {
    'bg': "#F0F2F5",        # Light Grey
    'fg': "#202124",        # Near Black text
    'primary': "#1f4788",   # Brand Blue
    'accent': "#3498DB",    # Bright Blue
    'input_bg': "#FFFFFF",  # White Inputs
    'input_fg': "#202124",
    'btn_bg': "#FFFFFF",
    'btn_border': "#DADCE0",   # Google-style border
    'header_bg': "#1f4788",    # Dark Blue Header
    'header_fg': "#FFFFFF",
    'subtext': "#5f6368",      # Google Grey text
}

DARK_THEME: dict[str, str] = {
    'bg': "#202124",        # Main Background (Dark Grey/Black)
    'fg': "#E8EAED",        # High contrast light grey text
    'primary': "#8AB4F8",   # Google Blue (Desaturated)
    'accent': "#8AB4F8",    # Same blue for consistency
    'input_bg': "#303134",  # Lighter grey for Inputs
    'input_fg': "#E8EAED",  # White text
    'btn_bg': "#303134",    # Button matches input
    'btn_border': "#5f6368",   # Subtle border
    'header_bg': "#3c4043",    # DISTINCT Header (Lighter than bg)
    'header_fg': "#E8EAED",
    'subtext': "#9AA0A6",      # Subtitles
}

PALETTES: dict[str, dict[str, str]] = {
    'light': LIGHT_THEME,
    'dark': DARK_THEME,
}


def palette_for(theme_name: str) -> dict[str, str]:
    """Return the colour dict for ``theme_name``; falls back to light."""
    return PALETTES.get(theme_name, LIGHT_THEME)


# --- apply_theme ------------------------------------------------------------

def apply_theme(
    root: tk.Misc,
    theme_name: str,
    *,
    ui_font: tkfont.Font,
    input_font: tkfont.Font,
    base_size: int = 14,
) -> None:
    """Configure ttk styles for the given theme.

    Parameters mirror the per-instance state the legacy
    ``MedicalEquipmentApp.setup_styles`` used to read off ``self``:
    ``root`` is the Tk root (so we can repaint its background),
    ``ui_font``/``input_font`` are the live ``tkfont.Font`` objects
    whose size has already been bumped by the caller for font-size
    controls, and ``base_size`` is the integer used to derive padding
    + heading sizes.

    The style names this function defines are the public contract that
    the per-screen views still rely on:

    * ``TFrame`` / ``TLabel`` / ``TLabelFrame`` / ``TLabelFrame.Label``
    * ``TButton`` / ``Action.TButton`` / ``Large.TButton`` / ``Font.TButton``
    * ``TEntry`` / ``Right.TEntry``
    * ``Treeview`` / ``Treeview.Heading``
    * ``Title.TLabel`` / ``Subtitle.TLabel`` / ``Normal.TLabel``
      / ``Medium.TLabel`` / ``Small.TLabel``
    * RTL variants: ``Right.TLabel``, ``Right.Subtitle.TLabel``,
      ``Right.Medium.TLabel``, ``Right.Small.TLabel``
    """
    style = ttk.Style()
    style.theme_use('clam')

    is_dark = theme_name == 'dark'
    colors = palette_for(theme_name)

    # --- Apply global settings ---
    root.configure(bg=colors['bg'])

    style.configure(
        '.',
        background=colors['bg'],
        foreground=colors['fg'],
        font=ui_font,
    )

    # --- Frames & labels ---
    style.configure('TFrame', background=colors['bg'])
    style.configure(
        'TLabel',
        background=colors['bg'],
        foreground=colors['fg'],
    )

    style.configure(
        'TLabelFrame',
        background=colors['bg'],
        foreground=colors['primary'],
        bordercolor=colors['btn_border'],
        borderwidth=1,
    )
    style.configure(
        'TLabelFrame.Label',
        font=('Helvetica', base_size, 'bold'),
        background=colors['bg'],
        foreground=colors['primary'],
    )

    # --- Buttons ---
    pad_btn = int(base_size * 0.5)

    style.configure(
        'TButton',
        font=ui_font,
        padding=pad_btn,
        background=colors['btn_bg'],
        foreground=colors['fg'],
        bordercolor=colors['btn_border'],
        relief="flat",
        borderwidth=1,
    )
    style.map(
        'TButton',
        background=[('active', colors['btn_border'])],
        foreground=[('active', colors['fg'])],
    )

    # Action Button (Primary). In dark mode we use a desaturated blue
    # *and* dark text on top, because the original UI did.
    style.configure(
        'Action.TButton',
        font=('Helvetica', base_size, 'bold'),
        padding=10,
        background=colors['accent'] if is_dark else colors['primary'],
        foreground="#202124" if is_dark else "#FFFFFF",
        bordercolor=colors['accent'],
        relief="flat",
        borderwidth=0,
    )
    style.map(
        'Action.TButton',
        background=[('active', colors['fg'] if is_dark else colors['accent'])],
    )

    # Large Dashboard Buttons
    style.configure(
        'Large.TButton',
        font=('Helvetica', base_size + 2),
        padding=20,
        background=colors['btn_bg'],
        foreground=colors['fg'] if is_dark else colors['primary'],
        bordercolor=colors['btn_border'],
        relief="flat",
        borderwidth=1,
    )

    # --- Inputs ---
    input_size = input_font.cget("size")
    pad_input = int(input_size * 0.4)

    style.configure(
        'TEntry',
        font=input_font,
        padding=pad_input,
        fieldbackground=colors['input_bg'],
        foreground=colors['input_fg'],
        bordercolor=colors['btn_border'],
        relief="flat",
        borderwidth=1,
        insertcolor=colors['fg'],
    )
    style.configure(
        'Right.TEntry',
        font=input_font,
        padding=pad_input,
        justify='right',
        fieldbackground=colors['input_bg'],
        foreground=colors['input_fg'],
        bordercolor=colors['btn_border'],
        relief="flat",
        borderwidth=1,
        insertcolor=colors['fg'],
    )

    # --- Treeview (Table) ---
    style.configure(
        'Treeview',
        font=ui_font,
        rowheight=int(base_size * 2.8),
        background=colors['bg'],
        fieldbackground=colors['bg'],
        foreground=colors['fg'],
        borderwidth=0,
    )
    style.configure(
        'Treeview.Heading',
        font=('Helvetica', base_size, 'bold'),
        background=colors['header_bg'],
        foreground=colors['header_fg'],
        borderwidth=0,
        relief="flat",
    )
    style.map(
        'Treeview.Heading',
        background=[('active', colors['btn_border'])],
    )

    # --- Text & titles ---
    style.configure(
        'Title.TLabel',
        font=('Helvetica', base_size + 10, 'bold'),
        foreground=colors['primary'],
    )
    style.configure(
        'Subtitle.TLabel',
        font=('Helvetica', base_size + 2, 'bold'),
        foreground=colors['subtext'],
    )
    style.configure('Normal.TLabel', font=ui_font)
    style.configure('Medium.TLabel', font=('Helvetica', base_size + 1))
    style.configure(
        'Small.TLabel',
        font=('Helvetica', base_size - 2),
        foreground=colors['subtext'],
    )

    # RTL specifics
    style.configure('Right.TLabel', font=ui_font, anchor='e')
    style.configure(
        'Right.Subtitle.TLabel',
        font=('Helvetica', base_size + 2, 'bold'),
        anchor='e',
        foreground=colors['subtext'],
    )
    style.configure('Right.Medium.TLabel', font=('Helvetica', base_size + 1), anchor='e')
    style.configure(
        'Right.Small.TLabel',
        font=('Helvetica', base_size - 2),
        foreground=colors['subtext'],
        anchor='e',
    )

    style.configure('Font.TButton', font=('Helvetica', 10, 'bold'))
