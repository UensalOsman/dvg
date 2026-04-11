# zahlungssystem/config.py
import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_QUEUE = "payment_queue"
DB_FILE = os.getenv("DB_FILE", "payments.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")