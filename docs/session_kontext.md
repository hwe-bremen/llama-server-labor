# Session-Kontext — llama-server Lab

Wiedereinstiegspunkt: Wo stehen wir, was ist offen, wie kommt man rein.
Ergänzt `docs/RUNBOOK.md` (Bedienung) um den *Stand* und die *nächsten Schritte*.

Letzte Session: 2026-10-09 · Branch `main`. **retrieval-bench abgeschlossen bis
zum Chat-Test:** Retrieval-Benchmark (FAISS/Qdrant/BM25/Hybrid), Antwortstufe mit
Qwen3.6 und Apertus, RAG-Proxy vor dem Router für echte Chats im Web-UI. Details:
`docs/runbook-retrieval-bench.md` und Projekt-Notiz `retrieval-bench-notizen.md`.
Davor (2026-09-24): Kirby-MCP als zweite MCP-Instanz, `docs/runbook-mcp-kirby.md`.

---

## Wo wir stehen (erledigt & committet)

- **retrieval-bench** (`retrieval-bench/`, eigenes venv, Launcher `rb.command`):
  - Korpus: Henne-Katalogdaten (öffentlich, stillgelegter Demo-Mandant), einmalig
    kopiert; Referenz-DB mit AskValentinAI-Chunks nur lesend, URLs mit `---`
    per Textabgleich repariert. Zwei Chunking-Varianten `avai` / `lab`.
  - Eval-Set: 25 Fragen, 24 gelabelt (URL-Ebene, Grade 1–3), 19 davon von Hawe
    mit vorher bekannter Zielseite.
  - Retrieval-Benchmark (`bench.run`): Qdrant dense = FAISS dense; Hybrid nur
    mit deutschem Stemming und RRF-k ≤ 30 besser (+7 Recall auf avai, ±0 auf lab);
    URL-Dedupe vor dem k-Schnitt ist Pflicht. Latenz: Embedding dominiert (~115 ms),
    Suche < 3 ms.
  - Antwortstufe (`bench.answer`): Qwen3.6 27B ohne Thinking ~24/25 richtig bei
    beiden Retrievern und k=5 wie k=3 → Retrieval-Unterschied in den Antworten
    nicht nachweisbar. Apertus 8B nicht tragfähig (Abschreiben, Überläufe,
    Halluzination). Thinking ohne Budget unbrauchbar; `--no-think` greift.
  - RAG-Proxy (`rag_proxy.py`, Port 8090): Web-UI mit Henne-Wissen, Quellenliste,
    Chat-Log. Erster Chat 4/6 gut; Folgefragen ohne Thema → `RB_HISTORY_TURNS`
    (Vorfrage fließt in die Suche ein), Mengenfragen über mehrere Produkte an der Grenze.
- **Kirby-MCP** (2026-09-24): zweite Instanz von `lab_mcp_server.py` (Port 8788,
  read-only, Sperrliste) für ein Kirby-Testprojekt; `models.ini`: Qwen3.6
  `ctx-size 65536` für Cline. Siehe `docs/runbook-mcp-kirby.md`.
- **MCP-Server** (`mcp-server/lab_mcp_server.py`): Tools list/read/search/write/
  delete + git status/diff/log/commit, `web_search` (DuckDuckGo). Traversal-
  geschützter Scope, `run_python` aus, read-only als Default. Transporte: stdio
  (Claude Desktop, Harness) und streamable-http (Web-UI, Port 8787).
  `write_file` akzeptiert `content_b64` (Escaping-Probleme kleiner Modelle).
- **Reusable Agent-Basis** (`core/mcp_agent.py`) + Harness (`agents/llama_harness.py`);
  Weekly-Digest-Agent (`agents/weekly_digest.py`, RSS, SQLite, launchd).
- **Web-UI-Anbindung**: llama.cpp-Web-UI spricht MCP-Server über `--ui-mcp-proxy` an.
- **Orchestrator** (`scripts/launch_lab.command`): MCP-Server + Router mit einem
  Aufruf; `read`/`write`; `LAB_BIND` `local`/`tailscale`/`serve`/`all`.
- **Remote-Zugang (iPad/iPhone)** über Tailscale Serve (HTTPS) bestätigt.
- **Doku**: `docs/RUNBOOK.md`, `docs/runbook-mcp-kirby.md`, `docs/runbook-retrieval-bench.md`.

---

## Offene Punkte (bewusst, für die nächste Session)

1. **retrieval-bench — Chat-Test fortsetzen.** Lino-Folgefrage mit
   `RB_HISTORY_TURNS=1` wiederholen; reicht das nicht → Frage per Modell
   umformulieren lassen (zweiter kurzer Aufruf, ~3–5 s). Fachliche Prüfung der
   Qwen-Antworten (Artikelnummern, Maße) im Report
   `retrieval-bench/results/answers_20261009_184838_avai.md`.
2. **retrieval-bench — Korpus vervollständigen.** high_level-Dokumente
   (PDF/JSON/DOCX) in den Lader; Artikelliste nach ArtikelNummer gruppieren
   (liegt im Langformat); lab-Chunking in der Antwortstufe.
3. **Transfer nach AskValentinAI** (dort, nicht hier): `---`-URL-Fehler im Index
   (19 Seiten), Hybrid nur mit Stemming + RRF-k ≤ 30, Thinking-Budget,
   Verzichtsverhalten messen. Eval-Set-Methode („Seite zuerst, Frage danach")
   übertragbar.
4. **ACL-Härtung** im privaten Tailnet weiterhin offen (Ein-Personen-Tailnet,
   Priorität niedrig). SSH-Entscheidung vor Entfernen der owner-Regel.
5. **Mac Mini (Büro)** als Server/Client einbinden; Rolle noch offen.
   Für retrieval-bench dort: Referenz-DB von Hand kopieren (nicht im Git).

---

## Schnellstart nächste Session

Lokal arbeiten (Standard):
```
bash scripts/launch_lab.command            # read-only, Router+MCP lokal
bash scripts/launch_lab.command write      # schreibfähig
```

retrieval-bench (Ollama muss laufen):
```
bash retrieval-bench/rb.command check                       # Eval-Set
bash retrieval-bench/rb.command run lab avai                # Retrieval-Benchmark
bash retrieval-bench/rb.command compare                     # Aufschlüsselung
RB_PER_URL=1 bash retrieval-bench/rb.command answer avai \
  --model "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL" --no-think  # Antwortstufe (Router läuft)
RB_PER_URL=1 bash retrieval-bench/rb.command proxy          # Chat: http://127.0.0.1:8090
```

Remote (iPad) — Serve/HTTPS:
```
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve --bg 8080
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve status
```

Modellwahl: Qwen3.6 27B nur mit `--no-think` bzw. `enable_thinking=false` für
RAG-Antworten; Mellum braucht `reasoning-budget` (in `models.ini` gesetzt);
Gemma 4 26B (33 GB) nicht parallel zu Ollama laden.

---

## Wichtige Fakten / Referenzen

- Repo: Branch `main`, `origin`-Remote. Push per `git push` (bzw. `gh`).
- Tailnet: `tail08de73.ts.net` (privat). Geräte: `macbook-pro-von-hans-werner`
  (100.89.16.112), `ipad165` (100.112.7.40), `iphone181` (100.106.12.65).
- Tailscale-CLI-Pfad (macOS): `/Applications/Tailscale.app/Contents/MacOS/Tailscale`.
- Ports: Router 8080 · Lab-MCP 8787 · Kirby-MCP 8788 · RAG-Proxy 8090 · Ollama 11434.
- Lebenschecks: `curl http://127.0.0.1:8787/mcp` → 406 = läuft;
  `curl -sI http://127.0.0.1:8080/health` → 200; `curl -s http://127.0.0.1:11434/v1/models`.
- Embedding-Modell: bge-m3 über Ollama (`/v1/embeddings`), 1.024 Dim.; Ollama
  aktuelle Version (nicht mehr 0.11.11).
- Modell-IDs im Router: `unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL`,
  `jondale/Apertus-8B-Instruct-2509-GGUF:Q4_K_M`,
  `JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q6_K:Q6_K`.

---

## Betriebsnotizen / Stolpersteine

- **PyCharm-Terminal startet im Repo-Root mit Projekt-venv.** retrieval-bench
  hat ein eigenes venv → immer über `bash retrieval-bench/rb.command …`, nie
  `python -m bench.run` direkt aus dem Root.
- **Launcher nie überschreiben, während er läuft** (Bash liest Skripte
  stückweise → Syntaxfehler am Ende des Laufs).
- **llama-server liefert das Web-UI nur als gzip** und antwortet ohne
  `Accept-Encoding: gzip` mit 415. Ein Reverse-Proxy muss den Header
  durchreichen; httpx setzt ihn ungefragt selbst, wenn man ihn weglässt.
  Nach einer kaputten Antwort hält der Browser-Cache die Seite fest → privates
  Fenster oder `?v=2`.
- **Thinking-Modelle:** ohne Budget/Schalter frisst die Denkphase das Token-
  Limit, Antwort bleibt leer. `chat_template_kwargs.enable_thinking=false` wird
  vom Router ausgewertet.
- **Eval-Labels** nicht aus Retriever-Kandidaten vergeben — bevorteilt messbar
  genau diesen Retriever. Seite zuerst, Frage danach.
- **RRF mit k=60** macht aus Hybrid „Schnittmenge zuerst" — k 10–30 nehmen.
- **Bind-Wechsel-Falle**: läuft noch eine Instanz auf einer anderen Bind-Adresse,
  erst `pkill -f llama-server`, dann neu. Banner `Bind:` prüfen.
- **MCP-Server (`llama-server-lab`, stdio via Claude Desktop)** geht nach
  Prozess-Neustarts in Timeout; Claude Desktop neu starten.
- **`write_file` über MCP** setzt kein Ausführungsbit → `chmod +x` für `.command`.
- **origin-Remote**: Kontextdateien enthalten Tailnet-Name, Gerätenamen und
  Tailscale-IPs — keine Secrets, aber bewusst wahrnehmen.

---

## Grenze (immer)

Reines Lab. Kein AskValentinAI-Code, keine echten Mandanten-/Kundendaten, nichts
Produktives. Sobald ein Vorhaben das berührt → gehört ins AskValentinAI-Projekt,
nicht hierher. Der Henne-Korpus ist eine einmalige Kopie öffentlicher Katalogdaten
eines stillgelegten Demo-Mandanten; keine Importpfade zurück ins AskValentinAI-Repo.
