# ShopEasy – Sprint 2

In Sprint 2 habe ich mit KI-Unterstützung die Bausteine für die Integration eines
simulierten Retourenprozesses umgesetzt: eine Mock-REST-API, einen gRPC-Service
zur Artikelbewertung und Statusnachrichten über RabbitMQ.

## Umsetzung und KI-Unterstützung

### 1. Mock-REST-API

Ich habe mit KI-Unterstützung eine Mock-REST-API für Retouren von Amazon und Zalando
umgesetzt. Die KI hat bei offenen Fragen zu FastAPI, bei der Erstellung und
Überarbeitung des Codes sowie bei der Eingabevalidierung unterstützt.

Die API bietet:

- eine Liste aller Retouren mit Filtern nach Marktplatz und Status,
- die Abfrage einer einzelnen Retoure über ihre `return_id`,
- die Abfrage der zu einer `order_id` gehörenden simulierten Retourendaten,
- die Aktualisierung des Retourenstatus.

Die Beispieldaten liegen in `examples/` und werden beim Start bereitgestellt.
Das Datenmodell ist gegenüber dem JSON-Beispiel der Aufgabenstellung vereinfacht.
Die Bestellabfrage liefert die zugehörigen Retouren mit Artikelkennung und Menge.

### 2. REST-Client

Ich habe mit KI-Unterstützung einen Kommandozeilenclient umgesetzt, mit dem ich
Listen, Filter, Einzel- und Bestellabfragen sowie Statusänderungen aufrufen kann.
Die KI hat bei der Codeerstellung, den HTTP-Aufrufen und der Behandlung von
Verbindungs- und HTTP-Fehlern unterstützt.

Datei: `tools/rest_client.py`.

### 3. gRPC-Service zur Artikelbewertung

Ich habe mit KI-Unterstützung den Artikelbewertungsservice auf Basis des vorhandenen
vorgegebenen Vertrags `proto/article_condition_service.proto` umgesetzt.
Die KI hat bei Fragen zu gRPC und Protobuf, der Erstellung und Überarbeitung der
Serviceimplementierung sowie der Einbindung der generierten Stubs unterstützt.
Der Vertrag wurde bei der Überarbeitung nicht verändert.

Der Service bietet:

- `CheckCondition`: einen Artikel bewerten,
- `CheckConditionBatch`: mehrere Artikel in einem Stapel bewerten,
- `GetCheckResult`: ein gespeichertes Ergebnis erneut abrufen.

Ich habe die simulierten Bewertungsregeln mit KI-Unterstützung umgesetzt:

| Befund | Empfehlung |
|---|---|
| Neuwertig, Etiketten und Originalverpackung vorhanden | `ACCEPT` |
| Beschädigt oder deutlich getragen | `REJECT` |
| Übrige Fälle | `MANUAL_REVIEW` |

Der `confidence_score` ist ein fester Simulationswert: 0.95 bei Annahme/Ablehnung
und 0.6 bei manueller Prüfung. Bild-URLs werden gespeichert, aber nicht automatisch
ausgewertet. Der Service führt noch keine Erstattung oder spätere Workflow-Schritte aus.

### 4. gRPC-Client und Fehlerbehandlung

Ich habe mit KI-Unterstützung einen Client für Einzelprüfungen, Stapelprüfungen und
Ergebnisabfragen umgesetzt. Die KI hat bei der Codeerstellung, der Umwandlung von
JSON in Protobuf-Nachrichten und der Behandlung von gRPC-Fehlern unterstützt.

Identische Prüfungen liefern das gespeicherte Ergebnis. Abweichende Befunde für
dieselbe Retouren-ID und SKU liefern `ALREADY_EXISTS`. Ungültige Eingaben liefern
`INVALID_ARGUMENT`, fehlende Ergebnisse `NOT_FOUND`. Ein Stapel enthält 1 bis 100
Artikel; bei ungültigen Eingaben oder Konflikten bleiben keine neuen Teilergebnisse
zurück. Die KI hat auch bei der Implementierung dieser Prüfungen unterstützt.

Datei: `tools/warehouse_client.py`.

### 5. Statusnachrichten mit RabbitMQ

Ich habe mit KI-Unterstützung einen Producer und einen Consumer für Statusupdates
umgesetzt. Die KI hat bei Fragen zu AMQP, der Erstellung und Überarbeitung der
RabbitMQ-Anbindung und der Definition des Nachrichtenformats unterstützt.

Die Statusfolge lautet:

```text
REGISTERED → RECEIVED → INSPECTED
```

Eine tatsächliche Statusänderung erzeugt ein Ereignis `return.status_updated`.
Der Producer sendet die Nachricht an die Queue `shopeasy.return.status.v1`.
Der Consumer speichert das Ereignis und kann den Retourenstatus vorwärts aktualisieren.
Ältere Ereignisse setzen einen fortgeschrittenen Status nicht zurück.

Ich habe mit KI-Unterstützung die Fehlerbehandlung umgesetzt:

- Ausstehende Nachrichten bleiben bei Verbindungsproblemen in der SQLite-Outbox.
- Der Producer markiert eine Nachricht erst nach bestätigter Veröffentlichung als versendet.
- Der Consumer bestätigt Nachrichten erst nach erfolgreicher Speicherung.
- Doppelte Ereignisse werden über ihre `event_id` erkannt.
- Ungültige Nachrichten werden ohne erneute Zustellung abgewiesen.
- Vorübergehende Speicherfehler führen zur erneuten Zustellung.

### 6. Speicherung und Ausführungsumgebung

Ich habe mit KI-Unterstützung SQLite für Retouren, Bewertungsergebnisse, ausstehende
und empfangene Nachrichten eingebunden. Außerdem habe ich mit KI-Unterstützung die
Docker-Konfiguration umgesetzt. Die KI hat dabei Code und Konfiguration erstellt
und überarbeitet sowie offene Fragen zu Transaktionen, Volumes und Dienststart geklärt.

REST und gRPC laufen gemeinsam im App-Container; RabbitMQ läuft in einem eigenen
Container. Python, SQLite und Docker sind technische Entscheidungen dieser Umsetzung.
RabbitMQ ist eine der in der Aufgabe erlaubten Broker-Optionen.

### 7. Funktionsprüfung und Dokumentation

Ich habe die Umsetzung mit KI-Unterstützung gegen die Aufgabenstellung abgleichen
und durch einmalige Funktionsprüfungen überprüfen lassen. Die KI hat die Prüfabläufe
erstellt und ausgeführt, Fehler untersucht und die README erstellt und überarbeitet.

Am 02.11.2026 waren 84 Funktionsprüfungen erfolgreich. Geprüft wurden REST und gRPC
mit ihren Clients, Bewertungs- und Fehlerfälle, Stapelverarbeitung, RabbitMQ-Zustellung,
Duplikate, ungültige Nachrichten, erneute Zustellung nach Speicherfehlern sowie
Verbindungsunterbrechung und Wiederverbindung. Auch der Datenerhalt nach Neustart
und der vollständige Docker-Build und Start wurden geprüft.
Die Prüfungen verwendeten temporäre Daten und eine eigene Queue. Ein separater
Testcontainer und pytest gehören nicht zum aktuellen Projekt.

## Starten

Voraussetzungen: Docker Desktop mit Linux-Engine läuft; die Hostports 8000, 50051,
5672 und 15672 sind frei. Der erste Build benötigt Internet.

Im Projektordner:

```powershell
docker compose up --build -d --wait app
docker compose ps
```

| Oberfläche / Verbindung | Adresse |
|---|---|
| REST-Dokumentation | http://localhost:8000/docs |
| REST-Bereitschaft | http://localhost:8000/health |
| gRPC | localhost:50051 |
| RabbitMQ-Verwaltung | http://localhost:15672 |
| AMQP | localhost:5672 |

RabbitMQ-Anmeldung für die lokale Demo: `osman` / `passwort`.

## REST vorführen

```powershell
docker compose exec app python -m tools.rest_client list
docker compose exec app python -m tools.rest_client list --marketplace AMAZON --status REGISTERED
docker compose exec app python -m tools.rest_client order BESTELLUNG-DEMO-001
```

Eine `return_id` aus der Liste übernehmen:

```powershell
$retoureId = "HIER_RETURN_ID_EINFUEGEN"
docker compose exec app python -m tools.rest_client get $retoureId
docker compose exec app python -m tools.rest_client status $retoureId RECEIVED
docker compose exec app python -m tools.rest_client status $retoureId INSPECTED
```

Die Statusfolge muss eingehalten werden. Sprünge und Rückschritte liefern HTTP 409,
unbekannte Retouren HTTP 404. Bereits gespeicherte Statusänderungen bleiben nach
einem Neustart erhalten; für die Vorführung den aktuellen Status aus der Liste beachten.

## Messaging vorführen

Nach einer Statusänderung die vom Consumer empfangenen Ereignisse anzeigen:

```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/status-updates?return_id=$retoureId" | ConvertTo-Json -Depth 10
```

Die Verarbeitung ist asynchron und kann kurz dauern. Eine leere RabbitMQ-Queue ist
normal, wenn der Consumer alle Nachrichten bereits verarbeitet hat.

## gRPC vorführen

```powershell
docker compose exec app python -m tools.warehouse_client check RET-PROF-001 SKU-001 AS_NEW --tags-present --original-packaging
docker compose exec app python -m tools.warehouse_client check RET-PROF-002 SKU-001 DAMAGED
docker compose exec app python -m tools.warehouse_client check RET-PROF-003 SKU-001 MINOR_WEAR
docker compose exec app python -m tools.warehouse_client result RET-PROF-001 SKU-001
```

Die ersten drei Aufrufe liefern `ACCEPT`, `REJECT` und `MANUAL_REVIEW`.
Die Retouren-ID darf hier gemäß Vertrag eine freie Zeichenfolge sein und muss
nicht vorher in der Mock-REST-API angelegt worden sein.

Für eine Stapelprüfung eine JSON-Datei mit `items` gemäß `ConditionCheckBatchRequest`
verwenden. Die Datei muss im Container erreichbar sein:

```powershell
docker compose cp meine-pruefungen.json app:/tmp/pruefungen.json
docker compose exec app python -m tools.warehouse_client batch /tmp/pruefungen.json
```

## Beenden

```powershell
docker compose down
```

Die Datenvolumes bleiben erhalten.

## Quellcode

| Datei | Aufgabe |
|---|---|
| `shopeasy/rest_api.py` | Mock-REST-API |
| `shopeasy/article_condition_service.py` | Artikelbewertung |
| `shopeasy/grpc_service.py` | gRPC-Serverstart |
| `shopeasy/messaging.py` | RabbitMQ-Producer und Consumer |
| `shopeasy/storage.py` | Speicherung, Mock-Daten, Outbox und Deduplizierung |
| `shopeasy/runtime.py`, `shopeasy/__main__.py` | Gemeinsamer Anwendungsstart |
| `tools/rest_client.py` | REST-Client |
| `tools/warehouse_client.py` | gRPC-Client |
| `tools/generate_proto.py` | Generierung der gRPC-Stubs |
| `compose.yaml`, `Dockerfile`, `requirements*.txt` | Ausführungsumgebung |

## Verantwortung und Abgabe

Ich habe KI als Unterstützung bei der Projektbearbeitung und zur Klärung offener
Fragen genutzt. Die konkreten Bereiche einschließlich der Codeerstellung sind oben
aufgeführt. Die Verantwortung für die fachliche Prüfung, das Verständnis des Codes
und die Erklärung im Review liegt bei mir. Eine vollständige historische Liste
aller Prompts wurde nicht aufgezeichnet.

Die Funktionsprüfung bestätigt den getesteten Zustand. Vor der Abgabe müssen der
aktuelle Code auf GitHub und der zugehörige Link in ILIAS bereitgestellt werden.
