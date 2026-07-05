# Runbook — llama-server Lab

Betriebsanleitung für die lokale und remote Nutzung des Labs. Alle Befehle aus
dem Projekt-Root (`~/PycharmProjects/llama-server`) ausführen.

## Komponenten & Ports

| Komponente        | Port / Transport         | Zweck                                              |
|-------------------|--------------------------|----------------------------------------------------|
| llama-server Router | 8080 (HTTP)            | Chat-UI, OpenAI-API, MCP-CORS-Proxy (`--ui-mcp-proxy`) |
| MCP-Server (Tools)  | 8787 (streamable-http) | Tools für die Web-UI (list/read/search/write/… im Scope) |
| MCP-Server (Tools)  | stdio                  | Tools für Claude Desktop und den llama-Harness     |

Scope aller Tools: das Projekt-Root, Traversal-geschützt. `run_python` ist aus.
Read-only ist der Default; Schreibzugriff wird bewusst aktiviert.

## Einmalige Voraussetzungen

- MCP-Server-venv: `cd mcp-server && bash setup.sh` (installiert `mcp`).
- Projekt-venv für den Harness: im `.venv` `pip install openai mcp`.
- Claude Desktop: `llama-server-lab`-Eintrag in `claude_desktop_config.json`
  (stdio, `MCP_SCOPE_ROOT` = Projekt-Root). Läuft danach automatisch.
- Remote: Tailscale auf Mac **und** iPad/iPhone, gleicher Account/Tailnet.
- macOS: die Tailscale-CLI liegt unter
  `/Applications/Tailscale.app/Contents/MacOS/Tailscale`. Bequemer per Alias in
  `~/.zshrc`: `alias tailscale="/Applications/Tailscale.app/Contents/MacOS/Tailscale"`.

---

## Szenario A — Lokal: Chat-UI + Tools (Standardfall)

Ein Aufruf startet MCP-Server (8787) **und** Router (8080) und öffnet die UI:

```bash
bash scripts/launch_lab.command          # read-only (sicher)
bash scripts/launch_lab.command write    # schreib-/löschfähig
```

Doppelklick-Varianten (macOS Finder): `launch_lab.command` (read-only),
`launch_lab_write.command` (write). Beenden: Ctrl+C im Terminal — stoppt beide
Dienste.

In der Web-UI einmalig den MCP-Server eintragen (Browser-Storage ist pro Gerät):
1. MCP Servers → Add New Server → URL `http://127.0.0.1:8787/mcp`
2. Server per Stift-Icon **editieren** → Toggle „use llama-server proxy" AN
   (der Toggle erscheint nur beim Editieren, nicht beim Hinzufügen)

Wichtig: die UI über **`http://127.0.0.1:8080`** öffnen, nicht `localhost` (CORS).

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

## Szenario D — Remote (iPad / iPhone) via Tailscale Serve

**Das ist der funktionierende Remote-Weg.** Der direkte Bind an die
Tailscale-IP (`LAB_BIND=tailscale`) scheitert auf macOS an der
„Local Network"-Berechtigung / Firewall-Schicht — Serve umgeht das, weil der
signierte Tailscale-Daemon die eingehende Verbindung annimmt und an localhost
weiterreicht. llama-server bleibt dabei komplett auf localhost.

```bash
# 1) Router LOKAL starten (KEIN LAB_BIND):
bash scripts/launch_lab.command

# 2) Zweites Terminal — Serve davor hängen:
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve --bg 8080
```

Serve gibt eine URL wie `https://macbook-pro-von-hans-werner.<tailnet>.ts.net`.
Diese am iPad/iPhone öffnen (nicht die `100.x`-IP).

- Status / Stop: `tailscale serve status` / `tailscale serve reset`
- Falls `serve` einen Zertifikatsfehler wirft: im Tailscale-Admin
  (login.tailscale.com → DNS) MagicDNS und HTTPS-Certificates aktivieren.
- MCP-Eintrag in der Remote-UI wie in Szenario A: `http://127.0.0.1:8787/mcp`
  + Proxy-Toggle (der Proxy löst die URL serverseitig auf).

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

| Variable / Argument      | Wirkung                                                        |
|--------------------------|---------------------------------------------------------------|
| `launch_lab.command write` | Frontend-Modell darf schreiben + löschen (sonst read-only)  |
| `MCP_READONLY=0/1`       | read-only-Gate des MCP-Servers (Argument von launch_lab gewinnt) |
| `LAB_BIND=local`         | llama-server nur auf localhost (Default)                       |
| `LAB_BIND=tailscale`     | Bind an Tailscale-IP — **auf macOS unzuverlässig, Serve bevorzugen** |
| `LAB_BIND=all`           | `0.0.0.0`, alle Interfaces inkl. LAN (breit, nur bewusst)      |
| `HARNESS_MODEL` / `HARNESS_READONLY` | Modellwahl bzw. read-only für den Harness         |

---

## Sicherheit / Hygiene

- Read-only ist überall Default; Schreibzugriff bewusst aktivieren.
- Vor schreibenden Läufen committen (Rollback). Der Harness und der
  Write-Launcher warnen bei unsauberem Git-Baum.
- Tools sind Traversal-geschützt auf das Projekt-Root begrenzt; `run_python` aus.
- Remote nur über **Serve** (tailnet-only, WireGuard-verschlüsselt), nie
  **Funnel** (öffentlich). llama-server hat keine native Auth — Schutz ist die
  Tailnet-Grenze plus ACL.
- Offener Härtungsschritt: Tailscale-ACL auf iPad/iPhone begrenzen
  (`config/tailscale-acl-example.json` als Vorlage, im Tailscale-Admin setzen).

---

## Troubleshooting

- **`ERR_CONNECTION_REFUSED` auf der Tailscale-IP:** meist läuft noch eine
  localhost-Instanz. Bind prüfen: `lsof -iTCP:8080 -sTCP:LISTEN -n -P`. Zeigt es
  `127.0.0.1` → `pkill -f llama-server`, dann sauber neu starten und im Banner
  `Bind:` prüfen. Für Remote generell **Serve** statt Direct-Bind nutzen.
- **iPad kommt nicht durch, iPhone/Mac schon:** iPad-spezifisch — die
  `.ts.net`-URL frisch eingeben (nicht die gecachte IP), Private Relay / anderes
  VPN am iPad prüfen. Chrome am iPad funktioniert.
- **MCP-Server-Check:** `curl http://127.0.0.1:8787/mcp` → Antwort
  „Not Acceptable / text/event-stream" (bzw. HTTP 406) heißt: der Server lauscht.
- **Tailnet-Verbindung prüfen:** `tailscale status` (Geräte + Account),
  `tailscale ping <gerät>` (reine Peer-Verbindung, unabhängig vom Port).
- **`command not found: tailscale`:** vollen Pfad nutzen oder den zsh-Alias
  setzen (siehe Voraussetzungen).

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
