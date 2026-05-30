#!/bin/zsh
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGS="$ROOT/.logs"
mkdir -p "$LOGS"

echo "=== DVG Sprint 4 – Services starten ==="
echo ""

# gRPC Server
echo "▶ gRPC Server..."
cd "$ROOT/grpc"
python3 server.py > "$LOGS/grpc.log" 2>&1 &
echo "  PID $! → logs: .logs/grpc.log"

sleep 1

# Zahlungsservice
echo "▶ Zahlungsservice..."
cd "$ROOT/zahlungsservice"
python3 payment_system.py > "$LOGS/zahlungsservice.log" 2>&1 &
echo "  PID $! → logs: .logs/zahlungsservice.log"

sleep 1

# Camunda Worker
echo "▶ Camunda Worker..."
cd "$ROOT/worker"
python3 worker.py > "$LOGS/worker.log" 2>&1 &
echo "  PID $! → logs: .logs/worker.log"

sleep 1

# Web-UI
echo "▶ Web-UI..."
cd "$ROOT/ui"
python3 app.py > "$LOGS/ui.log" 2>&1 &
echo "  PID $! → logs: .logs/ui.log"

# Warten bis die UI den Port meldet (max 8 Sek.)
UI_URL=""
for i in $(seq 1 8); do
  sleep 1
  UI_URL=$(grep -o 'http://localhost:[0-9]*' "$LOGS/ui.log" 2>/dev/null | head -1)
  [[ -n "$UI_URL" ]] && break
done

echo ""
echo "✓ Alle Services laufen."
echo "  UI: ${UI_URL:-http://localhost:8080 (Port aus .logs/ui.log prüfen)}"
echo ""
echo "  Logs live ansehen:  tail -f .logs/worker.log"
echo "  Alles stoppen:      ./stop.sh"
