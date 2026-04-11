# Sprint 1

In diesem Projekt präsentieren wir die 1. Abgabe (Sprint 1) des DVG Moduls

In diesem ersten Sprint des DVG-Moduls haben wir die Basiskomponenten für ein automatisiertes Rechnungsverarbeitungssystem entwickelt. 
Ziel ist es, Medienbrüche im aktuellen Prozess zu reduzieren und die manuelle Datenerfassung zu minimieren.

![Diagramm Name](dia.png)

## Technologien
* **Programmiersprache:** Python
* **Kommunikation:** gRPC, RabbitMQ
* **Datenbank:** SQLite
* **Containerisierung:** RabbitMQ läuft via Docker

## Installation & Ausführung

## Setup
 
```bash
pip install -r requirements.txt
```


1. Protofile erstellen (für den Vertrag zw. Client und Server) `python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/invoice.proto`
1. Docker Container starten: `docker run -d --name rabbitmq -p 5672:5672 rabbitmq`
2. gRPC Server starten: `python server.py`
3. Client ausführen: `python client.py`

![Sequenzdiagramm](seq_dia.png)
