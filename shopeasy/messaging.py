import json
import logging
import threading

import pika

from .storage import DomainError


QUEUE = "shopeasy.return.status.v1"
logger = logging.getLogger(__name__)


class Messaging:
    def __init__(self, store, port=5672, host="broker", username="demo", password="demo", virtual_host="/"):
        self.store = store
        self.port = port
        self.host = host
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        self.publisher_connected = False
        self.consumer_connected = False
        self.received_count = 0
        self.duplicate_count = 0
        self.stopping = threading.Event()
        self.threads = []

    def connection(self):
        return pika.BlockingConnection(pika.ConnectionParameters(
            host=self.host,port=self.port,virtual_host=self.virtual_host,
            credentials=pika.PlainCredentials(self.username,self.password),
            heartbeat=10,socket_timeout=2,stack_timeout=5,
            blocked_connection_timeout=3,connection_attempts=1,
        ))

    def close_connection(self, connection):
        if connection is not None and connection.is_open:
            try:
                connection.close()
            except Exception:
                logger.debug("Verbindung bereits getrennt.",exc_info=True)

    def publish(self, channel, payload):
        event = json.loads(payload)
        channel.basic_publish(
            exchange="",routing_key=QUEUE,body=payload.encode("utf-8"),mandatory=True,
            properties=pika.BasicProperties(
                content_type="application/json",delivery_mode=2,
                message_id=event["event_id"],correlation_id=event["correlation_id"],
            ),
        )

    def publish_loop(self):
        connection = None
        channel = None
        try:
            while not self.stopping.is_set():
                try:
                    if connection is None or not connection.is_open:
                        self.close_connection(connection)
                        connection = self.connection()
                        channel = connection.channel()
                        channel.queue_declare(queue=QUEUE,durable=True)
                        channel.confirm_delivery()
                    self.publisher_connected = True
                    for event in self.store.pending():
                        if self.stopping.is_set():
                            break
                        self.publish(channel,event["payload"])
                        self.store.published(event["event_id"])
                    connection.process_data_events(time_limit=0)
                    self.stopping.wait(0.1)
                except Exception:
                    self.publisher_connected = False
                    self.close_connection(connection)
                    connection = None
                    self.stopping.wait(0.5)
        finally:
            self.publisher_connected = False
            self.close_connection(connection)

    def on_message(self, channel, method, properties, body):
        try:
            event = json.loads(body)
            inserted = self.store.consume(event)
            self.received_count += 1
            if not inserted:
                self.duplicate_count += 1
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except (ValueError, KeyError, TypeError, DomainError):
            logger.exception("Ungueltige Statusnachricht wird verworfen.")
            if channel.is_open:
                channel.basic_nack(delivery_tag=method.delivery_tag,requeue=False)
        except Exception:
            logger.exception("Statusnachricht konnte nicht gespeichert werden.")
            if channel.is_open:
                channel.basic_nack(delivery_tag=method.delivery_tag,requeue=True)
            self.stopping.wait(0.1)

    def consume_loop(self):
        connection = None
        try:
            while not self.stopping.is_set():
                try:
                    if connection is None or not connection.is_open:
                        self.close_connection(connection)
                        connection = self.connection()
                        channel = connection.channel()
                        channel.queue_declare(queue=QUEUE,durable=True)
                        channel.basic_qos(prefetch_count=1)
                        channel.basic_consume(queue=QUEUE,on_message_callback=self.on_message,auto_ack=False)
                    self.consumer_connected = True
                    connection.process_data_events(time_limit=0.2)
                except Exception:
                    self.consumer_connected = False
                    self.close_connection(connection)
                    connection = None
                    self.stopping.wait(0.5)
        finally:
            self.consumer_connected = False
            self.close_connection(connection)

    def start(self):
        for target in (self.publish_loop,self.consume_loop):
            thread = threading.Thread(target=target,daemon=True)
            thread.start()
            self.threads.append(thread)

    def stop(self):
        self.stopping.set()
        for thread in self.threads:
            thread.join(timeout=10)
