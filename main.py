"""
Main GUI Application for Medical Equipment Loan Management System
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter import font as tkfont
from datetime import datetime
import pandas as pd
from tkinter import filedialog
import configparser
import sqlite3
import logging
import shutil
import glob
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    print("Warning: Pillow library not found. Icon resizing will be basic.")
    print("For better icon resizing, please install Pillow: pip install Pillow")
    PIL_AVAILABLE = False

# Add parent directory to path for imports

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from reports import ReportGenerator


# ============ Internationalization (i18n) Strings ============

I18N_STRINGS = {
    'en': {
        'window_title': "Medical Equipment Loan Management System",
        'dashboard_title': "Medical Equipment Loan Management",
        'dashboard_subtitle': "Welcome to the loan management system",
        'btn_new_loan': "New Loan (Check-Out)",
        'btn_process_return': "Process Return (Check-In)",
        'btn_search_inventory': "Search Inventory",
        'btn_manage_borrowers': "Manage Borrowers",
        'font_size': "Size",
        'btn_generate_reports': "Generate Reports",
        'inventory_title': "Equipment Inventory",
        'back_to_dashboard': "← Back to Dashboard",
        'search': "Search:",
        'search_btn': "Search",
        'show_all': "Show All",
        'add_new_equipment': "Add New Equipment",
        'col_id': "ID",
        'col_name': "Equipment Name",
        'col_serial': "Serial Number",
        'col_status': "Status",
        'col_deposit': "Deposit (₪)",
        'col_description': "Description",
        'status_values': {
            'In-Stock': 'In-Stock',
            'On-Loan': 'On-Loan',
            'Returned': 'Returned',
            'Not Returned': 'Not Returned',
            'Lost': 'Lost',
            'Active': 'OnLoan'
        },
        'edit_selected': "Edit Selected",
        'view_summary': "View Summary",
        'add_eq_title': "Add New Equipment",
        'eq_name': "Item Name:",
        'eq_desc': "Description:",
        'eq_serial': "Serial Number:",
        'eq_deposit': "Deposit Amount (₪):",
        'save': "Save",
        'cancel': "Cancel",
        'update': "Update",
        'edit_eq_title': "Edit Equipment",
        'warn_select_item': "Please select an equipment item",
        'err_not_found': "Equipment not found",
        'err_required_fields': "Name and Serial Number are required",
        'err_invalid_deposit': "Invalid deposit amount",
        'err_add_fail': "Failed to add equipment: {e}",
        'err_update_fail': "Failed to update equipment: {e}",
        'success_add': "Equipment added successfully",
        'success_update': "Equipment updated successfully",
        'summary_title': "Inventory Summary",
        'col_total': "Total",
        'col_in_stock': "In Stock",
        'col_on_loan': "On Loan",
        'close': "Close",
        'new_loan_title': "New Loan - Step 1: Select Equipment",
        'search_available_eq': "Search Available Equipment:",
        'search_by_name_serial': "Search by name or serial...",
        'search_by_eq_name': "Search by equipment name...",
        'search_by_loan': "Search by borrower name, ID, or equipment...",
        'search_by_borrower': "Search by name, ID, or phone...",
        'show_all_available': "Show All Available",
        'loan_this_item': "Loan This Item →",
        'new_loan_title_step2': "New Loan - Step 2: Borrower & Deposit",
        'back': "← Back",
        'selected_equipment': "Selected Equipment",
        'eq_label': "Equipment: {name}",
        'serial_label': "Serial Number: {serial}",
        'deposit_label': "Required Deposit: ₪{amount:.2f}",
        'search_borrower': "Search for Borrower",
        'search_by_id_phone': "Search by ID Number or Phone...",
        'borrower_not_found': "Borrower not found. Please enter new borrower details below.",
        'borrower_details': "Borrower Details",
        'full_name': "Full Name *:",
        'id_number': "ID Number *:",
        'primary_phone': "Primary Phone *:",
        'secondary_phone': "Secondary Phone:",
        'address': "Address:",
        'financial_details': "Financial Details",
        'deposit_paid': "Deposit Paid (₪) *:",
        'donation': "Donation (₪):",
        'confirm_print': "Confirm & Print Agreement",
        'err_fill_required': "Please fill in all required fields (*)",
        'err_invalid_deposit_donation': "Invalid deposit or donation amount",
        'err_create_loan_fail': "Failed to create loan: {e}",
        'success_loan_created': "Loan created successfully!\nLoan ID: {id}\n\nThe loan agreement has been opened for printing.",
        'warn_agreement_fail': "Loan created but failed to generate agreement: {e}",
        'select_borrower_title': "Select Borrower",
        'found_borrowers': "Found Matching Borrowers",
        'col_num': "#",
        'col_id_num': "ID Number",
        'col_phone': "Phone",
        'col_full_name': "Full Name",
        'col_primary_phone': "Primary Phone",
        'col_secondary_phone': "Secondary Phone",
        'col_address': "Address",
        'select': "Select",
        'warn_select_borrower': "Please select a borrower",
        'return_title': "Process Return (Check-In)",
        'search_active_loans': "Search Active Loans:",
        'show_all_active': "Show All Active",
        'col_loan_id': "Loan ID",
        'col_equipment': "Equipment",
        'col_borrower': "Borrower Name",
        'col_loan_date': "Loan Date",
        'col_not_returned': "Not Returned",
        'col_lost': "Lost/Retired",
        'btn_process_return_action': "Process Return",
        'btn_forfeit_deposit': "Mark as Non-Returned (Forfeit Deposit)",
        'warn_select_loan': "Please select a loan",
        'confirm_return_title': "Confirm Return",
        'confirm_return_msg': "Process return for this loan?\n\nDeposit to return: ₪{amount}",
        'success_return': "Return successful!\n\nPlease return ₪{amount} deposit to the borrower.",
        'err_return_fail': "Failed to process return",
        'err_generic': "Error: {e}",
        'confirm_forfeit_title': "Confirm Forfeiture",
        'confirm_forfeit_msg': "Mark this loan as non-returned?\n\nThis will forfeit the ₪{amount} deposit.\nThis action cannot be undone.",
        'success_forfeit': "Loan marked as non-returned.\nDeposit of ₪{amount} has been forfeited.",
        'err_forfeit_fail': "Failed to process",
        'borrowers_title': "Manage Borrowers",
        'btn_view_history': "View Loan History",
        'history_title': "Loan History - {name}",
        'history_for_label': "Loan History for {name}",
        'col_return_date': "Return Date",
        'reports_title': "Generate Reports",
        'reports_select': "Select a report to generate:",
        'btn_inventory_report': "Full Inventory Report",
        'btn_loans_report': "Equipment on Loan Report",
        'success_report': "Report generated successfully!\n\n{path}",
        'err_report_fail': "Failed to generate report: {e}",
        'delete_selected': "Delete Selected",
        'confirm_delete_title': "Confirm Deletion",
        'confirm_delete_msg': "Are you sure you want to delete '{name}'?\n\nWARNING: This will remove the item and ALL its loan history permanently.",
        'success_delete_msg': "Item deleted successfully.",
        'success_title': "Success",
        'btn_add_borrower': "Add New Borrower",
        'title_add_borrower': "Add New Borrower",
        'success_borrower_add': "Borrower added successfully",
        'err_borrower_exists': "A borrower with this ID Number already exists.",
        'btn_edit_details': "Edit Details",
        'btn_change_borrower': "Change / New",
    },
    'he': {
        'window_title': "מערכת ניהול השאלת ציוד רפואי",
        'dashboard_title': "ניהול השאלת ציוד רפואי",
        'dashboard_subtitle': "ברוכים הבאים למערכת ניהול ההשאלות",
        'btn_new_loan': "השאלה חדשה",
        'btn_process_return': "קבלת החזרה",
        'btn_search_inventory': "חיפוש במלאי",
        'btn_manage_borrowers': "ניהול שואלים",
        'btn_generate_reports': "הפקת דוחות",
        'inventory_title': "מלאי ציוד",
        'back_to_dashboard': "← חזרה למסך הראשי",
        'search': ":חיפוש",
        'font_size': "גודל",
        'search_btn': "חפש",
        'show_all': "הצג הכל",
        'add_new_equipment': "הוספת ציוד חדש",
        'col_id': "מזהה",
        'col_name': "שם ציוד",
        'col_serial': "מספר סידורי",
        'col_status': "סטטוס",
        'col_deposit': "(₪) פיקדון",
        'col_description': "תיאור",
        'status_values': {
            'In-Stock': 'במלאי',
            'On-Loan': 'בהשאלה',
            'Returned': 'הוחזר',
            'Not Returned': 'לא הוחזר',
            'Lost': 'אבד',
            'Active': 'בהשאלה'
        },
        'edit_selected': "עריכת פריט נבחר",
        'view_summary': "צפייה בסיכום",
        'add_eq_title': "הוספת ציוד חדש",
        'eq_name': ":שם פריט",
        'eq_desc': ":תיאור",
        'eq_serial': ":מספר סידורי",
        'eq_deposit': ":(₪) סכום פיקדון",
        'save': "שמור",
        'cancel': "ביטול",
        'update': "עדכן",
        'edit_eq_title': "עריכת ציוד",
        'warn_select_item': "אנא בחר פריט ציוד",
        'err_not_found': "הציוד לא נמצא",
        'err_required_fields': "שם ומספר סידורי הם שדות חובה",
        'err_invalid_deposit': "סכום פיקדון שגוי",
        'err_add_fail': "נכשל בהוספת ציוד: {e}",
        'err_update_fail': "נכשל בעדכון ציוד: {e}",
        'success_add': "הציוד נוסף בהצלחה",
        'success_update': "הציוד עודכן בהצלחה",
        'summary_title': "סיכום מלאי",
        'col_total': "סה\"כ",
        'col_in_stock': "במלאי",
        'col_on_loan': "בהשאלה",
        'close': "סגור",
        'new_loan_title': "השאלה חדשה - שלב 1: בחירת ציוד",
        'search_available_eq': ":חיפוש ציוד זמין",
        'search_by_name_serial': "...חפש לפי שם או מספר סידורי",
        'search_by_eq_name': "...חפש לפי שם ציוד",
        'search_by_loan': "...חפש לפי שם שואל, ת.ז., או ציוד",
        'search_by_borrower': "...חפש לפי שם, ת.ז., או טלפון",
        'show_all_available': "הצג הכל זמין",
        'loan_this_item': "השאל פריט זה →",
        'new_loan_title_step2': "השאלה חדשה - שלב 2: שואל ופיקדון",
        'back': "← חזור",
        'selected_equipment': "ציוד נבחר",
        'eq_label': "ציוד: {name}",
        'serial_label': "מספר סידורי: {serial}",
        'deposit_label': "פיקדון נדרש: ₪{amount:.2f}",
        'search_borrower': "חיפוש שואל",
        'search_by_id_phone': "...חפש לפי ת.ז. או טלפון",
        'borrower_not_found': "השואל לא נמצא. אנא הזן פרטי שואל חדש.",
        'borrower_details': "פרטי השואל",
        'full_name': ":* שם מלא",
        'id_number': ":* מספר ת.ז.",
        'primary_phone': ":* טלפון ראשי",
        'secondary_phone': ":טלפון משני",
        'address': ":כתובת",
        'financial_details': "פרטים כספיים",
        'deposit_paid': ": * (₪) פיקדון ששולם",
        'donation': ":(₪) תרומה",
        'confirm_print': "אישור והדפסת הסכם",
        'err_fill_required': "(*) אנא מלא את כל שדות החובה",
        'err_invalid_deposit_donation': "סכום פיקדון או תרומה שגוי",
        'err_create_loan_fail': "נכשל ביצירת השאלה: {e}",
        'success_loan_created': "השאלה נוצרה בהצלחה!\nמספר השאלה: {id}\n\nהסכם ההשאלה נפתח להדפסה.",
        'warn_agreement_fail': "ההשאלה נוצרה אך יצירת ההסכם נכשלה: {e}",
        'select_borrower_title': "בחר שואל",
        'found_borrowers': "נמצאו שואלים תואמים",
        'col_num': "#",
        'col_id_num': "מספר ת.ז.",
        'col_phone': "טלפון",
        'col_full_name': "שם מלא",
        'col_primary_phone': "טלפון ראשי",
        'col_secondary_phone': "טלפון משני",
        'col_address': "כתובת",
        'select': "בחר",
        'warn_select_borrower': "אנא בחר שואל",
        'return_title': "קבלת החזרה",
        'search_active_loans': ":חיפוש השאלות פעילות",
        'show_all_active': "הצג הכל פעילות",
        'col_loan_id': "מס' השאלה",
        'col_equipment': "ציוד",
        'col_borrower': "שם השואל",
        'col_loan_date': "תאריך השאלה",
        'col_not_returned': "לא הוחזר",
        'col_lost': "אבד",
        'btn_process_return_action': "קבל החזרה",
        'btn_forfeit_deposit': "סמן כלא הוחזר (חילוט פיקדון)",
        'warn_select_loan': "אנא בחר השאלה",
        'confirm_return_title': "אישור החזרה",
        'confirm_return_msg': "האם לקבל החזרה עבור השאלה זו?\n\nפיקדון להחזרה: ₪{amount}",
        'success_return': "ההחזרה בוצעה בהצלחה!\n\nאנא החזר ₪{amount} פיקדון לשואל.",
        'err_return_fail': "נכשל בביצוע ההחזרה",
        'err_generic': "שגיאה: {e}",
        'confirm_forfeit_title': "אישור חילוט",
        'confirm_forfeit_msg': "האם לסמן השאלה זו כלא הוחזרה?\n\nפעולה זו תחלט את הפיקדון בסך ₪{amount}.\nלא ניתן לבטל פעולה זו.",
        'success_forfeit': "ההשאלה סומנה כלא הוחזרה.\nהפיקדון בסך ₪{amount} חולט.",
        'err_forfeit_fail': "נכשל בביצוע הפעולה",
        'borrowers_title': "ניהול שואלים",
        'btn_view_history': "צפה בהיסטוריית השאלות",
        'history_title': "היסטוריית השאלות - {name}",
        'history_for_label': "{name} היסטוריית השאלות עבור",
        'col_return_date': "תאריך החזרה",
        'reports_title': "הפקת דוחות",
        'reports_select': ":בחר דוח להפקה",
        'btn_inventory_report': "דוח מלאי מלא",
        'btn_loans_report': "דוח ציוד בהשאלה",
        'success_report': "הדוח הופק בהצלחה!\n\n{path}",
        'err_report_fail': "נכשל בהפקת הדוח: {e}",
        'delete_selected': "מחק פריט",
        'confirm_delete_title': "אישור מחיקה",
        'confirm_delete_msg': "האם אתה בטוח שברצונך למחוק את '{name}'?\n\nאזהרה: פעולה זו תסיר את הפריט ואת כל היסטוריית ההשאלות שלו לצמיתות.",
        'success_delete_msg': "הפריט נמחק בהצלחה.",
        'success_title': "הצלחה",
        'btn_add_borrower': "הוסף שואל חדש",
        'title_add_borrower': "הוספת שואל חדש",
        'success_borrower_add': "השואל נוסף בהצלחה",
        'err_borrower_exists': ".קיים כבר שואל עם מספר תעודת זהות זה",
        'btn_edit_details': "ערוך פרטים",
        'btn_change_borrower': "החלף / חדש",
    },
    'ar': {
        'window_title': "نظام إدارة إعارة المعدات الطبية",
        'dashboard_title': "إدارة إعارة المعدات الطبية",
        'dashboard_subtitle': "مرحبًا بك في نظام إدارة الإعارات",
        'btn_new_loan': "إعارة جديدة",
        'btn_process_return': "استلام مُرجع",
        'btn_search_inventory': "بحث في المخزون",
        'btn_manage_borrowers': "إدارة المستعيرين",
        'btn_generate_reports': "إصدار تقارير",
        'inventory_title': "مخزون المعدات",
        'back_to_dashboard': "← رجوع إلى اللوحة الرئيسية",
        'search': ":بحث",
        'search_btn': "بحث",
        'show_all': "عرض الكل",
        'add_new_equipment': "إضافة معدات جديدة",
        'col_id': "المعرف",
        'col_name': "اسم المعدة",
        'col_serial': "الرقم التسلسلي",
        'col_status': "الحالة",
        'font_size': "الحجم",
        'col_deposit': "(₪) التأمين",
        'col_description': "الوصف",
        'status_values': {
            'In-Stock': 'في المخزن',
            'On-Loan': 'مُعارة',
            'Returned': 'تم الإرجاع',
            'Not Returned': 'لم يُرجع',
            'Lost': 'مفقود',
            'Active': 'مُعارة'
        },
        'edit_selected': "تعديل المحدد",
        'view_summary': "عرض الملخص",
        'add_eq_title': "إضافة معدات جديدة",
        'eq_name': ":اسم العنصر",
        'eq_desc': ":الوصف",
        'eq_serial': ":الرقم التسلسلي",
        'eq_deposit': ":(₪) مبلغ التأمين",
        'save': "حفظ",
        'cancel': "إلغاء",
        'update': "تحديث",
        'edit_eq_title': "تعديل المعدات",
        'warn_select_item': "يرجى تحديد عنصر معدات",
        'err_not_found': "لم يتم العثور على المعدات",
        'err_required_fields': "الاسم والرقم التسلسلي مطلوبان",
        'err_invalid_deposit': "مبلغ تأمين غير صالح",
        'err_add_fail': "فشل في إضافة المعدات: {e}",
        'err_update_fail': "فشل في تحديث المعدات: {e}",
        'success_add': "تمت إضافة المعدات بنجاح",
        'success_update': "تم تحديث المعدات بنجاح",
        'summary_title': "ملخص المخزون",
        'col_total': "المجموع",
        'col_in_stock': "في المخزن",
        'col_on_loan': "مُعارة",
        'close': "إغلاق",
        'new_loan_title': "إعارة جديدة - خطوة 1: اختيار المعدات",
        'search_available_eq': ":بحث عن معدات متاحة",
        'search_by_name_serial': "...بحث حسب الاسم أو الرقم التسلسلي",
        'search_by_eq_name': "...بحث حسب اسم المعدة",
        'search_by_loan': "...بحث حسب اسم المستعير، الهوية، أو المعدة",
        'search_by_borrower': "...بحث حسب الاسم، الهوية، أو الهاتف",
        'show_all_available': "عرض كل المتاح",
        'loan_this_item': "إعارة هذا العنصر →",
        'new_loan_title_step2': "إعارة جديدة - خطوة 2: المستعير والتأمين",
        'back': "← رجوع",
        'selected_equipment': "المعدات المختارة",
        'eq_label': "المعدة: {name}",
        'serial_label': "الرقم التسلسلي: {serial}",
        'deposit_label': "التأمين المطلوب: ₪{amount:.2f}",
        'search_borrower': "بحث عن مستعير",
        'search_by_id_phone': "...بحث حسب رقم الهوية أو الهاتف",
        'borrower_not_found': "لم يتم العثور على المستعير. يرجى إدخال تفاصيل مستعير جديد.",
        'borrower_details': "تفاصيل المستعير",
        'full_name': ":* الاسم الكامل",
        'id_number': ":* رقم الهوية",
        'primary_phone': ":* الهاتف الأساسي",
        'secondary_phone': ":هاتف ثانوي",
        'address': ":العنوان",
        'financial_details': "تفاصيل مالية",
        'deposit_paid': ":* (₪) التأمين المدفوع",
        'donation': ":(₪) تبرع",
        'confirm_print': "تأكيد وطباعة الاتفاقية",
        'err_fill_required': "(*) يرجى ملء جميع الحقول المطلوبة",
        'err_invalid_deposit_donation': "مبلغ التأمين أو التبرع غير صالح",
        'err_create_loan_fail': "فشل في إنشاء الإعارة: {e}",
        'success_loan_created': "تم إنشاء الإعارة بنجاح!\nرقم الإعارة: {id}\n\nتم فتح اتفاقية الإعارة للطباعة.",
        'warn_agreement_fail': "تم إنشاء الإعارة ولكن فشل إنشاء الاتفاقية: {e}",
        'select_borrower_title': "اختيار مستعير",
        'found_borrowers': "تم العثور على مستعيرين مطابقين",
        'col_num': "#",
        'col_id_num': "رقم الهوية",
        'col_phone': "الهاتف",
        'col_full_name': "الاسم الكامل",
        'col_primary_phone': "الهاتف الأساسي",
        'col_secondary_phone': "هاتف ثانوي",
        'col_address': "العنوان",
        'select': "اختيار",
        'warn_select_borrower': "يرجى اختيار مستعير",
        'return_title': "استلام مُرجع",
        'search_active_loans': ":بحث عن إعارات نشطة",
        'show_all_active': "عرض كل النشطة",
        'col_loan_id': "رقم الإعارة",
        'col_equipment': "المعدة",
        'col_borrower': "اسم المستعير",
        'col_loan_date': "تاريخ الإعارة",
        'col_not_returned': "لم يُرجع",
        'col_lost': "مفقود",
        'btn_process_return_action': "استلام المرجع",
        'btn_forfeit_deposit': "تحديد كـ (لم يُرجع) (مصادرة التأمين)",
        'warn_select_loan': "يرجى تحديد إعارة",
        'confirm_return_title': "تأكيد الإرجاع",
        'confirm_return_msg': "هل تريد استلام هذا المرجع؟\n\nالتأمين المُراد إرجاعه: ₪{amount}",
        'success_return': "تم الإرجاع بنجاح!\n\nيرجى إعادة ₪{amount} كتأمين للمستعير.",
        'err_return_fail': "فشل في معالجة الإرجاع",
        'err_generic': "خطأ: {e}",
        'confirm_forfeit_title': "تأكيد المصادرة",
        'confirm_forfeit_msg': "هل تريد تحديد هذه الإعارة كـ (لم تُرجع)؟\n\nسيؤدي هذا إلى مصادرة التأمين البالغ ₪{amount}.\nلا يمكن التراجع عن هذا الإجراء.",
        'success_forfeit': "تم تحديد الإعارة كـ (لم تُرجع).\nتم مصادرة التأمين البالغ ₪{amount}.",
        'err_forfeit_fail': "فشل في معالجة الإجراء",
        'borrowers_title': "إدارة المستعيرين",
        'btn_view_history': "عرض سجل الإعارات",
        'history_title': "سجل الإعارات - {name}",
        'history_for_label': "{name} سجل الإعارات لـ",
        'col_return_date': "تاريخ الإرجاع",
        'reports_title': "إصدار تقارير",
        'reports_select': ":اختر تقريرًا لإصداره",
        'btn_inventory_report': "تقرير المخزون الكامل",
        'btn_loans_report': "تقرير المعدات المُعارة",
        'success_report': "تم إصدار التقرير بنجاح!\n\n{path}",
        'err_report_fail': "فشل في إصدار التقرير: {e}",
        'delete_selected': "حذف المحدد",
        'confirm_delete_title': "تأكيد الحذف",
        'confirm_delete_msg': "هل أنت متأكد أنك تريد حذف '{name}'؟\n\nتحذير: سيؤدي هذا إلى إزالة العنصر وجميع سجلات إعارته بشكل دائم.",
        'success_delete_msg': "تم حذف العنصر بنجاح.",
        'success_title': "نجاح",
        'btn_add_borrower': "إضافة مستعير جديد",
        'title_add_borrower': "إضافة مستعير جديد",
        'success_borrower_add': "تمت إضافة المستعير بنجاح",
        'err_borrower_exists': "يوجد بالفعل مستعير برقم الهوية هذا.",
        'btn_edit_details': "تعديل البيانات",
        'btn_change_borrower': "تغيير / جديد",
    }
}


class MedicalEquipmentApp:
    def __init__(self, root):
        self.root = root

        # Initialize database and reports
        self.db = Database()
        self.perform_backup()
        self.load_configuration()
        self.reports = ReportGenerator(config=self.config)
        self.current_theme = 'light'
        # ============ PERSISTENT STATE VARIABLES ============
        # These keep your text safe when language/font changes
        self.search_vars = {
            'inventory': tk.StringVar(),
            'loan_step1': tk.StringVar(),
            'loan_step2': tk.StringVar(),
            'return': tk.StringVar(),
            'borrowers': tk.StringVar()
        }
        # Variables for the Step 2 Form (Name, ID, etc.)
        self.form_vars = {
            'name': tk.StringVar(),
            'id': tk.StringVar(),
            'phone1': tk.StringVar(),
            'phone2': tk.StringVar(),
            'address': tk.StringVar(),
            'deposit': tk.StringVar(),
            'donation': tk.StringVar()
        }

        # ============  DYNAMIC FONT OBJECTS  ============
        self.base_font_size = 14
        # Font for UI (Labels, Buttons)
        self.ui_font = tkfont.Font(family="Helvetica", size=self.base_font_size)
        self.input_font = tkfont.Font(family="Helvetica", size=self.base_font_size + 2)

        # Language settings
        self.lang = 'he'  # Default to Hebrew
        self.is_rtl = self.lang in ['he', 'ar']
        self.i18n = I18N_STRINGS

        self.root.title(self.i18n[self.lang]['window_title'])
        try:
            icon_path = resource_path(os.path.join('icons', 'app_icon.ico'))
            self.root.iconbitmap(icon_path)
        except Exception:
            pass  # Use default if missing
        self.root.geometry("1200x700")

        # Load icons
        self.load_icons()

        # Configure style
        self.base_font_size = 14  # Set the default font size
        self.setup_styles(self.base_font_size)

        # Main frame to hold everything
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True)

        # Show main dashboard
        self.show_dashboard()

        # Register the validation functions
        self.vcmd_numbers = (self.root.register(self.validate_numbers_only), '%P')
        self.vcmd_id = (self.root.register(self.validate_id_input), '%P')

    def perform_backup(self):
        """Create a backup of the database on startup"""
        db_path = self.db.db_path
        if not os.path.exists(db_path):
            return

        # Create backups folder if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Create new backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.db"
        shutil.copy2(db_path, os.path.join(backup_dir, backup_name))

        # Cleanup: Keep only the last 5 backups
        backups = sorted(glob.glob(os.path.join(backup_dir, "*.db")))
        while len(backups) > 5:
            os.remove(backups.pop(0))

    def load_icons(self):
        """Load and process icons based on the current theme"""
        icon_path = resource_path('icons')

        icon_map = {
            'new_loan': 'NewLoan.png',
            'process_return': 'ReturnProcess.png',
            'search_inventory': 'SearchInventory.png',
            'manage_borrowers': 'ManageBorrowers.png',
            'generate_reports': 'GenerateReports.png',
            'flag_en': 'flag_en.png',
            'flag_he': 'flag_he.png',
            'flag_ar': 'flag_ar.png'
        }

        main_icon_size = (24, 24)
        flag_icon_size = (24, 16)

        # Import invert if available
        try:
            from PIL import ImageOps
        except ImportError:
            ImageOps = None

        for icon_attr, filename in icon_map.items():
            full_path = os.path.join(icon_path, filename)
            try:
                if PIL_AVAILABLE:
                    img = Image.open(full_path)

                    # Resize first
                    if 'flag' in icon_attr:
                        img = img.resize(flag_icon_size, Image.Resampling.LANCZOS)
                    else:
                        img = img.resize(main_icon_size, Image.Resampling.LANCZOS)

                        # --- COLOR INVERSION FOR DARK MODE ---
                        # Only invert non-flag icons if we are in dark mode
                        if self.current_theme == 'dark' and ImageOps:
                            if img.mode == 'RGBA':
                                r, g, b, a = img.split()
                                rgb_image = Image.merge('RGB', (r, g, b))
                                inverted_image = ImageOps.invert(rgb_image)
                                r2, g2, b2 = inverted_image.split()
                                img = Image.merge('RGBA', (r2, g2, b2, a))
                            else:
                                img = ImageOps.invert(img)
                        # -------------------------------------

                    tk_image = ImageTk.PhotoImage(img)
                    setattr(self, f'icon_{icon_attr}', tk_image)
                else:
                    # Basic fallback without Pillow
                    img = tk.PhotoImage(file=full_path)
                    setattr(self, f'icon_{icon_attr}', img)
            except Exception as e:
                print(f"Error loading icon {filename}: {e}")
                setattr(self, f'icon_{icon_attr}', None)

    def toggle_theme(self, current_view_callback):
        """Switch between light and dark themes"""
        if self.current_theme == 'light':
            self.current_theme = 'dark'
        else:
            self.current_theme = 'light'

        # 1. Reload icons (so they turn white/black)
        self.load_icons()

        # 2. Re-apply styles
        self.setup_styles(self.base_font_size)

        # 3. Refresh the current view
        current_view_callback()

    def setup_dialog_window(self, dialog, min_width=400):
        """
        1. Makes the window Modal (blocks main app).
        2. Auto-sizes the window to fit content perfectly.
        3. Centers the window on the screen.
        """
        # 1. Make Modal (Block main window)
        dialog.transient(self.root)
        dialog.grab_set()

        # 2. Update the window to calculate required size
        dialog.update_idletasks()

        # Get the calculated size based on widgets
        width = dialog.winfo_reqwidth()
        height = dialog.winfo_reqheight()

        # Ensure it's not too thin (optional minimum width)
        if width < min_width:
            width = min_width

        # 3. Calculate Center Position
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # Apply geometry (Size + Position)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def auto_size_treeview_columns(self, tree):
        """Auto-sizes all columns in a Treeview to fit their content AND sets text alignment."""

        # Use a standard font for measuring
        try:
            # Try to get the font from the treeview's style
            font = tkfont.Font(font=tree.cget("font"))
        except:
            # Fallback to a default
            font = tkfont.Font(family="Helvetica", size=self.base_font_size)

        # Get all column identifiers
        columns = tree["columns"]

        # --- NEW ALIGNMENT LOGIC ---

        # 1. Define which column IDs should be centered (for numbers)
        # We use the *logical* IDs, not the translated text
        number_cols = [
            'ID', 'LoanID', 'IDNum', 'Phone', 'Phone1', 'Phone2',
            'Total', 'InStock', 'OnLoan', 'Deposit', 'NotReturned', 'Lost', 'Num'
        ]

        # 2. Define the anchor for TEXT based on language
        # tk.E = East (Right), tk.W = West (Left)
        text_anchor = tk.E if self.is_rtl else tk.W

        # --- END OF NEW LOGIC ---

        for col in columns:
            if col == 'Spacer': continue
            if col in number_cols:
                col_anchor = tk.CENTER
            else:
                col_anchor = text_anchor

            # 1. Start with the width of the heading
            heading_text = tree.heading(col, 'text')
            max_width = font.measure(heading_text) + 10  # Add padding

            # 2. Check all data cells in that column
            for iid in tree.get_children():
                cell_value = tree.set(iid, col)
                if cell_value:
                    cell_width = font.measure(cell_value)
                    if cell_width > max_width:
                        max_width = cell_width

            # 3. Apply the new width (with a little extra padding)
            final_width = max(70, min(max_width + 20, 400))

            # --- MODIFIED: Add the 'anchor' property ---
            tree.column(col, width=final_width, stretch=False, anchor=col_anchor)

    def setup_styles(self, base_size=14):
        """
        Configure styles with a 'Google-like' Dark Mode (Neutral Black/Grey).
        """
        style = ttk.Style()
        style.theme_use('clam')

        if self.current_theme == 'light':
            # --- LIGHT MODE (Standard Enterprise) ---
            colors = {
                'bg': "#F0F2F5",  # Light Grey
                'fg': "#202124",  # Near Black text
                'primary': "#1f4788",  # Brand Blue
                'accent': "#3498DB",  # Bright Blue
                'input_bg': "#FFFFFF",  # White Inputs
                'input_fg': "#202124",
                'btn_bg': "#FFFFFF",
                'btn_border': "#DADCE0",  # Google-style border
                'header_bg': "#1f4788",  # Dark Blue Header
                'header_fg': "#FFFFFF",
                'subtext': "#5f6368"  # Google Grey text
            }
        else:
            # --- DARK MODE (Google Style - Neutral Black/Grey) ---
            colors = {
                'bg': "#202124",  # Main Background (Dark Grey/Black)
                'fg': "#E8EAED",  # High contrast light grey text
                'primary': "#8AB4F8",  # Google Blue (Desaturated)
                'accent': "#8AB4F8",  # Same blue for consistency
                'input_bg': "#303134",  # Lighter grey for Inputs
                'input_fg': "#E8EAED",  # White text
                'btn_bg': "#303134",  # Button matches input
                'btn_border': "#5f6368",  # Subtle border
                'header_bg': "#3c4043",  # DISTINCT Header (Lighter than background)
                'header_fg': "#E8EAED",  # Header Text
                'subtext': "#9AA0A6"  # Subtitles
            }

        # --- APPLY GLOBAL SETTINGS ---
        self.root.configure(bg=colors['bg'])

        style.configure('.',
                        background=colors['bg'],
                        foreground=colors['fg'],
                        font=self.ui_font
                        )

        # --- WIDGET STYLING ---
        style.configure('TFrame', background=colors['bg'])
        style.configure('TLabel', background=colors['bg'], foreground=colors['fg'])

        style.configure('TLabelFrame',
                        background=colors['bg'],
                        foreground=colors['primary'],
                        bordercolor=colors['btn_border'],
                        borderwidth=1
                        )
        style.configure('TLabelFrame.Label',
                        font=('Helvetica', base_size, 'bold'),
                        background=colors['bg'],
                        foreground=colors['primary']
                        )

        # --- BUTTONS ---
        pad_btn = int(base_size * 0.5)

        # Standard Button
        style.configure('TButton',
                        font=self.ui_font,
                        padding=pad_btn,
                        background=colors['btn_bg'],
                        foreground=colors['fg'],
                        bordercolor=colors['btn_border'],
                        relief="flat",
                        borderwidth=1
                        )
        style.map('TButton',
                  background=[('active', colors['btn_border'])],  # Slight highlight
                  foreground=[('active', colors['fg'])]
                  )

        # Action Button (Primary)
        style.configure('Action.TButton',
                        font=('Helvetica', base_size, 'bold'),
                        padding=10,
                        background=colors['accent'] if self.current_theme == 'dark' else colors['primary'],
                        foreground="#202124" if self.current_theme == 'dark' else "#FFFFFF",
                        # Dark text on blue for Dark Mode
                        bordercolor=colors['accent'],
                        relief="flat",
                        borderwidth=0
                        )
        style.map('Action.TButton',
                  background=[('active', colors['fg'] if self.current_theme == 'dark' else colors['accent'])]
                  )

        # Large Dashboard Buttons
        style.configure('Large.TButton',
                        font=('Helvetica', base_size + 2),
                        padding=20,
                        background=colors['btn_bg'],
                        foreground=colors['fg'] if self.current_theme == 'dark' else colors['primary'],
                        bordercolor=colors['btn_border'],
                        relief="flat",
                        borderwidth=1
                        )

        # --- INPUTS ---
        input_size = self.input_font.cget("size")
        pad_input = int(input_size * 0.4)

        style.configure('TEntry',
                        font=self.input_font,
                        padding=pad_input,
                        fieldbackground=colors['input_bg'],
                        foreground=colors['input_fg'],
                        bordercolor=colors['btn_border'],
                        relief="flat",
                        borderwidth=1,
                        insertcolor=colors['fg']
                        )

        style.configure('Right.TEntry',
                        font=self.input_font,
                        padding=pad_input,
                        justify='right',
                        fieldbackground=colors['input_bg'],
                        foreground=colors['input_fg'],
                        bordercolor=colors['btn_border'],
                        relief="flat",
                        borderwidth=1,
                        insertcolor=colors['fg']
                        )

        # --- TREEVIEW (Table) ---
        style.configure('Treeview',
                        font=self.ui_font,
                        rowheight=int(base_size * 2.8),
                        background=colors['bg'],  # Table body matches window background
                        fieldbackground=colors['bg'],
                        foreground=colors['fg'],
                        borderwidth=0
                        )

        # HEADER STYLING (The Fix)
        style.configure('Treeview.Heading',
                        font=('Helvetica', base_size, 'bold'),
                        background=colors['header_bg'],  # Distinct Lighter Grey in Dark Mode
                        foreground=colors['header_fg'],
                        borderwidth=0,
                        relief="flat"
                        )
        style.map('Treeview.Heading',
                  background=[('active', colors['btn_border'])]
                  )

        # --- TEXT & TITLES ---
        style.configure('Title.TLabel', font=('Helvetica', base_size + 10, 'bold'), foreground=colors['primary'])
        style.configure('Subtitle.TLabel', font=('Helvetica', base_size + 2, 'bold'), foreground=colors['subtext'])
        style.configure('Normal.TLabel', font=self.ui_font)
        style.configure('Medium.TLabel', font=('Helvetica', base_size + 1))
        style.configure('Small.TLabel', font=('Helvetica', base_size - 2), foreground=colors['subtext'])

        # RTL Specifics
        style.configure('Right.TLabel', font=self.ui_font, anchor='e')
        style.configure('Right.Subtitle.TLabel', font=('Helvetica', base_size + 2, 'bold'), anchor='e',
                        foreground=colors['subtext'])
        style.configure('Right.Medium.TLabel', font=('Helvetica', base_size + 1), anchor='e')
        style.configure('Right.Small.TLabel', font=('Helvetica', base_size - 2), foreground=colors['subtext'],
                        anchor='e')

        style.configure('Font.TButton', font=('Helvetica', 10, 'bold'))

    def validate_numbers_only(self, p):
        """
        Real-time validation:
        Allows only digits or an empty string.
        Also allows '-' specifically for the override rule.
        """
        if p == "": return True
        if p == "-": return True
        return p.isdigit()

    def validate_id_input(self, p):
        """
        Real-time validation for ID:
        1. Allows exactly '-'
        2. Allows digits only
        3. strict length check (max 9 chars)
        """
        if p == "": return True
        if p == "-": return True

        # Check if it's a number AND length is 9 or less
        if p.isdigit() and len(p) <= 9:
            return True

        return False

    def configure_status_tags(self, tree):
        """Configures color tags. FORCES BLACK TEXT for readability on colored backgrounds."""

        # We use the same pastel colors for both modes now,
        # because we are forcing the text to be black.
        colors = {
            'In-Stock': '#d9ead3',  # Light Green
            'On-Loan': '#fce5cd',  # Light Orange
            'Returned': '#d0e0e3',  # Light Blue
            'Not Returned': '#ea9999',  # Light Red
            'Lost': '#efefef',  # Light Grey
            'Active': '#fce5cd'
        }

        tag_map = {
            'In-Stock': 'InStock',
            'On-Loan': 'OnLoan',
            'Returned': 'Returned',
            'Not Returned': 'NotReturned',
            'Lost': 'Lost',
            'Active': 'OnLoan'
        }

        for status_key, tag_name in tag_map.items():
            bg_color = colors.get(status_key, '')
            if bg_color:
                # FIXED: Added foreground='#000000' to force black text
                tree.tag_configure(tag_name, background=bg_color, foreground='#000000')

    def clear_window(self):
        """Clear all widgets from main_frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _get_translated_status(self, status_key: str) -> str:
        """Translates a database status key into the current language."""
        if not status_key:
            return ""
        # Get the status map for the current language, default to English's map
        status_map = self.i18n[self.lang].get('status_values',
                                              self.i18n['en'].get('status_values', {}))

        # Find the translation, default to the original key if not found
        return status_map.get(status_key, status_key)

    def _get_status_tag(self, status_key: str) -> str:
        """Maps a database status key to its corresponding tag name."""
        if not status_key:
            return ""

        tag_map = {
            'In-Stock': 'InStock',
            'On-Loan': 'OnLoan',
            'Returned': 'Returned',
            'Not Returned': 'NotReturned',
            'Lost': 'Lost',
            'Active': 'OnLoan'
        }
        return tag_map.get(status_key, "")  # Default to no tag

    def show_global_controls(self, parent_frame, current_view_callback):
        """Adds language, font, AND theme controls"""
        is_rtl = self.is_rtl

        controls_frame = ttk.Frame(parent_frame)
        controls_frame.pack(fill='x', pady=5, padx=10)

        # --- 1. Language Selector ---
        lang_frame = ttk.Frame(controls_frame)
        lang_frame.pack(side='right' if not is_rtl else 'left')

        def set_lang(new_lang):
            self.lang = new_lang
            self.is_rtl = self.lang in ['he', 'ar']
            self.root.title(self.i18n[self.lang]['window_title'])
            self.setup_styles(self.base_font_size)
            current_view_callback()

        ttk.Button(lang_frame, text="EN", image=self.icon_flag_en,
                   command=lambda: set_lang('en')).pack(side='left', padx=3)
        ttk.Button(lang_frame, text="HE", image=self.icon_flag_he,
                   command=lambda: set_lang('he')).pack(side='left', padx=3)
        ttk.Button(lang_frame, text="AR", image=self.icon_flag_ar,
                   command=lambda: set_lang('ar')).pack(side='left', padx=3)

        # --- 2. Left Side Controls (Font & Theme) ---
        left_controls = ttk.Frame(controls_frame)
        left_controls.pack(side='left' if not is_rtl else 'right')

        # Font Controls - LOCALIZED
        font_label_text = f"{self.i18n[self.lang]['font_size']}:"
        ttk.Label(left_controls, text=font_label_text).pack(side='left', padx=2)

        ttk.Button(left_controls, text="-", style='Font.TButton', width=2,
                   command=lambda: self.adjust_font_size(-1, current_view_callback)).pack(side='left', padx=1)
        ttk.Button(left_controls, text="+", style='Font.TButton', width=2,
                   command=lambda: self.adjust_font_size(1, current_view_callback)).pack(side='left', padx=1)

        # Separator
        ttk.Label(left_controls, text="|").pack(side='left', padx=10)

        # Theme Toggle - CONSISTENT SPACING
        # Added extra space for the moon to match the sun's width roughly
        if self.current_theme == 'light':
            theme_text = "🌙  Dark Mode"
        else:
            theme_text = "☀️  Light Mode"

        ttk.Button(left_controls, text=theme_text, style='Font.TButton',
                   command=lambda: self.toggle_theme(current_view_callback)).pack(side='left', padx=5)

    def adjust_font_size(self, amount, current_view_callback):
        """Adjusts font size by updating the Font Objects directly"""
        MIN_SIZE = 9
        MAX_SIZE = 24

        new_size = self.base_font_size + amount
        new_size = max(MIN_SIZE, min(MAX_SIZE, new_size))

        # We update if size changed OR if we just want to force a refresh
        if new_size != self.base_font_size:
            self.base_font_size = new_size

            # 1. UPDATE THE FONT OBJECTS (Instant Text Resize)
            self.ui_font.configure(size=new_size)
            self.input_font.configure(size=new_size + 2)

            # 2. Re-run setup_styles to update PADDING (Box Resize)
            self.setup_styles(self.base_font_size)

            # 3. Refresh view
            current_view_callback()

    def show_dashboard(self):
        """Show main dashboard"""
        self.clear_window()
        self.show_global_controls(self.main_frame, self.show_dashboard)

        is_rtl = self.is_rtl
        style_title = 'Title.TLabel'
        style_subtitle = 'Subtitle.TLabel'

        # Title
        title = ttk.Label(self.main_frame, text=self.i18n[self.lang]['dashboard_title'], style=style_title)
        title.pack(pady=20)

        subtitle = ttk.Label(self.main_frame, text=self.i18n[self.lang]['dashboard_subtitle'], style=style_subtitle)
        subtitle.pack(pady=10)

        # Main menu buttons frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=30)

        # Button text and icons
        buttons = [
            (self.i18n[self.lang]['btn_new_loan'], self.show_new_loan, self.icon_new_loan),
            (self.i18n[self.lang]['btn_process_return'], self.show_process_return, self.icon_process_return),
            (self.i18n[self.lang]['btn_search_inventory'], self.show_inventory, self.icon_search_inventory),
            (self.i18n[self.lang]['btn_manage_borrowers'], self.show_borrowers, self.icon_manage_borrowers),
            (self.i18n[self.lang]['btn_generate_reports'], self.show_reports, self.icon_generate_reports),
            # NEW BUTTON: Data Management
            ("Excel Export / Import", self.show_data_menu, self.icon_generate_reports)
        ]

        for i, (text, command, icon) in enumerate(buttons):
            row = i // 2
            col = i % 2

            # RTL adjustment
            grid_col = 1 - col if is_rtl else col

            btn = ttk.Button(button_frame, text=text, command=command,
                             style='Large.TButton', width=25,
                             image=icon, compound=tk.TOP)
            btn.grid(row=row, column=grid_col, padx=20, pady=15)

        for i, (text, command, icon) in enumerate(buttons):
            row = i // 2
            col = i % 2

            grid_col = 1 - col if is_rtl else col

            btn = ttk.Button(button_frame, text=text, command=command,
                           style='Large.TButton', width=25,
                           image=icon, compound=tk.TOP)
            btn.grid(row=row, column=grid_col, padx=20, pady=15)

    def show_data_menu(self):
        """Show a popup to choose Export or Import"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Data Management")
        self.setup_dialog_window(dialog, min_width=300)

        ttk.Label(dialog, text="Excel Data Management", font=('Helvetica', 12, 'bold')).pack(pady=15)

        ttk.Button(dialog, text="📤 Export Database to Excel",
                   command=lambda: [dialog.destroy(), self.export_to_excel()],
                   style='Action.TButton', width=25).pack(pady=10)

        ttk.Button(dialog, text="📥 Import Database from Excel",
                   command=lambda: [dialog.destroy(), self.import_from_excel()],
                   style='TButton', width=25).pack(pady=10)

        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

    # ============ INVENTORY SCREEN ============

    def show_inventory(self):
        """Show inventory management screen"""
        self.clear_window()
        self.show_global_controls(self.main_frame, self.show_inventory)

        is_rtl = self.is_rtl
        side_left = 'right' if is_rtl else 'left'
        side_right = 'left' if is_rtl else 'right'

        # Style helpers
        style_subtitle = 'Right.Subtitle.TLabel' if is_rtl else 'Subtitle.TLabel'
        style_entry = 'Right.TEntry' if is_rtl else 'TEntry'

        # For Treeview/Scrollbar
        col_tree = 1 if is_rtl else 0
        col_scroll = 0 if is_rtl else 1

        # Header
        header = ttk.Frame(self.main_frame)
        header.pack(pady=10, fill='x', padx=20)

        ttk.Label(header, text=self.i18n[self.lang]['inventory_title'],
                  style=style_subtitle).pack(side=side_left)
        ttk.Button(header, text=self.i18n[self.lang]['back_to_dashboard'],
                   command=self.show_dashboard).pack(side=side_right)

        # Search and action frame
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(pady=10, fill='x', padx=20)

        anchor_w = 'e' if is_rtl else 'w'

        if is_rtl:
            col_spacer = 0
            col_btn_add = 1
            col_btn_show = 2
            col_entry = 3
            col_lbl = 4
        else:  # LTR
            col_lbl = 0
            col_entry = 1
            col_btn_show = 2
            col_btn_add = 3
            col_spacer = 4

        # --- Configure the grid: Make the entry column (col_entry) stretch ---
        search_frame.grid_columnconfigure(col_spacer, weight=1)

        # 1. "Search:" Label
        ttk.Label(search_frame, text=self.i18n[self.lang]['search']).grid(
            row=0, column=col_lbl, padx=5, sticky=anchor_w)

        # 2. Search Entry Box
        search_var = self.search_vars['inventory']
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20, style=style_entry, font=self.input_font)
        search_entry.grid(row=0, column=col_entry, padx=5, sticky=anchor_w)

        # 3. Hint Label (under the entry box)
        hint_style = 'Right.Small.TLabel' if is_rtl else 'Small.TLabel'
        hint_label = ttk.Label(search_frame, text=self.i18n[self.lang]['search_by_name_serial'], style=hint_style)
        hint_label.grid(row=1, column=col_entry, padx=5, sticky=anchor_w)  # Aligns left/right

        # 4. "Add New" Button
        ttk.Button(search_frame, text=self.i18n[self.lang]['add_new_equipment'],
                   command=self.show_add_equipment,
                   style='Action.TButton').grid(row=0, column=col_btn_add, rowspan=2, padx=5)  # Spans two rows

        # 5. "Show All" Button (initially hidden)
        show_all_btn = ttk.Button(search_frame, text=self.i18n[self.lang]['show_all'])

        def on_search_change(event):
            search_term = search_var.get()
            self.search_inventory_items(search_term, tree)
            if search_term:
                show_all_btn.grid(row=0, column=col_btn_show, rowspan=2, padx=5)
            else:
                show_all_btn.grid_forget()

        # Configure the 'Show All' button command
        show_all_btn.config(command=lambda: (
            search_var.set(''),
            self.load_inventory(tree),
            on_search_change(None)
        ))

        # --- Bind the event to the entry box
        search_entry.bind("<KeyRelease>", on_search_change)

        if search_var.get():
            on_search_change(None)

        # Treeview frame
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(pady=10, fill='both', expand=True, padx=20)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        cols = ['ID', 'Num', 'Name', 'Serial', 'Status', 'Deposit', 'Description', 'Spacer']
        visual_cols = ['Num', 'Name', 'Serial', 'Status', 'Deposit', 'Description']

        if self.is_rtl:
            visual_cols = ['Spacer'] + visual_cols[::-1]

        # Treeview
        tree = ttk.Treeview(tree_frame, columns=cols, displaycolumns=visual_cols, show='headings', height=8,
                            yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.column('Spacer', width=1, stretch=True)
        tree.heading('Spacer', text="")

        self.configure_status_tags(tree)
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        # Column headings
        tree.heading('ID', text=self.i18n[self.lang]['col_id'])
        tree.heading('Num', text=self.i18n[self.lang]['col_num'])
        tree.heading('Name', text=self.i18n[self.lang]['col_name'])
        tree.heading('Serial', text=self.i18n[self.lang]['col_serial'])
        tree.heading('Status', text=self.i18n[self.lang]['col_status'])
        tree.heading('Deposit', text=self.i18n[self.lang]['col_deposit'])
        tree.heading('Description', text=self.i18n[self.lang]['col_description'])

        # Pack everything
        tree.grid(row=0, column=col_tree, sticky='nsew')
        vsb.grid(row=0, column=col_scroll, sticky='ns')
        hsb.grid(row=1, column=0, columnspan=2, sticky='ew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(col_tree, weight=1)

        # Action buttons
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(pady=10, padx=20)

        ttk.Button(action_frame, text=self.i18n[self.lang]['edit_selected'],
                  command=lambda: self.edit_equipment(tree)).pack(side='left', padx=5)
        ttk.Button(action_frame, text=self.i18n[self.lang]['delete_selected'],
                   command=lambda: self.delete_equipment_action(tree)).pack(side='left', padx=5)
        ttk.Button(action_frame, text=self.i18n[self.lang]['view_summary'],
                  command=self.show_inventory_summary).pack(side='left', padx=5)

        # Load data
        self.load_inventory(tree)

    def load_inventory(self, tree):
        """Load all equipment into treeview"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)

        equipment_list = self.db.get_all_equipment()

        # Load equipment
        for i, eq in enumerate(equipment_list, 1):
            status = eq['status']
            tree.insert('', 'end', values=(
                eq['id'],  # Index 0 (Hidden, used for logic)
                i,  # Index 1 (Visible #)
                eq['item_name'],
                eq['serial_number'],
                self._get_translated_status(status),
                f"{eq['deposit_amount']:.2f}",
                eq['description'] or ''
            ), tags=(self._get_status_tag(status),))

        self.auto_size_treeview_columns(tree)

    def search_inventory_items(self, search_term, tree):
        """Search inventory"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)

        if not search_term:
            self.load_inventory(tree)
            return

        # Search equipment
        equipment_list = self.db.search_equipment(search_term)
        for i, eq in enumerate(equipment_list, 1):  # Added enumerate
            status = eq['status']
            tree.insert('', 'end', values=(
                eq['id'],
                i,
                eq['item_name'],
                eq['serial_number'],
                self._get_translated_status(eq['status']),
                f"{eq['deposit_amount']:.2f}",
                eq['description'] or ''
            ), tags=(self._get_status_tag(status),))

        self.auto_size_treeview_columns(tree)

    def show_add_equipment(self):
        """Show add equipment dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.i18n[self.lang]['add_eq_title'])
        # dialog.geometry("500x400")
        # dialog.transient(self.root)  # Keep on top
        dialog.grab_set()

        is_rtl = self.is_rtl
        anchor_w = 'e' if is_rtl else 'w'  # 'w' (west) becomes 'e' (east)
        col_label = 1 if is_rtl else 0
        col_entry = 0 if is_rtl else 1

        # Style helpers
        style_label = 'Right.TLabel' if is_rtl else 'TLabel'
        style_entry = 'Right.TEntry' if is_rtl else 'TEntry'

        # Form fields
        ttk.Label(dialog, text=self.i18n[self.lang]['add_eq_title'], font=('Helvetica', 14, 'bold')).pack(pady=10)

        form_frame = ttk.Frame(dialog)
        form_frame.pack(pady=20, padx=20, fill='both')

        justify_text = 'right' if is_rtl else 'left'

        # Item Name
        ttk.Label(form_frame, text=self.i18n[self.lang]['eq_name'], style=style_label).grid(row=0, column=col_label, sticky=anchor_w, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=name_var, width=40, justify=justify_text, font=self.input_font).grid(row=0, column=col_entry, pady=5)

        # Description
        ttk.Label(form_frame, text=self.i18n[self.lang]['eq_desc'], style=style_label).grid(row=1, column=col_label, sticky=anchor_w, pady=5)
        desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=desc_var, width=40, justify=justify_text, font=self.input_font).grid(row=1,
                                                                                                                column=col_entry,
                                                                                                                pady=5)
        # Serial Number
        ttk.Label(form_frame, text=self.i18n[self.lang]['eq_serial'], style=style_label).grid(row=2, column=col_label, sticky=anchor_w, pady=5)
        serial_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=serial_var, width=40, justify=justify_text, font=self.input_font).grid(row=2,
                                                                                                                  column=col_entry,
                                                                                                                  pady=5)
        # Deposit Amount
        ttk.Label(form_frame, text=self.i18n[self.lang]['eq_deposit'], style=style_label).grid(row=3, column=col_label, sticky=anchor_w, pady=5)
        deposit_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=deposit_var, width=40, justify=justify_text, font=self.input_font).grid(
            row=3, column=col_entry, pady=5)
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        def save_equipment():
            try:
                name = name_var.get().strip()
                description = desc_var.get().strip()
                serial = serial_var.get().strip()
                deposit = float(deposit_var.get())

                if not name or not serial:
                    messagebox.showerror("Error", self.i18n[self.lang]['err_required_fields'])
                    return

                self.db.add_equipment(name, description, serial, deposit)
                messagebox.showinfo("Success", self.i18n[self.lang]['success_add'])
                dialog.destroy()
                self.show_inventory()
            except ValueError:
                messagebox.showerror("Error", self.i18n[self.lang]['err_invalid_deposit'])
            except Exception as e:
                messagebox.showerror("Error", self.i18n[self.lang]['err_add_fail'].format(e=str(e)))

        ttk.Button(button_frame, text=self.i18n[self.lang]['save'], command=save_equipment).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.i18n[self.lang]['cancel'], command=dialog.destroy).pack(side='left', padx=5)

        self.setup_dialog_window(dialog)

    def edit_equipment(self, tree):
        """Edit selected equipment"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", self.i18n[self.lang]['warn_select_item'])
            return

        item = tree.item(selection[0])
        eq_id = item['values'][0]
        equipment = self.db.get_equipment(eq_id)

        if not equipment:
            messagebox.showerror("Error", self.i18n[self.lang]['err_not_found'])
            return

        # Edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(self.i18n[self.lang]['edit_eq_title'])
        dialog.grab_set()

        # --- RTL HELPER BLOCK ---
        is_rtl = self.is_rtl
        anchor_w = 'e' if is_rtl else 'w'
        col_label = 1 if is_rtl else 0
        col_entry = 0 if is_rtl else 1

        # NEW: Justify text based on language
        justify_text = 'right' if is_rtl else 'left'

        # Style helpers
        style_label = 'Right.TLabel' if is_rtl else 'TLabel'
        # --- END OF BLOCK ---

        ttk.Label(dialog, text=self.i18n[self.lang]['edit_eq_title'], font=('Helvetica', 14, 'bold')).pack(pady=10)

        form_frame = ttk.Frame(dialog)
        form_frame.pack(pady=20, padx=20, fill='both')

        # Pre-fill fields

        # 1. Name
        ttk.Label(form_frame, text=self.i18n[self.lang]['eq_name'], style=style_label).grid(
            row=0, column=col_label, sticky=anchor_w, pady=5)
        name_var = tk.StringVar(value=equipment['item_name'])
        # UPDATED: Added font and justify
        ttk.Entry(form_frame, textvariable=name_var, width=40, justify=justify_text, font=self.input_font).grid(
            row=0, column=col_entry, pady=5)

        # 2. Description
        ttk.Label(form_frame, text=self.i18n[self.lang]['eq_desc'], style=style_label).grid(
            row=1, column=col_label, sticky=anchor_w, pady=5)
        desc_var = tk.StringVar(value=equipment['description'] or '')
        # UPDATED: Added font and justify
        ttk.Entry(form_frame, textvariable=desc_var, width=40, justify=justify_text, font=self.input_font).grid(
            row=1, column=col_entry, pady=5)

        # 3. Serial
        ttk.Label(form_frame, text=self.i18n[self.lang]['eq_serial'], style=style_label).grid(
            row=2, column=col_label, sticky=anchor_w, pady=5)
        serial_var = tk.StringVar(value=equipment['serial_number'])
        # UPDATED: Added font and justify
        ttk.Entry(form_frame, textvariable=serial_var, width=40, justify=justify_text, font=self.input_font).grid(
            row=2, column=col_entry, pady=5)

        # 4. Deposit
        ttk.Label(form_frame, text=self.i18n[self.lang]['eq_deposit'], style=style_label).grid(
            row=3, column=col_label, sticky=anchor_w, pady=5)
        deposit_var = tk.StringVar(value=str(equipment['deposit_amount']))
        # UPDATED: Added font and justify
        ttk.Entry(form_frame, textvariable=deposit_var, width=40, justify=justify_text, font=self.input_font).grid(
            row=3, column=col_entry, pady=5)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        def update_equipment():
            try:
                name = name_var.get().strip()
                description = desc_var.get().strip()
                serial = serial_var.get().strip()
                deposit = float(deposit_var.get())

                if not name or not serial:
                    messagebox.showerror("Error", self.i18n[self.lang]['err_required_fields'])
                    return

                self.db.update_equipment(eq_id, name, description, serial, deposit)
                messagebox.showinfo("Success", self.i18n[self.lang]['success_update'])
                dialog.destroy()
                self.show_inventory()
            except ValueError:
                messagebox.showerror("Error", self.i18n[self.lang]['err_invalid_deposit'])
            except Exception as e:
                messagebox.showerror("Error", self.i18n[self.lang]['err_update_fail'].format(e=str(e)))

        ttk.Button(button_frame, text=self.i18n[self.lang]['update'], command=update_equipment).pack(side='left',
                                                                                                     padx=5)
        ttk.Button(button_frame, text=self.i18n[self.lang]['cancel'], command=dialog.destroy).pack(side='left', padx=5)

        self.setup_dialog_window(dialog)

    def delete_equipment_action(self, tree):
        """Delete selected equipment using standard messagebox"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", self.i18n[self.lang]['warn_select_item'])
            return

        item = tree.item(selection[0])
        eq_id = item['values'][0]
        eq_name = item['values'][1]

        # Prepare translated strings
        title = self.i18n[self.lang]['confirm_delete_title']
        msg = self.i18n[self.lang]['confirm_delete_msg'].format(name=eq_name)

        # Use the standard Yes/No popup
        if messagebox.askyesno(title, msg):
            try:
                self.db.delete_equipment(eq_id)

                # Success message - NOW TRANSLATED
                s_title = self.i18n[self.lang]['success_title']
                s_msg = self.i18n[self.lang]['success_delete_msg']

                messagebox.showinfo(s_title, s_msg)

                # Refresh the list
                self.load_inventory(tree)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")

    def show_inventory_summary(self):
        """Show active inventory summary"""
        summary = self.db.get_equipment_summary()

        dialog = tk.Toplevel(self.root)
        dialog.title(self.i18n[self.lang]['summary_title'])
        # dialog.geometry("800x500")
        # dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=self.i18n[self.lang]['summary_title'],
                  font=('Helvetica', 14, 'bold')).pack(pady=10)

        # Treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(pady=10, fill='both', expand=True, padx=20)

        # Updated columns: Only showing ACTIVE status counts
        cols = ['Num', 'Name', 'Total', 'InStock', 'OnLoan', 'Spacer']
        # For summary, cols == visual_cols (except spacer logic)
        base_visuals = ['Num', 'Name', 'Total', 'InStock', 'OnLoan']

        if self.is_rtl:
            visual_cols = ['Spacer'] + base_visuals[::-1]
        else:
            visual_cols = base_visuals

        tree = ttk.Treeview(tree_frame, columns=cols, displaycolumns=visual_cols, show='headings')

        tree.column('Spacer', width=1, stretch=True)
        tree.heading('Spacer', text="")

        tree.heading('Num', text=self.i18n[self.lang]['col_num'])
        tree.heading('Name', text=self.i18n[self.lang]['col_name'])
        tree.heading('Total', text=self.i18n[self.lang]['col_total'])
        tree.heading('InStock', text=self.i18n[self.lang]['col_in_stock'])
        tree.heading('OnLoan', text=self.i18n[self.lang]['col_on_loan'])

        # Center the numbers
        tree.column('Total', anchor='center', width=80)
        tree.column('InStock', anchor='center', width=80)
        tree.column('OnLoan', anchor='center', width=80)

        tree.pack(fill='both', expand=True)

        # Load data
        for i, item in enumerate(summary, 1):
            tree.insert('', 'end', values=(
                i,
                item['item_name'],
                item['total_count'],
                item['in_stock'],
                item['on_loan']
            ))

        self.auto_size_treeview_columns(tree)

        ttk.Button(dialog, text=self.i18n[self.lang]['close'], command=dialog.destroy).pack(pady=10)

        self.setup_dialog_window(dialog, min_width=600)

    # ============ NEW LOAN SCREEN ============

    def show_new_loan(self):
        """Show new loan screen - Step 1: Select Equipment"""
        self.clear_window()
        self.show_global_controls(self.main_frame, self.show_new_loan)

        # --- RTL HELPER BLOCK ---
        is_rtl = self.is_rtl
        side_left = 'right' if is_rtl else 'left'
        side_right = 'left' if is_rtl else 'right'

        # Style helpers
        style_subtitle = 'Right.Subtitle.TLabel' if is_rtl else 'Subtitle.TLabel'
        style_entry = 'Right.TEntry' if is_rtl else 'TEntry'

        # For Treeview/Scrollbar
        col_tree = 1 if is_rtl else 0
        col_scroll = 0 if is_rtl else 1

        # Header
        header = ttk.Frame(self.main_frame)
        header.pack(pady=10, fill='x', padx=20)

        ttk.Label(header, text=self.i18n[self.lang]['new_loan_title'],
                  style=style_subtitle).pack(side=side_left)
        ttk.Button(header, text=self.i18n[self.lang]['back_to_dashboard'],
                   command=self.show_dashboard).pack(side=side_right)

        # Search frame
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(pady=10, fill='x', padx=20)

        anchor_w = 'e' if is_rtl else 'w'  # Define anchor for the hint

        # --- Define Grid Columns for RTL ---
        if is_rtl:
            # Spacer(0) | Show(1) | Entry(2) | Label(3)
            col_spacer = 0
            col_btn_show = 1
            col_entry = 2
            col_lbl = 3
        else:  # LTR
            # Label(0) | Entry(1) | Show(2) | Spacer(3)
            col_lbl = 0
            col_entry = 1
            col_btn_show = 2
            col_spacer = 3

        # --- Configure the grid: Make the entry column (col_entry) stretch ---
        search_frame.grid_columnconfigure(col_spacer, weight=1)

        # 1. "Search:" Label
        ttk.Label(search_frame, text=self.i18n[self.lang]['search_available_eq']).grid(
            row=0, column=col_lbl, padx=5, sticky=anchor_w)

        # 2. Search Entry Box
        search_var = self.search_vars['loan_step1']
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20, style=style_entry, font=self.input_font)
        search_entry.grid(row=0, column=col_entry, padx=5, sticky=anchor_w)

        # 3. Hint Label (under the entry box)
        hint_style = 'Right.Small.TLabel' if is_rtl else 'Small.TLabel'
        hint_label = ttk.Label(search_frame, text=self.i18n[self.lang]['search_by_eq_name'], style=hint_style)
        hint_label.grid(row=1, column=col_entry, padx=5, sticky=anchor_w)

        # 4. "Show All" Button (initially hidden)
        show_all_btn = ttk.Button(search_frame, text=self.i18n[self.lang]['show_all'])

        def on_search_change(event):
            search_term = search_var.get()
            self.search_available_equipment(search_term, tree)
            if search_term:
                show_all_btn.grid(row=0, column=col_btn_show, rowspan=2, padx=5)
            else:
                show_all_btn.grid_forget()

        # Configure the 'Show All' button command
        show_all_btn.config(command=lambda: (
            search_var.set(''),
            self.load_available_equipment(tree),
            on_search_change(None)
        ))

        # --- Bind the event to the entry box
        search_entry.bind("<KeyRelease>", on_search_change)

        if search_var.get():
            on_search_change(None)

        # Treeview
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(pady=10, fill='both', expand=True, padx=20)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        cols = ['ID', 'Num', 'Name', 'Serial', 'Deposit', 'Description', 'Spacer']
        visual_cols = ['Num', 'Name', 'Serial', 'Deposit', 'Description']

        if self.is_rtl:
            visual_cols = ['Spacer'] + visual_cols[::-1]

        tree = ttk.Treeview(tree_frame, columns=cols,
                            displaycolumns=visual_cols,
                            show='headings', height=8, yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.column('Spacer', width=1, stretch=True)
        tree.heading('Spacer', text="")

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        tree.heading('ID', text=self.i18n[self.lang]['col_id'])
        tree.heading('Num', text=self.i18n[self.lang]['col_num'])
        tree.heading('Name', text=self.i18n[self.lang]['col_name'])
        tree.heading('Serial', text=self.i18n[self.lang]['col_serial'])
        tree.heading('Deposit', text=self.i18n[self.lang]['col_deposit'])
        tree.heading('Description', text=self.i18n[self.lang]['col_description'])

        tree.grid(row=0, column=col_tree, sticky='nsew')
        vsb.grid(row=0, column=col_scroll, sticky='ns')
        hsb.grid(row=1, column=0, columnspan=2, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(col_tree, weight=1)

        # Action button
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(pady=20)

        ttk.Button(action_frame, text=self.i18n[self.lang]['loan_this_item'],
                   command=lambda: self.proceed_to_borrower_step(tree),
                   style='Action.TButton').pack()

        # Load available equipment
        self.load_available_equipment(tree)

    def clear_loan_form(self):
        """Clear the persistent form variables"""
        for key in self.form_vars:
            self.form_vars[key].set("")
        self.search_vars['loan_step2'].set("")

    def load_available_equipment(self, tree):
        """Load available equipment"""
        for item in tree.get_children():
            tree.delete(item)

        equipment_list = self.db.get_available_equipment()
        for i, eq in enumerate(equipment_list, 1):
            tree.insert('', 'end', values=(
                eq['id'], i, eq['item_name'], eq['serial_number'],
                f"{eq['deposit_amount']:.2f}", eq['description'] or ''
            ))

        self.auto_size_treeview_columns(tree)

    def search_available_equipment(self, search_term, tree):
        """Search available equipment"""
        for item in tree.get_children():
            tree.delete(item)

        if not search_term:
            self.load_available_equipment(tree)
            return

        equipment_list = self.db.get_available_equipment(search_term)
        for i, eq in enumerate(equipment_list, 1):
            tree.insert('', 'end', values=(
                eq['id'], i, eq['item_name'], eq['serial_number'],
                f"{eq['deposit_amount']:.2f}", eq['description'] or ''
            ))

        self.auto_size_treeview_columns(tree)

    def proceed_to_borrower_step(self, tree):
        """Proceed to Step 2: Borrower & Deposit"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", self.i18n[self.lang]['warn_select_item'])
            return

        item = tree.item(selection[0])
        eq_id = item['values'][0]
        equipment = self.db.get_equipment(eq_id)

        self.show_borrower_step(equipment)

    def show_borrower_step(self, equipment):
        """Show Step 2: Borrower & Deposit - Buttons Centered & Hidden Initially"""
        self.clear_window()
        self.show_global_controls(self.main_frame, lambda: self.show_borrower_step(equipment))

        # --- RTL Helpers ---
        is_rtl = self.is_rtl
        anchor_w = 'e' if is_rtl else 'w'
        justify_text = 'right' if is_rtl else 'left'
        label_anchor = 'ne' if is_rtl else 'nw'

        # Header
        header = ttk.Frame(self.main_frame)
        header.pack(pady=(10, 20), fill='x', padx=20)

        title_side = 'right' if is_rtl else 'left'
        btn_side = 'left' if is_rtl else 'right'

        ttk.Label(header, text=self.i18n[self.lang]['new_loan_title_step2'],
                  style='Subtitle.TLabel').pack(side=title_side)
        ttk.Button(header, text=self.i18n[self.lang]['back'],
                   command=self.show_new_loan).pack(side=btn_side)

        # ============ MAIN CONTENT LAYOUT ============
        content_container = ttk.Frame(self.main_frame)
        content_container.pack(fill='x', padx=20)

        pane_borrower = ttk.Frame(content_container)
        pane_item = ttk.Frame(content_container)

        if is_rtl:
            pane_borrower.pack(side='right', fill='both', expand=True, padx=(10, 0))
            pane_item.pack(side='right', fill='both', expand=True, padx=(0, 10))
        else:
            pane_borrower.pack(side='left', fill='both', expand=True, padx=(0, 10))
            pane_item.pack(side='left', fill='both', expand=True, padx=(10, 0))

            # ============ FILL PANE 1: BORROWER ============

        # 1. Search Section
        search_container = ttk.LabelFrame(pane_borrower, text=self.i18n[self.lang]['search_borrower'],
                                          padding=10, labelanchor=label_anchor)
        search_container.pack(fill='x', pady=(0, 10))

        search_var = self.search_vars['loan_step2']

        if is_rtl:
            ttk.Button(search_container, text=self.i18n[self.lang]['search_btn'],
                       command=lambda: search_borrower_logic()).grid(row=0, column=0, padx=5)
            entry = ttk.Entry(search_container, textvariable=search_var, width=20,
                              justify=justify_text, font=self.input_font)
            entry.grid(row=0, column=1, padx=5, sticky='ew')
            search_container.columnconfigure(1, weight=1)
        else:
            entry = ttk.Entry(search_container, textvariable=search_var, width=20, font=self.input_font)
            entry.grid(row=0, column=0, padx=5, sticky='ew')
            ttk.Button(search_container, text=self.i18n[self.lang]['search_btn'],
                       command=lambda: search_borrower_logic()).grid(row=0, column=1, padx=5)
            search_container.columnconfigure(0, weight=1)

        ttk.Label(search_container, text=self.i18n[self.lang]['search_by_id_phone'],
                  font=('Helvetica', 9), foreground='grey').grid(row=1, column=0, columnspan=2, sticky=anchor_w, padx=5)

        # 2. Borrower Details Form
        form_container = ttk.LabelFrame(pane_borrower, text=self.i18n[self.lang]['borrower_details'],
                                        padding=10, labelanchor=label_anchor)
        form_container.pack(fill='x', expand=False)

        # >>> TOOLBAR (Initially Hidden) <<<
        # We create it, but we don't pack the buttons yet
        tools_frame = ttk.Frame(form_container)
        tools_frame.pack(fill='x', pady=(0, 10))

        # >>> INNER FRAME FOR GRID <<<
        fields_frame = ttk.Frame(form_container)
        fields_frame.pack(fill='x', expand=True)

        # Logic to enable/disable fields
        borrower_entry_widgets = []

        def set_fields_state(state):
            for widget in borrower_entry_widgets:
                widget.config(state=state)

        # --- NEW: Button Visibility Logic ---
        # Create buttons but don't pack them
        btn_edit = ttk.Button(tools_frame, text=self.i18n[self.lang]['btn_edit_details'],
                              command=lambda: set_fields_state('normal'), width=15)
        btn_change = ttk.Button(tools_frame, text=self.i18n[self.lang]['btn_change_borrower'],
                                command=lambda: on_change_click(), width=15)

        def show_edit_buttons():
            # Pack them centered
            # We use a clean slate to avoid packing twice
            btn_edit.pack_forget()
            btn_change.pack_forget()

            # Center using pack side logic or just simple pack in order
            # Since they are in a frame, we can just pack them next to each other
            # and align the frame to center? No, easier to pack them side by side.
            if is_rtl:
                btn_change.pack(side='top', pady=2)  # Stack them or side by side?
                btn_edit.pack(side='top', pady=2)  # Let's stack them to save width? Or side?
                # You asked for "Center".
                # Let's re-pack tools_frame to center
            else:
                # Let's just pack them side by side, but using a centered inner frame
                pass

            # Simple Center Approach:
            btn_edit.pack(side='left', expand=True, padx=5)
            btn_change.pack(side='left', expand=True, padx=5)

        def hide_edit_buttons():
            btn_edit.pack_forget()
            btn_change.pack_forget()

        def on_change_click():
            # 1. Clear Data
            self.clear_loan_form()
            borrower_data['borrower_id'] = None

            # 2. Unlock Fields
            set_fields_state('normal')

            # 3. Hide Buttons (since we are in "New" mode now)
            hide_edit_buttons()

            # 4. RESET DEFAULTS (Fix for finance reset issue)
            deposit_var.set(str(equipment['deposit_amount']))
            donation_var.set("0")

        # Form Fields Setup
        f_col_lbl = 1 if is_rtl else 0
        f_col_ent = 0 if is_rtl else 1

        name_var = self.form_vars['name']
        id_var = self.form_vars['id']
        phone1_var = self.form_vars['phone1']
        phone2_var = self.form_vars['phone2']
        address_var = self.form_vars['address']
        deposit_var = self.form_vars['deposit']
        donation_var = self.form_vars['donation']

        # Defaults
        if not deposit_var.get(): deposit_var.set(str(equipment['deposit_amount']))
        if not donation_var.get(): donation_var.set("0")

        def add_row(parent, row, label_key, var, validator=None):
            ttk.Label(parent, text=self.i18n[self.lang][label_key]).grid(
                row=row, column=f_col_lbl, sticky=anchor_w, pady=5)

            e = ttk.Entry(parent, textvariable=var, width=25, justify=justify_text,
                          font=self.input_font)
            if validator:
                e.config(validate='key', validatecommand=validator)
            e.grid(row=row, column=f_col_ent, sticky='ew', pady=5)

            borrower_entry_widgets.append(e)

        add_row(fields_frame, 0, 'full_name', name_var)
        add_row(fields_frame, 1, 'id_number', id_var, self.vcmd_id)
        add_row(fields_frame, 2, 'primary_phone', phone1_var, self.vcmd_numbers)
        add_row(fields_frame, 3, 'secondary_phone', phone2_var, self.vcmd_numbers)
        add_row(fields_frame, 4, 'address', address_var)

        fields_frame.columnconfigure(f_col_ent, weight=1)

        # ============ FILL PANE 2: ITEM ============

        eq_container = ttk.LabelFrame(pane_item, text=self.i18n[self.lang]['selected_equipment'],
                                      padding=10, labelanchor=label_anchor)
        eq_container.pack(fill='x', pady=(0, 10))

        ttk.Label(eq_container, text=equipment['item_name'], font=('Helvetica', 12, 'bold')).pack(anchor=anchor_w)
        ttk.Label(eq_container, text=f"{self.i18n[self.lang]['col_serial']}: {equipment['serial_number']}").pack(
            anchor=anchor_w)
        ttk.Label(eq_container, text=f"{self.i18n[self.lang]['col_deposit']}: {equipment['deposit_amount']:.2f}").pack(
            anchor=anchor_w)

        fin_container = ttk.LabelFrame(pane_item, text=self.i18n[self.lang]['financial_details'],
                                       padding=10, labelanchor=label_anchor)
        fin_container.pack(fill='x')

        def add_fin_row(row, label_key, var):
            ttk.Label(fin_container, text=self.i18n[self.lang][label_key]).grid(
                row=row, column=f_col_lbl, sticky=anchor_w, pady=5)
            ttk.Entry(fin_container, textvariable=var, width=25, justify=justify_text,
                      font=self.input_font).grid(row=row, column=f_col_ent, sticky='ew', pady=5)

        add_fin_row(0, 'deposit_paid', deposit_var)
        add_fin_row(1, 'donation', donation_var)

        fin_container.columnconfigure(f_col_ent, weight=1)

        # ============ ACTION BUTTONS ============
        btn_frame = ttk.Frame(self.main_frame, padding=20)
        btn_frame.pack(fill='x')

        borrower_data = {'borrower_id': None}

        def confirm_loan_logic():
            try:
                name = name_var.get().strip()
                id_number = id_var.get().strip()
                phone1 = phone1_var.get().strip()

                # --- FIX: Optional Donation & Deposit ---
                dep_val = deposit_var.get().strip()
                don_val = donation_var.get().strip()

                deposit = float(dep_val) if dep_val else 0.0
                donation = float(don_val) if don_val else 0.0
                # ----------------------------------------

                if not name or not id_number or not phone1:
                    messagebox.showerror("Error", self.i18n[self.lang]['err_fill_required'])
                    return

                if id_number != '-' and len(id_number) != 9:
                    messagebox.showerror("Error", "ID Number must be exactly 9 digits (or '-' to skip).")
                    return

                if borrower_data['borrower_id']:
                    borrower_id = borrower_data['borrower_id']
                    self.db.update_borrower(borrower_id, name, id_number, phone1,
                                            phone2_var.get().strip(), address_var.get().strip())
                else:
                    existing = self.db.get_borrower_by_id_number(id_number)
                    if existing:
                        borrower_id = existing['id']
                        self.db.update_borrower(borrower_id, name, id_number, phone1,
                                                phone2_var.get().strip(), address_var.get().strip())
                    else:
                        borrower_id = self.db.add_borrower(name, id_number, phone1,
                                                           phone2_var.get().strip(), address_var.get().strip())

                loan_id = self.db.create_loan(borrower_id, equipment['id'], deposit, donation)
                loan_data = self.db.get_loan(loan_id)

                try:
                    pdf_path = self.reports.generate_loan_agreement(loan_data, self.lang)
                    self.reports.open_pdf(pdf_path)
                    messagebox.showinfo("Success", self.i18n[self.lang]['success_loan_created'].format(id=loan_id))
                except Exception as e:
                    messagebox.showwarning("Warning", f"Loan created, but agreement failed: {e}")

                self.clear_loan_form()
                self.show_dashboard()

            except ValueError:
                messagebox.showerror("Error", self.i18n[self.lang]['err_invalid_deposit_donation'])
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")

        ttk.Button(btn_frame, text=self.i18n[self.lang]['confirm_print'],
                   style='Action.TButton', command=confirm_loan_logic).pack(fill='x', ipady=5)

        # ============ SEARCH LOGIC ============

        def search_borrower_logic():
            term = search_var.get().strip()

            if not term:
                results = self.db.get_all_borrowers()
            else:
                results = self.db.search_borrower(term)

            if results:
                # When user selects someone:
                # 1. Lock fields
                # 2. Show buttons
                self.show_borrower_selection(results, name_var, id_var, phone1_var,
                                             phone2_var, address_var, borrower_data,
                                             on_select_callback=lambda: (
                                             set_fields_state('disabled'), show_edit_buttons()))
            else:
                messagebox.showinfo("Not Found", self.i18n[self.lang]['borrower_not_found'])
                borrower_data['borrower_id'] = None
                set_fields_state('normal')
                hide_edit_buttons()

        # 2. Bind the Enter key to the entry box
        entry.bind('<Return>', lambda event: search_borrower_logic())

    def show_borrower_selection(self, borrowers, name_var, id_var, phone1_var,
                                phone2_var, address_var, borrower_data, on_select_callback=None):
        """Show borrower selection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.i18n[self.lang]['select_borrower_title'])
        dialog.grab_set()

        ttk.Label(dialog, text=self.i18n[self.lang]['found_borrowers'],
                  font=('Helvetica', 12, 'bold')).pack(pady=10)

        # Treeview
        cols = ['ID', 'Num', 'Name', 'IDNum', 'Phone', 'Spacer']
        visual_cols = ['Num', 'Name', 'IDNum', 'Phone']

        if self.is_rtl:
            visual_cols = ['Spacer'] + visual_cols[::-1]

        tree = ttk.Treeview(dialog, columns=cols, displaycolumns=visual_cols, show='headings')

        tree.column('Spacer', width=1, stretch=True)
        tree.heading('Spacer', text="")

        tree.heading('ID', text=self.i18n[self.lang]['col_id'])
        tree.heading('Num', text=self.i18n[self.lang]['col_num'])
        tree.heading('Name', text=self.i18n[self.lang]['col_full_name'])
        tree.heading('IDNum', text=self.i18n[self.lang]['col_id_num'])
        tree.heading('Phone', text=self.i18n[self.lang]['col_phone'])

        tree.pack(pady=10, fill='both', expand=True, padx=20)

        for i, borrower in enumerate(borrowers, 1):
            tree.insert('', 'end', values=(
                borrower['id'], i, borrower['full_name'],
                borrower['id_number'], borrower['primary_phone']
            ))

        self.auto_size_treeview_columns(tree)

        def select_borrower():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", self.i18n[self.lang]['warn_select_borrower'])
                return

            item = tree.item(selection[0])
            borrower_id = item['values'][0]
            borrower = self.db.get_borrower(borrower_id)

            # Fill in the form
            name_var.set(borrower['full_name'])
            id_var.set(borrower['id_number'])
            phone1_var.set(borrower['primary_phone'])
            phone2_var.set(borrower.get('secondary_phone') or '')
            address_var.set(borrower.get('address') or '')

            # Set the ID tracking
            borrower_data['borrower_id'] = borrower_id

            # Trigger the lock!
            if on_select_callback:
                on_select_callback()

            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text=self.i18n[self.lang]['select'], command=select_borrower).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.i18n[self.lang]['cancel'], command=dialog.destroy).pack(side='left', padx=5)

        self.setup_dialog_window(dialog, min_width=600)

    # ============ PROCESS RETURN SCREEN ============

    def show_process_return(self):
        """Show process return screen"""
        self.clear_window()
        self.show_global_controls(self.main_frame, self.show_process_return)

        # --- RTL HELPER BLOCK ---
        is_rtl = self.is_rtl
        side_left = 'right' if is_rtl else 'left'
        side_right = 'left' if is_rtl else 'right'

        # Style helpers
        style_subtitle = 'Right.Subtitle.TLabel' if is_rtl else 'Subtitle.TLabel'
        style_entry = 'Right.TEntry' if is_rtl else 'TEntry'

        # For Treeview/Scrollbar
        col_tree = 1 if is_rtl else 0
        col_scroll = 0 if is_rtl else 1

        # Header
        header = ttk.Frame(self.main_frame)
        header.pack(pady=10, fill='x', padx=20)

        ttk.Label(header, text=self.i18n[self.lang]['return_title'],
                  style=style_subtitle).pack(side=side_left)
        ttk.Button(header, text=self.i18n[self.lang]['back_to_dashboard'],
                   command=self.show_dashboard).pack(side=side_right)

        # Search frame
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(pady=10, fill='x', padx=20)

        anchor_w = 'e' if is_rtl else 'w'  # Define anchor for the hint

        # --- Define Grid Columns for RTL ---
        if is_rtl:
            # Spacer(0) | Show(1) | Entry(2) | Label(3)
            col_spacer = 0
            col_btn_show = 1
            col_entry = 2
            col_lbl = 3
        else:  # LTR
            # Label(0) | Entry(1) | Show(2) | Spacer(3)
            col_lbl = 0
            col_entry = 1
            col_btn_show = 2
            col_spacer = 3

        # --- Configure the grid: Make the entry column (col_entry) stretch ---
        search_frame.grid_columnconfigure(col_spacer, weight=1)

        # 1. "Search:" Label
        ttk.Label(search_frame, text=self.i18n[self.lang]['search_active_loans']).grid(
            row=0, column=col_lbl, padx=5, sticky=anchor_w)

        # 2. Search Entry Box
        search_var = self.search_vars['return']
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20, style=style_entry, font=self.input_font)
        search_entry.grid(row=0, column=col_entry, padx=5, sticky=anchor_w)

        # 3. Hint Label (under the entry box)
        hint_style = 'Right.Small.TLabel' if is_rtl else 'Small.TLabel'
        hint_label = ttk.Label(search_frame, text=self.i18n[self.lang]['search_by_loan'], style=hint_style)
        hint_label.grid(row=1, column=col_entry, padx=5, sticky=anchor_w)

        # 4. "Show All" Button (initially hidden)
        show_all_btn = ttk.Button(search_frame, text=self.i18n[self.lang]['show_all'])

        def on_search_change(event):
            search_term = search_var.get()
            self.search_active_loans_list(search_term, tree)
            if search_term:
                show_all_btn.grid(row=0, column=col_btn_show, rowspan=2, padx=5)
            else:
                show_all_btn.grid_forget()

        # Configure the 'Show All' button command
        show_all_btn.config(command=lambda: (
            search_var.set(''),
            self.load_active_loans(tree),
            on_search_change(None)
        ))

        # --- Bind the event to the entry box
        search_entry.bind("<KeyRelease>", on_search_change)

        if search_var.get():
            on_search_change(None)

        # Treeview
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(pady=10, fill='both', expand=True, padx=20)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        cols = ['LoanID', 'Num', 'Equipment', 'Serial', 'Borrower', 'Phone', 'LoanDate', 'Deposit', 'Spacer']
        visual_cols = ['Num', 'Equipment', 'Serial', 'Borrower', 'Phone', 'LoanDate', 'Deposit']

        if self.is_rtl:
            visual_cols = ['Spacer'] + visual_cols[::-1]

        tree = ttk.Treeview(tree_frame, columns=cols,
                            displaycolumns=visual_cols,
                            show='headings', height=8, yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.column('Spacer', width=1, stretch=True)
        tree.heading('Spacer', text="")

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        tree.heading('LoanID', text=self.i18n[self.lang]['col_loan_id'])
        tree.heading('Num', text=self.i18n[self.lang]['col_num'])
        tree.heading('Equipment', text=self.i18n[self.lang]['col_equipment'])
        tree.heading('Serial', text=self.i18n[self.lang]['col_serial'])
        tree.heading('Borrower', text=self.i18n[self.lang]['col_borrower'])
        tree.heading('Phone', text=self.i18n[self.lang]['col_phone'])
        tree.heading('LoanDate', text=self.i18n[self.lang]['col_loan_date'])
        tree.heading('Deposit', text=self.i18n[self.lang]['col_deposit'])

        # tree.column('LoanID', width=70)
        # tree.column('Equipment', width=180)
        # tree.column('Serial', width=130)
        # tree.column('Borrower', width=180)
        # tree.column('Phone', width=120)
        # tree.column('LoanDate', width=100)
        # tree.column('Deposit', width=80)

        tree.grid(row=0, column=col_tree, sticky='nsew')
        vsb.grid(row=0, column=col_scroll, sticky='ns')
        # --- THIS IS THE FIX ---
        hsb.grid(row=1, column=0, columnspan=2, sticky='ew')
        # ---

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(col_tree, weight=1)

        # Action buttons
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(pady=20)

        ttk.Button(action_frame, text=self.i18n[self.lang]['btn_process_return_action'],
                   command=lambda: self.process_selected_return(tree),
                   style='Action.TButton').pack(side=side_left, padx=5)
        ttk.Button(action_frame, text=self.i18n[self.lang]['btn_forfeit_deposit'],
                   command=lambda: self.forfeit_selected_deposit(tree)).pack(side=side_left, padx=5)

        # Load active loans
        self.load_active_loans(tree)

    def load_active_loans(self, tree):
        """Load active loans"""
        for item in tree.get_children():
            tree.delete(item)

        loans = self.db.get_active_loans()
        for i, loan in enumerate(loans, 1):
            loan_date = datetime.strptime(loan['loan_date'],
                                          '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            tree.insert('', 'end', values=(
                loan['id'], i, loan['equipment_name'], loan['equipment_serial'],
                loan['borrower_name'], loan['borrower_phone'],
                loan_date, f"{loan['deposit_paid']:.0f}"
            ))

        self.auto_size_treeview_columns(tree)

    def search_active_loans_list(self, search_term, tree):
        """Search active loans"""
        for item in tree.get_children():
            tree.delete(item)

        if not search_term:
            self.load_active_loans(tree)
            return

        loans = self.db.search_active_loans(search_term)
        for i, loan in enumerate(loans, 1):
            loan_date = datetime.strptime(loan['loan_date'],
                                          '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            tree.insert('', 'end', values=(
                loan['id'], i, loan['equipment_name'], loan['equipment_serial'],
                loan['borrower_name'], loan['borrower_phone'],
                loan_date, f"{loan['deposit_paid']:.0f}"
            ))

        self.auto_size_treeview_columns(tree)

    def process_selected_return(self, tree):
        """Process return for selected loan"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", self.i18n[self.lang]['warn_select_loan'])
            return

        item = tree.item(selection[0])
        loan_id = item['values'][0]
        deposit_amount = item['values'][6]

        # Confirm return
        result = messagebox.askyesno(self.i18n[self.lang]['confirm_return_title'],
            self.i18n[self.lang]['confirm_return_msg'].format(amount=deposit_amount))

        if result:
            try:
                success = self.db.process_return(loan_id)
                if success:
                    messagebox.showinfo("Success",
                        self.i18n[self.lang]['success_return'].format(amount=deposit_amount))
                    self.show_process_return()
                else:
                    messagebox.showerror("Error", self.i18n[self.lang]['err_return_fail'])
            except Exception as e:
                messagebox.showerror("Error", self.i18n[self.lang]['err_generic'].format(e=str(e)))

    def forfeit_selected_deposit(self, tree):
        """Mark loan as non-returned and forfeit deposit"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", self.i18n[self.lang]['warn_select_loan'])
            return

        item = tree.item(selection[0])
        loan_id = item['values'][0]
        deposit_amount = item['values'][6]

        # Confirm forfeiture
        result = messagebox.askyesno(self.i18n[self.lang]['confirm_forfeit_title'],
            self.i18n[self.lang]['confirm_forfeit_msg'].format(amount=deposit_amount))

        if result:
            try:
                success = self.db.forfeit_deposit(loan_id)
                if success:
                    messagebox.showinfo("Success",
                        self.i18n[self.lang]['success_forfeit'].format(amount=deposit_amount))
                    self.show_process_return()
                else:
                    messagebox.showerror("Error", self.i18n[self.lang]['err_forfeit_fail'])
            except Exception as e:
                messagebox.showerror("Error", self.i18n[self.lang]['err_generic'].format(e=str(e)))

    # ============ BORROWERS SCREEN ============

    def show_borrowers(self):
        """Show borrowers management screen"""
        self.clear_window()
        self.show_global_controls(self.main_frame, self.show_borrowers)

        # --- RTL HELPER BLOCK ---
        is_rtl = self.is_rtl
        side_left = 'right' if is_rtl else 'left'
        side_right = 'left' if is_rtl else 'right'

        # Style helpers
        style_subtitle = 'Right.Subtitle.TLabel' if is_rtl else 'Subtitle.TLabel'
        style_entry = 'Right.TEntry' if is_rtl else 'TEntry'

        # For Treeview/Scrollbar
        col_tree = 1 if is_rtl else 0
        col_scroll = 0 if is_rtl else 1
        # --- END OF BLOCK ---

        # Header
        header = ttk.Frame(self.main_frame)
        header.pack(pady=10, fill='x', padx=20)

        ttk.Label(header, text=self.i18n[self.lang]['borrowers_title'],
                  style=style_subtitle).pack(side=side_left)
        ttk.Button(header, text=self.i18n[self.lang]['back_to_dashboard'],
                   command=self.show_dashboard).pack(side=side_right)

        # Search frame
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(pady=10, fill='x', padx=20)

        anchor_w = 'e' if is_rtl else 'w'  # Define anchor for the hint

        # --- Define Grid Columns for RTL ---
        if is_rtl:
            # Spacer(0) | Show(1) | Entry(2) | Label(3)
            col_spacer = 0
            col_btn_show = 1
            col_entry = 2
            col_lbl = 3
        else:  # LTR
            # Label(0) | Entry(1) | Show(2) | Spacer(3)
            col_lbl = 0
            col_entry = 1
            col_btn_show = 2
            col_spacer = 3

        # Make the SPACER column expand
        search_frame.grid_columnconfigure(col_spacer, weight=1)

        # 1. "Search:" Label
        ttk.Label(search_frame, text=self.i18n[self.lang]['search']).grid(
            row=0, column=col_lbl, padx=5, sticky=anchor_w)

        # 2. Search Entry Box
        search_var = self.search_vars['borrowers']
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20, style=style_entry, font=self.input_font)
        search_entry.grid(row=0, column=col_entry, padx=5, sticky=anchor_w)

        # 3. Hint Label (under the entry box)
        hint_style = 'Right.Small.TLabel' if is_rtl else 'Small.TLabel'
        hint_label = ttk.Label(search_frame, text=self.i18n[self.lang]['search_by_borrower'], style=hint_style)
        hint_label.grid(row=1, column=col_entry, padx=5, sticky=anchor_w)

        # 4. "Show All" Button (initially hidden)
        show_all_btn = ttk.Button(search_frame, text=self.i18n[self.lang]['show_all'])

        def on_search_change(event):
            search_term = search_var.get()
            self.search_borrowers_list(search_term, tree)
            if search_term:
                show_all_btn.grid(row=0, column=col_btn_show, rowspan=2, padx=5)
            else:
                show_all_btn.grid_forget()

        # Configure the 'Show All' button command
        show_all_btn.config(command=lambda: (
            search_var.set(''),
            self.load_all_borrowers(tree),
            on_search_change(None)
        ))

        # --- Bind the event to the entry box
        search_entry.bind("<KeyRelease>", on_search_change)

        if search_var.get():
            on_search_change(None)

        # Treeview
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(pady=10, fill='both', expand=True, padx=20)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        cols = ['ID', 'Num', 'Name', 'IDNum', 'Phone1', 'Phone2', 'Address', 'Spacer']
        visual_cols = ['Num', 'Name', 'IDNum', 'Phone1', 'Phone2', 'Address']

        if self.is_rtl:
            visual_cols = ['Spacer'] + visual_cols[::-1]

        tree = ttk.Treeview(tree_frame, columns=cols,
                            displaycolumns=visual_cols,
                            show='headings', height=8, yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.column('Spacer', width=1, stretch=True)
        tree.heading('Spacer', text="")

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        tree.heading('ID', text=self.i18n[self.lang]['col_id'])
        tree.heading('Num', text=self.i18n[self.lang]['col_num'])
        tree.heading('Name', text=self.i18n[self.lang]['col_full_name'])
        tree.heading('IDNum', text=self.i18n[self.lang]['col_id_num'])
        tree.heading('Phone1', text=self.i18n[self.lang]['col_primary_phone'])
        tree.heading('Phone2', text=self.i18n[self.lang]['col_secondary_phone'])
        tree.heading('Address', text=self.i18n[self.lang]['col_address'])

        tree.grid(row=0, column=col_tree, sticky='nsew')
        vsb.grid(row=0, column=col_scroll, sticky='ns')
        hsb.grid(row=1, column=0, columnspan=2, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(col_tree, weight=1)

        # Action buttons
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(pady=10)

        ttk.Button(action_frame, text=self.i18n[self.lang]['btn_add_borrower'],
                   command=lambda: self.add_borrower_action(tree)).pack(side=side_left, padx=5)

        ttk.Button(action_frame, text=self.i18n[self.lang]['btn_view_history'],
                   command=lambda: self.view_borrower_history(tree)).pack(side=side_left, padx=5)

        # Load all borrowers
        self.load_all_borrowers(tree)

    def load_all_borrowers(self, tree):
        """Load all borrowers"""
        for item in tree.get_children():
            tree.delete(item)

        borrowers = self.db.get_all_borrowers()
        for i, borrower in enumerate(borrowers, 1):
            tree.insert('', 'end', values=(
                borrower['id'], i, borrower['full_name'], borrower['id_number'],
                borrower['primary_phone'], borrower.get('secondary_phone') or '',
                borrower.get('address') or ''
            ))

        self.auto_size_treeview_columns(tree)

    def search_borrowers_list(self, search_term, tree):
        """Search borrowers"""
        for item in tree.get_children():
            tree.delete(item)

        if not search_term:
            self.load_all_borrowers(tree)
            return

        borrowers = self.db.search_borrower(search_term)
        for i, borrower in enumerate(borrowers, 1):
            tree.insert('', 'end', values=(
                borrower['id'], i, borrower['full_name'], borrower['id_number'],
                borrower['primary_phone'], borrower.get('secondary_phone') or '',
                borrower.get('address') or ''
            ))

        self.auto_size_treeview_columns(tree)

    def view_borrower_history(self, tree):
        """View loan history for selected borrower"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", self.i18n[self.lang]['warn_select_borrower'])
            return

        item = tree.item(selection[0])
        borrower_id = item['values'][0]
        borrower_name = item['values'][1]

        history = self.db.get_borrower_loan_history(borrower_id)

        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(self.i18n[self.lang]['history_title'].format(name=borrower_name))

        # --- REMOVED OLD GEOMETRY LINES HERE ---

        ttk.Label(dialog, text=self.i18n[self.lang]['history_for_label'].format(name=borrower_name),
                  font=('Helvetica', 14, 'bold')).pack(pady=10)

        # Treeview
        cols = ['LoanID', 'Num', 'Equipment', 'LoanDate', 'ReturnDate', 'Status', 'Deposit', 'Spacer']
        visual_cols = ['Num', 'Equipment', 'LoanDate', 'ReturnDate', 'Status', 'Deposit']

        if self.is_rtl:
            visual_cols = ['Spacer'] + visual_cols[::-1]

        hist_tree = ttk.Treeview(dialog, columns=cols, displaycolumns=visual_cols, show='headings', height=8)

        hist_tree.column('Spacer', width=1, stretch=True)
        hist_tree.heading('Spacer', text="")

        self.configure_status_tags(hist_tree)

        hist_tree.heading('LoanID', text=self.i18n[self.lang]['col_loan_id'])
        hist_tree.heading('Num', text=self.i18n[self.lang]['col_num'])
        hist_tree.heading('Equipment', text=self.i18n[self.lang]['col_equipment'])
        hist_tree.heading('LoanDate', text=self.i18n[self.lang]['col_loan_date'])
        hist_tree.heading('ReturnDate', text=self.i18n[self.lang]['col_return_date'])
        hist_tree.heading('Status', text=self.i18n[self.lang]['col_status'])
        hist_tree.heading('Deposit', text=self.i18n[self.lang]['col_deposit'])

        # Center columns
        hist_tree.column('LoanID', anchor='center', width=80)
        hist_tree.column('LoanDate', anchor='center', width=100)
        hist_tree.column('ReturnDate', anchor='center', width=100)
        hist_tree.column('Status', anchor='center', width=100)
        hist_tree.column('Deposit', anchor='center', width=80)

        hist_tree.pack(pady=10, fill='both', expand=True, padx=20)

        for i, loan in enumerate(history, 1):
            loan_date = datetime.strptime(loan['loan_date'],
                                          '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            return_date = ''
            if loan.get('actual_return_date'):
                return_date = datetime.strptime(loan['actual_return_date'],
                                                '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

            status = loan['loan_status']

            hist_tree.insert('', 'end', values=(
                loan['id'], i, loan['equipment_name'], loan_date,
                return_date, self._get_translated_status(status), f"{loan['deposit_paid']:.0f}"
            ), tags=(self._get_status_tag(status),))

        self.auto_size_treeview_columns(hist_tree)

        ttk.Button(dialog, text=self.i18n[self.lang]['close'], command=dialog.destroy).pack(pady=10)

        # --- AUTO SIZE AND CENTER ---
        self.setup_dialog_window(dialog, min_width=900)

    def add_borrower_action(self, tree):
        """Show dialog to add a new borrower directly"""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.i18n[self.lang]['title_add_borrower'])
        dialog.grab_set()

        # --- RTL Setup ---
        is_rtl = self.is_rtl
        anchor_w = 'e' if is_rtl else 'w'
        col_label = 1 if is_rtl else 0
        col_entry = 0 if is_rtl else 1
        style_label = 'Right.TLabel' if is_rtl else 'TLabel'

        # NOTE: We don't need 'style_entry' anymore because we use direct font binding
        justify_text = 'right' if is_rtl else 'left'

        ttk.Label(dialog, text=self.i18n[self.lang]['title_add_borrower'],
                  font=('Helvetica', 14, 'bold')).pack(pady=15)

        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill='both', expand=True)

        # Helper to create rows
        def create_row(row_idx, label_key, var, validator=None):
            ttk.Label(form_frame, text=self.i18n[self.lang][label_key],
                      style=style_label).grid(row=row_idx, column=col_label, sticky=anchor_w, pady=10)

            # ADDED font=self.input_font HERE
            e = ttk.Entry(form_frame, textvariable=var, width=35, font=self.input_font, justify=justify_text)

            if validator:
                e.config(validate='key', validatecommand=validator)

            e.grid(row=row_idx, column=col_entry, pady=10, sticky='ew')

        # Variables
        name_var = tk.StringVar()
        id_var = tk.StringVar()
        phone1_var = tk.StringVar()
        phone2_var = tk.StringVar()
        address_var = tk.StringVar()

        # Create Fields WITH VALIDATORS
        create_row(0, 'full_name', name_var)
        create_row(1, 'id_number', id_var, self.vcmd_id)
        create_row(2, 'primary_phone', phone1_var, self.vcmd_numbers)
        create_row(3, 'secondary_phone', phone2_var, self.vcmd_numbers)
        create_row(4, 'address', address_var)

        form_frame.columnconfigure(col_entry, weight=1)

        # Save Logic
        def save_new_borrower():
            name = name_var.get().strip()
            id_num = id_var.get().strip()
            phone = phone1_var.get().strip()

            if not name or not id_num or not phone:
                messagebox.showerror("Error", self.i18n[self.lang]['err_fill_required'])
                return

            if id_num != '-' and len(id_num) != 9:
                messagebox.showerror("Error", "ID Number must be exactly 9 digits (or '-' to skip).")
                return

            try:
                self.db.add_borrower(name, id_num, phone,
                                     phone2_var.get().strip(),
                                     address_var.get().strip())

                messagebox.showinfo("Success", self.i18n[self.lang]['success_borrower_add'])
                dialog.destroy()
                self.load_all_borrowers(tree)
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", self.i18n[self.lang]['err_borrower_exists'])
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text=self.i18n[self.lang]['save'], command=save_new_borrower).pack(side='left', padx=5)
        ttk.Button(btn_frame, text=self.i18n[self.lang]['cancel'], command=dialog.destroy).pack(side='left', padx=5)

        self.setup_dialog_window(dialog)

    # ============ REPORTS SCREEN ============

    def show_reports(self):
        """Show reports screen"""
        self.clear_window()
        self.show_global_controls(self.main_frame, self.show_reports)

        # --- RTL HELPER BLOCK ---
        is_rtl = self.is_rtl
        side_left = 'right' if is_rtl else 'left'
        side_right = 'left' if is_rtl else 'right'
        style_subtitle = 'Right.Subtitle.TLabel' if is_rtl else 'Subtitle.TLabel'
        # --- END OF BLOCK ---

        # Header
        header = ttk.Frame(self.main_frame)
        header.pack(pady=10, fill='x', padx=20)

        ttk.Label(header, text=self.i18n[self.lang]['reports_title'],
                  style=style_subtitle).pack(side=side_left)  # <-- MODIFIED
        ttk.Button(header, text=self.i18n[self.lang]['back_to_dashboard'],
                   command=self.show_dashboard).pack(side=side_right)  # <-- MODIFIED

        # Report buttons
        report_frame = ttk.Frame(self.main_frame)
        report_frame.pack(pady=50)

        ttk.Label(report_frame, text=self.i18n[self.lang]['reports_select'],
                  font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)

        # --- RTL Grid Swap ---
        col_1 = 1 if is_rtl else 0
        col_2 = 0 if is_rtl else 1
        # ---

        ttk.Button(report_frame, text=self.i18n[self.lang]['btn_inventory_report'],
                   command=self.generate_inventory_report,
                   style='Large.TButton', width=30).grid(row=1, column=col_1, padx=20, pady=15)  # <-- MODIFIED

        ttk.Button(report_frame, text=self.i18n[self.lang]['btn_loans_report'],
                   command=self.generate_loans_report,
                   style='Large.TButton', width=30).grid(row=1, column=col_2, padx=20, pady=15)  # <-- MODIFIED

    def generate_inventory_report(self):
        """Generate and open inventory report"""
        try:
            summary = self.db.get_equipment_summary()
            lost_items = self.db.get_lost_equipment()
            pdf_path = self.reports.generate_inventory_report(summary, lost_items, self.lang)
            self.reports.open_pdf(pdf_path)
            messagebox.showinfo("Success",
                self.i18n[self.lang]['success_report'].format(path=pdf_path))
        except Exception as e:
            messagebox.showerror("Error", self.i18n[self.lang]['err_report_fail'].format(e=str(e)))

    def generate_loans_report(self):
        """Generate and open loans report"""
        try:
            active_loans = self.db.get_active_loans()
            pdf_path = self.reports.generate_loans_report(active_loans, self.lang)
            self.reports.open_pdf(pdf_path)
            messagebox.showinfo("Success",
                self.i18n[self.lang]['success_report'].format(path=pdf_path))
        except Exception as e:
            messagebox.showerror("Error", self.i18n[self.lang]['err_report_fail'].format(e=str(e)))

    # ============ DATA EXPORT / IMPORT ============

    def export_to_excel(self):
        """Export all tables to a multi-sheet Excel file"""
        try:
            # 1. Ask user where to save
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                initialfile=f"System_Backup_{timestamp}.xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Export Data"
            )

            if not filename:
                return

            # 2. Fetch Data
            equip_data = self.db.get_dataframe_data('equipment')
            borrower_data = self.db.get_dataframe_data('borrower')
            loan_data = self.db.get_dataframe_data('loan')

            # 3. Create DataFrames
            df_equip = pd.DataFrame(equip_data)
            df_borrower = pd.DataFrame(borrower_data)
            df_loan = pd.DataFrame(loan_data)

            # 4. Write to Excel
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                if not df_equip.empty:
                    df_equip.to_excel(writer, sheet_name='Equipment', index=False)
                if not df_borrower.empty:
                    df_borrower.to_excel(writer, sheet_name='Borrowers', index=False)
                if not df_loan.empty:
                    df_loan.to_excel(writer, sheet_name='Loans', index=False)

            messagebox.showinfo("Success", f"Data successfully exported to:\n{filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {e}")

    def import_from_excel(self):
        """Import data from Excel (Merge/Update)"""
        filename = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Import Data"
        )

        if not filename:
            return

        confirm = messagebox.askyesno("Confirm Import",
                                      "Importing will merge data into your database.\n"
                                      "Existing items (by Serial/ID) will be updated.\n"
                                      "New items will be added.\n\n"
                                      "Do you want to proceed?")
        if not confirm:
            return

        try:
            # 1. Read Excel File
            xls = pd.ExcelFile(filename)

            # 2. Import Borrowers
            if 'Borrowers' in xls.sheet_names:
                df_borrower = pd.read_excel(xls, 'Borrowers')
                # Replace NaN with None (for SQL nulls)
                df_borrower = df_borrower.where(pd.notnull(df_borrower), None)
                for _, row in df_borrower.iterrows():
                    self.db.upsert_borrower_from_dict(row.to_dict())

            # 3. Import Equipment
            if 'Equipment' in xls.sheet_names:
                df_equip = pd.read_excel(xls, 'Equipment')
                df_equip = df_equip.where(pd.notnull(df_equip), None)
                for _, row in df_equip.iterrows():
                    self.db.upsert_equipment_from_dict(row.to_dict())

            # 4. Import Loans (Optional/Advanced)
            # Only import loans if explicitly requested (restoring backup)
            # because IDs must match exactly.
            if 'Loans' in xls.sheet_names:
                df_loan = pd.read_excel(xls, 'Loans')
                df_loan = df_loan.where(pd.notnull(df_loan), None)
                for _, row in df_loan.iterrows():
                    self.db.import_loan_record(row.to_dict())

            messagebox.showinfo("Success", "Import completed successfully!")

            # Refresh whatever view we are on
            self.show_dashboard()

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import data: {e}")

    def load_configuration(self):
        """Load config or create default if missing"""
        self.config = configparser.ConfigParser()

        # Config file sits next to the database
        config_path = os.path.join(os.path.dirname(self.db.db_path), 'config.ini')

        if not os.path.exists(config_path):
            # CREATE DEFAULT CONFIG
            self.config['General'] = {
                'institution_name': 'Medical Loan Center'
            }
            self.config['PDF_Terms'] = {
                'term1': '1. The borrower agrees to return the equipment in good condition.',
                'term2': '2. The deposit will be refunded upon return.',
                'term3': '3. The borrower is responsible for damages.',
                'term4': '4. Equipment must be returned on time.'
            }
            with open(config_path, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        else:
            # READ EXISTING
            self.config.read(config_path, encoding='utf-8')


def main():
    # --- LOGGING SETUP ---
    # Log file will be created next to the executable/script
    logging.basicConfig(
        filename='app_errors.log',
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Handle uncaught exceptions (crashes)
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        # Optional: Show a popup to the user saying "Check the logs"
        messagebox.showerror("Critical Error", f"An error occurred. See app_errors.log.\n\n{exc_value}")

    sys.excepthook = handle_exception

    root = tk.Tk()
    app = MedicalEquipmentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()