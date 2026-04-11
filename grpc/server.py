import grpc
from concurrent import futures
from config import LOG_LEVEL
from database import InvoiceDB 
from protos import invoice_pb2,invoice_pb2_grpc

db = InvoiceDB()

class InvoiceServicer(invoice_pb2_grpc.InvoiceServiceServicer):
    
    def CreateInvoice(self, request, context):
        db.create(request.invoice_id, request.supplier_name,
                request.amount, request.date, request.description)
        return invoice_pb2.SaveResponse(success=True, message="Invoice saved")

    def GetInvoice(self, request, context):
        row = db.get(request.invoice_id)

        if row:
            return invoice_pb2.InvoiceMetadata(
                invoice_id=row[0], supplier_name=row[1],
                amount=row[2], date=row[3], description=row[4]
            )
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("Invoice not found")
        return invoice_pb2.InvoiceMetadata()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    invoice_pb2_grpc.add_InvoiceServiceServicer_to_server(InvoiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server running on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()








