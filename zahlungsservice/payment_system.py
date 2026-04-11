import pika
import pika.exceptions
import json
import logging
from typing import Dict, Any
from config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_QUEUE,
    RABBITMQ_EXCHANGE,
    RABBITMQ_ROUTING_KEY,
    LOG_LEVEL,
)

# Logging konfigurieren
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PaymentSystem:
    """Zahlungssystem: Konsumiert Zahlungsaufträge von RabbitMQ"""
    
    def __init__(self):
        self.connection = None
        self.channel = None

    def _validate_payment(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Zahlungsauftrag validieren"""
        required_fields = ["invoice_id", "amount", "currency", "recipient", "timestamp"]

        # Pflichtfelder prüfen
        for field in required_fields:
            if field not in data:
                return False, f"Pflichtfeld '{field}' fehlt"

        # Betrag prüfen
        try:
            amount = float(data["amount"])
            if amount <= 0:
                return False, "Betrag muss > 0 sein"
        except (ValueError, TypeError):
            return False, "Betrag muss eine Zahl sein"

        # Währung prüfen (ISO 4217: 3 Grossbuchstaben)
        currency = data.get("currency")
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isupper():
            return False, "Waehrung muss ein 3-stelliger ISO-Code in Grossbuchstaben sein (z.B. EUR)"

        return True, "OK"
        
    def _process_payment(self, data: Dict[str, Any]) -> bool:
        """Zahlungsauftrag verarbeiten"""
        # 1. Validieren
        is_valid, message = self._validate_payment(data)
        if not is_valid:
            logger.error(f"Validierungsfehler: {message}")
            return False

        # 2. Speichern
        if not self._save_payment(data):
            return False

        # 3. Loggen
        logger.info(f"Zahlung verarbeitet: {data['invoice_id']} - {data['amount']} {data['currency']} an {data['recipient']}")
        return True

    def _callback(self, ch, method, properties, body):
        """Callback für jede empfangene Nachricht"""
        try:
            # JSON parsen
            data = json.loads(body)
            logger.info(f"Nachricht empfangen: {data['invoice_id']}")

            # Verarbeiten
            if self._process_payment(data):
                # ACK senden (Nachricht als verarbeitet markieren)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                # NACK ohne requeue (invalide oder duplikate Nachricht verwerfen)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except json.JSONDecodeError:
            logger.error(f"JSON Parse-Fehler: {body}")
            ch.basic_ack(delivery_tag=method.delivery_tag)  # ACK: invalide Nachricht verwerfen
        except Exception as e:
            logger.error(f"Fehler bei Verarbeitung: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def connect(self):
        """Mit RabbitMQ verbinden"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    connection_attempts=3,
                    retry_delay=2
                )
            )
            self.channel = self.connection.channel()
            
            # Exchange + Queue deklarieren und binden
            self.channel.exchange_declare(
                exchange=RABBITMQ_EXCHANGE,
                exchange_type="direct",
                durable=True
            )
            self.channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            self.channel.queue_bind(
                exchange=RABBITMQ_EXCHANGE,
                queue=RABBITMQ_QUEUE,
                routing_key=RABBITMQ_ROUTING_KEY
            )
            
            # QoS: Nur 1 Nachricht gleichzeitig verarbeiten
            self.channel.basic_qos(prefetch_count=1)
            
            logger.info(f"Mit RabbitMQ verbunden ({RABBITMQ_HOST}:{RABBITMQ_PORT})")
            logger.info(f"Exchange: {RABBITMQ_EXCHANGE}")
            logger.info(f"Queue: {RABBITMQ_QUEUE}")
            logger.info(f"Routing-Key: {RABBITMQ_ROUTING_KEY}")
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"RabbitMQ Verbindungsfehler: {e}")
            raise
    
    def start_consuming(self):
        """Mit dem Konsumieren von Nachrichten starten"""
        try:
            logger.info("Zahlungssystem gestartet - warte auf Zahlungsauftraege...")
            
            if self.channel is None:
                raise RuntimeError("Channel not initialized. Call connect() first.")
            
            self.channel.basic_consume(
                queue=RABBITMQ_QUEUE,
                on_message_callback=self._callback,
                auto_ack=False  # Manuelles ACK
            )
            
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Zahlungssystem gestoppt (Ctrl+C)")
            self.stop()
        except Exception as e:
            logger.error(f"Fehler beim Konsumieren: {e}")
            raise
    
    def stop(self):
        """Zahlungssystem beenden"""
        if self.channel:
            self.channel.stop_consuming()
        if self.connection:
            self.connection.close()
        logger.info("Verbindung geschlossen")


if __name__ == "__main__":
    system = PaymentSystem()
    system.connect()
    system.start_consuming()
