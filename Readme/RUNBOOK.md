# Runbook — Lokale Coding-Modell-Testumgebung (llama.cpp)

**Zweck:** Isolierte Probier- und Testumgebung, um die Coding-Qualität lokaler
Modelle (z.B. Mellum2) auf dem Mac einzuschätzen. Reine Exploration.

**Scope / Mode B:**
- Berührt die produktive Ollama-Instanz und die bge-m3-Embeddings **nicht**.
- Kein Import aus dem AskValentinAI-Repo, keine Tenant-Daten.
- Rollback = diesen Ordner löschen. Kein Deployment, keine Persistenz.

> ⚠️ **Nicht die produktive Ollama-Instanz anfassen.** Diese Umgebung nutzt
> ausschließlich llama.cpp als separaten Prozess. Ollama bleibt außen vor,
> damit die gepinnte Version und die bge-m3-Embeddings unberührt bleiben.

---

## 0. Überblick

```
Mac (M4 Pro, 48 GB)
│
├── llama-server (Port 8080)  ← Modell A, eingebaute Web-UI
├── llama-server (Port 8081)  ← Modell B (nur für A/B nötig)
│
├── run_ab.py                 ← Wegwerf-Testharness (Python)
│
└── PyCharm AI Assistant      ← optional: llama-server als Provider (Chat/Codegen)
```

PyCharm/Editor ist nur zum Bearbeiten. Das Modell läuft immer im separaten
`llama-server`-Prozess. Zugriff via Browser (Web-UI) oder OpenAI-kompatibler
API (`/v1`).

---

## 1. Installation (einmalig)

### llama.cpp

```bash
brew install llama.cpp
```

Prüfen, dass die Binaries da sind:

```bash
llama-server --version
llama-cli --version
```

### Python-Testprojekt (für das erweiterte Harness)

```bash
mkdir -p ~/mellum-test && cd ~/mellum-test
python3 -m venv .venv
source .venv/bin/activate
pip install openai
```

`openai` als Client, weil `llama-server` OpenAI-kompatibel ist — derselbe SDK
wie bei einer echten OpenAI-API, nur andere `base_url`.

Lege `run_ab.py` (Harness) in diesen Ordner.

---

## 2. Basis-Betrieb — ein Modell mit Web-UI

Server starten (blockiert das Terminal, läuft im Vordergrund):

```bash
llama-server -hf JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M --port 8080
```

- Beim **ersten Start** lädt llama.cpp das GGUF automatisch von HuggingFace
  (`-hf …`) — einige GB, danach im lokalen Cache.
- Warten bis in der Ausgabe steht:
  `server listening on http://127.0.0.1:8080`

Dann im Browser öffnen:

```
http://localhost:8080
```

→ eingebaute Chat-UI. Hier sofort „von Hand" Prompts werfen, um ein erstes
Gefühl für die Qualität zu bekommen. Kein weiterer Setup nötig.

**Server stoppen:** `Ctrl+C` im Terminal.

### Alternative: nur Terminal-Chat (ohne UI, ohne Server)

```bash
llama-cli -hf JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M
```

Gut für „läuft es überhaupt". Für strukturierte Tests aber unpraktisch
(mehrzeilige Snippets fummelig, kein reproduzierbares Wiederholen) — dafür
die Web-UI oder das Harness nehmen.

---

## 3. Erweiterte Testumgebung — A/B-Vergleich via Harness

Vergleicht zwei Modelle/Quantisierungen mit denselben Prompts, Antworten
nebeneinander in einer Markdown-Datei.

### 3.1 Zwei Server starten

A/B braucht **zwei Ports**, weil `llama-server` pro Prozess nur ein Modell
hält.

```bash
# Terminal 1 — Kandidat A
llama-server -hf JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M --port 8080

# Terminal 2 — Kandidat B (z.B. Q6_K-Gegenprobe oder anderes Coding-Modell)
llama-server -hf <ANDERER_GGUF_REPO_ODER_TAG> --port 8081
```

Beide müssen laufen und „listening" melden, bevor das Harness startet.

### 3.2 Harness konfigurieren

In `run_ab.py`:

- **`ENDPOINTS`** — Labels und Ports der zwei Kandidaten anpassen.
  Nur *ein* Modell testen? Zweiten Eintrag auskommentieren → alles läuft
  gegen 8080.
- **`PROMPTS`** — die Testaufgaben. Eine reale FastAPI-Aufgabe ist bereits
  eingebaut. Eigene Aufgaben anhängen:

  ```python
  {"name": "Kurzbeschreibung", "prompt": "..."},
  ```

  → Nimm **echte** Refactorings/Bugs aus deinem Alltag (die, bei denen du
  sonst Claude/GPT fragst). Synthetische Spielzeug-Prompts sagen nichts über
  die Qualität *für deine* Arbeit.

### 3.3 Harness starten

Drittes Terminal:

```bash
cd ~/mellum-test
source .venv/bin/activate
python run_ab.py
```

- Live-Ausgabe im Terminal.
- Vollständige Antworten nebeneinander in **`results_ab.md`**.
- `temperature=0.2` ist bewusst niedrig → vergleichbare, reproduzierbare
  Antworten statt kreativer Streuung.

---

## 4. Mellum direkt in PyCharm (AI Assistant)

Alternativer Test-Pfad: dasselbe lokale Modell nicht über das Harness, sondern
direkt im Editor als Chat- und Codegen-Helfer nutzen. Voraussetzung: ein
`llama-server` läuft (Abschnitt 2), und PyCharm hat mindestens eine
**Pro-Subscription** (AI Assistant ist dort nicht im kostenlosen Umfang).

### 4.1 Server als Provider einbinden

1. `llama-server` starten (Abschnitt 2), z.B. auf Port 8080.
2. In PyCharm: **Settings → Tools → AI Assistant → Providers & API keys**.
3. Unter den OpenAI-kompatiblen Endpoints die URL eintragen:
   ```
   http://localhost:8080/v1
   ```
4. **Test Connection** → **Apply**.

llama.cpp ist ein von JetBrains ausdrücklich unterstützter OpenAI-kompatibler
Endpoint — kein Umweg über Ollama nötig, die produktive Ollama-Instanz bleibt
unberührt.

### 4.2 Modell den Features zuweisen

Unter **Models Assignment** legst du fest, wofür das lokale Modell genutzt wird:

- **Core features** — In-Editor-Codegenerierung, Default-Modell im Chat,
  Commit-Messages. → Hierfür ist die Mellum2-*Thinking*-Variante geeignet.
- **Completion model** — Inline-Autocomplete. **Achtung:** funktioniert nur
  mit **FIM-Modellen** (Fill-in-the-Middle). Die Thinking-Variante ist ein
  Reasoning-/Chat-Modell und dafür **nicht** das richtige Werkzeug — dieses
  Feld also leer lassen bzw. dafür ein dediziertes FIM-Completion-Modell
  verwenden.

### 4.3 Was hier NICHT geht (wichtig)

Lokale Modelle decken **Chat + Codegen** ab, aber **nicht** den autonomen
Agent-Modus:

- **Junie** (JetBrains' autonomer Coding-Agent) unterstützt keine lokalen
  Modelle.
- **MCP-Tools** können mit lokalen Modellen nicht aufgerufen werden.

Der volle Agent „wie Claude" bleibt damit cloud-gebunden. Mellum lokal ist ein
brauchbarer Coding-*Chat* und Inline-Helfer — kein autonomer Agent. Für die
reine Einschätzung der Coding-Qualität ist das aber genau ausreichend.

### 4.4 Mode-B-Grenze

Das bleibt dein Editor-Tooling: keine Änderung an AskValentinAI, keine
Embeddings, keine Tenants. Testest weiterhin nur die Coding-Qualität, jetzt im
Editor-Kontext statt über das Harness. Grün.

---

## 5. Die eingebaute Testaufgabe (was sie prüft)

Ein FastAPI-Endpoint, als `async` deklariert, ruft aber `requests.get()` und
`time.sleep()` auf — beide **blockierend**. Sie legen den Event-Loop lahm:
während ein Request wartet, kann FastAPI keinen anderen bedienen (niedrige
CPU, trotzdem träge).

Ein Modell, das FastAPI wirklich versteht, erkennt **beide** Blocker konkret
und schlägt `httpx.AsyncClient` + `asyncio.sleep`, `run_in_threadpool` oder
eine `def`-statt-`async def`-Route vor — statt nur floskelhaft „nutze async".
Genau an dieser Tiefe trennt sich Spreu von Weizen.

---

## 6. Quantisierung (M4 Pro, 48 GB)

- **Q4_K_M** — Default für den ersten Test. Schnell, Qualität für eine
  Einschätzung völlig ausreichend.
- **Q6_K** — Gegenprobe, wenn ein Kandidat überzeugt und du genauer
  hinschauen willst. Etwas langsamer, näher am Original.

48 GB RAM tragen beide bei diesem Modell (12B total, ~2,5B aktiv als MoE)
locker.

### Optionaler Durchsatz-Check

```bash
llama-bench -m <pfad_zum_gguf>
```

Zeigt Tokens/Sekunde für Prompt-Processing und Generation.

---

## 7. Troubleshooting

| Symptom | Ursache / Fix |
|---|---|
| `command not found: llama-server` | `brew install llama.cpp` erneut, ggf. `brew link llama.cpp` |
| Download hängt / bricht ab | erneut starten — llama.cpp setzt auf dem Cache auf |
| `Connection refused` im Harness | Server noch nicht „listening" oder falscher Port |
| Port belegt | anderen `--port` wählen oder alten Prozess beenden (`lsof -i :8080`) |
| Antworten unbrauchbar knapp | in Web-UI: max tokens / context erhöhen |
| Zu langsam | kleinere Quant (Q4_K_M statt Q6_K) |

---

## 8. Aufräumen / Rollback

```bash
# Server stoppen: Ctrl+C in den jeweiligen Terminals
# Testprojekt entfernen:
rm -rf ~/mellum-test
```

Der llama.cpp-GGUF-Cache liegt separat (unter `~/Library/Caches/llama.cpp`
bzw. dem HF-Cache) und kann bei Bedarf ebenfalls gelöscht werden. Die
produktive Ollama-Instanz ist zu keinem Zeitpunkt betroffen.

---

## 9. Kurz-Notiz-Vorlage (nach dem Test ausfüllen)

```
Getestet:      <Modell(e) + Quant>
Aufgaben:      <Anzahl / Art>
Ergebnis:      <Qualität? FastAPI-Bug erkannt? beide Blocker?>
Geschwindigk.: <grob tok/s oder „gefühlt schnell/träge">
Weiterverfolg? <ja/nein — warum>
```

> Wird aus diesem Experiment eine feste Einbindung in AskValentinAI (Router,
> FastAPI-Anbindung, Model-Registry), ist das **Mode A** — neuen Chat im
> Projekt *AskValentinAI — Mode A / Hardening* eröffnen. Hier endet Mode B.
