# Sprint 1

In diesem Projekt präsentieren wir die 1. Abgabe (Sprint 1) des DVG Moduls

In diesem ersten Sprint des DVG-Moduls haben wir die Basiskomponenten für ein automatisiertes Rechnungsverarbeitungssystem entwickelt. 
Ziel ist es, Medienbrüche im aktuellen Prozess zu reduzieren und die manuelle Datenerfassung zu minimieren.

![Diagramm Name](images/dia.png)

## Technologien
* **Programmiersprache:** Python
* **Kommunikation:** gRPC, RabbitMQ
* **Datenbank:** SQLite
* **Containerisierung:** RabbitMQ läuft via Docker

## Installation & Ausführung
 
0. Abhängigkeiten installieren `pip install -r requirements.txt`
1. Protofile erstellen  `python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/invoice.proto`
2. Docker Container starten: `docker run -d --name rabbitmq -p 5672:5672 rabbitmq`
3. gRPC Server starten: `python server.py`
4. Client ausführen: `python client.py`

![Sequenzdiagramm](images/seq_dia.png)
