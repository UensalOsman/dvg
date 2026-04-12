# RabbitMQ Docker Setup

## Ziel

RabbitMQ läuft als Message Broker im Docker-Container und stellt den Nachrichtenaustausch zwischen Client und Zahlungsservice bereit.

## Voraussetzungen

* Docker ist installiert und läuft

## Starten

```powershell
cd zahlungsservice\RabbitMQ
docker build -t rabbitmq-dvg .
docker run -d --name rabbitmq-dvg -p 5672:5672 -p 15672:15672 rabbitmq-dvg
```

`-p` verbindet `Host-Port:Container-Port`. Hier: `5672:5672` (Nachrichten) und `15672:15672` (Web-Oberfläche).

## Zugriff

* URL: http://localhost:15672
* Benutzer: admin
* Passwort: avg

## Vorkonfiguration (definitions.json)

* Queue: `payment-queue`
* Exchange: `payment-exchange` (Typ: `direct`)
* Binding: Routing-Key `payment` von Exchange zur Queue

## Hinweis

Beim Start werden die oben genannten Objekte sowie der Benutzer automatisch importiert.
