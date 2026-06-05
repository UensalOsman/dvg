import grpc
from concurrent import futures
from config import LOG_LEVEL
from database import InvoiceDB 
import logging
import uuid
from protos import invoice_pb2,invoice_pb2_grpc

# Logging konfigurieren
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

db = InvoiceDB()

class InvoiceServicer(invoice_pb2_grpc.InvoiceServiceServicer):
    
    def CreateInvoice(self, request, context):
        # Server generiert die ID
        invoice_id = f"Invoice-{uuid.uuid4().hex[:6].upper()}"

        positions = [
            {
                "position_no":    p.position_no,
                "article":        p.article,
                "quantity":       p.quantity,
                "unit":           p.unit,
                "unit_price_net": p.unit_price_net,
                "tax_rate":       p.tax_rate,
            }
            for p in request.positions
        ]

        db.create(
            invoice_id, request.invoice_name, request.invoice_date, request.supplier_name, request.vendor_number,
            request.customer_number, request.amount, request.currency,
            request.due_date, request.description,
            positions=positions,       
        )

        return invoice_pb2.InvoiceResponse(
            success=True,
            message="Rechnung gespeichert",
            invoice_id=invoice_id,
            invoice_name=request.invoice_name,
            supplier_name=request.supplier_name,
            amount=request.amount,
            currency=request.currency,
        )
    
    # Exkurs - Nicht Sprint 1 relevant (Mario Mansaku)
    def GetInvoice(self, request, context):
        row = db.get(request.invoice_id)

        if not row:
            return invoice_pb2.InvoiceResponse(
                success=False,
            )
        
        return invoice_pb2.InvoiceResponse(
            success=True, 
            message="Rechnung gefunden",
            invoice_id=row[1],
            invoice_name=row[2])

def serve():

    # Erstellt einen gRPC-Servec mit einem Thread pool von 10 Workern also er kann bis zu 10 Anfragen gleichzeitig bearbeiten
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Service registrieren
    invoice_pb2_grpc.add_InvoiceServiceServicer_to_server(InvoiceServicer(), server)

    # Server port
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Server running on port 50051")

    # Server herunterfahren und Datanbankdaten löschen
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=5)
        db.clear()
        logger.info("Datenbank geleert, Server gestoppt")

if __name__ == '__main__':
    serve()








