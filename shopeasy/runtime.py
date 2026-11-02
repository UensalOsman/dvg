import socket
import threading
import time
from pathlib import Path

import uvicorn

from .grpc_service import start_grpc
from .messaging import Messaging
from .rest_api import create_app
from .storage import Store


ROOT = Path(__file__).resolve().parents[1]


def wait_until(predicate, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise TimeoutError("Die Komponente wurde nicht rechtzeitig bereit.")


def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1",port),timeout=0.2):
            return True
    except OSError:
        return False


class Application:
    def __init__(self, directory, rest_port=8000, grpc_port=50051, broker_port=5672, broker_host="broker", bind_host="127.0.0.1", broker_username="demo", broker_password="demo", broker_vhost="/"):
        self.directory = Path(directory)
        self.rest_port = rest_port
        self.grpc_port = grpc_port
        self.bind_host = bind_host
        self.store = Store(self.directory / "returns.sqlite3")
        self.store.seed_examples(ROOT / "examples")
        self.messaging = Messaging(self.store,broker_port,broker_host,broker_username,broker_password,broker_vhost)
        self.app = create_app(self.store,self.messaging)
        self.grpc_server = None
        self.http_server = None
        self.http_thread = None

    def start(self):
        if port_open(self.rest_port) or port_open(self.grpc_port):
            raise RuntimeError("REST- oder gRPC-Port ist bereits belegt.")
        self.messaging.start()
        try:
            self.grpc_server = start_grpc(self.store,self.grpc_port,self.bind_host)
            self.http_server = uvicorn.Server(uvicorn.Config(self.app,host=self.bind_host,port=self.rest_port,log_level="warning"))
            self.http_thread = threading.Thread(target=self.http_server.run,daemon=True)
            self.http_thread.start()
            wait_until(lambda:self.http_server.started or not self.http_thread.is_alive(),10)
            if not self.http_server.started:
                raise RuntimeError("REST-Server konnte nicht starten.")
            wait_until(lambda:self.messaging.consumer_connected and self.messaging.publisher_connected,60)
        except BaseException:
            self.stop()
            raise

    def stop(self):
        if self.http_server:
            self.http_server.should_exit = True
        if self.http_thread:
            self.http_thread.join(timeout=5)
        if self.grpc_server:
            self.grpc_server.stop(2).wait(timeout=5)
        self.messaging.stop()
