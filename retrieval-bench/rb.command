#!/usr/bin/env bash
# retrieval-bench Launcher – setzt Verzeichnis, venv und Embedding-Endpunkt, egal von wo aufgerufen.
#
#   bash retrieval-bench/rb.command check                 # Eval-Set pruefen
#   bash retrieval-bench/rb.command run lab avai          # Benchmark fuer ein oder mehrere Chunkings
#   bash retrieval-bench/rb.command compare               # juengste Ergebnisse aufschluesseln
#   bash retrieval-bench/rb.command inspect               # Korpus-Bestandsaufnahme
#   bash retrieval-bench/rb.command shell                 # Subshell mit aktivem venv im richtigen Ordner
#
# Retriever/Optionen fuer 'run' per Umgebungsvariable:
#   RB_RETRIEVERS="faiss bm25 hybrid_faiss"  RB_PER_URL=2  RB_REPEAT=5  RB_EXTRA="--show 5"
# Embedding-Endpunkt: Standard Ollama auf 11434 mit bge-m3 (RB_EMBED_BASE_URL / RB_EMBED_MODEL ueberschreibbar).
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  echo "venv fehlt – einmalig: bash retrieval-bench/setup.sh" >&2
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

export RB_EMBED_BASE_URL="${RB_EMBED_BASE_URL:-http://127.0.0.1:11434/v1}"
export RB_EMBED_MODEL="${RB_EMBED_MODEL:-bge-m3}"
RETRIEVERS="${RB_RETRIEVERS:-faiss bm25 hybrid_faiss}"
PER_URL="${RB_PER_URL:-2}"
REPEAT="${RB_REPEAT:-5}"
EXTRA="${RB_EXTRA:-}"

cmd="${1:-help}"; shift || true
case "$cmd" in
  check)   python scripts/check_eval.py "$@" ;;
  inspect) python scripts/inspect_corpus.py "$@" ;;
  compare) python scripts/compare_results.py "$@" ;;
  run)
    [[ $# -gt 0 ]] || { echo "run braucht Chunking(s): lab und/oder avai" >&2; exit 1; }
    if ! curl -sf "${RB_EMBED_BASE_URL}/models" >/dev/null 2>&1; then
      echo "Embedding-Endpunkt ${RB_EMBED_BASE_URL} antwortet nicht – laeuft Ollama?" >&2
      exit 1
    fi
    echo "== Embedding: ${RB_EMBED_MODEL} @ ${RB_EMBED_BASE_URL} | Retriever: ${RETRIEVERS} | per_url=${PER_URL} repeat=${REPEAT}"
    for c in "$@"; do
      # shellcheck disable=SC2086
      python -m bench.run --chunking "$c" --retriever $RETRIEVERS --embedder api \
        --repeat "$REPEAT" --per-url "$PER_URL" $EXTRA
    done
    ;;
  shell)   exec "${SHELL:-bash}" -i ;;
  *)       sed -n '2,13p' "$0" ;;
esac
