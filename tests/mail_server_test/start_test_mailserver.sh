#!/usr/bin/env bash
# start_test_mailserver.sh — Startet GreenMail per Docker für Tests.
#
# Nutzung:
#   bash start_test_mailserver.sh [--stop]
#
# Ports:
#   SMTP: 3025
#   IMAP: 3143
#   HTTPS: 3144 (nicht benötigt)
#
# Container-Name: mail-server-test
# Benutzer/Passwort: testuser / testpass

set -euo pipefail

ACTION="${1:-start}"
CONTAINER_NAME="mail-server-test"
SMTP_PORT=3025
IMAP_PORT=3143
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEYCHAIN_SERVICE="lab-mail-imap-test"

# Cleanup-Funktion für Fehlerfälle
cleanup_on_error() {
    echo "Fehler aufgetreten, räume auf..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    security delete-generic-password -s "$KEYCHAIN_SERVICE" 2>/dev/null || true
}

trap cleanup_on_error ERR

stop_container() {
    echo "Stoppe GreenMail-Container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    echo "Container gestoppt."
}

check_ports() {
    echo "Prüfe Ports $SMTP_PORT und $IMAP_PORT..."
    if lsof -i ":$SMTP_PORT" >/dev/null 2>&1 || lsof -i ":$IMAP_PORT" >/dev/null 2>&1; then
        echo "Port $SMTP_PORT oder $IMAP_PORT ist bereits belegt."
        echo "Beende blockierenden Prozess oder wähle andere Ports."
        exit 1
    fi
    echo "Ports sind frei."
}

create_keychain_entry() {
    echo "Erstelle Schlüsselbund-Eintrag für $KEYCHAIN_SERVICE..."
    security add-generic-password \
        -s "$KEYCHAIN_SERVICE" \
        -a "testuser" \
        -w "testpass" \
        -U
    echo "Schlüsselbund-Eintrag erstellt."
}

start_container() {
    # Prüfen, ob Container bereits läuft
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Container '${CONTAINER_NAME}' läuft bereits."
        return 0
    fi

    # Prüfen, ob Container existiert (gestoppt)
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Container '${CONTAINER_NAME}' existiert, starte ihn..."
        docker start "$CONTAINER_NAME"
        return 0
    fi

    echo "Starte GreenMail-Container..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "127.0.0.1:${SMTP_PORT}:3025" \
        -p "127.0.0.1:${IMAP_PORT}:3143" \
        -e MAIL_USER_ACCOUNT_AUTO_CREATE=true \
        -e MAIL_USER_TESTUSER=testpass \
        greenmail/standalone:2.1.0
    echo "Container gestartet."
}

wait_for_ready() {
    echo "Warte auf GreenMail-Start..."
    for i in $(seq 1 30); do
        if python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(('127.0.0.1', ${IMAP_PORT}))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
            echo "GreenMail ist bereit."
            return 0
        fi
        sleep 1
    done
    echo "GreenMail ist nicht innerhalb von 30 Sekunden bereit."
    return 1
}

deliver_mails() {
    echo "Liefere Test-Mails per SMTP ein..."
    python3 "$SCRIPT_DIR/einliefern.py" \
        --host 127.0.0.1 \
        --port "$SMTP_PORT" \
        --user testuser \
        --password testpass \
        --mail-dir "$SCRIPT_DIR/mails"
    echo "Mails eingeliefert."
}

run_dry() {
    echo "Führe Trockenlauf durch (keine Änderungen)..."
    MAIL_PLAN_DIR="$SCRIPT_DIR/output" \
    MAIL_IMAP_UNENCRYPTED=1 \
    python3 agents/mail_planung/mail_planung.py --dry-run
    echo "Trockenlauf abgeschlossen."
}

run_real() {
    echo "Führe echten Lauf durch (Änderungen)..."
    MAIL_PLAN_DIR="$SCRIPT_DIR/output" \
    MAIL_IMAP_UNENCRYPTED=1 \
    python3 agents/mail_planung/mail_planung.py
    echo "Echter Lauf abgeschlossen."
}

run_second() {
    echo "Führe zweiten Lauf durch (Dedup-Prüfung)..."
    MAIL_PLAN_DIR="$SCRIPT_DIR/output" \
    MAIL_IMAP_UNENCRYPTED=1 \
    python3 agents/mail_planung/mail_planung.py
    echo "Zweiter Lauf abgeschlossen."
}

run_verify() {
    echo "Führe Prüfskript aus..."
    python3 "$SCRIPT_DIR/pruefen.py" \
        --plan-dir "$SCRIPT_DIR/output" \
        --expectations "$SCRIPT_DIR/erwartungen.json"
    echo "Prüfskript abgeschlossen."
}

cleanup_keychain() {
    echo "Lösche Schlüsselbund-Eintrag..."
    security delete-generic-password -s "$KEYCHAIN_SERVICE" 2>/dev/null || true
    echo "Schlüsselbund-Eintrag gelöscht."
}

case "$ACTION" in
    --stop|stop)
        stop_container
        ;;
    --start|start|"")
        echo "=== Schritt 1: Port-Check ==="
        check_ports

        echo "=== Schritt 2: Schlüsselbund-Eintrag ==="
        create_keychain_entry

        echo "=== Schritt 3: GreenMail-Container starten ==="
        start_container

        echo "=== Schritt 4: Warten auf GreenMail ==="
        wait_for_ready

        echo "=== Schritt 5: Test-Mails einliefern ==="
        deliver_mails

        echo "=== Schritt 6: Trockenlauf ==="
        run_dry

        echo "=== Schritt 7: Echter Lauf ==="
        run_real

        echo "=== Schritt 8: Planungsdatei anzeigen ==="
        if [ -f "$SCRIPT_DIR/output/planung.json" ]; then
            cat "$SCRIPT_DIR/output/planung.json"
        else
            echo "Planungsdatei nicht gefunden!"
            exit 1
        fi

        echo "=== Schritt 9: Zweiter Lauf (Dedup) ==="
        run_second

        echo "=== Schritt 10: Prüfskript ==="
        run_verify

        echo "=== Schritt 11: Container stoppen ==="
        stop_container

        echo "=== Schritt 12: Schlüsselbund-Eintrag löschen ==="
        cleanup_keychain

        echo "=== Test abgeschlossen ==="
        ;;
    *)
        echo "Unbekannte Aktion: $ACTION"
        echo "Verwendung: bash start_test_mailserver.sh [--start|--stop]"
        exit 1
        ;;
esac
