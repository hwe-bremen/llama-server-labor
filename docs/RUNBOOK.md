# Runbook — llama-server Lab

Betriebsanleitung für die lokale und remote Nutzung des Labs. Alle Befehle aus
dem Projekt-Root (`~/PycharmProjects/llama-server`) ausführen.

## Komponenten & Ports

| Komponente          | Port / Transport         | Zweck                                              |
|---------------------|--------------------------|----------------------------------------------------|
| llama-server Router | 8080 (HTTP)              | Chat-UI, OpenAI-API, MCP-CORS-Proxy (`--ui-mcp-proxy`) |
| MCP-Server (Tools)  | 8787 (streamable-http)   | Tools für die Web-UI (list/read/search/write/… im Scope) |
| MCP-Server (Tools)  | stdio                    | Tools für Claude Desktop und den llama-Harness     |

Scope aller Tools: das Projekt-Root, Traversal-geschützt. `run_python` ist aus.
Read-only ist der Default; Schreibzugriff wird bewusst aktiviert.

## Einmalige Voraussetzungen

- MCP-Server-venv: `cd mcp-server && bash setup.sh` (installiert `mcp`).
- Projekt-venv für den Harness: im `.venv` `pip install openai mcp`.
- Claude Desktop: `llama-server-lab`-Eintrag in `claude_desktop_config.json`
  (stdio, `MCP_SCOPE_ROOT` = Projekt-Root). Läuft danach automatisch.
- Remote: Tailscale auf Mac **und** den Client-Geräten, gleicher Account/Tailnet.
- macOS: die Tailscale-CLI liegt unter
  `/Applications/Tailscale.app/Contents/MacOS/Tailscale`. Bequemer per Alias in
  `~/.zshrc`: `alias tailscale="/Applications/Tailscale.app/Contents/MacOS/Tailscale"`.
- Für Serve: im Tailscale-Admin (login.tailscale.com → DNS) MagicDNS und
  HTTPS-Certificates aktivieren.

---

## Szenario A — Lokal: Chat-UI + Tools (Standardfall)

Ein Aufruf startet MCP-Server (8787) **und** Router (8080) und öffnet die UI:

```bash
bash scripts/launch_lab.command          # read-only (sicher)
bash scripts/launch_lab.command write    # schreib-/löschfähig
```

Doppelklick-Varianten (Finder): `launch_lab.command` (read-only),
`launch_lab_write.command` (write). Beenden: Ctrl+C — stoppt beide Dienste.

MCP in der UI einmalig eintragen (Browser-Storage ist pro Gerät):
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
stdio-Subprozess (Config), und Claude nutzt die Tools direkt.

---

## Szenario D — Remote (iPad / iPhone / …) via Tailscale Serve

**Empfohlener Remote-Weg, jetzt ein Befehl.** Der Router läuft lokal auf
`127.0.0.1:8080`, der Tailscale-Daemon (Serve) macht die HTTPS-Exposition ins
Tailnet — llama-server selbst bleibt auf localhost.

```bash
LAB_BIND=serve bash scripts/launch_lab.command          # remote, read-only
LAB_BIND=serve bash scripts/launch_lab.command write    # remote, schreibfähig
```

Der Orchestrator startet Serve mit (`tailscale serve --bg 8080`), zeigt die
`https://<mac-name>.<tailnet>.ts.net`-URL, und räumt Serve beim Beenden per
`tailscale serve reset` wieder ab. Diese URL am Client öffnen (nicht die
`100.x`-IP). MCP-Eintrag wie in Szenario A: `http://127.0.0.1:8787/mcp` +
Proxy-Toggle (der Proxy löst die URL serverseitig auf).

Manuell (falls Serve dauerhaft laufen soll, auch nach dem Beenden des Routers):
`tailscale serve --bg 8080` in einem eigenen Terminal; abschalten mit
`tailscale serve reset`.

**Direkter Bind als Alternative** (`LAB_BIND=tailscale`): funktioniert (iPhone/
iPad-Chrome getestet), bindet llama-server aber direkt an die Tailscale-IP und
kann je nach Client (iPad-Safari mit Private Relay/Cache) zicken. Serve ist
robuster und der Standardweg.

---

## Neues Gerät dazuhängen (z.B. Mac Mini Büro)

Als **zweiter Server** (eigener llama-server im Büro):
1. Repo klonen/pullen, dann `cd mcp-server && bash setup.sh`.
2. `LAB_BIND=serve bash scripts/launch_lab.command` — ergibt eine eigene
   `https://mac-mini-….ts.net`-URL.
3. Gerät taggen: `tailscale up --advertise-tags=tag:llm-server` (oder im Admin).
   Damit greift die ACL unverändert; du hast dann zwei Chat-Endpunkte im Tailnet.

Als **Client** (greift auf einen bestehenden Server zu):
1. Tailscale drauf, gleicher Account.
2. Gerät taggen: `tag:llm-client` (Admin oder `--advertise-tags`).
3. Im Browser die `.ts.net`-URL des Servers öffnen.

Der Tag entscheidet die Rolle — die ACL-Regel (`tag:llm-client → tag:llm-server:8080`)
bleibt gleich, egal wie viele Geräte dazukommen.

---

## Einzel-Launcher (falls getrennt gewünscht)

```bash
bash mcp-server/run_webui.sh        # nur MCP-Server (streamable-http, read-only), 8787
bash scripts/launch_router.command  # nur Router, 8080
bash mcp-server/run_http.sh         # MCP-Server für den MCP-Inspector-Test
```

`run_webui.sh` read-only ist Default; Schreibzugriff: `MCP_READONLY=0 bash mcp-server/run_webui.sh`.

---

## Modi & Umgebungsvariablen

| Variable / Argument        | Wirkung                                                       |
|----------------------------|--------------------------------------------------------------|
| `launch_lab.command write` | Frontend-Modell darf schreiben + löschen (sonst read-only)   |
| `MCP_READONLY=0/1`         | read-only-Gate des MCP-Servers (Argument von launch_lab gewinnt) |
| `LAB_BIND=serve`           | **Remote empfohlen:** Router lokal + Tailscale Serve (HTTPS)  |
| `LAB_BIND=tailscale`       | direkter Bind an die Tailscale-IP (funktioniert, Serve robuster) |
| `LAB_BIND=all`             | `0.0.0.0`, alle Interfaces inkl. LAN (breit, nur bewusst)     |
| `LAB_BIND` (unset)         | nur localhost (Default)                                       |
| `HARNESS_MODEL` / `HARNESS_READONLY` | Modellwahl bzw. read-only für den Harness          |

---

## Sicherheit / Hygiene

- Read-only ist überall Default; Schreibzugriff bewusst aktivieren.
- Vor schreibenden Läufen committen (Rollback). Harness und Write-Launcher
  warnen bei unsauberem Git-Baum.
- Tools sind Traversal-geschützt auf das Projekt-Root begrenzt; `run_python` aus.
- Remote nur über **Serve** (tailnet-only, WireGuard-verschlüsselt), nie
  **Funnel** (öffentlich). llama-server hat keine native Auth — Schutz ist die
  Tailnet-Grenze plus ACL.
- **ACL (Härtung):** `config/tailscale-acl-example.json` als Vorlage im
  Tailscale-Admin setzen. Rollen über Tags (`tag:llm-server`, `tag:llm-client`),
  Regel `tag:llm-client → tag:llm-server:8080`. Gilt auch für Serve. Vorsicht:
  eine restriktive Policy ersetzt die Default-Allow-All — im Admin-Preview
  testen, bevor du speicherst, sonst sperrst du dir andere Zugriffe ab.

---

## Troubleshooting

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
- **Tailnet-Verbindung prüfen:** `tailscale status` (Geräte + Account),
  `tailscale ping <gerät>` (reine Peer-Verbindung, unabhängig vom Port).
- **`command not found: tailscale`:** vollen Pfad nutzen oder den zsh-Alias setzen.

---

## Projektstruktur (Kurzreferenz)

```
llama-server/
├── core/         mcp_agent.py — wiederverwendbare MCP-Agenten-Basis
├── agents/       dev_agent, dev_agent_diff, excel_agent, llama_harness
├── scripts/      launch_lab(.command/_write), launch_router, run_ab, tool_demo
├── config/       models.ini, tailscale-acl-example.json
├── mcp-server/   lab_mcp_server.py, run_webui.sh, run_http.sh, setup.sh
├── sandbox/      Wegwerf-Experimente
└── docs/         dieses Runbook
```
