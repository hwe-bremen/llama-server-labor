#!/usr/bin/env bash
# start_test_mailserver.sh — Startet GreenMail per Docker fuer Tests.
#
# Nutzung:
#   bash tests/mail_server_test/start_test_mailserver.sh
#
# Ports:
#   SMTP: 3025 (unverschuesselt)
#   IMAP: 3143 (unverschuesselt)
#
# Container-Name: mail-server-test
# Benutzer/Passwort: testuser / testpass

set -euo pipefail

CONTAINER_NAME="mail-server-test"
SMTP_PORT=3025
IMAP_PORT=3143
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEYCHAIN_SERVICE="lab-mail-imap-test"

# Frischer Zustand: temporares Verzeichnis fuer Planungsdatei und DB
MAIL_PLAN_DIR="$(mktemp -d)"
export MAIL_PLAN_DIR

# Verbindung und Rueckgabe: Immer dieselben Variablen fuer alle drei Läufe
export IMAP_HOST="127.0.0.1"
export IMAP_PORT="$IMAP_PORT"
export IMAP_USER="testuser"
export MAIL_IMAP_UNENCRYPTED="1"
export MAIL_IMAP_KEYCHAIN_SERVICE="$KEYCHAIN_SERVICE"
export MAIL_LLM_URL="http://localhost:8080"
# Ausgabe sofort zeigen (sonst puffert Python hinter "| tee" bis zum Ende)
export PYTHONUNBUFFERED=1

# Cleanup-Funktion: Wird bei JEDEM Exit aufgerufen (auch nach exit 1)
cleanup() {
    echo "Raume auf..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    security delete-generic-password -s "$KEYCHAIN_SERVICE" 2>/dev/null || true
    echo "Aufräumen abgeschlossen."
}

# EXIT-Trap: läuft bei jedem Exit (auch nach exit 1)
trap cleanup EXIT

# Vorherigen Container entfernen (nicht wiederverwenden)
echo "Entferne vorherigen Container (falls vorhanden)..."
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

echo "=== Schritt 1: Port-Check ==="
if lsof -i ":$SMTP_PORT" >/dev/null 2>&1 || lsof -i ":$IMAP_PORT" >/dev/null 2>&1; then
    echo "Port $SMTP_PORT oder $IMAP_PORT ist bereits belegt."
    exit 1
fi
echo "Ports sind frei."

echo "=== Schritt 2: Schluesselbund-Eintrag ==="
security add-generic-password \
    -s "$KEYCHAIN_SERVICE" \
    -a "testuser" \
    -w "testpass" \
    -U
echo "Schluesselbund-Eintrag erstellt."

echo "=== Schritt 3: GreenMail-Container starten ==="
# GreenMail-Anmeldung: testuser/testpass mit Auth aktiv via GREENMAIL_OPTS
# Quelle: GreenMail-Doku, Abschnitt Docker
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "127.0.0.1:${SMTP_PORT}:3025" \
    -p "127.0.0.1:${IMAP_PORT}:3143" \
    -e GREENMAIL_OPTS="-Dgreenmail.setup.test.all -Dgreenmail.hostname=0.0.0.0 -Dgreenmail.users=testuser:testpass@lab.local" \
    greenmail/standalone:2.1.0
echo "Container gestartet."

echo "=== Schritt 4: Warten auf GreenMail ==="
READY=0
# Nicht nur "Port offen" pruefen: Docker Desktop nimmt Verbindungen schon an,
# bevor GreenMail laeuft. Bereit = IMAP-Gruss "* OK" UND SMTP-Gruss "220".
for i in $(seq 1 60); do
    if python3 -c "
import socket, sys
def gruss(port, anfang):
    try:
        s = socket.create_connection(('127.0.0.1', port), timeout=2)
        s.settimeout(2)
        daten = s.recv(64)
        s.close()
        return daten.startswith(anfang)
    except OSError:
        return False
sys.exit(0 if gruss(${IMAP_PORT}, b'* OK') and gruss(${SMTP_PORT}, b'220') else 1)
" 2>/dev/null; then
        echo "GreenMail ist bereit."
        READY=1
        break
    fi
    sleep 1
done

if [ "$READY" -ne 1 ]; then
    echo "GreenMail ist nicht innerhalb von 60 Sekunden bereit. Letzte Container-Logs:"
    docker logs --tail 30 "$CONTAINER_NAME" 2>&1 || true
    exit 1
fi

echo "=== Schritt 5: Test-Mails einliefern ==="
python3 "$SCRIPT_DIR/einliefern.py" \
    --smtp-host 127.0.0.1 \
    --smtp-port "$SMTP_PORT" \
    --rcpt "testuser@lab.local" \
    --dir "$SCRIPT_DIR/mails"
echo "Mails eingeliefert."

echo "=== Schritt 5.5: mail_projects.json anlegen ==="
echo '[{"keyword": "Testprojekt", "project": "Testprojekt"}]' > "$MAIL_PLAN_DIR/mail_projects.json"
echo "mail_projects.json erstellt."

echo "=== Schritt 6: Trockenlauf ==="
python3 agents/mail_planung/mail_planung.py --dry-run
echo "Trockenlauf abgeschlossen."

echo "=== Schritt 7: Echter Lauf ==="
python3 agents/mail_planung/mail_planung.py
echo "Echter Lauf abgeschlossen."

cp "$MAIL_PLAN_DIR/planung.md" "$MAIL_PLAN_DIR/planung_lauf1.md"

echo "=== Schritt 8: Planungsdatei anzeigen ==="
if [ -f "$MAIL_PLAN_DIR/planung.md" ]; then
    cat "$MAIL_PLAN_DIR/planung.md"
else
    echo "Planungsdatei nicht gefunden!"
    exit 1
fi

echo "=== Schritt 9: Zweiter Lauf (Dedup) ==="
python3 agents/mail_planung/mail_planung.py
echo "Zweiter Lauf abgeschlossen."

echo "=== Schritt 10: Pruefskript ==="
python3 "$SCRIPT_DIR/pruefen.py" \
    --plan-dir "$MAIL_PLAN_DIR" \
    --expectations "$SCRIPT_DIR/erwartungen.json" \
    --first-run-plan "$MAIL_PLAN_DIR/planung_lauf1.md"
echo "Pruefskript abgeschlossen."

echo "=== Test abgeschlossen ==="
