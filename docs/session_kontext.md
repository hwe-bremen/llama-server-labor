# Session-Kontext — llama-server Lab

Wiedereinstiegspunkt: Wo stehen wir, was ist offen, wie kommt man rein.
Ergänzt `docs/RUNBOOK.md` (Bedienung) um den *Stand* und die *nächsten Schritte*.

Letzte Session: 2026-07-05 · Branch `main`, working tree clean.

---

## Wo wir stehen (erledigt & committet)

- **MCP-Server** (`mcp-server/lab_mcp_server.py`): Tools list/read/search/write/
  delete + git status/diff/log/commit. Traversal-geschützter Scope aufs
  Projekt-Root, `run_python` aus, read-only als Default. Transporte: stdio
  (Claude Desktop, Harness) und streamable-http (Web-UI, Port 8787).
- **Reusable Agent-Basis** (`core/mcp_agent.py`) + dünner Harness
  (`agents/llama_harness.py`): lokales Modell als MCP-Agent, Modell-
  Autodiscovery (bevorzugt Mellum).
- **Web-UI-Anbindung**: llama.cpp-Web-UI spricht den MCP-Server über den
  `--ui-mcp-proxy` an (URL in der UI: `http://127.0.0.1:8787/mcp` + Toggle
  „use llama-server proxy"). Lokal und remote bestätigt.
- **Orchestrator** (`scripts/launch_lab.command`): startet MCP-Server + Router
  mit einem Aufruf. Modi:
  - Zugriff: `read` (Default) / `write` (1. Argument), plus Doppelklick-Wrapper
    `launch_lab_write.command`.
  - Netzwerk via `LAB_BIND`: `local` (Default) / `tailscale` (Direct-Bind) /
    `serve` (Router lokal + Tailscale Serve, HTTPS) / `all`.
- **Router-Fix** (`scripts/launch_router.command`): öffnet 127.0.0.1 statt
  localhost (CORS); prüft die Ziel-URL statt nur den Port (Bind-Wechsel-Fallstrick).
- **Remote-Zugang (iPad/iPhone)**: funktioniert. Zwei Wege erprobt —
  Direct-Bind (`LAB_BIND=tailscale`, URL `http://100.85.131.87:8080`) und
  Tailscale Serve (URL `https://macbook-pro-von-hans-werner.tail7f9148.ts.net`).
  Serverseitig sind beide fertig; der IP-Weg lief am zuverlässigsten.
- **Tailscale-ACL**: tag-basiert (`tag:llm-client → tag:llm-server:8080`),
  gespeichert und aktiv. Vorlage: `config/tailscale-acl-example.json`.
- **Doku**: `Readme/` → `docs/` migriert, `docs/RUNBOOK.md` auf Stand.

---

## Offene Punkte (bewusst, für die nächste Session)

1. **ACL-Härtung scharf stellen.** In der gespeicherten Policy ist noch die
   Übergangsregel `{ "action":"accept", "src":["autogroup:owner"], "dst":["*:*"] }`
   drin (verhindert Aussperren beim Taggen). Solange sie drin ist, greift die
   „nur getaggte Clients auf 8080"-Isolation **nicht scharf**.
   - **Blocker/Entscheidung:** Tailscale-SSH war aktiv. Wird SSH zwischen den
     eigenen Geräten gebraucht? Wenn ja → vor dem Entfernen der owner-Regel eine
     eigene SSH-Regel ergänzen. Wenn nein → owner-Regel ersatzlos entfernen,
     dann per `Preview rules` gegenprüfen: 8080 = accept, 22 = deny.

2. **Mac Mini (Büro) einbinden.** Morgen geplant.
   - Als **Server**: Repo klonen/pullen → `cd mcp-server && bash setup.sh` →
     `LAB_BIND=serve bash scripts/launch_lab.command` → im Admin `tag:llm-server`
     taggen. Ergibt eigene `.ts.net`-URL. ACL bleibt unverändert.
   - Als **Client**: Tailscale drauf, `tag:llm-client` taggen, Server-URL öffnen.

3. **Serve + HTTPS am iPad final glätten** (optional, Kür). Serverseitig fertig
   (curl gab `HTTP/2 … server: llama.cpp`). Reststolpersteine sind iPad-seitig:
   iCloud Private Relay aus, „Use Tailscale DNS" an, Tab frisch laden. Der
   IP-Weg funktioniert derweil zuverlässig.

---

## Schnellstart nächste Session

Lokal arbeiten (Standard):
```
bash scripts/launch_lab.command            # read-only, Router+MCP lokal
bash scripts/launch_lab.command write      # schreibfähig
```

Remote (iPad) — zuverlässiger IP-Weg:
```
pkill -f llama-server
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve reset
LAB_BIND=tailscale bash scripts/launch_lab.command
# iPad: http://100.85.131.87:8080
```

Remote (iPad) — saubere HTTPS-Variante:
```
bash scripts/launch_lab.command
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve --bg 8080
# iPad: https://macbook-pro-von-hans-werner.tail7f9148.ts.net
```

Modellwahl: bei „Server unavailable" / langsamem Laden im UI-Dropdown das
leichteste Modell nehmen — `JetBrains/Mellum2-…-Q4_K_M:Q4_K_M`. Große Modelle
(`Qwen3.6-27B`, `gemma-4-26B`) können beim On-demand-Laden hängen/OOM auslösen.

---

## Wichtige Fakten / Referenzen

- Repo: Branch `main` (von `master` umbenannt), mit `origin`-Remote.
- Tailnet: `tail7f9148.ts.net`, Account `plan2-hw@dobben-united.de`.
- Geräte: `macbook-pro-von-hans-werner` (100.85.131.87), `ipad165`
  (100.112.234.5), `iphone181` (100.112.185.65).
- Tailscale-CLI-Pfad (macOS): `/Applications/Tailscale.app/Contents/MacOS/Tailscale`
  (kein `tailscale` im PATH; ggf. Alias in `~/.zshrc`).
- MagicDNS + HTTPS-Certificates im Tailscale-Admin sind **aktiviert**.
- Serve abschalten: `tailscale serve reset` (bzw. `--https=443 off`).
- MCP-Server-Lebenscheck: `curl http://127.0.0.1:8787/mcp` → „Not Acceptable /
  text/event-stream" bzw. 406 = läuft.
- Router-Lebenscheck: `curl -sI http://127.0.0.1:8080/health` → 200.

---

## Betriebsnotizen / Stolpersteine (aus dieser Session)

- **Bind-Wechsel-Falle**: läuft noch eine Instanz auf einer anderen Bind-Adresse
  (localhost vs. Tailscale-IP), erst `pkill -f llama-server`, dann neu. Banner
  `Bind:` prüfen.
- **iPad-Safari** zickte (Private Relay/Cache) — Chrome ging. Bei Problemen die
  `.ts.net`/IP-URL frisch eintippen, nicht aus dem Verlauf.
- **`git mv`-Falle**: die Datei heißt `docs/RUNBOOK.md` (Großschreibung).
- **origin-Remote**: Push ist eine bewusste Entscheidung. Falls das Remote
  öffentlich ist — die ACL-Vorlage und diese Kontextdatei enthalten Tailnet-Name,
  Gerätenamen und `100.x`-Tailscale-IPs. Das sind keine Passwörter/Secrets (die
  IPs sind nur im Tailnet nutzbar), aber bewusst wahrnehmen.
- **MCP-Server (`llama-server-lab`, stdio via Claude Desktop)** ging während der
  Session mehrfach in Timeout, nachdem Prozesse neu gestartet wurden. Für
  direkten Datei-/Git-Zugriff über Claude ggf. Claude Desktop neu starten;
  sonst Datei-Handoff über `/mnt/user-data/outputs/`. Nach einem Neustart den
  Scope-Pfad im Config-Eintrag prüfen (muss auf `…/llama-server` zeigen).

---

## Grenze (immer)

Reines Lab. Kein AskValentinAI-Code, keine echten Mandanten-/Kundendaten, nichts
Produktives. Sobald ein Vorhaben das berührt → gehört ins AskValentinAI-Projekt,
nicht hierher.
