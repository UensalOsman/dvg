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
KI wurde unterstützend eingesetzt für: Datenbanklogik (SQLite), gRPC Server-/Client-Implementierung,
Fehlerbehandlung und Logging-Konfiguration.

### database.py - Autor: Mario Mansaku

Der Code in diesem Modul wurde kollaborativ mit KI (Claude OPUS 4.6) entwickelt.
Die Projektstruktur, Funktionsnamen und der grundlegende Aufbau wurden eigenständig erstellt.
KI wurde unterstützend eingesetzt für: Datenbanklogik (SQLite), gRPC Server-/Client-Implementierung,
Fehlerbehandlung und Logging-Konfiguration.

### README.md Autor: Justin Perrone

Diese File wurde mithilfe von Claude OPUS 4.6 erstellt und dann manuell angepasst.


### ui/app.py & ui/templates/ – Autor: Jeton Rama

Die Web-UI für die manuelle Rechnungserfassung wurde kollaborativ mit KI (Claude Sonnet 4.6) entwickelt.
Projektstruktur, Anforderungsanalyse und die Entscheidung für Flask sowie die Camunda-Anbindung
über die Zeebe REST API v2 wurden eigenständig erarbeitet. KI wurde eingesetzt für:
die Implementierung der Flask-Routen, die HTML/CSS-Gestaltung der ERP-Oberfläche,
die Integration der Camunda Tasklist- und Zeebe REST API sowie die start.sh/stop.sh-Skripte.
Der Code wurde nach Review und manuellem Testen eingecheckt und gepusht.

## KI-Verwendung pro Sprint

### Sprint 2 – Process Mining mit Celonis

In diesem Sprint wurde Claude vor allem als Lernhilfe eingesetzt, um Celonis zu
verstehen. Die eigentliche Analyse, die Auswahl der Daten und die Interpretation
der Ergebnisse haben wir selbst durchgeführt. Claude haben wir genutzt, um die
Funktionsweise des Tools zu erklären: welche Ansichten es gibt (z.B. Variant
Explorer und Process Explorer), welche Funktionen zur Verfügung stehen, was ein
Studio bzw. ein Data Pool ist und wie man Daten in Celonis einspeist und ein
Datenmodell aufbaut. Die so gewonnenen Erklärungen haben wir anschließend selbst
am konkreten Datensatz angewendet und die Bottleneck-Analyse eigenständig
erstellt.

### Sprint 3 – Soll-Prozess und BPMN-Modellierung

Den Soll-Prozess haben wir selbst entworfen, fachlich definiert und in BPMN im
Camunda Modeler modelliert. Die Optimierungen und Gateway-Entscheidungen wurden
von uns aus der Sprint-2-Analyse abgeleitet. Claude wurde erst danach eingesetzt:
Wir haben das fertige Modell vorgelegt und prüfen lassen, ob es fachlich und
BPMN-technisch korrekt ist, und haben Hinweise und Verbesserungsvorschläge
erhalten (z.B. zu Task-Typen und zur Schleifenlogik). Die Entscheidungen über
Änderungen haben wir selbst getroffen.

### Sprint 4 – Workflow-Implementierung und Job Worker

Um die Funktionsweise der Zeebe Job Worker zu verstehen, haben wir Claude
genutzt, um uns das zugrundeliegende Konzept erklären zu lassen (Pull- statt
Push-Prinzip, Long Polling, Zusammenspiel von BPMN, Job Types und Worker sowie
der Datenfluss über Process Variables). Auf dieser Grundlage haben wir die
Worker-Logik selbst implementiert und an unsere Sprint-1-Komponenten angebunden.
Die Datei test_connection.py zum Prüfen der Cluster-Verbindung wurde von Claude
OPUS 4.6 erstellt. Bei der Worker-Implementierung half Claude zudem bei der
Lösung eines Windows-spezifischen Problems mit dem asyncio-Event-Loop sowie bei
der Klärung des Variablen-Mappings zwischen Camunda-Formular, Worker und den
Sprint-1-Funktionen. Code und Konzepte wurden vor der Übernahme jeweils geprüft
und nachvollzogen.
