import logging
import os
import sqlite3

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("erp-ui")

CLUSTER_ID    = os.environ.get("ZEEBE_CLUSTER_ID", "")
REGION        = os.environ.get("ZEEBE_REGION", "")
CLIENT_ID     = os.environ.get("ZEEBE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ZEEBE_CLIENT_SECRET", "")

# Zeebe REST API v2 – wird für Zeebe User Tasks benötigt
ZEEBE_BASE    = f"https://{REGION}.zeebe.camunda.io/{CLUSTER_ID}"
AUTH_URL      = "https://login.cloud.camunda.io/oauth/token"
DB_PATH       = os.path.join(os.path.dirname(__file__), "..", "grpc", "invoices.db")


def _get_token() -> str:
    resp = requests.post(
        AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "audience": "zeebe.camunda.io",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    try:
        resp = requests.post(
            f"{ZEEBE_BASE}/v2/user-tasks/search",
            headers=_headers(),
            json={"filter": {"state": "CREATED"}, "page": {"limit": 50}},
            timeout=10,
        )
        resp.raise_for_status()
        body = resp.json()
        # Zeebe REST API v2 gibt {"items": [...]} zurück
        tasks = body.get("items", body) if isinstance(body, dict) else body
        # Felder auf das Format normalisieren das das Frontend erwartet
        normalized = [
            {
                "id":                str(t.get("userTaskKey", t.get("id", ""))),
                "name":              t.get("name") or t.get("elementId", "Aufgabe"),
                "processInstanceKey": t.get("processInstanceKey", ""),
                "creationTime":      t.get("creationDate") or t.get("creationTime", ""),
            }
            for t in tasks
        ]
        return jsonify({"success": True, "tasks": normalized})
    except requests.HTTPError as e:
        log.exception("Fehler beim Laden der Tasks")
        return jsonify({"success": False, "error": f"{e.response.status_code}: {e.response.text}"}), 500
    except Exception as e:
        log.exception("Fehler beim Laden der Tasks")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tasks/<task_id>/complete", methods=["POST"])
def complete_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Kein JSON-Body"}), 400

    required = ["invoiceName", "supplier", "amount", "dueDate"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"success": False, "error": f"Pflichtfelder fehlen: {', '.join(missing)}"}), 400

    # Zeebe REST API v2: einfaches Key-Value Dict
    variables = {
        "invoiceName": data["invoiceName"],
        "supplier":    data["supplier"],
        "amount":      float(data["amount"]),
        "currency":    data.get("currency", "EUR"),
        "dueDate":     data["dueDate"],
        "description": data.get("description", ""),
        "channel":     "Web-UI",
    }

    try:
        resp = requests.post(
            f"{ZEEBE_BASE}/v2/user-tasks/{task_id}/completion",
            headers=_headers(),
            json={"variables": variables},
            timeout=10,
        )
        resp.raise_for_status()
        log.info("Task %s abgeschlossen: invoice=%s, supplier=%s",
                 task_id, data["invoiceName"], data["supplier"])
        return jsonify({"success": True})
    except requests.HTTPError as e:
        log.exception("HTTP-Fehler beim Abschließen von Task %s", task_id)
        return jsonify({"success": False, "error": f"Camunda {e.response.status_code}: {e.response.text}"}), 500
    except Exception as e:
        log.exception("Fehler beim Abschließen von Task %s", task_id)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/rechnungen", methods=["GET"])
def rechnungen():
    return render_template("rechnungen.html")


@app.route("/api/invoices", methods=["GET"])
def list_invoices():
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT invoice_id, invoice_name, vendor, amount, currency, due_date, description, created_at "
            "FROM invoices ORDER BY created_at DESC"
        ).fetchall()
        con.close()
        return jsonify({"success": True, "invoices": [dict(r) for r in rows]})
    except Exception as e:
        log.exception("Fehler beim Laden der Rechnungen")
        return jsonify({"success": False, "error": str(e)}), 500


def _free_port(start: int = 8080) -> int:
    import socket
    for port in range(start, start + 20):
        with socket.socket() as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
    return start


if __name__ == "__main__":
    port = _free_port()
    print(f"\n  ✓ ERP-UI läuft: http://localhost:{port}\n")
    app.run(debug=True, port=port)
