import logging
import os
import signal
import threading
from pathlib import Path

from .runtime import Application


def main():
    logging.basicConfig(level=logging.WARNING,format="%(levelname)s: %(message)s")
    stopped = threading.Event()
    for signal_number in (signal.SIGINT,signal.SIGTERM):
        signal.signal(signal_number,lambda received_signal,frame:stopped.set())
    application = Application(
        Path(os.environ.get("SHOPEASY_DATA_DIR","/data")),
        broker_host=os.environ.get("SHOPEASY_BROKER_HOST","broker"),
        bind_host=os.environ.get("SHOPEASY_BIND_HOST","0.0.0.0"),
        broker_username=os.environ.get("SHOPEASY_BROKER_USER","demo"),
        broker_password=os.environ.get("SHOPEASY_BROKER_PASSWORD","demo"),
        broker_vhost=os.environ.get("SHOPEASY_BROKER_VHOST","/"),
    )
    try:
        application.start()
        print("ShopEasy bereit: REST :8000, gRPC :50051; RabbitMQ im separaten Container.",flush=True)
        stopped.wait()
    finally:
        application.stop()


if __name__ == "__main__":
    main()
