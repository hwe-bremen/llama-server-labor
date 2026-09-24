# Runbook: Kirby-MCP am lokalen llama-server (M2 Mac mini)

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
llama-server Router (8080, --ui-mcp-proxy)  ──►  Modell-Instanz (Port zufällig, max. 1)
   │  CORS-Proxy
   ▼
Kirby-MCP (127.0.0.1:8788, read-only)  ──►  ~/Sites/bremer-kke.de
```

| Dienst | Port | Start |
|---|---|---|
| llama-server Router | 8080 | siehe „Starten“ |
| Lab-MCP | 8787 | wie bisher |
| Kirby-MCP | 8788 | `./scripts/start-mcp-kirby.sh` |

Alles bindet ausschließlich an `127.0.0.1`.

## Dateien

| Datei | Inhalt |
|---|---|
| `config/models-m2.ini` | Router-Preset für den M2 (24 GB RAM) |
| `scripts/start-m2.sh` | Router-Start mit `--models-max 1` |
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

## Starten

Drei Terminal-Tabs, am besten benannt („Router 8080“, „Kirby-MCP 8788“, „Shell“),
damit Ctrl+C nicht im falschen Fenster landet. Alle Befehle im Repo-Root.

**Tab 1: Kirby-MCP**

```bash
./scripts/start-mcp-kirby.sh
```

Anderes Projekt: Pfad als Argument anhängen, z. B.
`./scripts/start-mcp-kirby.sh ~/Sites/kirby-test`.

Erwartetes Banner: `readonly : True`, `web_search : False`,
`name : kirby-bremer-kke`, Sperrliste, dann `Uvicorn running on http://127.0.0.1:8788`.

**Tab 2: Router mit MCP-Proxy**

```bash
llama-server --port 8080 --models-preset config/models-m2.ini --models-max 1 --ui-mcp-proxy
```

`start-m2.sh` enthält `--ui-mcp-proxy` noch nicht. Ohne das Flag kann die
Web-UI keinen MCP-Server erreichen.

## In der Web-UI verbinden (einmalig)

1. http://127.0.0.1:8080 öffnen, ⚙ oben rechts → MCP → „Add New Server“
2. URL: `http://127.0.0.1:8788/mcp`
3. Erwartet: `kirby-bremer-kke`, 6 Tools (`list_directory`, `read_file`,
   `search_files`, `git_status`, `git_diff`, `git_log`)

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

## Fehlerbilder

| Symptom | Ursache | Lösung |
|---|---|---|
| UI: „proxy error: Could not establish connection“ | Kirby-MCP läuft nicht | `lsof -nP -i :8788` → leer? Tab 1 neu starten, in der UI ↻ |
| Router: „couldn't bind … port 8080“ | alter Router läuft noch | `lsof -nP -i :8080`, dann `kill <PID>`; danach `pgrep -fl llama-server` und verwaiste Modell-Instanzen ebenfalls beenden |
| `preset file does not exist` | Router nicht aus dem Repo-Root gestartet | `cd` ins Repo-Root |
| 404 auf `http://127.0.0.1:8788` | Browser ruft Root auf | normal, MCP-Endpunkt ist `/mcp` |
| Modell antwortet sehr lange beim ersten Aufruf | Download ins HF-Cache | `du -sh ~/.cache/huggingface/hub/models--<name>` beobachten |
| Modell wiederholt alte Antworten | Chatverlauf wird mitgeschickt | für Vergleiche immer neuen Chat öffnen |

Fallstricke im Terminal:

- `#`-Kommentare funktionieren in zsh interaktiv nicht, nur in Skripten.
- `$0` ist im Terminal der Shell-Name, nicht ein Skriptpfad. Zeilen mit `$0`
  gehören nur in Skripte.
- Blöcke mit `cat > datei << 'EOF'` im Terminal einfügen, nicht im Editor.

## Sicherheit

- **Nur localhost.** Router und MCP binden an `127.0.0.1`. Der CORS-Proxy ist
  laut llama.cpp experimentell und nicht für nicht vertrauenswürdige Umgebungen
  gedacht. Bei einer Freigabe per Tailscale reicht der Proxy den Kirby-MCP mit
  nach außen durch: vorher bewusst entscheiden.
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
- Qwen3.6 27B Q3 unter Speicherdruck testen
- `mcp<2` in `mcp-server/requirements.txt`
- Gemma 4 12B QAT ins M2-Preset (Repo-Name prüfen)
