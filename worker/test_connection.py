"""
test_connection.py - Verbindungstest fuer den Zeebe-Worker

ALS ALLERERSTES ausfuehren, bevor der richtige worker.py laeuft.

Dieser Test prueft NUR, ob:
  1. die .env-Credentials korrekt geladen werden,
  2. sich der Worker mit dem Camunda-Cluster verbinden kann.

Es wird KEIN gRPC und KEIN RabbitMQ benoetigt. Der Worker lauscht auf einen
Dummy-Job-Type "test-connection", der im BPMN gar nicht vorkommt - er soll
einfach nur ohne Fehler starten und warten.

Erwartetes Verhalten:
  - Laeuft ohne Auth-Fehler durch und gibt "Verbindung steht..." aus
    -> Credentials und Cluster-Anbindung funktionieren. Mit Strg+C beenden.
  - Bricht mit einem Fehler ab (z.B. Unauthenticated / KeyError)
    -> .env pruefen (Werte korrekt? Datei am richtigen Ort?).
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from pyzeebe import ZeebeWorker, create_camunda_cloud_channel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("connection-test")

load_dotenv()

# Pruefen, ob alle vier Credentials vorhanden sind - sonst frueh und klar abbrechen.
benoetigt = ["ZEEBE_CLIENT_ID", "ZEEBE_CLIENT_SECRET", "ZEEBE_CLUSTER_ID", "ZEEBE_REGION"]
fehlend = [name for name in benoetigt if not os.environ.get(name)]
if fehlend:
    log.error("Folgende Werte fehlen in der .env: %s", ", ".join(fehlend))
    log.error("Lege eine .env-Datei im worker-Ordner an (siehe .env.example).")
    raise SystemExit(1)


async def main():
    log.info("Credentials geladen. Verbinde mit Cluster '%s' (Region %s)...",
             os.environ["ZEEBE_CLUSTER_ID"], os.environ["ZEEBE_REGION"])

    # WICHTIG: Channel und Worker werden INNERHALB von main() erstellt.
    # Grund: pyzeebe legt beim Erstellen des async-gRPC-Channels intern einen
    # Event-Loop an. Wenn der Channel auf Modulebene (vor asyncio.run) erstellt
    # wird, haengt er an einem anderen Loop als der spaeter laufende Worker
    # -> Fehler "attached to a different loop". Deshalb hier drin erstellen.
    channel = create_camunda_cloud_channel(
        client_id=os.environ["ZEEBE_CLIENT_ID"],
        client_secret=os.environ["ZEEBE_CLIENT_SECRET"],
        cluster_id=os.environ["ZEEBE_CLUSTER_ID"],
        region=os.environ["ZEEBE_REGION"],
    )
    worker = ZeebeWorker(channel)

    # Dummy-Handler, der nie aufgerufen wird (Job-Type kommt im BPMN nicht vor).
    @worker.task(task_type="test-connection")
    async def dummy(**kwargs):
        return {}

    log.info("Verbindung steht, wenn jetzt KEIN Auth-Fehler kommt.")
    log.info("Worker wartet auf (nicht existierende) Jobs - mit Strg+C beenden.")
    await worker.work()


if __name__ == "__main__":
    # Auf Windows den SelectorEventLoop erzwingen. Der Standard-Loop auf Windows
    # (ProactorEventLoop) vertraegt sich mit grpc/asyncio nicht zuverlaessig.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Test beendet.")