# local-memory – Notizen

Stand: 13.10.2026 · eigenes Repo `~/PycharmProjects/local-memory` (lokal, kein Remote) · M4 MacBook Pro
Kopie der Projekt-Notiz aus dem Claude-Projekt „LLM-Lokal-Labor". Bedienung: `docs/RUNBOOK.md` (Szenario F/G), Bild: `docs/architektur-lab.svg`.

## Vorhaben

Ein lokales, modell- und anbieterunabhängiges Langzeitgedächtnis für lokale LLMs. Ausgangspunkt:
Cloud-„Memory" geht beim Modell- oder Anbieterwechsel verloren. Kernidee: Gedächtnis ist Daten,
nicht Modell – Klartext-Markdown unter `memory/`, von einem lokalen Modell gepflegt, in Git versioniert.

Bewusst **getrennt** vom retrieval-bench (Henne): Henne ist ein Experiment mit Ende und Wegwerf-Korpus,
das Gedächtnis ist langlebiger Bestand mit privaten Fakten. Geteilt wird nur Code (Retrieval-Module
kopiert, nicht importiert) und der llama-server Router – kein Zustand, keine Dateien.

## Architektur

- **Lesen:** Proxy :8091 vor dem Router :8080. `profile.md` + `preferences.md` immer vollständig im
  System-Prompt; dazu Top-3 Abschnitte (`## …`) aus `topics/`, `people/` per Hybrid-Retrieval
  (bge-m3/Ollama + BM25 mit Stemming, RRF-k 20 – Startwerte aus dem Henne-Bench). Vektoren sind
  abgeleiteter Cache (`cache/`, pro Abschnitts-Hash); die Markdown-Datei bleibt die Quelle. Chatlog nach `results/`.
- **Client-Prompts:** `LM_SYSTEM_MODE=merge` (Standard) lässt den System-Prompt des Clients stehen
  (OpenCode, Cline) und hängt das Gedächtnis an; `replace` nur für reine Chat-UIs. Tool-Schritte von
  Agenten bekommen Kontext, landen aber nicht im Chatlog.
- **Schreiben (`memorize`):** Chatlog oder `--text` → Qwen (no-think, T 0.1) destilliert JSON-Ops
  (`append` / `replace` / `delete`) → Trockenlauf als Standard → `--apply` mit Git-Snapshot davor →
  `git diff memory/` zeigt, was das Modell gelernt hat. Prompt liegt in `prompts/memorize.md`.
  Keine Ranking-Funktion beim Schreiben: was dauerhaft ist, entscheidet das Modell nach Regeln; der
  Code prüft nur Form (Pfad, exakt ein Treffer, kein Duplikat).
- **Schutz im Code, nicht im Prompt:** Tag `[stated]` setzt der Code; `replace`/`delete` nur bei genau
  einem Treffer der alten Zeile (assert-OLD-Muster); Pfade auf `memory/` begrenzt (Traversal abgewiesen);
  Duplikate abgelehnt; nur 127.0.0.1.
- Launcher `lm.command`: test | status | recall | context | memorize | proxy | reload | diff | keep | undo.
- Einbindung ins Lab: `LAB_MEMORY=1` in `launch_lab.command` startet den Proxy mit; Büro-Launcher
  `launch_lab_remote.command` legt Tailscale Serve auf 8091 → Gedächtnis auch vom Mini/iPad.
  OpenCode nutzt dieselbe URL (`…ts.net/v1`), Vorlage in `examples/opencode.json`.
  Von außen gibt es nur diesen einen Weg (mit Gedächtnis); 8080 ohne Gedächtnis bleibt lokal.

## Ergebnisse erster Abend (Qwen3.6 27B Q4_K_XL, no-think)

Fünf Grundfälle, alle bestanden:

| Fall | Eingabe | Ergebnis |
|---|---|---|
| Anlegen | zwei Rechner (zuhause/Büro) | 2× `append` in neuer `topics/hardware.md`, Frontmatter-`description` vom Modell sinnvoll |
| Verfallendes | „Heute teste ich Port 8091" | übersprungen: „temporäre Aufgabe, verfällt" |
| Fremdaussage | Assistent schlägt Port 8092 vor | übersprungen: „stammt vom Assistenten" – sogar als der Satz (Parser-Fehler) als Nutzertext ankam |
| Aktualisieren | „Mac mini ausgetauscht, jetzt M4" | genau eine `replace`-Op mit exakter Bestandszeile; Bestand kam per Retrieval in den Prompt |
| Nichts speichern | 3 Chat-Runden (Rückfragen, RRF-Erklärung) | `0 Ops`, Begründung korrekt |

Leseseite im Web-UI über den Proxy: aktualisierter Stand korrekt wiedergegeben; fachliche
Frage (RRF) ohne Gedächtnis-Schnörkel; „Was weißt du über mich?" liefert exakt die drei Zeilen.

Laufzeiten: memorize 8–15 s (warm), 32 s kalt; Chat-Antwort aus Gedächtnis ~1 s + Generierung.
Reproduzierbar: identischer Satz → identische Ops.

## Startbestand (12.10.2026)

Sieben Dateien aus dem Claude-Memory importiert und ins Deutsche übertragen (Format war bereits
kompatibel: `name`/`description`-Kopf, `- [stated]`-Zeilen): `profile`, `preferences`,
`topics/philosophie`, `arbeiten-2026`, `lab-stack`, `arbeitsweise-lab` – plus `hardware` vom Vortag.
65 Zeilen. Weggelassen: datierte Chronik-Blöcke (verfallen), Zwischenstände, `sources`/`aliases`.
Bewusst **nicht** importiert (Entscheidung Hawe): `altersvorsorge` (Finanzen) und `askvalentinai`
(Mandantennamen).

**Lehre:** Der Testsatz vom Vortag („Mini ausgetauscht, jetzt M4") stand als Fakt im Gedächtnis und
wäre beim Import ins Profil gewandert – Testdaten müssen zurückgedreht werden (`lm.command undo`
oder synthetischer Nutzer per `LM_MEMORY_DIR`), sonst sind sie die ersten Streichkandidaten.

## Remote-Test (12.10.2026, abends)

Vom iPhone über `https://….ts.net` (Büro-Launcher, Serve → 8091): „Womit arbeite ich im Büro?"

| Modell | Antwort | Bewertung |
|---|---|---|
| Qwen3.6 27B, no-think | „Im Büro arbeitest du an einem M2 Mac mini (24 GB RAM)." (1,4 s / 18 Token) | richtig; Zeile aus `topics/hardware.md` per Retrieval gefunden (nicht im Immer-Block) |
| Mellum2 12B Q4 | „Im Büo arbeitet Hawe als M1-Orchestrator: …" | falsch – greift die Profilzeile („*Arbeitet* im M1-Orchestrator-Modell") statt der Hardware-Zeile; dritte Person; Tippfehler |

Gleicher Prompt, gleicher Kontext, gleiches Retrieval → **das Modell entscheidet**, wie im Henne-Bench.
Zweiter Datenpunkt unterhalb 27B (12B-Klasse), eine Frage, Coding-Modell – als Hinweis, nicht als Messung.
Vorbehalt: `enable_thinking=false` ist ein Qwen-Schalter; ob Mellums Template ihn versteht oder per
`reasoning-budget` gedacht hat, ist offen – „beide ohne Thinking" ist nicht garantiert.
Konsequenz: Qwen für den Gedächtnis-Chat; Mellum am Mini nur als lokaler Coding-Fallback.

## Erste Modell-Vorschläge und iPad-Test (13.10.2026)

**Erste eigene Vorschläge des Modells** (aus dem Scout-Agent-Gespräch vom 12.10.): 2 Zeilen, beide
überarbeitungsbedürftig → verworfen. Kern richtig (Hawe will einen wöchentlichen LLM-Scout), aber
(a) Details aus Assistenten-Antworten übernommen (Pfad `agents/llm_scout/`, „Markdown-Infopaper",
Modell-ID), (b) Absicht als Tat formuliert („Baut …", obwohl nichts gebaut war – Qwen hatte das
Schreiben nur simuliert). Erste Streichquote: 2/2.

**iPad-Test:** 2 Runden über Serve → 8091 korrekt geloggt, verlaufsbewusste Suchanfrage greift.
Aber das Retrieval verfehlte die launchd-Stelle (`lab-stack#komponenten`/`#offen`) – Runde 2 kippte
deshalb auf einen unbegründeten Vorschlag (APScheduler/Hintergrund-Thread). Antwortzeit 60–77 s
(lange Antworten, nicht das Gedächtnis: Retrieval 0,2–0,4 s).

**Messung (BM25 allein, 13 Abschnitte, 14 Fragen in `eval/questions.jsonl`):** hit@1 0,43 ·
hit@3 0,57 · hit@5 0,93. Die iPad-Frage findet BM25 gar nicht („wiederkehrend" vs. „launchd").
Hybrid mit Embeddings noch zu messen (`lm.command evalret`), danach LM_K entscheiden.

## Ausbau (13.10.2026)

- `prompts/memorize.md`: neue Regeln „Keine Details aus Assistenten-Antworten", „Absicht ist nicht
  Tat", „nichts ergänzen", „bestehende Abschnitte verwenden"; Inventar nennt jetzt die Abschnitte.
- Werkzeug-Hinweis in beiden System-Prompt-Varianten: Werkzeuge im Gedächtnis sind die des Nutzers,
  nicht die des Modells; nie behaupten, etwas ausgeführt zu haben.
- Vorschlags-Kreislauf: `pending` / `accept` / `edit` / `reject`; `reject` schreibt den Stand fort;
  solange Vorschläge offen sind, startet kein neuer Lauf.
- `review`: ganze Datei aufräumen (Doppelungen, Widersprüche, Verfallenes) – nur replace/delete in
  dieser Datei, Unklares als Frage.
- `evalret` + `eval/questions.jsonl`: Retrieval-Eval für das Gedächtnis (hit@k je Retriever).
- `nightly install`: launchd-Job, täglich Trockenlauf um 03:30, Log in `results/nightly.log`.
- Tests auf eigenes Temp-Verzeichnis (`LM_RESULTS_DIR`), Smoke-Test um 13 Prüfungen erweitert.

## Beobachtungen / Vorbehalte

- Qwen ergänzte „48 GB" zu „48 GB RAM" – harmlos, aber Muster für stille Anreicherung. Falls häufiger:
  Regel 6 im Prompt schärfen („keine Ergänzungen, nur Normalform").
- Alle Testsätze hatten deutliche Signale („Heute…", „Assistant: … schlage ich vor"). Belastbarkeit im
  Alltag ist offen – die eigentliche Metrik ist die **Streichquote** nach ~10 echten Gesprächen.
- Mit wenigen Abschnitten spielt das Retrieval kaum eine Rolle (Top-3 ≈ alles). Es wird erst mit
  Dutzenden Abschnitten entscheidend; ob die Bench-Startwerte für kurze Faktzeilen taugen, dann nachmessen.
- Unfertige Hälfte ist die Schreibseite: keine Widerspruchserkennung über Retrieval-Fenster hinaus,
  kein Verblassen alter Fakten, keine Verdichtung langer Dateien, kein Zeitbezug für das Modell
  (Datum liegt nur in Git). Wird das Gedächtnis „komisch", liegt es hier – Hebel ist `prompts/memorize.md`.
- Parser-Fix: Marker `User:`/`Assistant:` werden jetzt auch inline erkannt.
- Trockenlauf mit 0 Ops markiert Runden als verarbeitet; mit vorgeschlagenen Ops nicht (damit `--apply` sie noch erreicht).
- OpenCode mit llama-server: Tool `subagent` hat ein unverankertes Schema-`pattern` → Router lehnt
  mit 400 ab; `"tools": {"subagent": false}` in `opencode.jsonc`. Diagnose: `scripts/toolcheck.py`.
- Mellum lokal am M2 Mac mini (24 GB): läuft, aber Bildschirmflackern unter Last (GPU/Speicher geteilt).
  Hebel: `ctx-size 16384`, `reasoning-budget 2048`, nur Q4. Der Mini ist Client, kein zweiter Server.

## Entscheidungen

- `memory/` versioniert, Repo ohne Remote (Git = Rollback). Vor einem Remote: `memory/` ausnehmen.
- Kein Auto-Memorize nach jeder Runde, solange die Streichquote unbekannt ist.
- Testen mit synthetischem Nutzer (`LM_MEMORY_DIR`) oder bewusst unkritischen Fakten.
- Nur ein Gedächtnis (am M4); der Mini nutzt es über Serve. Mellum lokal am Mini läuft ohne Gedächtnis.

## Weiterverfolgen

1. Startbestand einmal durchlesen = erste Streichquote vor dem ersten Modell-Schreibvorgang.
2. 10 echte Gespräche über den Proxy (Web-UI und OpenCode), dann Streichquote zählen.
3. Apertus 8B (und Mellum) als Extraktionsmodell: schafft es die fünf Fälle? (`LM_MODEL=…`)
4. Konflikt-Fälle: Nutzer widerspricht Bestand im Chat; zwei Fakten in einer Zeile; Personen (`people/`).
5. Stille Anreicherung messen (Diff Nutzerwortlaut ↔ gespeicherte Zeile).
6. Später: Auto-Memorize im Proxy (nur wenn verdient); Verdichtung/Verblassen; Zeitbezug.
