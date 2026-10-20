#!/bin/bash
# Wissensbreite GGUF – Starter. Doppelklick oder: bash start_wissensbreite.command [router|next|bewerten]
#
#   router   (Default) Lab muss mit start_eval.command laufen (8080, 1 Modell im Speicher).
#            Selbsttest, Referenz der Prüfdateien, dann je 3 Läufe: Qwen3.6, Qwen3.8, Mellum Q4_K_M.
#            Modelle mit schon 3 fertigen Läufen werden übersprungen (kein doppeltes Rechnen).
#   next     Qwen3-Next muss über scripts/launch_qwen3next.command laufen (8083). 3 Läufe.
#   bewerten Alle Ergebnisordner bewerten, Übersicht nach ergebnisse/TABELLE.md.
#
# Die Prüfdateien werden selbst gesucht (HF-Cache, externe SSD). Alles wird zusätzlich nach
# ergebnisse/starter_<zeit>.log geschrieben.
set -euo pipefail

HIER="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HIER/../../.." && pwd)"
cd "$REPO"
PY="$REPO/.venv/bin/python"
MODUS="${1:-router}"
ROUTER="${ROUTER_URL:-http://127.0.0.1:8080}"
NEXT="${NEXT_URL:-http://127.0.0.1:8083}"
HF="${HF_HUB:-$HOME/.cache/huggingface/hub}"
D4="${D4:-/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf}"
MODELLE_ROUTER=(
  "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL"
  "unsloth/Qwen3.8-27B-GGUF:Q4_K_XL"
  "JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M:Q4_K_M"
)
MODELL_NEXT="Qwen3-Coder-Next-80B-A3B"

mkdir -p "$HIER/ergebnisse"
LOG="$HIER/ergebnisse/starter_$(date +%Y%m%d_%H%M%S)_${MODUS}.log"
exec > >(tee -a "$LOG") 2>&1

die() { echo; echo "ABBRUCH: $*"; exit 1; }
schritt() { echo; echo "=== $(date +%H:%M:%S) $*"; }

finde() {   # erste Datei im HF-Cache, deren Pfad auf das Muster passt (Symlinks folgen)
  find -L "$HF" -path "$1" -name "*.gguf" -size +1G 2>/dev/null | head -n 1
}

server_da() { curl -s -m 10 "$1/v1/models" >/dev/null; }

[ -x "$PY" ] || die ".venv fehlt ($PY)."
"$PY" -c "import numpy, yaml" 2>/dev/null || { schritt "numpy/pyyaml in die .venv"; "$PY" -m pip install -q numpy pyyaml; }

D2="$(finde '*Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M*')"
D3="$(finde '*Qwen3.6-27B-MTP-GGUF*UD-Q4_K_XL*')"
[ -n "$D2" ] || die "Mellum Q4_K_M nicht im HF-Cache ($HF) gefunden."
[ -n "$D3" ] || die "Qwen3.6 Q4_K_XL nicht im HF-Cache ($HF) gefunden."
DATEIEN=("$D2" "$D3")
if [ -f "$D4" ]; then DATEIEN+=("$D4"); else D4_FEHLT=1; fi
echo "Prüfdateien:"; printf '  %s\n' "${DATEIEN[@]}"
[ -z "${D4_FEHLT:-}" ] || echo "  (Qwen3-Next-Datei fehlt – externe SSD nicht angeschlossen)"

case "$MODUS" in
  router)
    server_da "$ROUTER" || die "Router $ROUTER antwortet nicht – erst start_eval.command starten."
    schritt "Selbsttest des Prüfers"
    "$PY" -m unittest "$HIER/selbsttest/test_pruefen.py" || die "Selbsttest rot – Ausgabe an Claude."
    schritt "Referenz der Prüfdateien"
    "$PY" "$HIER/pruefen.py" referenz "${DATEIEN[@]}" || die "Referenz fehlgeschlagen."
    for m in "${MODELLE_ROUTER[@]}"; do
      schritt "Läufe $m"
      "$PY" "$HIER/lauf.py" --url "$ROUTER" --modell "$m" --ueberspringen-wenn-fertig || echo "!! $m mit Fehler beendet – weiter mit dem nächsten Modell"
    done
    schritt "Router-Modelle fertig"
    echo "Weiter: Lab beenden, 'sudo purge', scripts/launch_qwen3next.command starten,"
    echo "        dann: bash $HIER/start_wissensbreite.command next"
    ;;
  next)
    [ -z "${D4_FEHLT:-}" ] || die "externe SSD anschließen (Qwen3-Next-Datei wird auch zum Prüfen gebraucht)."
    server_da "$NEXT" || die "Qwen3-Next auf $NEXT antwortet nicht – scripts/launch_qwen3next.command starten."
    schritt "Läufe $MODELL_NEXT"
    "$PY" "$HIER/lauf.py" --url "$NEXT" --modell "$MODELL_NEXT" --ueberspringen-wenn-fertig
    schritt "Fertig. Weiter: bash $HIER/start_wissensbreite.command bewerten"
    ;;
  bewerten)
    [ -z "${D4_FEHLT:-}" ] || echo "WARNUNG: ohne Qwen3-Next-Datei – Teil A dann max. 24 statt 32."
    ORDNER=()
    for o in "$HIER"/ergebnisse/*/; do [ -d "$o" ] && ORDNER+=("$o"); done
    [ ${#ORDNER[@]} -gt 0 ] || die "keine Ergebnisordner."
    schritt "Bewerten (${#ORDNER[@]} Ordner)"
    "$PY" "$HIER/pruefen.py" bewerten --bonus "${ORDNER[@]}" --dateien "${DATEIEN[@]}"
    "$PY" "$HIER/pruefen.py" tabelle "$HIER/ergebnisse" | tee "$HIER/ergebnisse/TABELLE.md"
    schritt "Fertig: ergebnisse/TABELLE.md und je Lauf bewertung.md – Claude kann beides selbst lesen."
    ;;
  *) die "Modus '$MODUS' unbekannt (router | next | bewerten)." ;;
esac
echo; echo "Log: $LOG"
