#!/bin/zsh
echo "=== Services stoppen ==="
pkill -f "grpc/server.py"      && echo "✓ gRPC Server gestoppt"    || echo "– gRPC Server war nicht aktiv"
pkill -f "zahlungsservice/payment_system.py" && echo "✓ Zahlungsservice gestoppt" || echo "– Zahlungsservice war nicht aktiv"
pkill -f "worker/worker.py"    && echo "✓ Worker gestoppt"          || echo "– Worker war nicht aktiv"
pkill -f "ui/app.py"           && echo "✓ Web-UI gestoppt"          || echo "– Web-UI war nicht aktiv"
echo ""
echo "Fertig."
