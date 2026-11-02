from concurrent import futures

import grpc

from .article_condition_service import ArticleConditionService
from .generated import article_condition_service_pb2_grpc


def start_grpc(store, port, host="127.0.0.1"):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8),options=[("grpc.max_receive_message_length",1048576)])
    article_condition_service_pb2_grpc.add_ArticleConditionServiceServicer_to_server(ArticleConditionService(store), server)
    if server.add_insecure_port(f"{host}:{port}") == 0:
        raise RuntimeError(f"gRPC-Port {port} ist belegt.")
    server.start()
    return server
