import grpc
from concurrent import futures
from config import LOG_LEVEL
from database import InvoiceDB 
from protos import invoice_pb2,invoice_pb2_grpc

db = InvoiceDB()

class InvoiceServicer(invoice_pb2_grpc.InvoiceServiceServicer):
    
    def CreateInvoice(self, request, context):
        db.create(request.invoice_id, request.supplier,
                request.amount, request.currency, request.due_date, request.description)
        return invoice_pb2.InvoiceResponse(success=True, message="Rechnung gespeichert", invoice_id=request.invoice_id)

    def GetInvoice(self, request, context):
        row = db.get(request.invoice_id)

        if row:
            # row: (id, invoice_id, supplier, amount, currency, due_date, description, created_at)
            return invoice_pb2.InvoiceResponse(
                success=True,
                message="Rechnung gefunden",
                invoice_id=row[1]
            )
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("Rechnung nicht gefunden")
        return invoice_pb2.InvoiceResponse(success=False, message="Rechnung nicht gefunden")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    invoice_pb2_grpc.add_InvoiceServiceServicer_to_server(InvoiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server running on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()








