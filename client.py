import grpc
import json
import pika
from datetime import datetime

import invoice_pb2
import invoice_pb2_grpc


GRPC_SERVER = "localhost:50051"          # Marios gRPC Server
RABBITMQ_HOST = "localhost"              # RabbitMQ Docker Container
RABBITMQ_QUEUE = "payment_queue"         # Name der Queue


def speichere_rechnung(invoice_id, supplier, amount, currency, due_date, description):
    """
    Schritt 1: Rechnung per gRPC an Marios Server schicken.
    Gibt True zurück wenn erfolgreich, sonst False.
    """
    # Verbindung zum grpc server aufbauen
    channel = grpc.insecure_channel(GRPC_SERVER)
    stub = invoice_pb2_grpc.InvoiceServiceStub(channel)

    # Request objekt erstellen (wie in der proto definiert)
    request = invoice_pb2.InvoiceRequest(
        invoice_id=invoice_id,
        supplier=supplier,
        amount=amount,
        currency=currency,
        due_date=due_date,
        description=description,
    )

    try:
        # Funktion auf dem server aufrufen
        response = stub.CreateInvoice(request)
        if response.success:
            print(f"[gRPC] Rechnung {response.invoice_id} gespeichert: {response.message}")
            return True
        else:
            print(f"[gRPC] Fehler: {response.message}")
            return False
    except grpc.RpcError as e:
        print(f"[gRPC] Server nicht erreichbar: {e.code().name}")
        return False


def sende_zahlungsauftrag(invoice_id, amount, currency, recipient):
    """
    Schritt 2: Zahlungsauftrag als JSON in RabbitMQ ablegen.
    Jetons Zahlungssystem holt ihn dort ab.
    """
    # Nachricht im vereinbarten json format
    nachricht = {
        "invoice_id": invoice_id,
        "amount": amount,
        "currency": currency,
        "recipient": recipient,
        "timestamp": datetime.now().isoformat(),
    }

    try:
        # verbindung zu rabbitmq
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()

        # queue erstellen
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

        # nachricht in die queue schicken
        channel.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(nachricht),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Nachricht überlebt rabbitmq neustart
            ),
        )

        print(f"[RabbitMQ] Zahlungsauftrag gesendet: {nachricht}")
        connection.close()
        return True
    except pika.exceptions.AMQPConnectionError:
        print("[RabbitMQ] Verbindung fehlgeschlagen (Docker container checken)")
        return False


if __name__ == "__main__":
    print("=== Rechnungs-Client ===\n")

    # Bsp Rechnung
    INVOICE_ID = "R-001"
    SUPPLIER = "Firma X"
    AMOUNT = 500.00
    CURRENCY = "EUR"
    DUE_DATE = "2026-05-01"
    DESCRIPTION = "Büromaterial März 2026"

    # Rechnung speichern
    print("Schritt 1: Rechnung per gRPC speichern...")
    erfolg = speichere_rechnung(INVOICE_ID, SUPPLIER, AMOUNT, CURRENCY, DUE_DATE, DESCRIPTION)

    #wenn Speichern geklappt hat Zahlung auslösen
    if erfolg:
        print("\nSchritt 2: Zahlungsauftrag an RabbitMQ senden...")
        sende_zahlungsauftrag(INVOICE_ID, AMOUNT, CURRENCY, SUPPLIER)
    else:
        print("\nZahlung wird NICHT ausgelöst (Rechnung konnte nicht gespeichert werden)")

    print("\n=== Fertig ===")