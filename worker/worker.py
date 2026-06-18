import asyncio
import logging
import os
import sys

import httpx
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
log = logging.getLogger("dvg-worker")

JOB_TYPE_METADATA = os.environ["JOB_TYPE_METADATA"]
JOB_TYPE_PAYMENT = os.environ["JOB_TYPE_PAYMENT"]
JOB_TYPE_EXTRACT = os.environ["JOB_TYPE_EXTRACT"]


router = ZeebeTaskRouter()

# Handler zum Metadaten speichern
# @router.task = Wenn ein Zeebe Auftrag vom Typ JOB_TYPE_METADATA eintrifft, führe handle_save_metadata aus
@router.task(task_type=JOB_TYPE_METADATA)  
async def handle_save_metadata(
    invoiceName: str,
    invoiceDate: str,
    supplierName: str,
    vendorNumber: str,
    customerNumber: str,
    amount: float,
    currency: str,
    dueDate: str,
    description: str = "",
    positions: list = None,
):
    positions = positions or []

    for i, p in enumerate(positions, start=1):
        p["position_no"] = i

    log.info("Job '%s' empfangen: vendor=%s, amount=%s, %d Positionen",
             JOB_TYPE_METADATA, vendorNumber, amount, len(positions))
    
    invoice_id = insert_invoice(
        invoice_name=invoiceName,
        invoice_date=invoiceDate,
        supplier_name=supplierName,
        vendor_number=vendorNumber,
        customer_number = customerNumber,
        amount=amount,
        currency=currency,
        due_date=dueDate,
        description=f"{description}. Rechnung von {supplierName}.",
        positions=positions,  
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
# @router.task = Wenn ein Zeebe Auftrag vom Typ JOB_TYPE_PAYMENT eintrifft, führe handle_execute_payment aus
@router.task(task_type=JOB_TYPE_PAYMENT) 
async def handle_execute_payment(
    vendorNumber: str,
    amount: float,
    invoiceName: str,
    invoiceId: str,
    currency: str,
):
    log.info("Job '%s' empfangen: invoiceId=%s, vendorNumber=%s, amount=%s",
             JOB_TYPE_PAYMENT, invoiceId, vendorNumber, amount)

    ok = send_invoice(
        invoice_id=invoiceId,
        invoice_name=invoiceName,
        amount=amount,
        currency=currency,
        vendor_number=vendorNumber,
    )

    # send_invoice() gibt True bei Erfolg, False bei RabbitMQ-Problemen.
    if not ok:
        log.error("RabbitMQ nicht erreichbar - Job wird fehlschlagen")
        raise ConnectionError("RabbitMQ nicht erreichbar")

    log.info("Zahlungsauftrag gesendet fuer invoice_id=%s", invoiceId)
    return {"paymentSent": True}


# ---------------------------------------------------------------------------
# Hilfsfunktion: PDF-Bytes aus dem Camunda Document Store laden
# Wichtig: eigener OAuth-Token mit der Orchestration-Cluster-API-Scope,
# NICHT die Zeebe-Credentials (die koennen nur Jobs pollen).
# ---------------------------------------------------------------------------
async def fetch_pdf_from_document_store(document_id: str, store_id: str) -> bytes:
    async with httpx.AsyncClient() as client:
        # Schritt A: Token holen
        token_resp = await client.post(
            "https://login.cloud.camunda.io/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": os.environ["ZEEBE_CLIENT_ID"],
                "client_secret": os.environ["ZEEBE_CLIENT_SECRET"],
                "audience": "api.cloud.camunda.io",
            },
        )
        token_resp.raise_for_status()
        token = token_resp.json()["access_token"]

        # Schritt B: PDF-Bytes per GET aus dem Document Store laden
        rest_base = os.environ["CAMUNDA_REST_ADDRESS"]
        pdf_resp = await client.get(
            f"{rest_base}/v2/documents/{document_id}",
            params={"storeId": store_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        pdf_resp.raise_for_status()
        return pdf_resp.content


# Handler zur KI-Extraktion (Sprint 6)
# @router.task = Wenn ein Zeebe Auftrag vom Typ JOB_TYPE_EXTRACT eintrifft, führe handle_extract_invoice aus
@router.task(task_type=JOB_TYPE_EXTRACT)
async def handle_extract_invoice(attachments: list):
    # attachments kommt aus dem Email Inbound Connector als Liste von
    # Document-Referenzen: [{"documentId": "...", "storeId": "...", ...}]
    if not attachments:
        # Kein Anhang -> Job fehlschlagen lassen, sichtbar als Incident.
        log.error("Keine Anhaenge in der Prozessinstanz - Job wird fehlschlagen")
        raise ValueError("Keine Anhaenge in der Prozessinstanz gefunden")

    doc = attachments[0]
    log.info("Job '%s' empfangen: documentId=%s",
             JOB_TYPE_EXTRACT, doc.get("documentId"))

    # Schritt 1: PDF-Bytes aus dem Camunda Document Store holen
    pdf_bytes = await fetch_pdf_from_document_store(
        doc["documentId"], doc["storeId"]
    )
    log.info("PDF geladen: %d Bytes", len(pdf_bytes))

    # Schritt 2: PDF per multipart/form-data an den n8n-Webhook schicken
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            os.environ["N8N_WEBHOOK_URL"],  # z.B. https://xxxx.ngrok-free.app/webhook/...
            files={"data": ("invoice.pdf", pdf_bytes, "application/pdf")},
        )
        response.raise_for_status()

    result = response.json()
    log.info("KI-Extraktion fertig: confidence=%s, needsManualReview=%s",
             result.get("confidence"), result.get("needsManualReview"))

    # Schritt 3: Extrahierte Felder als Prozessvariablen zurueckgeben.
    # Diese fliessen in das spaetere Review-Formular und das Gateway.
    return {
        "invoiceName":       result["invoiceName"],
        "supplierName":      result["vendor"],
        "amount":            result["amount"],
        "currency":          result["currency"],
        "dueDate":           result["dueDate"],
        "confidence":        result["confidence"],
        "needsManualReview": result["needsManualReview"],
    }


# Worker starten
async def main():
    log.info("Worker startet, verbindet sich mit Camunda Cluster...")
    channel = create_camunda_cloud_channel(
        client_id=os.environ["ZEEBE_CLIENT_ID"],
        client_secret=os.environ["ZEEBE_CLIENT_SECRET"],
        cluster_id=os.environ["ZEEBE_CLUSTER_ID"],
        region=os.environ["ZEEBE_REGION"],
    )
    worker = ZeebeWorker(channel)

    # Fügt die Router Aufgaben zum Worker hinzu
    worker.include_router(router)
    log.info("Lausche auf Job Types: '%s', '%s', '%s'",
             JOB_TYPE_METADATA, JOB_TYPE_PAYMENT, JOB_TYPE_EXTRACT)
    log.info("Warte auf Jobs (Strg+C zum Beenden)...")
    await worker.work()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Worker beendet.")