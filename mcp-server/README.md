# llama-server-lab MCP

Lab-Tool-Server, der einem MCP-Client (Claude Desktop) Datei-, Such- und
Git-Zugriff **innerhalb des llama-server-Projektordners** gibt. Traversal-
geschützt, kein freier Shell-Zugriff, `run_python` standardmäßig aus.

## Ablageort

Dieser Ordner liegt als Unterordner im Projekt:

    llama-server/            <- Scope-Root (das, was Claude sehen darf)
    └── mcp-server/          <- dieses Lab-Tool (standalone)
        ├── lab_mcp_server.py
        ├── requirements.txt
        ├── setup.sh
        ├── run_http.sh
        └── claude_desktop_config.snippet.json

Wichtig: Der Scope-Root ist NICHT dieser Ordner, sondern das Projekt darüber.
Deshalb wird `MCP_SCOPE_ROOT` in der Config explizit gesetzt — sonst sähe
Claude nur `mcp-server/`.

## 1. Setup (einmalig)

    cd mcp-server
    bash setup.sh

## 2. Claude Desktop anbinden (stdio)

Öffne in Claude Desktop: Einstellungen → Developer → Edit Config
(macOS-Pfad: `~/Library/Application Support/Claude/claude_desktop_config.json`).
Füge den `llama-server-lab`-Eintrag aus `claude_desktop_config.snippet.json`
in dein `mcpServers`-Objekt ein. Danach Claude Desktop **komplett beenden**
(Cmd+Q) und neu starten.

Hinweis: absolute Pfade sind Pflicht — Claude Desktop startet mit minimalem
PATH, `python` allein schlägt fehl.

## 3. Verifikation

- In Claude Desktop: unten im Eingabefeld erscheint ein Tool-/Hammer-Symbol
  mit der Anzahl verfügbarer Tools. Anklicken zeigt die Liste
  (list_directory, read_file, search_files, write_file, delete_file,
  git_status/diff/log/commit).
- Alternativ vor dem Anbinden testen mit dem MCP-Inspector:

      bash run_http.sh                 # startet auf 127.0.0.1:8787
      npx @modelcontextprotocol/inspector   # in zweitem Terminal

## Sicherheit / Hygiene

- `run_python` ist aus (`MCP_ALLOW_PYTHON=0`). Nur bewusst aktivieren.
- Für einen vorsichtigen Erststart nur-lesend: `"MCP_READONLY": "1"` in den
  env-Block. Das entfernt write/delete/commit.
- stdio-Server laufen mit deinen vollen Nutzerrechten — der Scope-Guard ist
  der eigentliche Schutz. Vor agentischen Änderungen ein `git commit` als
  Rollback-Punkt.
- Keine Netzwerk-Exposition in dieser Stufe. Der iPad/Tailscale-Weg
  (streamable-http + ACL) ist ein separater, bewusster Schritt.
