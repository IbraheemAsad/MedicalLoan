"""
Reports module for Medical Equipment Loan Management System
Handles PDF generation for loan agreements and reports
"""

import os
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# --- RTL Support ---
# This module requires the python-bidi library for RTL text processing
# Please install it using: pip install python-bidi
# --- RTL Support ---
# This module requires python-bidi and arabic-reshaper

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    import bidi.algorithm
    BIDI_AVAILABLE = True
except ImportError:
    print("WARNING: 'python-bidi' library not found.")
    BIDI_AVAILABLE = False

try:
    import arabic_reshaper
    RESHAPER_AVAILABLE = True
except ImportError:
    print("WARNING: 'arabic-reshaper' library not found. Arabic letters will be disjointed.")
    RESHAPER_AVAILABLE = False
# ---
# ---

# --- i18n Strings for Reports ---
REPORT_STRINGS = {
    'en': {
        'agreement_title': "Medical Equipment Loan Agreement",
        'date': "Date",
        'loan_id': "Loan ID",
        'borrower_info': "Borrower Information",
        'name': "Name",
        'id_number': "ID Number",
        'primary_phone': "Primary Phone",
        'secondary_phone': "Secondary Phone",
        'address': "Address",
        'equipment_info': "Equipment Information",
        'equipment_name': "Equipment Name",
        'serial_number': "Serial Number",
        'description': "Description",
        'financial_info': "Financial Information",
        'deposit_amount': "Deposit Amount",
        'donation': "Donation",
        'terms_title': "Terms and Conditions",
        'term1': "1. The borrower agrees to return the equipment in good condition.",
        'term2': "2. The deposit will be refunded upon return of the equipment.",
        'term3': "3. The borrower is responsible for any damage to the equipment.",
        'term4': "4. The equipment must be returned within a reasonable timeframe.",
        'borrower_sig': "Borrower Signature",
        'staff_sig': "Staff Signature",
        'footer1': "Thank you for using our medical equipment loan service",
        'footer2': "",
        'inventory_report_title': "Full Inventory Report",
        'generated_on': "Generated on",
        'header_eq_name': "Equipment Name",
        'header_total': "Total",
        'header_in_stock': "In Stock",
        'header_on_loan': "On Loan",
        'header_deposit': "Deposit",
        'total_row': "TOTAL",
        'loans_report_title': "Equipment on Loan Report",
        'total_active_loans': "Total Active Loans",
        'no_active_loans': "No active loans at this time.",
        'header_serial': "Serial No.",
        'header_borrower': "Borrower",
        'header_phone': "Phone",
        'header_loan_date': "Loan Date",
        'header_not_returned': "Not Returned",
        'header_lost': "Lost/Retired",
        'lost_report_title': "Lost / Retired Equipment",
        'header_date_added': "Date Added",
    },
    'he': {
        'agreement_title': "הסכם השאלת ציוד רפואי",
        'date': "תאריך",
        'loan_id': "מספר השאלה",
        'borrower_info': "פרטי השואל",
        'name': "שם",
        'id_number': "תעודת זהות",
        'primary_phone': "טלפון ראשי",
        'secondary_phone': "טלפון משני",
        'address': "כתובת",
        'equipment_info': "פרטי הציוד",
        'equipment_name': "שם הציוד",
        'serial_number': "מספר סידורי",
        'description': "תיאור",
        'financial_info': "פרטים כספיים",
        'deposit_amount': "פיקדון",
        'donation': "תרומה",
        'terms_title': "תנאים",
        'term1': "1. השואל מתחייב להחזיר את הציוד במצב תקין.",
        'term2': "2. הפיקדון יוחזר עם החזרת הציוד.",
        'term3': "3. השואל אחראי לכל נזק שייגרם לציוד.",
        'term4': "4. יש להחזיר את הציוד תוך זמן סביר.",
        'borrower_sig': "חתימת השואל",
        'staff_sig': "חתימת הצוות",
        'footer1': "תודה על השימוש בשירות השאלת הציוד הרפואי שלנו",
        'footer2': "",
        'inventory_report_title': "דוח מלאי מלא",
        'generated_on': "הופק בתאריך",
        'header_eq_name': "שם ציוד",
        'header_total': "סה\"כ",
        'header_in_stock': "במלאי",
        'header_on_loan': "בהשאלה",
        'header_deposit': "פיקדון",
        'total_row': "סה\"כ",
        'loans_report_title': "דוח ציוד בהשאלה",
        'total_active_loans': "סה\"כ השאלות פעילות",
        'no_active_loans': "אין השאלות פעילות כרגע.",
        'header_serial': "מספר סידורי",
        'header_borrower': "שואל",
        'header_phone': "טלפון",
        'header_loan_date': "תאריך השאלה",
        'header_not_returned': "לא הוחזר",
        'header_lost': "אבד/יצא משימוש",
        'lost_report_title': "ציוד שאבד / יצא משימוש",
        'header_date_added': "תאריך הוספה",
    },
    'ar': {
        'agreement_title': "اتفاقية إعارة معدات طبية",
        'date': "التاريخ",
        'loan_id': "رقم الإعارة",
        'borrower_info': "بيانات المستعير",
        'name': "الاسم",
        'id_number': "رقم الهوية",
        'primary_phone': "الهاتف الأساسي",
        'secondary_phone': "هاتف ثانوي",
        'address': "العنوان",
        'equipment_info': "بيانات المعدات",
        'equipment_name': "اسم المعدة",
        'serial_number': "الرقم التسلسلي",
        'description': "الوصف",
        'financial_info': "بيانات مالية",
        'deposit_amount': "مبلغ التأمين",
        'donation': "تبرع",
        'terms_title': "الشروط والأحكام",
        'term1': "1. يوافق المستعير على إعادة المعدات بحالة جيدة.",
        'term2': "2. سيتم رد مبلغ التأمين عند إعادة المعدات.",
        'term3': "3. المستعير مسؤول عن أي ضرر يلحق بالمعدات.",
        'term4': "4. يجب إعادة المعدات في غضون فترة زمنية معقولة.",
        'borrower_sig': "توقيع المستعير",
        'staff_sig': "توقيع الموظف",
        'footer1': "شكرًا لاستخدام خدمتنا لإعارة المعدات الطبية",
        'footer2': "",
        'inventory_report_title': "تقرير المخزون الكامل",
        'generated_on': "أُصدر في",
        'header_eq_name': "اسم المعدة",
        'header_total': "المجموع",
        'header_in_stock': "في المخزن",
        'header_on_loan': "مُعارة",
        'header_deposit': "التأمين",
        'total_row': "المجموع",
        'loans_report_title': "تقرير المعدات المُعارة",
        'total_active_loans': "مجموع الإعارات النشطة",
        'no_active_loans': "لا توجد إعارات نشطة حاليًا.",
        'header_serial': "الرقم التسلسلي",
        'header_borrower': "المستعير",
        'header_phone': "الهاتف",
        'header_loan_date': "تاريخ الإعارة",
        'header_not_returned': "لم يُرجع",
        'header_lost': "مفقود/تالف",
        'lost_report_title': "معدات مفقودة / تالفة",
        'header_date_added': "تاريخ الإضافة",
    }
}


class ReportGenerator:
    def __init__(self, output_dir: str = "reports", config=None):
        """Initialize report generator"""
        self.output_dir = output_dir
        self.config = config
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.strings = REPORT_STRINGS

        # --- Font Registration ---
        # We need to register a font that supports Hebrew/Arabic.
        # 'DavidLibre-Regular.ttf' (for Hebrew) and 'NotoSansArabic-Regular.ttf' (for Arabic)
        # are good choices from Google Fonts.
        # We'll use a generic name 'RTL_Font' and try to load fonts.

        self.rtl_font_name = "RTL_Font"
        try:
            # Try loading common system fonts as fallbacks
            # This is not 100% reliable but avoids shipping font files
            hebrew_font = resource_path(os.path.join('fonts', 'DavidLibre-Regular.ttf'))
            arabic_font = resource_path(os.path.join('fonts', 'NotoSansArabic-Regular.ttf'))

            pdfmetrics.registerFont(TTFont('DavidLibre-Regular', hebrew_font))
            pdfmetrics.registerFont(TTFont('NotoSansArabic-Regular', arabic_font))

            pdfmetrics.registerFont(TTFont(self.rtl_font_name, 'DavidLibre-Regular.ttf')) # Default to Hebrew font
            print("Loaded 'DavidLibre-Regular.ttf' and 'NotoSansArabic-Regular.ttf'")
        except Exception as e:
            print(f"Could not load bundled RTL fonts: {e}")
            try:
                # Fallback for Windows
                pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
                self.rtl_font_name = 'Arial'
                print("Using system 'Arial' font.")
            except Exception as e2:
                print(f"Could not load 'arial.ttf' either: {e2}")
                print("WARNING: Could not load RTL fonts ('DavidLibre-Regular.ttf', 'NotoSansArabic-Regular.ttf', or 'arial.ttf').")
                print("Please download 'DavidLibre-Regular.ttf' and 'NotoSansArabic-Regular.ttf' from Google Fonts")
                print("and place them in the application directory for proper RTL support.")
                self.rtl_font_name = "Helvetica" # Last resort fallback

        if self.rtl_font_name == 'Arial':
             pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))

    def _get_strings(self, lang: str):
        """Get string dictionary for the given language"""
        return self.strings.get(lang, self.strings['en'])

    def _bidi(self, text: str):
        """Apply arabic reshaping and bidi algorithm if available"""
        processed_text = text

        # 1. Reshape first: Connects the Arabic letters (Initial/Medial/Final forms)
        if RESHAPER_AVAILABLE:
            try:
                processed_text = arabic_reshaper.reshape(processed_text)
            except Exception:
                pass  # Fail safe if text causes issues

        # 2. Reorder second: Handles Right-to-Left visual ordering
        if BIDI_AVAILABLE:
            return bidi.algorithm.get_display(processed_text)

        return processed_text

    def _get_font_for_lang(self, lang: str):
        """Selects the correct font based on language"""
        # Check specific fonts for Arabic/Hebrew if needed
        if lang == 'ar':
            try:
                pdfmetrics.getFont('NotoSansArabic-Regular')
                return 'NotoSansArabic-Regular'
            except KeyError:
                pass
        elif lang == 'he':
            try:
                pdfmetrics.getFont('DavidLibre-Regular')
                return 'DavidLibre-Regular'
            except KeyError:
                pass

        return self.rtl_font_name

    def generate_loan_agreement(self, loan_data: dict, lang: str = 'en') -> str:
        """
        Generate a loan agreement PDF
        Returns the path to the generated PDF
        """
        s = self._get_strings(lang)
        font_name = self._get_font_for_lang(lang)
        is_rtl = lang in ['he', 'ar']

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"loan_agreement_{loan_data['id']}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        # Create PDF
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter

        # --- Helper for RTL drawing ---
        def draw_string_rtl(x, y, text):
            if is_rtl:
                c.drawRightString(width - x, y, self._bidi(text))
            else:
                c.drawString(x, y, self._bidi(text))

        def draw_centered_string_rtl(y, text_en, text_rtl):
            if is_rtl:
                c.setFont(font_name, 18)
                c.drawCentredString(width / 2, y, self._bidi(text_rtl))
                c.setFont('Helvetica-Bold', 14)
                c.drawCentredString(width / 2, y + 0.3 * inch, text_en)
            else:
                c.setFont('Helvetica-Bold', 18)
                c.drawCentredString(width / 2, y, text_en)

        # Title
        draw_centered_string_rtl(height - 1.3 * inch, s['agreement_title'], s['agreement_title'])

        # Date
        c.setFont(font_name if is_rtl else 'Helvetica', 11)
        loan_date = datetime.strptime(loan_data['loan_date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        draw_string_rtl(1 * inch, height - 2 * inch, f"{s['date']}: {loan_date}")

        # Loan ID
        draw_string_rtl(1 * inch, height - 2.3 * inch, f"{s['loan_id']}: {loan_data['id']}")

        # Line separator
        c.line(1 * inch, height - 2.5 * inch, width - 1 * inch, height - 2.5 * inch)

        # --- Borrower Information ---
        y = height - 3 * inch
        c.setFont(font_name if is_rtl else 'Helvetica-Bold', 13)
        draw_string_rtl(1 * inch, y, s['borrower_info'])

        y -= 0.3 * inch
        c.setFont(font_name if is_rtl else 'Helvetica', 11)
        draw_string_rtl(1 * inch, y, f"{s['name']}: {loan_data['borrower_name']}")

        y -= 0.25 * inch
        draw_string_rtl(1 * inch, y, f"{s['id_number']}: {loan_data['borrower_id_number']}")

        y -= 0.25 * inch
        draw_string_rtl(1 * inch, y, f"{s['primary_phone']}: {loan_data['borrower_phone']}")

        if loan_data.get('borrower_secondary_phone'):
            y -= 0.25 * inch
            draw_string_rtl(1 * inch, y, f"{s['secondary_phone']}: {loan_data['borrower_secondary_phone']}")

        if loan_data.get('borrower_address'):
            y -= 0.25 * inch
            draw_string_rtl(1 * inch, y, f"{s['address']}: {loan_data['borrower_address']}")

        # Line separator
        y -= 0.3 * inch
        c.line(1 * inch, y, width - 1 * inch, y)

        # --- Equipment Information ---
        y -= 0.3 * inch
        c.setFont(font_name if is_rtl else 'Helvetica-Bold', 13)
        draw_string_rtl(1 * inch, y, s['equipment_info'])

        y -= 0.3 * inch
        c.setFont(font_name if is_rtl else 'Helvetica', 11)
        draw_string_rtl(1 * inch, y, f"{s['equipment_name']}: {loan_data['equipment_name']}")

        y -= 0.25 * inch
        draw_string_rtl(1 * inch, y, f"{s['serial_number']}: {loan_data['equipment_serial']}")

        if loan_data.get('equipment_description'):
            y -= 0.25 * inch
            draw_string_rtl(1 * inch, y, f"{s['description']}: {loan_data['equipment_description']}")

        # Line separator
        y -= 0.3 * inch
        c.line(1 * inch, y, width - 1 * inch, y)

        # --- Financial Information ---
        y -= 0.3 * inch
        c.setFont(font_name if is_rtl else 'Helvetica-Bold', 13)
        draw_string_rtl(1 * inch, y, s['financial_info'])

        y -= 0.3 * inch
        c.setFont(font_name if is_rtl else 'Helvetica', 11)
        draw_string_rtl(1 * inch, y, f"{s['deposit_amount']}: ₪{loan_data['deposit_paid']:.2f}")

        if loan_data.get('donation_amount', 0) > 0:
            y -= 0.25 * inch
            draw_string_rtl(1 * inch, y, f"{s['donation']}: ₪{loan_data['donation_amount']:.2f}")

        # --- Terms and Conditions ---
        y -= 0.5 * inch
        c.setFont(font_name if is_rtl else 'Helvetica-Bold', 12)
        draw_string_rtl(1 * inch, y, s['terms_title'])

        y -= 0.3 * inch
        c.setFont(font_name if is_rtl else 'Helvetica', 10)

        # Try to get terms from Config, otherwise fall back to 'en' defaults
        if self.config and 'PDF_Terms' in self.config:
            terms = [
                self.config['PDF_Terms'].get('term1', s['term1']),
                self.config['PDF_Terms'].get('term2', s['term2']),
                self.config['PDF_Terms'].get('term3', s['term3']),
                self.config['PDF_Terms'].get('term4', s['term4'])
            ]
        else:
            terms = [s['term1'], s['term2'], s['term3'], s['term4']]

        for term in terms:
            draw_string_rtl(1.2 * inch, y, self._bidi(term) if is_rtl else term)
            y -= 0.2 * inch

        # --- Signature section ---
        y -= 0.5 * inch
        c.line(1 * inch, y, width - 1 * inch, y)

        y -= 0.4 * inch
        c.setFont(font_name if is_rtl else 'Helvetica', 11)
        draw_string_rtl(1 * inch, y, f"{s['borrower_sig']}: _______________________")
        draw_string_rtl(4.5 * inch, y, f"{s['date']}: _____________")

        y -= 0.4 * inch
        draw_string_rtl(1 * inch, y, f"{s['staff_sig']}: _______________________")
        draw_string_rtl(4.5 * inch, y, f"{s['date']}: _____________")

        # Footer
        c.setFont(font_name if is_rtl else 'Helvetica', 8)
        c.drawCentredString(width / 2, 0.5 * inch, self._bidi(s['footer1']) if is_rtl else s['footer1'])

        c.save()
        return filepath

    def generate_inventory_report(self, equipment_summary: list, lost_items: list, lang: str = 'en') -> str:
        """
        Generate full inventory report with two tables: Active and Lost
        """
        s = self._get_strings(lang)
        font_name = self._get_font_for_lang(lang)
        bold_font_name = font_name
        if font_name == 'Arial':
            bold_font_name = 'Arial-Bold'
        elif font_name == 'Helvetica':
            bold_font_name = 'Helvetica-Bold'

        is_rtl = lang in ['he', 'ar']

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"inventory_report_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # --- TABLE 1: ACTIVE INVENTORY ---

        # Main Title
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontName=font_name,
                                     fontSize=18, textColor=colors.HexColor('#1f4788'),
                                     alignment=TA_CENTER, spaceAfter=20)
        title_text = self._bidi(s['inventory_report_title']) if is_rtl else s['inventory_report_title']
        elements.append(Paragraph(title_text, title_style))

        # Date
        date_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], fontName=font_name,
                                    alignment=TA_LEFT if not is_rtl else TA_RIGHT)
        date_para_text = f"{s['generated_on']}: {date_str}"
        elements.append(Paragraph(self._bidi(date_para_text) if is_rtl else date_para_text, date_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Headers for Table 1
        headers = [s['header_eq_name'], s['header_total'], s['header_in_stock'], s['header_on_loan']]
        if is_rtl: headers = [self._bidi(h) for h in headers][::-1]

        data = [headers]

        # Totals for calculation
        t_items = t_stock = t_loan = 0

        for item in equipment_summary:
            row = [
                self._bidi(item['item_name']),
                str(item['total_count']),
                str(item['in_stock']),
                str(item['on_loan'])
            ]
            if is_rtl: row.reverse()
            data.append(row)
            t_items += item['total_count']
            t_stock += item['in_stock']
            t_loan += item['on_loan']

        # Totals Row
        total_row = [self._bidi(s['total_row']) if is_rtl else s['total_row'],
                     str(t_items), str(t_stock), str(t_loan)]
        if is_rtl: total_row.reverse()
        data.append(total_row)

        # Draw Table 1
        t1 = Table(data, colWidths=[3.5 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d9e2f3')),  # Total row color
            ('FONTNAME', (0, -1), (-1, -1), bold_font_name),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 0.5 * inch))

        # --- TABLE 2: LOST ITEMS ---

        if lost_items:
            # Subtitle
            sub_style = ParagraphStyle('SubTitle', parent=styles['Heading2'], fontName=font_name,
                                       fontSize=14, textColor=colors.firebrick,
                                       alignment=TA_LEFT if not is_rtl else TA_RIGHT, spaceAfter=10)
            sub_text = self._bidi(s['lost_report_title']) if is_rtl else s['lost_report_title']
            elements.append(Paragraph(sub_text, sub_style))

            # Headers for Table 2
            headers_lost = [s['header_eq_name'], s['header_serial'], s['header_date_added']]
            if is_rtl: headers_lost = [self._bidi(h) for h in headers_lost][::-1]

            data_lost = [headers_lost]

            for item in lost_items:
                # Try to parse date, handle errors if format varies
                try:
                    created_date = item['created_date'].split(' ')[0]  # Just the YYYY-MM-DD part
                except (AttributeError, IndexError, TypeError):
                    created_date = item['created_date']

                row = [
                    self._bidi(item['item_name']),
                    item['serial_number'],
                    created_date
                ]
                if is_rtl: row.reverse()
                data_lost.append(row)

            # Draw Table 2
            t2 = Table(data_lost, colWidths=[3.5 * inch, 2 * inch, 1.7 * inch])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.firebrick),  # Red header for lost
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(t2)

        doc.build(elements)
        return filepath

    def generate_loans_report(self, active_loans: list, lang: str = 'en') -> str:
        """
        Generate equipment on loan report PDF
        Returns the path to the generated PDF
        """
        s = self._get_strings(lang)
        font_name = self._get_font_for_lang(lang)
        bold_font_name = font_name
        if font_name == 'Arial':
            bold_font_name = 'Arial-Bold'
        elif font_name == 'Helvetica':
            bold_font_name = 'Helvetica-Bold'

        is_rtl = lang in ['he', 'ar']

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"loans_report_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        title_text = self._bidi(s['loans_report_title']) if is_rtl else s['loans_report_title']
        title = Paragraph(title_text, title_style)
        elements.append(title)

        # Date
        date_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], fontName=font_name, alignment=TA_LEFT if not is_rtl else TA_RIGHT)
        date_para_text = f"{s['generated_on']}: {date_str}"
        date_para = Paragraph(self._bidi(date_para_text) if is_rtl else date_para_text, date_style)
        elements.append(date_para)
        elements.append(Spacer(1, 0.2 * inch))

        # Summary
        summary_style = ParagraphStyle('SummaryStyle', parent=styles['Normal'], fontName=font_name, alignment=TA_LEFT if not is_rtl else TA_RIGHT)
        summary_text = f"{s['total_active_loans']}: {len(active_loans)}"
        summary_para = Paragraph(self._bidi(summary_text) if is_rtl else f"<b>{summary_text}</b>",
                                summary_style)
        elements.append(summary_para)
        elements.append(Spacer(1, 0.3 * inch))

        if not active_loans:
            no_loans_style = ParagraphStyle('NoLoansStyle', parent=styles['Normal'], fontName=font_name, alignment=TA_LEFT if not is_rtl else TA_RIGHT)
            no_loans_para = Paragraph(self._bidi(s['no_active_loans']) if is_rtl else s['no_active_loans'], no_loans_style)
            elements.append(no_loans_para)
        else:
            # Table data
            headers = [s['header_eq_name'], s['header_serial'], s['header_borrower'],
                     s['header_phone'], s['header_loan_date'], s['header_deposit']]

            if is_rtl:
                headers = [self._bidi(h) for h in headers][::-1]

            data = [headers]

            for loan in active_loans:
                loan_date = datetime.strptime(loan['loan_date'],
                                            '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                row = [
                    self._bidi(loan['equipment_name']),
                    loan['equipment_serial'],
                    self._bidi(loan['borrower_name']),
                    loan['borrower_phone'],
                    loan_date,
                    f"₪{loan['deposit_paid']:.0f}"
                ]
                if is_rtl:
                    row.reverse()
                data.append(row)

            # Create table
            table = Table(data, colWidths=[1.5 * inch, 1 * inch, 1.3 * inch,
                                          1 * inch, 0.9 * inch, 0.7 * inch])

            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), bold_font_name),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))

            elements.append(table)

        # Build PDF
        doc.build(elements)
        return filepath

    def open_pdf(self, filepath: str):
        """Open PDF file with default system viewer"""
        import platform
        import subprocess

        system = platform.system()
        try:
            if system == 'Windows':
                os.startfile(filepath)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', filepath])
            else:  # Linux
                subprocess.run(['xdg-open', filepath])
        except Exception as e:
            print(f"Error opening PDF: {e}")
