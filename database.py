"""
Database module for Medical Equipment Loan Management System
Handles all database operations using SQLite
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os
import sys


class Database:
    def __init__(self, db_path: str = None):
        """Initialize database connection and create tables if they don't exist"""
        if db_path is None:
            if getattr(sys, 'frozen', False):
                # If running as compiled .exe, put DB next to the .exe file
                application_path = os.path.dirname(sys.executable)
            else:
                # If running as script, put DB next to the script
                application_path = os.path.dirname(os.path.abspath(__file__))

            self.db_path = os.path.join(application_path, "medical_equipment.db")
        else:
            self.db_path = db_path

        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
    
    def create_tables(self):
        """Create all necessary tables"""
        cursor = self.conn.cursor()
        
        # Equipment table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                description TEXT,
                serial_number TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'In-Stock',
                deposit_amount REAL NOT NULL,
                created_date TEXT NOT NULL
            )
        ''')
        
        # Borrower table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS borrower (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                id_number TEXT UNIQUE NOT NULL,
                primary_phone TEXT NOT NULL,
                secondary_phone TEXT,
                address TEXT,
                created_date TEXT NOT NULL
            )
        ''')
        
        # Loan table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                borrower_id INTEGER NOT NULL,
                equipment_id INTEGER NOT NULL,
                loan_date TEXT NOT NULL,
                deposit_paid REAL NOT NULL,
                deposit_status TEXT NOT NULL DEFAULT 'Held',
                expected_return_date TEXT,
                actual_return_date TEXT,
                donation_amount REAL DEFAULT 0,
                loan_status TEXT NOT NULL DEFAULT 'Active',
                notes TEXT,
                FOREIGN KEY (borrower_id) REFERENCES borrower(id),
                FOREIGN KEY (equipment_id) REFERENCES equipment(id)
            )
        ''')
        
        self.conn.commit()
    
    # ============ EQUIPMENT METHODS ============
    
    def add_equipment(self, item_name: str, description: str, serial_number: str, 
                     deposit_amount: float) -> int:
        """Add new equipment to inventory"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO equipment (item_name, description, serial_number, 
                                 deposit_amount, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (item_name, description, serial_number, deposit_amount, 
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_equipment(self, equipment_id: int) -> Optional[Dict]:
        """Get equipment by ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM equipment WHERE id = ?', (equipment_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_equipment(self) -> List[Dict]:
        """Get all equipment"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM equipment ORDER BY item_name')
        return [dict(row) for row in cursor.fetchall()]
    
    def search_equipment(self, search_term: str) -> List[Dict]:
        """Search equipment by name or serial number"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM equipment 
            WHERE item_name LIKE ? OR serial_number LIKE ?
            ORDER BY item_name
        ''', (f'%{search_term}%', f'%{search_term}%'))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_available_equipment(self, item_name: str = None) -> List[Dict]:
        """Get equipment that is available (In-Stock status)"""
        cursor = self.conn.cursor()
        if item_name:
            cursor.execute('''
                SELECT * FROM equipment 
                WHERE status = 'In-Stock' AND item_name LIKE ?
                ORDER BY item_name
            ''', (f'%{item_name}%',))
        else:
            cursor.execute('''
                SELECT * FROM equipment 
                WHERE status = 'In-Stock'
                ORDER BY item_name
            ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def update_equipment_status(self, equipment_id: int, status: str):
        """Update equipment status"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE equipment SET status = ? WHERE id = ?
        ''', (status, equipment_id))
        self.conn.commit()
    
    def update_equipment(self, equipment_id: int, item_name: str, description: str,
                        serial_number: str, deposit_amount: float):
        """Update equipment details"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE equipment 
            SET item_name = ?, description = ?, serial_number = ?, deposit_amount = ?
            WHERE id = ?
        ''', (item_name, description, serial_number, deposit_amount, equipment_id))
        self.conn.commit()
    
    def get_equipment_summary(self) -> List[Dict]:
        """Get summary of ACTIVE equipment (excludes Lost items)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                item_name,
                COUNT(*) as total_count,
                SUM(CASE WHEN status = 'In-Stock' OR status = 'Returned' THEN 1 ELSE 0 END) as in_stock,
                SUM(CASE WHEN status = 'On-Loan' THEN 1 ELSE 0 END) as on_loan
            FROM equipment
            WHERE status != 'Lost' 
            GROUP BY item_name
            ORDER BY item_name
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    # ============ BORROWER METHODS ============
    
    def add_borrower(self, full_name: str, id_number: str, primary_phone: str,
                    secondary_phone: str = None, address: str = None) -> int:
        """Add new borrower"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO borrower (full_name, id_number, primary_phone, 
                                secondary_phone, address, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (full_name, id_number, primary_phone, secondary_phone, address,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_borrower(self, borrower_id: int) -> Optional[Dict]:
        """Get borrower by ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM borrower WHERE id = ?', (borrower_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def search_borrower(self, search_term: str) -> List[Dict]:
        """Search borrower by name, ID number, or phone"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM borrower 
            WHERE full_name LIKE ? OR id_number LIKE ? OR primary_phone LIKE ?
            ORDER BY full_name
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_borrower_by_id_number(self, id_number: str) -> Optional[Dict]:
        """Get borrower by ID number"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM borrower WHERE id_number = ?', (id_number,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_borrower(self, borrower_id: int, full_name: str, id_number: str,
                       primary_phone: str, secondary_phone: str = None, 
                       address: str = None):
        """Update borrower details"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE borrower 
            SET full_name = ?, id_number = ?, primary_phone = ?, 
                secondary_phone = ?, address = ?
            WHERE id = ?
        ''', (full_name, id_number, primary_phone, secondary_phone, address, borrower_id))
        self.conn.commit()
    
    def get_all_borrowers(self) -> List[Dict]:
        """Get all borrowers"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM borrower ORDER BY full_name')
        return [dict(row) for row in cursor.fetchall()]
    
    # ============ LOAN METHODS ============
    
    def create_loan(self, borrower_id: int, equipment_id: int, deposit_paid: float,
                   donation_amount: float = 0, expected_return_date: str = None,
                   notes: str = None) -> int:
        """Create new loan transaction"""
        cursor = self.conn.cursor()
        loan_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO loan (borrower_id, equipment_id, loan_date, deposit_paid,
                            donation_amount, expected_return_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (borrower_id, equipment_id, loan_date, deposit_paid, 
              donation_amount, expected_return_date, notes))
        
        loan_id = cursor.lastrowid
        
        # Update equipment status to On-Loan
        self.update_equipment_status(equipment_id, 'On-Loan')
        
        self.conn.commit()
        return loan_id
    
    def get_loan(self, loan_id: int) -> Optional[Dict]:
        """Get loan by ID with joined borrower and equipment data"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                l.*,
                b.full_name as borrower_name,
                b.id_number as borrower_id_number,
                b.primary_phone as borrower_phone,
                b.secondary_phone as borrower_secondary_phone,
                b.address as borrower_address,
                e.item_name as equipment_name,
                e.serial_number as equipment_serial,
                e.description as equipment_description
            FROM loan l
            JOIN borrower b ON l.borrower_id = b.id
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.id = ?
        ''', (loan_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_active_loans(self) -> List[Dict]:
        """Get all active loans with joined data"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                l.*,
                b.full_name as borrower_name,
                b.id_number as borrower_id_number,
                b.primary_phone as borrower_phone,
                e.item_name as equipment_name,
                e.serial_number as equipment_serial
            FROM loan l
            JOIN borrower b ON l.borrower_id = b.id
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.loan_status = 'Active'
            ORDER BY l.loan_date DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def search_active_loans(self, search_term: str) -> List[Dict]:
        """Search active loans by borrower name, ID, or equipment"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                l.*,
                b.full_name as borrower_name,
                b.id_number as borrower_id_number,
                b.primary_phone as borrower_phone,
                e.item_name as equipment_name,
                e.serial_number as equipment_serial
            FROM loan l
            JOIN borrower b ON l.borrower_id = b.id
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.loan_status = 'Active' 
                AND (b.full_name LIKE ? OR b.id_number LIKE ? 
                     OR e.item_name LIKE ? OR e.serial_number LIKE ?)
            ORDER BY l.loan_date DESC
        ''', (f'%{search_term}%', f'%{search_term}%', 
              f'%{search_term}%', f'%{search_term}%'))
        return [dict(row) for row in cursor.fetchall()]
    
    def process_return(self, loan_id: int) -> bool:
        """Process equipment return"""
        cursor = self.conn.cursor()
        return_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get loan details
        loan = self.get_loan(loan_id)
        if not loan or loan['loan_status'] != 'Active':
            return False
        
        # Update loan
        cursor.execute('''
            UPDATE loan 
            SET actual_return_date = ?, 
                loan_status = 'Returned',
                deposit_status = 'Returned'
            WHERE id = ?
        ''', (return_date, loan_id))
        
        # Update equipment status back to In-Stock
        self.update_equipment_status(loan['equipment_id'], 'In-Stock')
        
        self.conn.commit()
        return True
    
    def forfeit_deposit(self, loan_id: int) -> bool:
        """Mark loan as not returned and forfeit deposit"""
        cursor = self.conn.cursor()
        
        # Get loan details
        loan = self.get_loan(loan_id)
        if not loan or loan['loan_status'] != 'Active':
            return False
        
        # Update loan
        cursor.execute('''
            UPDATE loan 
            SET loan_status = 'Not Returned',
                deposit_status = 'Forfeited'
            WHERE id = ?
        ''', (loan_id,))
        
        # Update equipment status to Lost/Retired
        self.update_equipment_status(loan['equipment_id'], 'Lost')
        
        self.conn.commit()
        return True
    
    def get_borrower_loan_history(self, borrower_id: int) -> List[Dict]:
        """Get loan history for a borrower"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                l.*,
                e.item_name as equipment_name,
                e.serial_number as equipment_serial
            FROM loan l
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.borrower_id = ?
            ORDER BY l.loan_date DESC
        ''', (borrower_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_loans(self) -> List[Dict]:
        """Get all loans with joined data"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                l.*,
                b.full_name as borrower_name,
                b.id_number as borrower_id_number,
                b.primary_phone as borrower_phone,
                e.item_name as equipment_name,
                e.serial_number as equipment_serial
            FROM loan l
            JOIN borrower b ON l.borrower_id = b.id
            JOIN equipment e ON l.equipment_id = e.id
            ORDER BY l.loan_date DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_lost_equipment(self) -> List[Dict]:
        """Get list of all equipment marked as Lost"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM equipment 
            WHERE status = 'Lost'
            ORDER BY item_name
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def delete_equipment(self, equipment_id: int):
        """
        Delete equipment and its associated history.
        WARNING: This removes the item and all loan records associated with it.
        """
        cursor = self.conn.cursor()
        # First, delete associated loans to prevent foreign key errors or orphan data
        cursor.execute('DELETE FROM loan WHERE equipment_id = ?', (equipment_id,))
        # Then delete the equipment
        cursor.execute('DELETE FROM equipment WHERE id = ?', (equipment_id,))
        self.conn.commit()

    # ============ BULK IMPORT/EXPORT HELPERS ============

    def get_dataframe_data(self, table_name: str) -> List[Dict]:
        """Fetch all data from a table for export"""
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM {table_name}')
        return [dict(row) for row in cursor.fetchall()]

    def upsert_borrower_from_dict(self, data: dict):
        """Insert or Update borrower based on ID Number"""
        cursor = self.conn.cursor()
        # Check if exists by unique ID Number
        cursor.execute('SELECT id FROM borrower WHERE id_number = ?', (data['id_number'],))
        row = cursor.fetchone()

        if row:
            # Update existing
            cursor.execute('''
                UPDATE borrower 
                SET full_name=?, primary_phone=?, secondary_phone=?, address=?
                WHERE id_number=?
            ''', (data['full_name'], data['primary_phone'],
                  data.get('secondary_phone'), data.get('address'), data['id_number']))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO borrower (full_name, id_number, primary_phone, secondary_phone, address, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['full_name'], data['id_number'], data['primary_phone'],
                  data.get('secondary_phone'), data.get('address'),
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()

    def upsert_equipment_from_dict(self, data: dict):
        """Insert or Update equipment based on Serial Number"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM equipment WHERE serial_number = ?', (data['serial_number'],))
        row = cursor.fetchone()

        if row:
            # Update existing (Name, Desc, Deposit, Status)
            cursor.execute('''
                UPDATE equipment 
                SET item_name=?, description=?, deposit_amount=?, status=?
                WHERE serial_number=?
            ''', (data['item_name'], data.get('description'),
                  data['deposit_amount'], data['status'], data['serial_number']))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO equipment (item_name, description, serial_number, status, deposit_amount, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['item_name'], data.get('description'), data['serial_number'],
                  data.get('status', 'In-Stock'), data['deposit_amount'],
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()

    def import_loan_record(self, data: dict):
        """
        Safely import a loan record.
        WARNING: This assumes Borrower ID and Equipment ID in Excel match the Database IDs.
        Best used for restoring backups.
        """
        cursor = self.conn.cursor()

        # We try to insert exactly as is (preserving history)
        # If ID exists, we replace it.
        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = list(data.values())

        sql = f'INSERT OR REPLACE INTO loan ({keys}) VALUES ({placeholders})'
        try:
            cursor.execute(sql, values)
            self.conn.commit()
        except Exception as e:
            print(f"Skipping loan import due to error: {e}")