import grpc
import json
import pika
from datetime import datetime

from protos import invoice_pb2,invoice_pb2_grpc
from config import (
    GRPC_SERVER,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_QUEUE,
    RABBITMQ_EXCHANGE,
    RABBITMQ_ROUTING_KEY,
)

def insert_invoice(name, supplier, amount, currency, due_date, description):
    """
    Rechnung per grpc an grpc server schicken.
    Gibt true zurück wenn erfolgreich, sonst false.
    """
    # Verbindung zum grpc server aufbauen
    channel = grpc.insecure_channel(GRPC_SERVER)
    stub = invoice_pb2_grpc.InvoiceServiceStub(channel)

    # Request objekt erstellen (wie in der proto definiert)
    request = invoice_pb2.InvoiceRequest(
        name=name,
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
            print(f"[gRPC] Rechnung {response.invoice_id}: {response.message}")
            return response.invoice_id
        else:
            print(f"[gRPC] Fehler: {response.message}")
            return False
    except grpc.RpcError as e:
        print(f"[gRPC] Server nicht erreichbar: {e.code().name}")
        return False
    

def get_invoice(invoice_id):
    channel = grpc.insecure_channel(GRPC_SERVER)
    stub = invoice_pb2_grpc.InvoiceServiceStub(channel)

    try:
        request = invoice_pb2.InvoiceQuery(invoice_id=invoice_id)
        response = stub.GetInvoice(request)
        
        if response.success:
            print(f"[gRPC] Rechnung gefunden: {response.invoice_id} / {response.name}")
        else:
            print(f"[gRPC] Fehler: {response.message}")
            return False
    except grpc.RpcError as e:
        print(f"[gRPC] Server nicht erreichbar: {e.code().name}")
        return False

def send_invoice(invoice_id, name, amount, currency, recipient):
    """
    Zahlungsauftrag als JSON in rabbitmq ablegen.
    Zahlungssystem holt ihn dort ab.
    """

    nachricht = {
        "invoice_id": invoice_id,
        "name": name,
        "amount": amount,
        "currency": currency,
        "recipient": recipient,
        "timestamp": datetime.now().isoformat(),
    }

    try:
        # verbindung zu rabbitmq
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            )
        )
        channel = connection.channel()

        # exchange + queue erstellen und binden
        channel.exchange_declare(
            exchange=RABBITMQ_EXCHANGE,
            exchange_type="direct",
            durable=True
        )
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.queue_bind(
            exchange=RABBITMQ_EXCHANGE,
            queue=RABBITMQ_QUEUE,
            routing_key=RABBITMQ_ROUTING_KEY
        )

        # nachricht ueber exchange in die queue schicken
        channel.basic_publish(
            exchange=RABBITMQ_EXCHANGE,
            routing_key=RABBITMQ_ROUTING_KEY,
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

    try:
        while True:
            print("1 - Rechnung erstellen")
            print("2 - Rechnung abrufen")
            print("3 - Beenden")
            choice = input("\nAuswahl: ")

            match choice:
                case "1":
                    NAME = input("Invoice Name: ")
                    SUPPLIER = input("Supplier: ")
                    AMOUNT = float(input("Amount: "))
                    CURRENCY = "EUR"
                    DUE_DATE = input("Due Date: ")
                    DESCRIPTION = input("Description: ")

                    print("\nSchritt 1: Rechnung per gRPC speichern...")
                    response_invoice_id = insert_invoice(NAME, SUPPLIER, AMOUNT, CURRENCY, DUE_DATE, DESCRIPTION)

                    if response_invoice_id:
                        print("\nSchritt 2: Zahlungsauftrag an RabbitMQ senden...")
                        send_invoice(response_invoice_id, NAME, AMOUNT, CURRENCY, SUPPLIER)
                    else:
                        print("\nZahlung wird NICHT ausgelöst")

                case "2":
                    invoice_id = input("Invoice ID: ")
                    get_invoice(invoice_id)

                case "3":
                    print("\n=== Client beendet ===")
                    break

                case _:
                    print("Ungültige Auswahl, bitte 1-3 eingeben.")

            print()

    except KeyboardInterrupt:
        print("\n\n=== Client beendet ===")
