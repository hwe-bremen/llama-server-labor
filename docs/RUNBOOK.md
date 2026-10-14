# Runbook — llama-server Lab

Betriebsanleitung für die lokale und remote Nutzung des Labs. Alle Befehle aus
dem Projekt-Root (`~/PycharmProjects/llama-server`) ausführen — Ausnahme: die
Befehle für `local-memory`, die im Nachbar-Repo liegen (voller Pfad steht dabei).

**Übersichtsbild:** `docs/architektur-lab.svg` zeigt alle Module, Ports und wer
wen aufruft. Im Browser oder in Vorschau öffnen; bei Unsicherheit zuerst dort schauen.

---

## 0. Gebrauchsanweisung — welcher Befehl wann?

Es gibt genau **zwei Launcher-Paare**, die du im Alltag brauchst (lokal / Büro-Tag,
jeweils read-only oder write). Alles andere sind Einzelteile, die diese intern aufrufen.

| Ich will …                                                     | Befehl (im Projekt-Root)                                   | Danach                          |
|----------------------------------------------------------------|------------------------------------------------------------|---------------------------------|
| lokal chatten, mit Datei-Tools, **ohne** Gedächtnis            | `bash scripts/launch_lab.command`                           | Browser `http://127.0.0.1:8080` |
| lokal chatten **mit** Gedächtnis                               | `LAB_MEMORY=1 bash scripts/launch_lab.command`              | Browser `http://127.0.0.1:8091` |
| vom Büro/iPad aus chatten, mit Gedächtnis (**Büro-Tag**)       | `bash scripts/launch_lab_remote.command` (Doppelklick geht) | Browser `https://macbook-pro-….ts.net` |
| mit **OpenCode** im Terminal am lokalen Modell arbeiten        | Launcher wie oben; `~/.config/opencode/opencode.jsonc` (Vorlage: `local-memory/examples/`) | `opencode` im Projektordner |
| das Henne-RAG-Experiment chatten                               | `RB_PER_URL=1 bash retrieval-bench/rb.command proxy` (Router muss laufen) | Browser `http://127.0.0.1:8090` |
| dem Gedächtnis beibringen, was im Chat gesagt wurde            | `bash ~/PycharmProjects/local-memory/lm.command memorize` (Trockenlauf) → `… memorize --apply` | – |
| das Frontend-Modell Dateien schreiben/löschen lassen           | Argument `write` anhängen: `bash scripts/launch_lab.command write` bzw. `bash scripts/launch_lab_remote.command write` — Doppelklick: `launch_lab_write.command` / `launch_lab_remote_write.command` | wie oben |

Zum Unterschied: **`write`** (Argument) = das Modell darf über den MCP-Server Dateien
schreiben. **`chmod +x`** (einmalig) = die `.command`-Datei darf per Doppelklick starten.
Das eine hat mit dem anderen nichts zu tun.

Merksätze:
- **8080 = Modell pur** (Kontrollgruppe) · **8090 = Henne-Wissen** · **8091 = dein Gedächtnis**.
- Nur Chats über **8091** landen im Gedächtnis-Chatlog. 8080 ist „ohne Mitschrift".
- **Remote nur über Tailscale Serve** (`LAB_BIND=serve` bzw. der Büro-Launcher).
  Ohne diesen Schalter ist die `.ts.net`-Adresse tot, egal was sonst läuft.
- **Ollama muss vorher laufen** (Menüleisten-App). Kein Launcher startet es.
- Beenden: **Ctrl+C im Launcher-Fenster** stoppt Router, MCP-Server und Gedächtnis-Proxy zusammen.
- Launcher **nie überschreiben, während er läuft** (Bash liest Skripte stückweise).
- Hinweistexte aus dem Chat sind keine Befehle: `zsh: command not found: Starte` heißt,
  ein Satz wurde ins Terminal eingefügt.

### MCP-Server in der Web-UI eintragen (Datei-Tools)

| Feld | Wert |
|---|---|
| URL | **`http://127.0.0.1:8787/mcp`** — Port 8787 und `/mcp` am Ende |
| „use llama-server proxy" | **AN** (Stift-Icon → editieren; der Schalter erscheint nur beim Editieren) |

- Gilt **überall gleich**: am Mac, am Mini im Büro, am iPad. Mit Proxy-Schalter geht die
  Anfrage über die geöffnete Adresse zum MacBook; `127.0.0.1` ist dort das MacBook selbst.
- **Falsch:** `http://127.0.0.1:8080` (das ist der Router/das Modell) → Fehler
  `404 File Not Found` beim `initialize`.
- Der Eintrag liegt im **Browser-Speicher pro Adresse** (Origin = Schema + Host + Port):
  `127.0.0.1:8080`, `127.0.0.1:8091` und die `.ts.net`-Adresse haben **je eigene** Einträge,
  ebenso jeder Browser und jedes Gerät. Privates Fenster oder „Website-Daten löschen" leeren ihn.
  Darum immer **dieselbe Adresse als Lesezeichen** nutzen (Büro/iPad: `.ts.net`, Mac: `8091`).
- Nach Wechsel read ↔ write oder MCP-Neustart: Eintrag aus/an, Seite neu laden, **neuer Chat**.

### Tagesablauf (Standard)

```
1. Ollama läuft?                 curl -s http://127.0.0.1:11434/v1/models | head -c 80
2. Launcher starten              siehe Tabelle oben
3. Im Launcher-Fenster warten auf  "Router bereit"  und (mit Gedächtnis)  "[lm] Proxy auf http://127.0.0.1:8091"
4. Browser: richtigen Port öffnen (Tabelle)  —  oder `opencode` im Projektordner
5. Abends: Ctrl+C im Launcher-Fenster
```

---

## 1. Komponenten & Ports

| Komponente              | Port / Transport       | Repo / Datei                         | Zweck                                                     |
|-------------------------|------------------------|--------------------------------------|-----------------------------------------------------------|
| llama-server Router     | 8080 (HTTP, localhost) | `scripts/launch_router.command`, `config/models.ini` | Chat-UI, OpenAI-API, MCP-CORS-Proxy (`--ui-mcp-proxy`) |
| Lab-MCP (Tools)         | 8787 (streamable-http) | `mcp-server/lab_mcp_server.py`       | Datei-Tools für die Web-UI (Scope: Projekt-Root)          |
| Lab-MCP (Tools)         | stdio                  | dito                                 | Tools für Claude Desktop und den llama-Harness            |
| Kirby-MCP (optional)    | 8788                   | `scripts/start-mcp-kirby.sh`         | zweite MCP-Instanz für das Kirby-Testprojekt              |
| RAG-Proxy Henne         | 8090 (localhost)       | `retrieval-bench/rag_proxy.py`       | Chat mit Henne-Katalogwissen (Experiment)                 |
| Gedächtnis-Proxy        | 8091 (localhost)       | `~/PycharmProjects/local-memory/lm/proxy.py` | Chat/OpenCode mit Langzeitgedächtnis (`memory/*.md`) |
| Ollama                  | 11434                  | eigener Dienst                       | bge-m3-Embeddings für beide Proxys und für memorize/recall|
| Tailscale Serve         | 443 (HTTPS, Tailnet)   | Tailscale-App                        | leitet `https://<mac>.ts.net` auf 8080 oder 8091          |
| OpenCode (Client)       | –                      | `~/.config/opencode/opencode.jsonc` oder `opencode.json` im Projekt | Terminal-Coding-Agent, spricht die OpenAI-API des Routers/Proxys |
| Mini-Router (Büro)      | 8080 am Mac mini       | `scripts/start-m2.sh`, `config/models-m2.ini` | eigener llama-server am Mini (Mellum2, 1 Modell im RAM) |
| toolcheck (Diagnose)    | 8089 (localhost)       | `scripts/toolcheck.py`               | zeigt, welche Tool-Schemas ein Agent an den Router schickt |

Scope aller MCP-Tools: das Projekt-Root, Traversal-geschützt. `run_python` ist aus.
Read-only ist der Default; Schreibzugriff wird bewusst aktiviert. Beide Proxys sind
reine Reverse-Proxys vor dem Router: sie binden nur an 127.0.0.1 und schreiben nur
in ihre eigenen `results/`-Ordner (der Gedächtnis-Proxy zusätzlich nie selbst in
`memory/` — das tut nur `memorize`).

## 2. Einmalige Voraussetzungen

- MCP-Server-venv: `cd mcp-server && bash setup.sh` (installiert `mcp`).
- Projekt-venv für den Harness: im `.venv` `pip install openai mcp`.
- retrieval-bench: `bash retrieval-bench/setup.sh` (eigenes venv), Details in
  `docs/runbook-retrieval-bench.md`.
- local-memory: `cd ~/PycharmProjects/local-memory && bash setup.sh && bash lm.command test`
  (eigenes Repo, eigenes venv; `test` muss `OK` melden).
- Ollama mit `bge-m3` (`ollama pull bge-m3`), Ollama-App läuft.
- Claude Desktop: `llama-server-lab`-Eintrag in `claude_desktop_config.json`
  (stdio, `MCP_SCOPE_ROOT` = Projekt-Root). Läuft danach automatisch.
- OpenCode: installiert; Konfiguration global in `~/.config/opencode/opencode.jsonc`
  (Vorlage und `baseURL`-Tabelle: `~/PycharmProjects/local-memory/examples/`), darin
  `"tools": { "subagent": false }` (siehe Troubleshooting).
- Remote: Tailscale auf Mac **und** den Client-Geräten, gleicher Account/Tailnet.
- macOS: die Tailscale-CLI liegt unter
  `/Applications/Tailscale.app/Contents/MacOS/Tailscale`. Bequemer per Alias in
  `~/.zshrc`: `alias tailscale="/Applications/Tailscale.app/Contents/MacOS/Tailscale"`.
- Für Serve: im Tailscale-Admin (login.tailscale.com → DNS) MagicDNS und
  HTTPS-Certificates aktivieren.
- `.command`-Dateien, die per MCP geschrieben wurden, einmalig ausführbar machen
  (nur für Doppelklick nötig, `bash …` geht auch ohne):
  `chmod +x scripts/launch_lab_remote.command scripts/launch_lab_remote_write.command`

---

## Szenario A — Lokal: Chat-UI + Tools (Standardfall)

Ein Aufruf startet MCP-Server (8787) **und** Router (8080) und öffnet die UI:

```bash
bash scripts/launch_lab.command          # read-only (sicher)
bash scripts/launch_lab.command write    # schreib-/löschfähig
```

Doppelklick-Varianten (Finder): `launch_lab.command` (read-only),
`launch_lab_write.command` (write). Beenden: Ctrl+C — stoppt beide Dienste.

MCP in der UI einmalig eintragen (Browser-Storage ist pro Adresse/Origin und Gerät, siehe Abschnitt 0):
1. MCP Servers → Add New Server → URL `http://127.0.0.1:8787/mcp`
2. Server per Stift-Icon **editieren** → Toggle „use llama-server proxy" AN
   (der Toggle erscheint nur beim Editieren, nicht beim Hinzufügen)

UI über **`http://127.0.0.1:8080`** öffnen, nicht `localhost` (CORS).

---

## Szenario B — Lokaler Agent (llama-Harness)

Der Harness macht ein lokales Modell zum MCP-Agenten (Logik in `core/mcp_agent.py`):

```bash
source .venv/bin/activate
python agents/llama_harness.py "Deine Aufgabe"          # schreibfähig
HARNESS_READONLY=1 python agents/llama_harness.py        # nur lesend
python agents/llama_harness.py                           # read-only Default-Task
```

- Router (8080) muss laufen (Szenario A).
- Modell wird automatisch gewählt (bevorzugt Mellum). Gezielt:
  `HARNESS_MODEL="JetBrains/Mellum2-…-Q6_K:Q6_K" python agents/llama_harness.py "…"`
- Tool-Calling ist bei Q4 fragiler als bei Q6 — bei leeren Argumenten Q6 nehmen.

---

## Szenario C — Claude Desktop

Kein Startbefehl. Sobald Claude Desktop läuft, startet es den MCP-Server als
stdio-Subprozess (Config), und Claude nutzt die Tools direkt. Claude kann damit
Dateien im Repo lesen und schreiben, aber **keine Prozesse starten** — Launcher,
Serve und Proxys müssen von Hand (Terminal) gestartet werden.

---

## Szenario D — Remote (iPad / iPhone / Mac mini) via Tailscale Serve

**Empfohlener Remote-Weg.** Der Router läuft lokal auf `127.0.0.1:8080`, der
Tailscale-Daemon (Serve) macht die HTTPS-Exposition ins Tailnet — llama-server
selbst bleibt auf localhost.

```bash
LAB_BIND=serve bash scripts/launch_lab.command          # remote, read-only, ohne Gedächtnis
LAB_BIND=serve bash scripts/launch_lab.command write    # remote, schreibfähig
bash scripts/launch_lab_remote.command                  # Büro-Tag: remote + Gedächtnis + Serve bleibt + kein Ruhezustand
bash scripts/launch_lab_remote.command write            # dito, Modell darf schreiben (Doppelklick: launch_lab_remote_write.command)
```

Der Orchestrator startet Serve (`tailscale serve --bg <port>`), zeigt die
`https://<mac-name>.<tailnet>.ts.net`-URL und räumt Serve beim Beenden per
`tailscale serve reset` wieder ab — außer `LAB_KEEP_SERVE=1` ist gesetzt (der
Büro-Launcher setzt es). Diese URL am Client öffnen (nicht die `100.x`-IP).
MCP-Eintrag wie in Szenario A: `http://127.0.0.1:8787/mcp` + Proxy-Toggle.

Mit `LAB_MEMORY=1` (bzw. dem Büro-Launcher) zeigt Serve auf **8091** — das
Gedächtnis ist dann auch remote aktiv (Browser **und** OpenCode am Mini);
8080 bleibt lokal erreichbar.

**Wichtig fürs Büro:** Serve läuft nur, wenn das MacBook wach ist und der
Launcher mit `serve` gestartet wurde. Vom Büro aus lässt sich das nicht
nachholen (Claude Desktop kann keine Prozesse starten). Deshalb morgens den
Büro-Launcher nehmen; er hält das MacBook per `caffeinate` wach, solange das
Fenster offen ist. Im Write-Modus gilt der Schreibzugriff auch für Chats, die
über Serve hereinkommen — vorher committen.

Gegenprobe vom Client: `curl -sI https://macbook-pro-von-hans-werner.tail08de73.ts.net/ | head -3`
— irgendeine HTTP-Antwort (200 oder 415) heißt „Serve steht". Keine Ausgabe
heißt „Serve nicht aktiv".

**Direkter Bind als Alternative** (`LAB_BIND=tailscale`, `launch_ipad.command`):
funktioniert, bindet llama-server aber direkt an die Tailscale-IP, setzt Serve
zurück und nimmt die Proxys (8090/8091) **nicht** mit. Nur für den Router pur.

---

## Szenario E — Henne-RAG (retrieval-bench)

Experiment mit Ende: Retrieval-Benchmark und Chat mit Henne-Katalogwissen.
Voraussetzung: Router (Szenario A) und Ollama laufen. Eigenes venv, eigener Launcher:

```bash
bash retrieval-bench/rb.command check          # Eval-Set prüfen
bash retrieval-bench/rb.command run lab avai   # Retrieval-Benchmark
bash retrieval-bench/rb.command compare        # Aufschlüsselung
RB_PER_URL=1 bash retrieval-bench/rb.command proxy   # Chat: http://127.0.0.1:8090
```

Alles Weitere (Antwortstufe, Env-Variablen, Befunde): `docs/runbook-retrieval-bench.md`.

---

## Szenario F — Gedächtnis (local-memory)

Eigenes Repo `~/PycharmProjects/local-memory` (lokal, **kein Remote** — enthält
private Fakten). Zwei Hälften:

- **Lesen** (Proxy 8091): `profile.md` + `preferences.md` immer, dazu Top-3
  passende Abschnitte aus `topics/`, `people/` → System-Prompt → Router.
  Hat der Client einen eigenen System-Prompt (OpenCode, Cline), bleibt der
  erhalten und das Gedächtnis wird angehängt (`LM_SYSTEM_MODE=merge`, Standard).
- **Schreiben** (`memorize`): Chatlog → Qwen destilliert Fakten → `append`/
  `replace`/`delete`-Ops auf `memory/*.md`. Standard ist **Trockenlauf**;
  `--apply` macht vorher einen Git-Snapshot. Tool-Schritte von Agenten landen
  nicht im Chatlog, nur echte Nutzer-Runden.

```bash
LM=~/PycharmProjects/local-memory/lm.command
bash $LM test                       # Pipeline-Test ohne Modell (muss OK melden)
bash $LM status                     # Dateien, offene Vorschläge, Nachtlauf
bash $LM proxy                      # Gedächtnis-Proxy einzeln (sonst: LAB_MEMORY=1 im Launcher)

# Kreislauf
bash $LM memorize                   # neue Chat-Runden → Vorschläge (nichts wird geschrieben)
bash $LM pending                    # Vorschläge ansehen
bash $LM accept                     # übernehmen (Git-Snapshot davor)
bash $LM edit                       # Vorschlag im Editor umformulieren, danach accept
bash $LM reject                     # verwerfen – die Runden gelten als entschieden
bash $LM reload                     # laufenden Proxy neu laden

# Pflege und Messung
bash $LM review                     # ganze Dateien aufräumen lassen (Doppelungen, Widersprüche) → Vorschläge
bash $LM evalret                    # Retrieval-Eval: findet die Suche die richtigen Abschnitte? (hit@1…6)
bash $LM diff | keep "msg" | undo   # Gedächtnis-Änderungen prüfen / committen / verwerfen

# Nachtlauf (launchd, nur Trockenlauf; braucht Router + Ollama, also Büro-Launcher offen lassen)
bash $LM nightly install            # täglich 03:30 (LM_NIGHTLY_AT=HH:MM)
bash $LM nightly status | uninstall
```

Regeln: nur `[stated]`-Zeilen (der Nutzer hat es gesagt), keine Vermutungen,
nichts Verfallendes, nichts Sensibles — der Prompt dazu liegt in
`prompts/memorize.md`, das Dateiformat in `memory/README.md`. Metrik ist die
**Streichquote** nach ~10 Gesprächen. Details: `docs/notizen-local-memory.md`.
Solange Vorschläge offen sind, startet kein neuer `memorize`/`review`-Lauf – erst entscheiden.
Der Gedächtnis-Proxy hat keine Schreib-Tools; `write`/read-only des Launchers
betrifft nur den MCP-Server, nicht `memory/`.

---

## Szenario G — OpenCode (Terminal-Coding-Agent) am lokalen Modell

OpenCode ist ein Client wie die Web-UI: Es spricht die OpenAI-API und bringt
seinen eigenen Agenten-Prompt und seine eigenen Datei-Tools mit (es arbeitet
im Projektordner, in dem es gestartet wird — nicht über den Lab-MCP).

1. Launcher starten (Szenario A oder D). Für Gedächtnis `LAB_MEMORY=1` bzw. Büro-Launcher.
2. Konfiguration — global `~/.config/opencode/opencode.jsonc` (`.json`/`.jsonc` gleichwertig;
   `node_modules/` daneben gehört OpenCode) oder pro Projekt `opencode.json`.
   Vorlage und `baseURL`-Tabelle: `~/PycharmProjects/local-memory/examples/`. Kurzfassung:

   | OpenCode läuft auf … | Provider / `baseURL`                                        |
   |----------------------|------------------------------------------------------------|
   | MacBook, mit Gedächtnis | `http://127.0.0.1:8091/v1`                              |
   | MacBook, ohne Gedächtnis | `http://127.0.0.1:8080/v1`                             |
   | Mac mini → M4, mit Gedächtnis | `https://macbook-pro-von-hans-werner.tail08de73.ts.net/v1` (Büro-Launcher am MacBook) |
   | Mac mini → lokal (Mellum2, ohne Gedächtnis) | `http://127.0.0.1:8080/v1` am Mini; vorher `bash scripts/start-m2.sh` dort |

   Beide Provider (`m4`, `mini`) in einer Datei → Auswahl im TUI per `/models`:
   stärker-remote oder schwächer-lokal, pro Sitzung.
3. Pflicht in der Config: `"tools": { "subagent": false }` — sonst lehnt
   llama-server jede Anfrage ab (siehe Troubleshooting „Pattern must start with").
4. `opencode` im Projektordner; `/models` muss die Modelle unter den Providern zeigen.
5. Gegenprobe Gedächtnis (M4-Weg): „Welchen Rechner habe ich im Büro?" — und im
   Launcher-Fenster erscheint eine `[lm]`-Zeile.

Hinweise: `limit.context` in der Konfiguration muss zum `ctx-size` des Presets
(`models.ini` 65536 für Qwen, `models-m2.ini` 32768) passen. Über den Proxy (8091)
wird Qwen automatisch ohne Thinking gefahren (`LM_NO_THINK=1`); direkt auf 8080
sendet OpenCode das nicht — denkt Qwen dort endlos, das Preset drosseln. Mellum
am Mini denkt per `reasoning-budget 8192` (Preset). Der Router bedient Anfragen
nacheinander: Büro-Chat und OpenCode teilen sich das Modell.

---

## Neues Gerät dazuhängen (z.B. Mac Mini Büro)

Als **zweiter Server** (eigener llama-server im Büro):
1. Repo klonen/pullen, dann `cd mcp-server && bash setup.sh`.
2. `bash scripts/start-m2.sh` (nur Router, Preset `config/models-m2.ini`, 1 Modell im RAM)
   oder `LAB_BIND=serve bash scripts/launch_lab.command` — ergibt eine eigene
   `https://mac-mini-….ts.net`-URL.
3. Gerät taggen: `tailscale up --advertise-tags=tag:llm-server` (oder im Admin).
   Damit greift die ACL unverändert; du hast dann zwei Chat-Endpunkte im Tailnet.

Als **Client** (greift auf einen bestehenden Server zu):
1. Tailscale drauf, gleicher Account.
2. Gerät taggen: `tag:llm-client` (Admin oder `--advertise-tags`).
3. Im Browser die `.ts.net`-URL des Servers öffnen — oder OpenCode mit dieser
   URL als `baseURL` (Szenario G).

Der Tag entscheidet die Rolle — die ACL-Regel bleibt gleich, egal wie viele
Geräte dazukommen. **Das Gedächtnis wird nicht kopiert:** Der Mini nutzt es
über Serve zum MacBook; eine zweite Kopie von `memory/` wäre eine Inkonsistenz.

---

## Einzel-Launcher (falls getrennt gewünscht)

```bash
bash mcp-server/run_webui.sh        # nur MCP-Server (streamable-http, read-only), 8787
bash scripts/launch_router.command  # nur Router, 8080
bash mcp-server/run_http.sh         # MCP-Server für den MCP-Inspector-Test
bash scripts/start-mcp-kirby.sh     # Kirby-MCP, 8788 (siehe docs/runbook-mcp-kirby.md)
bash scripts/start-m2.sh            # Router am Mac mini (models-m2.ini)
python3 scripts/toolcheck.py        # Diagnose-Proxy 8089 → 8080: Tool-Schemas eines Agenten prüfen
```

`run_webui.sh` read-only ist Default; Schreibzugriff: `MCP_READONLY=0 bash mcp-server/run_webui.sh`.

---

## Modi & Umgebungsvariablen

| Variable / Argument        | Wirkung                                                       |
|----------------------------|--------------------------------------------------------------|
| `… .command write`         | Frontend-Modell darf schreiben + löschen (sonst read-only); gilt für `launch_lab` und `launch_lab_remote` |
| `MCP_READONLY=0/1`         | read-only-gate des MCP-Servers (Argument von launch_lab gewinnt) |
| `LAB_BIND=serve`           | **Remote empfohlen:** Router lokal + Tailscale Serve (HTTPS)  |
| `LAB_KEEP_SERVE=1`         | Serve bleibt nach Ctrl+C aktiv (Router muss trotzdem laufen)  |
| `LAB_MEMORY=1`             | Gedächtnis-Proxy 8091 mitstarten; Serve zeigt dann auf 8091   |
| `LAB_MEMORY_DIR`           | Pfad zum local-memory-Repo (Default `~/PycharmProjects/local-memory`) |
| `LAB_BIND=tailscale`       | direkter Bind an die Tailscale-IP (funktioniert, Serve robuster; Proxys nicht erreichbar) |
| `LAB_BIND=all`             | `0.0.0.0`, alle Interfaces inkl. LAN (breit, nur bewusst)     |
| `LAB_BIND` (unset)         | nur localhost (Default)                                       |
| `HARNESS_MODEL` / `HARNESS_READONLY` | Modellwahl bzw. read-only für den Harness          |
| `RB_*`                     | retrieval-bench, siehe `docs/runbook-retrieval-bench.md`      |
| `LM_*`                     | local-memory, siehe README dort (`LM_MODEL`, `LM_K`, `LM_RETRIEVER`, `LM_SYSTEM_MODE`, …) |

---

## Sicherheit / Hygiene

- Read-only ist überall Default; Schreibzugriff bewusst aktivieren.
- Vor schreibenden Läufen committen (Rollback). Harness, Write-Launcher und
  `memorize --apply` warnen bzw. snapshotten bei unsauberem Git-Baum.
- Tools sind Traversal-geschützt auf das Projekt-Root begrenzt; `run_python` aus.
- Beide Proxys binden nur an 127.0.0.1 und sind reine Durchreicher; sie haben
  keine Schreib-Tools. Nach außen geht nur, was Serve weiterreicht.
- OpenCode bringt eigene Datei-Tools mit und arbeitet im Ordner, in dem es
  gestartet wird — gleiche Regel wie beim Harness: vorher committen.
- Remote nur über **Serve** (tailnet-only, WireGuard-verschlüsselt), nie
  **Funnel** (öffentlich). llama-server hat keine native Auth — Schutz ist die
  Tailnet-Grenze plus ACL. Das gilt für 8091 genauso wie für 8080.
- `local-memory` enthält private Fakten: Repo lokal halten, kein Remote, oder
  `memory/` vor einem Remote in `.gitignore` nehmen.
- **ACL (Härtung):** `config/tailscale-acl-example.json` als Vorlage im
  Tailscale-Admin setzen. Rollen über Tags (`tag:llm-server`, `tag:llm-client`).
  Offen und zu prüfen: Serve-Verkehr kommt am Server über den Tailscale-Daemon
  (HTTPS 443) an, nicht direkt auf 8080/8091 — die Port-Angabe in der Regel
  muss dazu passen; im Admin-Preview testen, bevor du speicherst, sonst sperrst
  du dir andere Zugriffe ab.
- **SSH-Entscheidung (offen):** Ohne Shell-Zugang Mini → MacBook lässt sich ein
  falsch gestarteter Launcher vom Büro aus nicht korrigieren. Tailscale-SSH nur
  für dieses Gerätepaar, per ACL begrenzt, wäre die passende Lösung — eigenes Vorhaben.

---

## Troubleshooting

- **Vom Büro/iPad: „Server is not running or unreachable"**, obwohl das MacBook
  per `tailscale ping` antwortet: Serve ist nicht aktiv — Launcher lief ohne
  `LAB_BIND=serve`. Vom Client bestätigt das ein leeres
  `curl -sI https://….ts.net/`. Lösung: am MacBook `launch_lab_remote.command`
  starten. Schläft das MacBook (`tailscale status` zeigt es offline), hilft nur Aufwecken.
- **Agent (OpenCode u.a.): `Unable to generate parser … JSON schema conversion failed:
  Pattern must start with '^' and end with '$'`:** Meldung von llama-server. Ein
  Tool-Schema des Agenten enthält ein Regex-`pattern`, das nicht mit `^…$` verankert
  ist; llama-server baut aus den Schemas eine Grammatik und lehnt die ganze Anfrage
  mit 400 ab, bevor das Modell läuft. Die Meldung nennt das Tool nicht →
  `python3 scripts/toolcheck.py` starten, im Client die `baseURL` kurz auf
  `http://127.0.0.1:8089/v1` setzen, Frage stellen; die Zeile `unverankert: […]`
  nennt Tool und Feld. Dann das Tool im Client abschalten (OpenCode:
  `"tools": { "<name>": false }`), `baseURL` zurück. Bekannt: OpenCode-Tool
  `subagent` (`sessionID`, Pattern `^ses`).
- **Gedächtnis antwortet nicht / Proxy startet nicht:** Ollama läuft nicht
  (`Errno 61` beim Embedding) oder `local-memory` hat kein venv
  (`bash setup.sh` dort). Der Launcher wartet bis 3 Minuten auf den Router,
  dann steht `[lm] Proxy auf http://127.0.0.1:8091` im Fenster.
- **Chat auf 8091 „kennt mich nicht":** Memorize noch nicht angewendet
  (`memorize` ohne `--apply` schreibt nichts) oder Proxy nach Handänderung
  nicht neu geladen (`lm.command reload`).
- **OpenCode: Modell nicht in `/models` / Fehler beim Aufruf:** `baseURL` prüfen
  (`…/v1` am Ende, richtiger Port laut Tabelle in Szenario G), Router läuft,
  Modell-ID exakt wie im Router (`curl -s http://127.0.0.1:8080/v1/models`).
  Die Config wird nur beim Start gelesen → OpenCode neu starten.
- **OpenCode „vergisst" seine Tools / antwortet wie ein Chat-Assistent:** Proxy
  läuft im Modus `replace` statt `merge` (`LM_SYSTEM_MODE`). Standard ist `merge`.
- **Router-Log: `proxying POST … 8788/mcp … Could not establish connection`:**
  die Web-UI hat den Kirby-MCP eingetragen, der nicht läuft. Harmlos; Eintrag
  unter MCP Servers löschen oder ignorieren.
- **`zsh: command not found: Starte` (o.ä.):** ein Hinweissatz wurde ins Terminal
  eingefügt. Kein Fehler im Lab.
- **Doppelklick auf `.command` tut nichts / „permission denied":** Ausführungsbit
  fehlt → `chmod +x scripts/<datei>.command` (einmalig).
- **`bash: lm.command: No such file`:** falscher Ordner. Launcher mit vollem Pfad
  aufrufen (`bash ~/PycharmProjects/local-memory/lm.command …`); er wechselt selbst
  in sein Verzeichnis.
- **`No module named 'bench'` / `'lm'`:** direkt mit `python -m …` aus dem falschen
  venv gestartet. Immer über `rb.command` bzw. `lm.command`.
- **Web-UI zeigt Zeichensalat über einen Proxy:** Browser-Cache nach einem
  Proxy-Fehler. Privates Fenster oder `?v=2` an die URL hängen.
- **Launcher bricht mit Syntaxfehler ab, obwohl er vorher lief:** er wurde
  überschrieben, während er lief. Neu starten.
- **`ERR_CONNECTION_REFUSED` auf der Tailscale-IP:** meist läuft noch eine
  localhost-Instanz. Bind prüfen: `lsof -iTCP:8080 -sTCP:LISTEN -n -P`. Zeigt es
  `127.0.0.1` → `pkill -f llama-server`, dann sauber neu starten und Banner-`Bind:`
  prüfen. Für Remote generell **Serve** nutzen.
- **`tailscale serve` schlägt fehl (Zertifikat):** im Admin (login.tailscale.com
  → DNS) MagicDNS und HTTPS-Certificates aktivieren.
- **Serve hängt / „background configuration already exists":** `tailscale serve reset`.
- **Ein Client kommt nicht durch, andere schon:** Client-spezifisch — die
  `.ts.net`-URL frisch eingeben (nicht die gecachte IP), Private Relay / anderes
  VPN am Gerät prüfen. (iPad-Safari war so ein Fall; Chrome ging.)
- **MCP-Server-Check:** `curl http://127.0.0.1:8787/mcp` → Antwort
  „Not Acceptable / text/event-stream" (bzw. HTTP 406) heißt: der Server lauscht.
- **Trotz `write` keine Schreib-Tools in der Web-UI** (Modell nennt nur list/read/search/git_*):
  erst prüfen, was wirklich läuft —
  `PID=$(lsof -ti :8787 -sTCP:LISTEN); ps eww -p $PID | tr ' ' '\n' | grep MCP_READONLY`.
  `=1` → alter Read-only-Server blockiert den Port: `kill $PID`, Launcher mit `write` neu starten
  (Fenster 1 muss `READONLY : 0` zeigen, nicht „MCP-Server laeuft bereits").
  `=0` → die Web-UI zeigt eine gecachte Tool-Liste: MCP-Eintrag 8787 aus/an (oder neu anlegen,
  Proxy-Toggle per Stift wieder an), Seite neu laden, **neuen Chat** beginnen.
- **Tailnet-Verbindung prüfen:** `tailscale status` (Geräte + Account),
  `tailscale ping <gerät>` (reine Peer-Verbindung, unabhängig vom Port).
- **`command not found: tailscale`:** vollen Pfad nutzen oder den zsh-Alias setzen.

---

## Projektstruktur (Kurzreferenz)

```
llama-server/
├── core/             mcp_agent.py — wiederverwendbare MCP-Agenten-Basis
├── agents/           dev_agent, dev_agent_diff, excel_agent, llama_harness, weekly_digest
├── scripts/          launch_lab(.command/_write/_remote/_remote_write), launch_router, launch_ipad,
│                     start-m2.sh, start-mcp-kirby, toolcheck.py, run_ab, tool_demo
├── config/           models.ini, models-m2.ini, tailscale-acl-example.json
├── mcp-server/       lab_mcp_server.py, run_webui.sh, run_http.sh, setup.sh
├── retrieval-bench/  Henne-RAG-Experiment (eigenes venv, rb.command, rag_proxy.py)
├── sandbox/          Wegwerf-Experimente
└── docs/             RUNBOOK.md (dieses), runbook-retrieval-bench.md, runbook-mcp-kirby.md,
                      session_kontext.md, architektur-lab.svg

~/PycharmProjects/local-memory/      Gedächtnis (eigenes Repo, kein Remote): lm.command, lm/, memory/, prompts/,
                                     examples/ (opencode.json-Vorlage)
```
