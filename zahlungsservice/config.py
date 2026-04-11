# zahlungssystem/config.py
import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "avg")
RABBITMQ_QUEUE = "payment-queue"
RABBITMQ_EXCHANGE = "payment-exchange"
RABBITMQ_ROUTING_KEY = "payment"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
