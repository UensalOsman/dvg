import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5


STATUSES = {"REGISTERED", "RECEIVED", "INSPECTED"}
STATUS_ORDER = {"REGISTERED": 0, "RECEIVED": 1, "INSPECTED": 2}


class DomainError(Exception):
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def validate_uuid(value):
    try:
        UUID(value)
    except (ValueError, TypeError, AttributeError):
        raise DomainError("INVALID_ARGUMENT", "return_id muss eine UUID sein.") from None


class Store:
    def __init__(self, database):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS returns (
                    return_id TEXT PRIMARY KEY,
                    marketplace TEXT NOT NULL,
                    external_return_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(marketplace, external_return_id)
                );
                CREATE TABLE IF NOT EXISTS article_checks (
                    return_id TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    response TEXT NOT NULL,
                    PRIMARY KEY (return_id, sku)
                );
                CREATE TABLE IF NOT EXISTS outbox (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    return_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    published_at TEXT
                );
                CREATE TABLE IF NOT EXISTS received_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    return_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    consumed_at TEXT NOT NULL
                );
            """)

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.database, timeout=15, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=15000")
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self):
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
                connection.commit()
            except BaseException:
                connection.rollback()
                raise

    def _read(self, connection, return_id):
        row = connection.execute("SELECT return_id,marketplace,external_return_id,payload,status,created_at FROM returns WHERE return_id=?", (return_id,)).fetchone()
        if row is None:
            raise DomainError("NOT_FOUND", "Retoure nicht gefunden.")
        result = dict(row)
        result.update(json.loads(result.pop("payload")))
        return result

    def get(self, return_id):
        validate_uuid(return_id)
        with self.connection() as connection:
            return self._read(connection, return_id)

    def list_returns(self, status=None, marketplace=None):
        with self.connection() as connection:
            records = [self._read(connection, row["return_id"]) for row in connection.execute("SELECT return_id FROM returns ORDER BY created_at, return_id")]
        return [record for record in records if (status is None or record["status"] == status) and (marketplace is None or record["marketplace"] == marketplace)]

    def check_articles(self, checks):
        results = []
        with self.transaction() as connection:
            for payload, recommendation in checks:
                existing = connection.execute("SELECT payload,response FROM article_checks WHERE return_id=? AND sku=?", (payload["return_id"], payload["sku"])).fetchone()
                if existing:
                    if existing["payload"] != canonical(payload):
                        raise DomainError("ALREADY_EXISTS", "Artikel wurde bereits mit anderen Befunddaten geprueft.")
                    results.append(json.loads(existing["response"]))
                    continue
                result = {"return_id": payload["return_id"], "sku": payload["sku"], **recommendation, "checked_at": now()}
                connection.execute("INSERT INTO article_checks VALUES (?,?,?,?)", (payload["return_id"], payload["sku"], canonical(payload), canonical(result)))
                results.append(result)
        return results

    def get_check(self, return_id, sku):
        with self.connection() as connection:
            row = connection.execute("SELECT response FROM article_checks WHERE return_id=? AND sku=?", (return_id, sku)).fetchone()
        if row is None:
            raise DomainError("NOT_FOUND", "Keine Zustandspruefung fuer diese Retoure und SKU vorhanden.")
        return json.loads(row["response"])

    def order(self, order_id):
        records = [record for record in self.list_returns() if record["order_id"] == order_id]
        if not records:
            raise DomainError("NOT_FOUND", "Bestellung nicht gefunden.")
        return {"order_id": order_id, "returns": records}

    def update_status(self, return_id, status):
        validate_uuid(return_id)
        if status not in STATUSES:
            raise DomainError("INVALID_ARGUMENT", "Unbekannter Retourenstatus.")
        with self.transaction() as connection:
            record = self._read(connection, return_id)
            if record["status"] == status:
                return record
            if STATUS_ORDER[status] != STATUS_ORDER[record["status"]] + 1:
                raise DomainError("CONFLICT", "Erlaubt ist REGISTERED -> RECEIVED -> INSPECTED.")
            connection.execute("UPDATE returns SET status=? WHERE return_id=?", (status, return_id))
            record = self._read(connection, return_id)
            self._event(connection, record, "return.status_updated")
            return record

    def _event(self, connection, record, event_type):
        event = {
            "schema_version": 1, "event_id": str(uuid4()), "event_type": event_type,
            "occurred_at": now(), "return_id": record["return_id"],
            "correlation_id": record["return_id"], "marketplace": record["marketplace"],
            "status": record["status"],
        }
        connection.execute("INSERT INTO outbox(event_id,return_id,payload) VALUES (?,?,?)", (event["event_id"], event["return_id"], canonical(event)))

    def seed_examples(self, directory):
        """Stellt simulierte Marktplatzmeldungen bereit; vorhandene Daten bleiben erhalten."""
        with self.transaction() as connection:
            for source in sorted(Path(directory).glob("*-return.json")):
                payload = json.loads(source.read_text(encoding="utf-8"))
                return_id = str(uuid5(NAMESPACE_URL, f"shopeasy:{payload['marketplace']}:{payload['external_return_id']}"))
                connection.execute(
                    "INSERT OR IGNORE INTO returns(return_id,marketplace,external_return_id,payload,status,created_at) VALUES (?,?,?,?,?,?)",
                    (return_id, payload["marketplace"], payload["external_return_id"], canonical(payload), "REGISTERED", now()),
                )

    def pending(self):
        with self.connection() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM outbox WHERE published_at IS NULL ORDER BY sequence LIMIT 100")]

    def pending_count(self):
        with self.connection() as connection:
            return connection.execute("SELECT count(*) FROM outbox WHERE published_at IS NULL").fetchone()[0]

    def published(self, event_id):
        with self.connection() as connection:
            connection.execute("UPDATE outbox SET published_at=? WHERE event_id=?", (now(),event_id))

    def consume(self, event):
        if not isinstance(event, dict):
            raise ValueError("Eine Statusnachricht muss ein JSON-Objekt sein.")
        for field in ("event_id", "event_type", "return_id", "correlation_id", "marketplace", "status", "occurred_at"):
            if not isinstance(event.get(field), str) or not event[field].strip():
                raise ValueError(f"{field} muss eine nichtleere Zeichenfolge sein.")
        if type(event.get("schema_version")) is not int or event["schema_version"] != 1:
            raise ValueError("Unbekannte Ereignisversion.")
        if event.get("event_type") != "return.status_updated" or event.get("status") not in STATUSES:
            raise ValueError("Unbekanntes Statusereignis.")
        if event.get("marketplace") not in ("AMAZON", "ZALANDO"):
            raise ValueError("Unbekannter Marktplatz.")
        UUID(event["event_id"])
        validate_uuid(event["return_id"])
        if event.get("correlation_id") != event["return_id"]:
            raise ValueError("correlation_id muss der return_id entsprechen.")
        timestamp = datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("occurred_at muss eine Zeitzone enthalten.")
        with self.transaction() as connection:
            record = self._read(connection, event["return_id"])
            if event["marketplace"] != record["marketplace"]:
                raise ValueError("Marktplatz passt nicht zur Retoure.")
            cursor = connection.execute("INSERT OR IGNORE INTO received_events(event_id,return_id,payload,consumed_at) VALUES (?,?,?,?)", (event["event_id"],event["return_id"],canonical(event),now()))
            if cursor.rowcount == 1 and STATUS_ORDER[event["status"]] > STATUS_ORDER[record["status"]]:
                connection.execute("UPDATE returns SET status=? WHERE return_id=?", (event["status"], event["return_id"]))
            return cursor.rowcount == 1

    def events(self, return_id=None):
        with self.connection() as connection:
            query = "SELECT payload,consumed_at FROM received_events"
            arguments = ()
            if return_id:
                query += " WHERE return_id=?"
                arguments = (return_id,)
            rows = connection.execute(query + " ORDER BY sequence", arguments)
            return [{**json.loads(row["payload"]),"consumed_at":row["consumed_at"]} for row in rows]
