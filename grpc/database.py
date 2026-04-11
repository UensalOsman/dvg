import sqlite3
import logging
from config import LOG_LEVEL

# Logging konfigurieren
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
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
                               supplier TEXT NOT NULL,
                               amount REAL NOT NULL,
                               currency TEXT NOT NULL,
                               due_date TEXT NOT NULL,
                               description TEXT NOT NULL,
                               created_at TEXT DEFAULT CURRENT_TIMESTAMP
                               )''')


    def create(self, invoice_id, supplier, amount, currency, due_date, description):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO invoices
                   (invoice_id, supplier, amount, currency, due_date, description)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (invoice_id, supplier, amount, currency, due_date, description)
            )


    def get(self, invoice_id):
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            'SELECT * FROM invoices WHERE invoice_id = ?',
            (invoice_id,)
        ).fetchone()

        conn.close()
        if row:
            logger.info(f"Rechnung gefunden: {invoice_id}")
        else:
            logger.warning(f"Rechnung nicht gefunden: {invoice_id}")
        return row

        
    
