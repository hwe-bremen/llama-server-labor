# Runbook: retrieval-bench — RAG-Benchmark und Chat-Test am Henne-Korpus

Stand: 09.10.2026 · M4 MacBook Pro (48 GB) · Ollama (bge-m3) · llama-server Router (Qwen3.6 27B, Apertus 8B)

## Zweck

Eigenständiges Lab-Experiment unter `retrieval-bench/`: Misst, ob Hybrid
Retrieval (dense + BM25 + RRF) und/oder Qdrant gegenüber FAISS dense etwas
bringt — erst auf Retrieval-Ebene (Recall@10), dann in den Antworten eines
lokalen LLM, zuletzt als echter Chat im llama-server Web-UI. Korpus sind
öffentliche Katalogdaten des stillgelegten Demo-Mandanten Henne (Herkunft:
`retrieval-bench/corpus/henne/PROVENANCE.md`). Keine AskValentinAI-Codeanteile;
Befunde fließen nur als bewusster Transfer dorthin.

Ausführliche Ergebnisse und Lehren: Projekt-Notiz `retrieval-bench-notizen.md`
(Claude-Projekt LLM-Lokal-Labor) sowie `retrieval-bench/results/`.

## Architektur

```
Benchmark (bench.run / bench.answer)          Chat-Test (rag_proxy.py)
                                              Browser → 127.0.0.1:8090 (Proxy)
corpus/henne ─► Chunking (avai|lab)                │  /v1/chat/completions: Frage
      │                                             │  → Retrieval → Kontext in System-Prompt
      ▼                                             ▼
Ollama :11434  bge-m3  ─► Embeddings (cache/)   Router :8080 (llama-server, --models-preset)
      │                                             │
      ▼                                             ▼
FAISS | Qdrant(:memory:) | BM25+stem | Hybrid   Modell (Qwen3.6 no-think, Apertus …)
```

| Dienst | Port | Start |
|---|---|---|
| Ollama (Embeddings, bge-m3) | 11434 | Ollama-App oder `ollama serve` |
| llama-server Router | 8080 | `bash scripts/launch_lab.command` (oder `launch_router.command`) |
| RAG-Proxy (Web-UI mit Henne-Wissen) | 8090 | `bash retrieval-bench/rb.command proxy` |

Alles bindet ausschließlich an `127.0.0.1`. Der Proxy ist rein lesend.

## Dateien

| Datei | Inhalt |
|---|---|
| `retrieval-bench/rb.command` | Launcher: setzt Ordner, venv, Embedding-Endpunkt; Unterbefehle s. u. |
| `retrieval-bench/setup.sh` | venv anlegen / Abhängigkeiten installieren (einmalig, nach `requirements.txt`-Änderung erneut) |
| `retrieval-bench/bench/config.py` | Pfade und `RB_*`-Umgebungsvariablen |
| `retrieval-bench/bench/corpus.py` | Korpus-Lader: `avai` (Referenz-DB-Chunks, URLs repariert), `lab` (eigenes Chunking) |
| `retrieval-bench/bench/embed.py` | Embeddings über OpenAI-kompatiblen Endpunkt, Cache in `cache/` |
| `retrieval-bench/bench/retrievers.py` | faiss, qdrant, bm25(+stem), hybrid (RRF) |
| `retrieval-bench/bench/run.py` | Retrieval-Benchmark → `results/<ts>_<chunking>.json` |
| `retrieval-bench/bench/answer.py` | Antwortstufe: Top-k an LLM → `results/answers_<ts>.jsonl` + `.md`-Report |
| `retrieval-bench/rag_proxy.py` | Reverse-Proxy vor dem Router, injiziert Retrieval → `results/chatlog_<datum>.jsonl` |
| `retrieval-bench/scripts/inspect_corpus.py` | Bestandsaufnahme Korpus/Referenz-DB |
| `retrieval-bench/scripts/check_eval.py` | Eval-Set prüfen (JSON, IDs, Typen, URLs im Crawl) |
| `retrieval-bench/scripts/compare_results.py` | Ergebnisse je Fragetyp und Frage aufschlüsseln |
| `retrieval-bench/eval/questions.jsonl` | 25 Fragen mit URL-Labels (Grade 1–3); Anleitung in `eval/README.md` |
| `retrieval-bench/corpus/henne/` | Crawl (1.349 MD), Artikelliste, high_level, Referenz-DB (gitignored) |

## Einmalige Einrichtung

```bash
bash retrieval-bench/setup.sh            # eigenes venv unter retrieval-bench/.venv
chmod +x retrieval-bench/rb.command      # write_file setzt kein Ausfuehrungsbit
bash retrieval-bench/rb.command check    # Eval-Set: erwartet "0 Probleme"
bash retrieval-bench/rb.command inspect  # Korpus-Kennzahlen
```

Die Referenz-DB `corpus/henne/reference_embeddings.db` ist nicht im Git (19 MB);
auf einer zweiten Maschine von Hand nachkopieren.

## Starten

Terminal-Tabs benennen („Router 8080“, „Proxy 8090“, „Shell“). Alle Befehle im
Repo-Root; der Launcher wechselt selbst nach `retrieval-bench/`.

**Voraussetzung immer:** Ollama läuft (`curl -s http://127.0.0.1:11434/v1/models`).
Für Antwortstufe und Proxy zusätzlich der Router (`curl -sI http://127.0.0.1:8080/health`).

**Retrieval-Benchmark** (ohne LLM, Sekunden nach dem ersten Embedding-Lauf):

```bash
bash retrieval-bench/rb.command run lab avai           # faiss bm25 hybrid_faiss, per_url=2, repeat=5
bash retrieval-bench/rb.command compare                # juengste Ergebnisse je Chunking aufschluesseln
RB_RETRIEVERS="faiss qdrant" bash retrieval-bench/rb.command run avai
RB_RRF_K=10 bash retrieval-bench/rb.command run lab avai
RB_BM25_STEM=0 bash retrieval-bench/rb.command run lab   # rohe BM25-Baseline
```

Erster Lauf pro Chunking embeddet den Korpus (~2–3 min über Ollama); danach Cache.

**Antwortstufe** (Router muss laufen; Modell-ID wie in `/v1/models`):

```bash
# Qwen3.6 ohne Thinking – Standardfall
RB_PER_URL=1 bash retrieval-bench/rb.command answer avai \
  --model "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL" --no-think

# Teilmenge / anderes k / Apertus
RB_PER_URL=1 bash retrieval-bench/rb.command answer avai \
  --model "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL" --no-think --k 3 --questions q01 q04 q12 q06
RB_PER_URL=1 bash retrieval-bench/rb.command answer avai \
  --model "jondale/Apertus-8B-Instruct-2509-GGUF:Q4_K_M"
```

Dauer: Qwen ~18–25 s pro Antwort → 25 Fragen × 2 Retriever ≈ 15–20 min;
Apertus ~12 s. Modelle einzeln starten (Router lädt on-demand, Wechsel kostet).
Report: `results/answers_<ts>_<chunking>.md` mit `Bewertung: ___` pro Antwort.

**Chat-Test im Web-UI:**

```bash
RB_PER_URL=1 bash retrieval-bench/rb.command proxy
```

Dann **http://127.0.0.1:8090** im Browser (nicht 8080). Modell im Dropdown
wählen (Qwen3.6; Thinking wird vom Proxy abgeschaltet), Temperatur im UI auf
0,2. Jede Antwort endet mit einer Quellenliste; jede Runde steht in
`results/chatlog_<datum>.jsonl` (Frage, Suchanfrage, Kontext-URLs, Antwort, Zeiten).

Varianten per Umgebung:

| Variable | Default | Bedeutung |
|---|---|---|
| `RB_CHUNKING` | avai | `avai` (Referenz-Chunks) oder `lab` |
| `RB_RETRIEVER` | hybrid_faiss | `faiss`, `bm25`, `hybrid_faiss`, `qdrant`, `hybrid` |
| `RB_K` | 5 | Chunks im Prompt |
| `RB_PER_URL` | 1 (Launcher-Default 2) | max. Chunks je URL im Kontext |
| `RB_HISTORY_TURNS` | 1 | vorherige Nutzerfragen, die in die **Suche** einfließen (Folgefragen) |
| `RB_NO_THINK` | 1 | `enable_thinking=false` an den Router |
| `RB_APPEND_SOURCES` | 1 | Quellenliste ans Antwortende |
| `RB_PROXY_PORT` | 8090 | Port des Proxys |
| `RB_EMBED_BASE_URL` / `RB_EMBED_MODEL` | Ollama / bge-m3 | Embedding-Endpunkt |
| `RB_LLM_BASE_URL` | http://127.0.0.1:8080/v1 | Router |
| `RB_RRF_K` | 60 (Benchmark: 10–30 empfohlen) | RRF-Konstante |
| `RB_BM25_STEM` | 1 | deutsches Stemming + Akzentfaltung |

Direktvergleich: dieselbe Frage auf 8080 (Modell ohne Katalogwissen) und 8090.

## Prüfen

- `bash retrieval-bench/rb.command check` → `0 Probleme`
- Benchmark-Plausibilität: `faiss` und `qdrant` müssen identische Trefferlisten liefern.
- Proxy: `curl -s --compressed http://127.0.0.1:8090/ | head -c 100` → HTML-Anfang;
  `curl -s -D - -o /dev/null -H 'Accept-Encoding: gzip' http://127.0.0.1:8090/ | grep -i content-encoding` → `gzip`.
- Chat-Praxistest: Frage mit Produktname (z. B. „Womit versende ich eine 0,2 L Apothekerflasche?“)
  → Antwort mit Artikelnummer und Quellen; Frage ohne Beleg („Kühlversand?“) → Verzichtssatz;
  Folgefrage ohne Thema („Gibt es die auch in Rot?“) → prüft `RB_HISTORY_TURNS`.

## Fehlerbilder

| Symptom | Ursache | Lösung |
|---|---|---|
| `can't open file 'scripts/…'` / `No module named 'bench'` | falsches Verzeichnis oder Projekt-venv statt retrieval-bench-venv | immer über `bash retrieval-bench/rb.command …` starten |
| `Connection refused` auf 11434 | Ollama läuft nicht | Ollama starten; Launcher prüft das vorab |
| „LLM-Endpunkt antwortet nicht“ | Router nicht gestartet | `bash scripts/launch_lab.command` |
| Browser auf 8090 zeigt Binärmüll (`index.html…`) | alte Proxy-Version ohne gzip-Durchreichung **oder** Browser-Cache | Proxy neu starten; privates Fenster oder `?v=2` an die URL |
| Router antwortet `415 Unsupported Media Type` auf `curl http://127.0.0.1:8080/` | llama-server liefert das UI nur mit `Accept-Encoding: gzip` | normal; Proxy reicht den Header durch |
| Antwortstufe: 1.500 Token, leere Antwort, 140 s | Thinking-Mode ohne Budget (Qwen) | `--no-think`; alternativ `reasoning-budget` in `models.ini` |
| `rb.command: syntax error near unexpected token` nach einem Lauf | Launcher wurde überschrieben, während er lief | harmlos; `bash -n retrieval-bench/rb.command` prüfen, Launcher nie während eines Laufs patchen |
| BM25-Index braucht 6–9 s | Stemming in reinem Python | normal; `RB_BM25_STEM=0` für die rohe Baseline |
| `URL-Reparatur (avai): 44/66 … 22 offen` | 22 Chunks der `---`-URLs nicht eindeutig zuzuordnen (Boilerplate) | bekannt, unkritisch |
| Hybrid schlechter als dense | `RB_RRF_K=60` (Default) oder Stemming aus | `RB_RRF_K` 10–30, `RB_BM25_STEM=1`, `--per-url` setzen |

Fallstricke:

- `write_file` über den Lab-MCP setzt kein Ausführungsbit → `chmod +x` für `rb.command`.
- `results/` ist im Git, `cache/` und die Referenz-DB nicht.
- Gemma 4 26B (33 GB) nicht parallel zu Ollama + Qdrant laden (OOM-Gefahr).

## Messwerte (M4, Stand 09.10.2026)

| Was | Wert |
|---|---|
| Recall@10 avai: dense / bm25+stem / hybrid k=10–30 | 0,74 / 0,67 / 0,81–0,82 |
| Recall@10 lab: dense / bm25+stem / hybrid k=10–30 | 0,83 / 0,71 / 0,81–0,83 |
| Suchzeit bei 3.549 Vektoren: FAISS / Qdrant eingebettet / BM25 | 0,2 / 2,3 / 1,5 ms |
| Query-Embedding bge-m3 über Ollama | ~115 ms |
| Qwen3.6 27B Q4 no-think, k=5 / k=3 | ~25 s / ~18 s pro Antwort, ~12 t/s |
| Antworten inhaltlich richtig (Qwen, 25 Fragen, dense wie hybrid) | ~24/25 |
| Apertus 8B: exakte Quelle zitiert dense / hybrid | 9/25 / 15/25, Überläufe, Halluzination bei q06 |

## Kernbefunde (Kurzfassung)

- Qdrant dense = FAISS dense; Datenbank ohne Einfluss auf Qualität und Latenz.
- Hybrid braucht Stemming und RRF-k ≤ 30, sonst schadet es. Mit beidem: +7 Recall auf avai, ±0 auf lab.
- In den Antworten eines 27B-Modells ist der Retrieval-Unterschied nicht nachweisbar (k=5 wie k=3); ein 8B-Modell profitiert von Hybrid, ist aber insgesamt nicht tragfähig.
- Thinking ohne Budget ist für RAG unbrauchbar.
- Chat: Folgefragen ohne Thema brauchen Gesprächskontext in der Suche (`RB_HISTORY_TURNS`); Mengenfragen über mehrere Produkte („32 Flaschen“) stoßen mit k=5 an die Grenze.
- Transfer-Befund für AskValentinAI: 19 Crawl-URLs mit `---` im Index abgeschnitten (`…/flaschenversand---stehbox` → `…/flaschenversand`).

## Sicherheit

- Nur localhost; der Proxy hat keine Schreibpfade und reicht nur an den Router durch.
- Korpus sind öffentliche Katalogdaten eines stillgelegten Demo-Mandanten; keine personenbezogenen Daten.
- Bei Tailscale-Freigabe des Routers (`LAB_BIND=serve`) ist der Proxy **nicht** mit freigegeben — er bindet an 127.0.0.1. Bewusst lassen.

## Offene Punkte

- Folgefragen per Modell umformulieren (zweiter kurzer LLM-Aufruf) statt Vorfrage anhängen, falls `RB_HISTORY_TURNS` nicht reicht
- Fachliche Prüfung der Qwen-Antworten (Artikelnummern, Maße) im Report
- high_level-Dokumente und Artikelliste (nach Artikelnummer gruppiert) in den Korpus
- lab-Chunking in der Antwortstufe
- Kompositum-Zerlegung für BM25; Reranker; Qdrant-natives Sparse; Qdrant Edge; bge-m3 als GGUF in llama-server
