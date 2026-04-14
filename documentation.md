## AI Verwendung in diesem Projekt:


### client.py - Autor: Justin Perrone

Der Code in diesem Modul wurde kollaborativ mit KI entwickelt.
Die Funktionsnamen im Modul client.py, die Struktur des Codes selbst sowie das erstellen der ausgelagerten config.py 
entstand durch händisches Programmieren, der restliche funktionsinhalt wurde mithilfe von Claude OPUS 4.6 erstellt.
Die Struktur der Rechnungsanfrage (Invoice Request) wurde manuell von mir erstellt, die invoice.proto file basierend
auf meinem Muster mithilfe von Claude OPUS 4.6 gebaut.
Nach Code Review und fehlerprüfung wurde das ganze dann eingecheckt und gepushed. Die Namen der commits über die
Github Weboberfläche stammen von GITHUB Copilot. Die Funktionsbeschreibungen im Code stammen von Github Copilot,
wurden allerdings nach überprüfung teils manuell angepasst.

### server.py - Autor: Mario Mansaku

Der Code in diesem Modul wurde kollaborativ mit KI (Claude OPUS 4.6) entwickelt.
Die Projektstruktur, Funktionsnamen und der grundlegende Aufbau wurden eigenständig erstellt.
KI wurde unterstützend eingesetzt für: gRPC Server - serve() Methode, Fehlerbehandlung und Logging-Konfiguration.

### database.py - Autor: Mario Mansaku

Der Code in diesem Modul wurde kollaborativ mit KI (Claude OPUS 4.6) entwickelt.
Die Projektstruktur, Funktionsnamen und der grundlegende Aufbau wurden eigenständig erstellt.
KI wurde unterstützend eingesetzt für: Datenbanklogik (SQLite), Fehlerbehandlung und Logging-Konfiguration.

### README.md Autor: Justin Perrone

Diese File wurde mithilfe von Claude OPUS 4.6 erstellt und dann manuell angepasst.

### definitions.json, Dockerfile, RabbitMQ.conf und README_RabbitMQ.md - Autor: Osman Ünsal

Ich habe die Dateien definitions.json, Dockerfile, RabbitMQ.conf und README_RabbitMQ.md selbst erstellt und umgesetzt. Codex habe ich als Unterstützung bei der Umsetzung, Anpassung und Fehlerbehebung genutzt. Die Commits habe ich anschließend direkt über die PowerShell ausgeführt und in Github gepusht.

### payment_system.py - Autor: Jeton
Der Code in diesem Modul wurde kollaborativ mit KI (Claude HAIKU 4.5) entwickelt.
Die Projektstruktur, Funktionsnamen und der grundlegende Aufbau wurden eigenständig erstellt.
KI wurde unterstützend eingesetzt für: RabbitMQ Consumer-Logik, SQLite Datenbankoperationen, 
Validierungsfunktionen und Fehlerbehandlung (ACK/NACK). Nach Code Review und Fehlertests 
wurde das Ganze eingecheckt und gepusht.

### config.py (zahlungssystem/) - Autor: Jeton

Die Config-Datei wurde eigenständig erstellt und lagert die RabbitMQ- und Datenbank-Einstellungen aus.
Ermöglicht Konfiguration via Umgebungsvariablen.