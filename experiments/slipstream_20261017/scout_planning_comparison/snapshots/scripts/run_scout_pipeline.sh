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

# LAB_DIR: übernehmen aus der Umgebung oder Default auf Repo-Pfad
DEFAULT_LAB_DIR="${REPO_ROOT}/agents/llm_scout/data"
DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=1
fi

if [ "$DRY_RUN" -eq 1 ]; then
    if [ -z "${LAB_DIR:-}" ]; then
        # Trockenlauf ohne explizites LAB_DIR: temporäres Verzeichnis
        LAB_DIR="$(mktemp -d)"
        echo "Trockenlauf: temporäres LAB_DIR=${LAB_DIR}" >&2
        # DB reinkopieren, falls vorhanden
        if [ -f "${DEFAULT_LAB_DIR}/llm_scout.db" ]; then
            cp "${DEFAULT_LAB_DIR}/llm_scout.db" "${LAB_DIR}/"
        fi
    fi
else
    LAB_DIR="${LAB_DIR:-${DEFAULT_LAB_DIR}}"
fi
export LAB_DIR

# Python-Interpreter aus dem Projekt-venv
PYTHON="${REPO_ROOT}/.venv/bin/python3"

echo "=== LLM Scout Pipeline gestartet ==="
if [ "$DRY_RUN" -eq 1 ]; then
    echo "(Trockenlauf-Modus)"
fi
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
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "Trockenlauf: Fehler-Mail uebersprungen (Scout Exit-Code ${SCOUT_EXIT})" >&2
    else
        # Fehler-Mail versuchen (set -e gefangen, damit der Wrapper den originalen Exit-Code gibt)
        "${PYTHON}" "${REPO_ROOT}/scripts/send_scout_email.py" --fail-mail --exit-code ${SCOUT_EXIT} || :
    fi
    exit ${SCOUT_EXIT}
fi

echo ""

# Schritt 2: Bericht per E-Mail versenden
echo "--- Schritt 2: E-Mail-Versand ---"
EMAIL_EXIT=0
if [ "$DRY_RUN" -eq 1 ]; then
    "${PYTHON}" "${REPO_ROOT}/scripts/send_scout_email.py" --dry-run || EMAIL_EXIT=$?
else
    "${PYTHON}" "${REPO_ROOT}/scripts/send_scout_email.py" || EMAIL_EXIT=$?
fi
if [ ${EMAIL_EXIT} -ne 0 ]; then
    echo "Fehler: send_scout_email.py beendet mit Exit-Code ${EMAIL_EXIT}." >&2
    exit ${EMAIL_EXIT}
fi

echo ""
echo "=== Pipeline erfolgreich abgeschlossen ==="
exit 0
