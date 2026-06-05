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

            # FKs sind in SQLite sind standardmäßig aus
            connection.execute("PRAGMA foreign_keys = ON")

            # Rechnungsdaten Tabelle
            connection.execute('''CREATE TABLE IF NOT EXISTS invoices (
                               id              INTEGER PRIMARY KEY AUTOINCREMENT,
                               invoice_id      TEXT NOT NULL UNIQUE,
                               invoice_name    TEXT NOT NULL UNIQUE,
                               invoice_date    TEXT NOT NULL,
                               supplier_name   TEXT NOT NULL, 
                               vendor_number   TEXT NOT NULL,
                               customer_number TEXT,
                               amount          REAL NOT NULL, 
                               currency        TEXT NOT NULL,
                               due_date        TEXT NOT NULL,
                               description     TEXT NOT NULL,
                               created_at      TEXT DEFAULT CURRENT_TIMESTAMP
                               )''')
            
            # Rechnungsposten - 1:n zu invoices
            connection.execute('''CREATE TABLE IF NOT EXISTS invoice_positions (
                               id             INTEGER PRIMARY KEY AUTOINCREMENT,
                               invoice_ref    INTEGER NOT NULL,        
                               position_no    INTEGER NOT NULL,       
                               article        TEXT NOT NULL,           
                               quantity       REAL NOT NULL,          
                               unit           TEXT,                  
                               unit_price_net REAL NOT NULL,          
                               tax_rate       REAL NOT NULL,           
                               FOREIGN KEY (invoice_ref) REFERENCES invoices(id) ON DELETE CASCADE
                               )''')
        
            # Logging the table
            for table in ("invoices", "invoice_positions"):
                cursor = connection.execute(f"PRAGMA table_info({table})")
                columns = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
                logger.info(f"Table '{table}' columns: {columns}")


    def create(self, invoice_id, invoice_name, invoice_date, supplier_name, vendor_number, customer_number,
               amount, currency, due_date, description, positions=None):
        positions = positions or []        
        try:
            logger.info(f"Insert invoice {invoice_id} mit {len(positions)} Positionen")
            with sqlite3.connect(self.db_path) as conn:    
                cursor = conn.execute(
                    '''INSERT OR REPLACE INTO invoices
                    (invoice_id, invoice_name, invoice_date, supplier_name, vendor_number, customer_number,
                    amount, currency, due_date, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (invoice_id, invoice_name, invoice_date, supplier_name, vendor_number, customer_number,
                    amount, currency, due_date, description)
                )

                ref = cursor.lastrowid    

                if positions:
                    conn.executemany(
                        '''INSERT INTO invoice_positions
                        (invoice_ref, position_no, article, quantity, unit, unit_price_net, tax_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        [
                            (ref, p["position_no"], p["article"], p["quantity"],
                            p.get("unit"), p["unit_price_net"], p["tax_rate"])
                            for p in positions
                        ]
                    )
            logger.info(f"Invoice gespeichert: {invoice_id} ({len(positions)} Positionen)")
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error while creating invoice {invoice_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            

    def get(self, invoice_id):
        try:
            logger.info(f"Fetching invoice with ID: {invoice_id}")
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    'SELECT * FROM invoices WHERE invoice_id = ?',
                    (invoice_id,)
                ).fetchone()
            if row:
                logger.info(f"Invoice found: {invoice_id}")
                return row
            logger.info(f"Invoice not found: {invoice_id}")
            return None
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error while fetching invoice {invoice_id}: {e}")
            return None

    
    def clear(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DROP TABLE IF EXISTS invoice_positions")
        conn.execute("DROP TABLE IF EXISTS invoices")
        conn.commit()
        conn.close()
            

        
    
