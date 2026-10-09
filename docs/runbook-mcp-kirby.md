# Runbook: Kirby-MCP am lokalen llama-server (M2 Mac mini + M4 MacBook)

Stand: 24.09.2026 · llama.cpp b9890 (Homebrew) · MCP-SDK 1.x

## Zweck

Die llama-server-Web-UI bekommt über MCP Lesezugriff auf ein Kirby-Testprojekt.
Dafür läuft eine **zweite Instanz** von `mcp-server/lab_mcp_server.py` mit
eigenem Scope, eigenem Port und eigener Sperrliste. Die Lab-Instanz (Port 8787)
bleibt davon unberührt.

## Architektur

```
Browser (Web-UI, 127.0.0.1:8080)
   │  MCP-Anfrage
   ▼
llama-server Router (8080, --ui-mcp-proxy)  ──►  Modell-Instanz (Port zufällig)
   │  CORS-Proxy
   ▼
Kirby-MCP (127.0.0.1:8788, read-only)  ──►  ~/Sites/bremer-kke.de
```

| Dienst | Port | Start |
|---|---|---|
| llama-server Router | 8080 | siehe „Starten“ |
| Lab-MCP | 8787 | `scripts/launch_lab.command` bzw. `mcp-server/run_webui.sh` |
| Kirby-MCP | 8788 | `./scripts/start-mcp-kirby.sh` |

Alles bindet ausschließlich an `127.0.0.1`.

## Dateien

| Datei | Inhalt |
|---|---|
| `config/models-m2.ini` | Router-Preset für den M2 (24 GB RAM) |
| `config/models.ini` | Router-Preset für den M4 (48 GB RAM) |
| `scripts/start-m2.sh` | Router-Start M2 mit `--models-max 1` |
| `scripts/launch_router.command` | Router-Start M4, `--models-max` per `LAB_MODELS_MAX` (Default 2), mit `--ui-mcp-proxy` |
| `scripts/launch_lab.command` | Lab-MCP (8787) **und** Router zusammen |
| `scripts/start-mcp-kirby.sh` | Kirby-MCP-Instanz (read-only, Sperrliste, ohne Web) |
| `mcp-server/lab_mcp_server.py` | MCP-Server, per Umgebungsvariablen konfiguriert |
| `scripts/test_mcp_deny.py` | Dry-Run-Test für Scope-Guard und Sperrliste |

## Konfiguration des MCP-Servers

Alle Schalter sind Umgebungsvariablen. Die Defaults entsprechen dem Verhalten
der Lab-Instanz.

| Variable | Default | Kirby-Instanz | Bedeutung |
|---|---|---|---|
| `MCP_SCOPE_ROOT` | Ordner der Serverdatei | `~/Sites/bremer-kke.de` | Einziger erlaubter Bereich |
| `MCP_PORT` | 8787 | 8788 | Port |
| `MCP_HOST` | 127.0.0.1 | 127.0.0.1 | Bind-Adresse |
| `MCP_TRANSPORT` | streamable-http | streamable-http | Endpunkt ist `/mcp` |
| `MCP_READONLY` | 0 | 1 | Schreib-/Lösch-Tools aus |
| `MCP_ALLOW_PYTHON` | 0 | 0 | `run_python` aus |
| `MCP_ALLOW_WEB` | 1 | 0 | `web_search` aus |
| `MCP_NAME` | llama-server-lab | kirby-bremer-kke | Name in der Web-UI |
| `MCP_DENY` | leer | siehe unten | Gesperrte Pfade relativ zum Scope |

Sperrliste der Kirby-Instanz:
`site/accounts, site/config, site/sessions, site/cache, .env, .license, media`

Gesperrt heißt: Der Pfad selbst und alles darunter ist für `read_file`,
`list_directory` und `search_files` tabu. `search_files` prüft jede Datei
einzeln, auch Symlinks, die aus dem Scope herauszeigen, werden übersprungen.

Der Kirby-Launcher nutzt das Python aus `.venv` im Repo-Root (auf M2 und M4
mit `mcp` 1.x vorhanden). `run_webui.sh` nutzt dagegen `mcp-server/.venv`.

## Starten

Terminal-Tabs am besten benennen („Router 8080“, „Kirby-MCP 8788“, „Shell“),
damit Ctrl+C nicht im falschen Fenster landet. Alle Befehle im Repo-Root.

**Tab 1: Kirby-MCP** (beide Maschinen)

```bash
./scripts/start-mcp-kirby.sh
```

Anderes Projekt: Pfad als Argument anhängen, z. B.
`./scripts/start-mcp-kirby.sh ~/Sites/kirby-test`.

Erwartetes Banner: `readonly : True`, `web_search : False`,
`name : kirby-bremer-kke`, Sperrliste, dann `Uvicorn running on http://127.0.0.1:8788`.

**Tab 2: Router mit MCP-Proxy**

M2:

```bash
llama-server --port 8080 --models-preset config/models-m2.ini --models-max 1 --ui-mcp-proxy
```

`start-m2.sh` enthält `--ui-mcp-proxy` noch nicht.

M4:

```bash
bash scripts/launch_router.command                   # nur Router, 2 Modelle gleichzeitig
LAB_MODELS_MAX=1 bash scripts/launch_router.command  # fuer Vergleichstests
```

Achtung: `launch_router.command` startet **nur** den Router. Der Lab-MCP (8787)
kommt nur mit `launch_lab.command`. Für die Kirby-Arbeit wird er nicht gebraucht.

## In der Web-UI verbinden (einmalig pro Browser/Maschine)

Die MCP-Einträge liegen im Browser und werden zwischen M2 und M4 nicht
synchronisiert.

1. http://127.0.0.1:8080 öffnen, ⚙ oben rechts → MCP → „Add New Server“
2. URL: `http://127.0.0.1:8788/mcp`
3. **Wichtig:** Den neuen Eintrag über das **Stift-Symbol bearbeiten** und
   „use llama-server proxy“ einschalten. Der Schalter erscheint nur beim
   Bearbeiten, nicht beim Anlegen. Ohne ihn blockiert der Browser die Anfrage
   (CORS, Log zeigt `"useProxy": false` und „Failed to fetch“).
4. Erwartet: `kirby-bremer-kke`, 6 Tools (`list_directory`, `read_file`,
   `search_files`, `git_status`, `git_diff`, `git_log`)
5. **Nur einen MCP-Server gleichzeitig aktiv lassen.** Ist auch
   `llama-server-lab` (8787) eingeschaltet, liefern beide Server gleichnamige
   Tools. Der Chat blieb im Test dann bei „Processing…“ hängen, ohne dass die
   Anfrage das Modell erreichte. Lab-Eintrag per Schalter deaktivieren.

Die Chats liegen im Browser, nicht im Server. Ein Router-Neustart löscht sie nicht.

## Prüfen

**Dry-Run-Test** (synthetischer Ordner in `/tmp`, nicht das echte Projekt):

```bash
.venv/bin/python scripts/test_mcp_deny.py
```

Erwartet: 13× `PASS`, am Ende `ALLES OK`.

**Praxistest im neuen Chat:**

- „Liste die Ordner im Projekt auf und sag mir, welche Templates es in
  site/templates gibt.“ → echte Dateinamen, `POST /mcp` im Kirby-Terminal
- „Lies die Datei site/accounts und sag mir, was drinsteht.“ → Tool meldet
  „gesperrt (MCP_DENY)“

Bei Antworten gilt: Verlässlich sind die aufklappbaren Tool-Aufrufe, nicht der
Fließtext. Mellum hat im Test eine Begründung für die Sperre dazuerfunden.

Woran man den benutzten Server erkennt: Im Connection Log steht die Ziel-URL
(`…8787…` = Lab, `…8788…` = Kirby) und unter `serverInfo` der Name.

## Fehlerbilder

| Symptom | Ursache | Lösung |
|---|---|---|
| UI: „proxy error: Could not establish connection“ | MCP-Server auf dem Zielport läuft nicht | `lsof -nP -i :8788` (bzw. `:8787`) → leer? Server starten, in der UI ↻ |
| UI: „Failed to fetch (check CORS?)“, Log `"useProxy": false` | Proxy-Schalter am Eintrag aus | Eintrag bearbeiten (Stift) → „use llama-server proxy“ an |
| Chat hängt bei „Processing…“, Router-Log zeigt nur `ListToolsRequest` | zwei MCP-Server mit gleichen Tool-Namen aktiv | nur einen Server aktiv lassen, Tab neu laden, neuer Chat |
| Modell findet kein Kirby, listet `core/`, `agents/` … | Chat nutzt den Lab-MCP (8787) | Kirby-Eintrag an, Lab-Eintrag aus |
| Router: „couldn't bind … port 8080“ | alter Router läuft noch | `lsof -nP -i :8080`, dann `kill <PID>`; danach `pgrep -fl llama-server` und verwaiste Modell-Instanzen ebenfalls beenden |
| `preset file does not exist` | Router nicht aus dem Repo-Root gestartet | `cd` ins Repo-Root |
| 404 auf `http://127.0.0.1:8788` | Browser ruft Root auf | normal, MCP-Endpunkt ist `/mcp` |
| `OPTIONS /mcp … 405` im Kirby-Terminal | direkter Browser-Versuch ohne Proxy | harmlos |
| Modell antwortet sehr lange beim ersten Aufruf | Download ins HF-Cache | `du -sh ~/.cache/huggingface/hub/models--<name>` beobachten |
| Modell wiederholt alte Antworten | Chatverlauf wird mitgeschickt | für Vergleiche immer neuen Chat öffnen |

Fallstricke im Terminal:

- `#`-Kommentare funktionieren in zsh interaktiv nicht, nur in Skripten.
- `$0` ist im Terminal der Shell-Name, nicht ein Skriptpfad. Zeilen mit `$0`
  gehören nur in Skripte.
- Blöcke mit `cat > datei << 'EOF'` im Terminal einfügen, nicht im Editor.

## Messwerte

| Maschine | Modell | Generierung |
|---|---|---|
| M2 (24 GB) | Apertus 8B Q4_K_M | 14,8 t/s |
| M4 (48 GB) | Qwen3.6 27B Q4_K_XL | 8,8 t/s |

## Sicherheit

- **Nur localhost.** Router und MCP binden an `127.0.0.1`. Der CORS-Proxy ist
  laut llama.cpp experimentell und nicht für nicht vertrauenswürdige Umgebungen
  gedacht. Bei einer Freigabe per Tailscale (`LAB_BIND=serve`) reicht der Proxy
  alle laufenden MCP-Server mit ins Tailnet durch, also auch den Kirby-MCP:
  vorher bewusst entscheiden.
- **Kein Web-Zugang für die Kirby-Instanz.** `web_search` wäre ein Kanal nach
  außen: Projektinhalte könnten als Suchbegriff das Haus verlassen, etwa durch
  Anweisungen in Content-Dateien (Prompt Injection).
- **Echte Daten.** `bremer-kke.de` ist ein reales Projekt. Für Tests besser eine
  Kopie mit synthetischem Content und geleertem `site/accounts/` verwenden.
- **Git-Tools prüfen die Sperrliste nicht.** Vor `git init` im Kirby-Ordner
  `site/accounts/` in dessen `.gitignore` eintragen.
- **MCP-SDK:** Version 2.x benennt `FastMCP` um, der Server startet dann nicht.
  In `requirements.txt` `mcp<2` pinnen.

## Vor Schreibzugriff (noch nicht umgesetzt)

1. Im Kirby-Ordner: `.gitignore` mit `site/accounts/` u. a., dann `git init`
   und erster Commit als Rollback-Punkt
2. Im Launcher `MCP_READONLY=0` setzen, `MCP_ALLOW_DELETE=0` explizit
3. Sperrliste beibehalten, Test erneut laufen lassen
4. Vor jeder agentischen Änderungsrunde committen

## Offene Punkte

- `--ui-mcp-proxy` in `scripts/start-m2.sh` übernehmen
- Tool-Namen pro Instanz unterscheidbar machen (Präfix), damit Lab- und
  Kirby-MCP gleichzeitig aktiv sein können
- `kirby/` (Framework-Core) evtl. auf die Sperrliste: hält Suchergebnisse klein
- Qwen3.6 27B Q3 auf dem M2 unter Speicherdruck testen
- `mcp<2` in `mcp-server/requirements.txt`
- Gemma 4 12B QAT ins M2-Preset (Repo-Name prüfen)
