#!/usr/bin/env bash
#
# run_scout_pipeline.sh
# Fuehrt den LLM Scout aus und versendet den Bericht per E-Mail.
#
# Wird von launchd (de.hawe.lab.llm_scout) aufgerufen.
# Exit-Code 0 bei Erfolg, != 0 bei Fehlern.
#
set -euo pipefail

# Repo-Root (elternverzeichnis dieses Skripts)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# LAB_DIR setzen, damit llm_scout.py und send_scout_email.py
# DB und Reports im Repo speichern (nicht in ~/lab)
export LAB_DIR="${REPO_ROOT}/agents/llm_scout/data"

# Python-Interpreter aus dem Projekt-venv
PYTHON="${REPO_ROOT}/.venv/bin/python3"

echo "=== LLM Scout Pipeline gestartet ==="
echo "Repo-Root: ${REPO_ROOT}"
echo "LAB_DIR:   ${LAB_DIR}"
echo ""

# Schritt 1: Scout-Bericht generieren
echo "--- Schritt 1: LLM Scout ---"
# (set -e wuerde sonst sofort abbrechen, bevor eine Meldung kommt)
SCOUT_EXIT=0
"${PYTHON}" "${REPO_ROOT}/agents/llm_scout/llm_scout.py" || SCOUT_EXIT=$?
if [ ${SCOUT_EXIT} -ne 0 ]; then
    echo "Fehler: llm_scout.py beendet mit Exit-Code ${SCOUT_EXIT}." >&2
    # Fehler-Mail versuchen (set -e gefangen, damit der Wrapper den originalen Exit-Code gibt)
    "${PYTHON}" "${REPO_ROOT}/scripts/send_scout_email.py" --fail-mail --exit-code ${SCOUT_EXIT} || :
    exit ${SCOUT_EXIT}
fi

echo ""

# Schritt 2: Bericht per E-Mail versenden
echo "--- Schritt 2: E-Mail-Versand ---"
EMAIL_EXIT=0
"${PYTHON}" "${REPO_ROOT}/scripts/send_scout_email.py" || EMAIL_EXIT=$?
if [ ${EMAIL_EXIT} -ne 0 ]; then
    echo "Fehler: send_scout_email.py beendet mit Exit-Code ${EMAIL_EXIT}." >&2
    exit ${EMAIL_EXIT}
fi

echo ""
echo "=== Pipeline erfolgreich abgeschlossen ==="
exit 0
