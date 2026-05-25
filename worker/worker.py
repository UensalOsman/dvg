import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from pyzeebe import ZeebeWorker, ZeebeTaskRouter, create_camunda_cloud_channel


HIER = os.path.dirname(os.path.abspath(__file__))
CLIENT_ORDNER = os.path.join(HIER, "..", "client")
sys.path.insert(0, CLIENT_ORDNER)
from client import insert_invoice, send_invoice  # noqa: E402

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("sprint4-worker")

JOB_TYPE_METADATA = os.environ["JOB_TYPE_METADATA"]
JOB_TYPE_PAYMENT = os.environ["JOB_TYPE_PAYMENT"]


# channel = create_camunda_cloud_channel(
#     client_id=os.environ["ZEEBE_CLIENT_ID"],
#     client_secret=os.environ["ZEEBE_CLIENT_SECRET"],
#     cluster_id=os.environ["ZEEBE_CLUSTER_ID"],
#     region=os.environ["ZEEBE_REGION"],
# )

router = ZeebeTaskRouter()

# Handler zum Metadaten speichern
@router.task(task_type=JOB_TYPE_METADATA)  
async def handle_save_metadata(
    supplier: str,
    amount: float,
    dueDate: str,
    invoiceName: str,
    currency: str,
    description: str = "",
    channel: str = "",
):
    log.info("Job '%s' empfangen: supplier=%s, amount=%s, invoiceName=%s",
             JOB_TYPE_METADATA, supplier, amount, invoiceName)

    invoice_id = insert_invoice(
        invoice_name=invoiceName,
        supplier=supplier,
        amount=amount,
        currency=currency,
        due_date=dueDate,
        description=f"{description}. Rechnung von {supplier}, Eingangskanal {channel}",
    )

    if not invoice_id:
        # Fehler -> Job fehlschlagen lassen. Zeebe versucht es erneut
        # (Retries) bzw. erzeugt einen Incident in Operate, der sichtbar ist.
        log.error("gRPC-Service nicht erreichbar - Job wird fehlschlagen")
        raise ConnectionError("gRPC-Service nicht erreichbar")

    log.info("Metadaten gespeichert, invoice_id=%s", invoice_id)

    # Output-Variable: die invoice_id fliesst zurueck in den Prozess und
    # wird spaeter beim Zahlungs-Task wieder gebraucht.
    return {"invoiceId": invoice_id}


#Handler zum Zahlungsverkehr ausführen
@router.task(task_type=JOB_TYPE_PAYMENT) 
async def handle_execute_payment(
    supplier: str,
    amount: float,
    invoiceName: str,
    invoiceId: str,
    currency: str,
):
    log.info("Job '%s' empfangen: invoiceId=%s, supplier=%s, amount=%s",
             JOB_TYPE_PAYMENT, invoiceId, supplier, amount)

    ok = send_invoice(
        invoice_id=invoiceId,
        invoice_name=invoiceName,
        amount=amount,
        currency=currency,
        recipient=supplier,
    )

    # send_invoice() gibt True bei Erfolg, False bei RabbitMQ-Problemen.
    if not ok:
        log.error("RabbitMQ nicht erreichbar - Job wird fehlschlagen")
        raise ConnectionError("RabbitMQ nicht erreichbar")

    log.info("Zahlungsauftrag gesendet fuer invoice_id=%s", invoiceId)
    return {"paymentSent": True}

#Worker starten
async def main():
    log.info("Worker startet, verbindet sich mit Camunda Cluster...")
    channel = create_camunda_cloud_channel(
        client_id=os.environ["ZEEBE_CLIENT_ID"],
        client_secret=os.environ["ZEEBE_CLIENT_SECRET"],
        cluster_id=os.environ["ZEEBE_CLUSTER_ID"],
        region=os.environ["ZEEBE_REGION"],
    )
    worker = ZeebeWorker(channel)
    worker.include_router(router)
    log.info("Lausche auf Job Types: '%s' und '%s'",
             JOB_TYPE_METADATA, JOB_TYPE_PAYMENT)
    log.info("Warte auf Jobs (Strg+C zum Beenden)...")
    await worker.work()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Worker beendet.")