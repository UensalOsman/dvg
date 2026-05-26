import sqlite3
import logging
from config import LOG_LEVEL

# Logging konfigurieren
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class InvoiceDB:

    def __init__(self, db_path="invoices.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):

        logger.info("Connection to database...")
        with sqlite3.connect(self.db_path) as connection:
            logger.info(f"Connected to {self.db_path}")
            connection.execute('''CREATE TABLE IF NOT EXISTS invoices (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               invoice_id TEXT NOT NULL UNIQUE,
                               invoice_name TEXT NOT NULL UNIQUE,
                               vendor TEXT NOT NULL,
                               amount REAL NOT NULL,
                               currency TEXT NOT NULL,
                               due_date TEXT NOT NULL,
                               description TEXT NOT NULL,
                               created_at TEXT DEFAULT CURRENT_TIMESTAMP
                               )''')
        
        # Logging the table
        cursor = connection.execute("PRAGMA table_info(invoices)")
        columns = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
        logger.info(f"Table columns: {columns}")


    def create(self, invoice_id, invoice_name, vendor, amount, currency, due_date, description):
        try:
            logging.info(f"Insert new invoice with ID: {invoice_id}")
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    '''INSERT OR REPLACE INTO invoices
                    (invoice_id, invoice_name, vendor, amount, currency, due_date, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (invoice_id, invoice_name, vendor, amount, currency, due_date, description)
                )
            logging.info(f"Invoice inserted or updated: {invoice_id}")
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error while creating invoice {invoice_id}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            

    def get(self, invoice_id):
        try:
            logging.info(f"Fetching invoice with ID: {invoice_id}")
            conn = sqlite3.connect(self.db_path)
            row = conn.execute(
                'SELECT * FROM invoices WHERE invoice_id = ?',
                (invoice_id,)
            ).fetchone()

            if row:
                logger.info(f"Invoice found: {invoice_id}")
                return row
            else: 
                logger.info(f"Invoice not found: {invoice_id}")
            conn.close()

        except sqlite3.DatabaseError as e:
            logging.error(f"Database error while fetching invoice {invoice_id} : {e}")

    
    def clear(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DROP TABLE IF EXISTS invoices")
        conn.commit()
        conn.close()
            

        
    
