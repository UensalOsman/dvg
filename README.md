# Sprint 1 – Rechnungsverarbeitungssystem

In diesem ersten Sprint des DVG-Moduls haben wir die Basiskomponenten für ein automatisiertes Rechnungsverarbeitungssystem entwickelt.
Ziel ist es, Medienbrüche im aktuellen Prozess zu reduzieren und die manuelle Datenerfassung zu minimieren.

![Architektur-Diagramm](images/dia.png)

## Installation & Ausführung

### 1. Virtual Environment erstellen und aktivieren

```bash
python -m venv venv

.\venv\Scripts\Activate.ps1 -> Windows 
source .venv/bin/activate -> Mac
```

### 2. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 3. gRPC Vertrag generieren (für jeden service ordner einzeln)

```bash
# Im Client ordner
cd client
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/invoice.proto

# Im gRPC Server ordner
cd ../grpc
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/invoice.proto
```

### 4. rabbitmq starten (Docker)

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
```

### 5. Services starten (jeweils in einem eigenen Terminal)

```bash
# Terminal 1: gRPC Server
cd grpc
python server.py

# Terminal 2: Zahlungsservice
cd zahlungsservice
python payment_consumer.py

# Terminal 3: Client ausführen
cd client
python client.py
```

## Nachrichtenformat (RabbitMQ)

```json
{
    "invoice_id": "R-001",
    "amount": 500.00,
    "currency": "EUR",
    "recipient": "Firma X",
    "timestamp": "2026-04-10T14:30:00"
}
```

![Sequenzdiagramm](images/seq_dia.png)
