# Session-Kontext — llama-server Lab

Wiedereinstiegspunkt: Wo stehen wir, was ist offen, wie kommt man rein.
Ergänzt `docs/RUNBOOK.md` (Bedienung) um den *Stand* und die *nächsten Schritte*.

Letzte Session: 2026-07-22 · Branch `main`. **Account-Migration geschäftlich →
privat = neues Tailnet** (`tail08de73`); alle alten Tailscale-Werte (Suffix,
100.x-IPs) ersetzt. iPad-Zugriff über Serve/HTTPS am iPad bestätigt.

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
- **Remote-Zugang (iPad/iPhone)**: funktioniert (2026-07-22 am iPad bestätigt).
  Zwei Wege — Direct-Bind (`LAB_BIND=tailscale`, URL `http://100.89.16.112:8080`)
  und Tailscale Serve (URL `https://macbook-pro-von-hans-werner.tail08de73.ts.net`).
  Aktuell aktiv: **Serve** (HTTPS, kein Neustart nötig); lief im neuen Tailnet auf
  Anhieb sauber (Serve aktivierte sich beim ersten `serve --bg 8080` selbst).
- **Tailscale-ACL**: Vorlage `config/tailscale-acl-example.json` weiterhin gültig,
  aber im **neuen** Tailnet noch NICHT angewandt — Tags existieren dort nicht,
  frisches Tailnet = Default allow-all. Für Ein-Personen-Tailnet optional.
- **Doku**: `Readme/` → `docs/` migriert, `docs/RUNBOOK.md` auf Stand.

---

## Offene Punkte (bewusst, für die nächste Session)

1. **ACL-Härtung scharf stellen.** In der (alten) Policy-Vorlage steckt noch die
   Übergangsregel `{ "action":"accept", "src":["autogroup:owner"], "dst":["*:*"] }`
   (verhindert Aussperren beim Taggen). Solange sie drin ist, greift die
   „nur getaggte Clients auf 8080"-Isolation **nicht scharf**.
   - **Blocker/Entscheidung:** Tailscale-SSH war aktiv. Wird SSH zwischen den
     eigenen Geräten gebraucht? Wenn ja → vor dem Entfernen der owner-Regel eine
     eigene SSH-Regel ergänzen. Wenn nein → owner-Regel ersatzlos entfernen,
     dann per `Preview rules` gegenprüfen: 8080 = accept, 22 = deny.
   - **Update 2026-07-22:** Durch den Account-Wechsel auf privat ist das ein
     neues, leeres Tailnet (allow-all, keine Tags/Policy gesetzt). Härtung startet
     damit bei Null — erst Geräte taggen (`tag:llm-server` / `tag:llm-client`),
     dann Vorlage einspielen. Priorität niedrig (Ein-Personen-Tailnet, privat,
     WireGuard-verschlüsselt, von außen nicht erreichbar).

2. **Mac Mini (Büro) einbinden.** Weiterhin geplant.
   - Als **Server**: Repo klonen/pullen → `cd mcp-server && bash setup.sh` →
     `LAB_BIND=serve bash scripts/launch_lab.command` → im Admin `tag:llm-server`
     taggen (sobald ACL/Tags im neuen Tailnet gesetzt sind). Ergibt eigene
     `.ts.net`-URL.
   - Als **Client**: Tailscale mit dem **privaten** Account anmelden, Server-URL
     öffnen. (Achtung: nicht versehentlich den alten geschäftlichen Account.)

3. **Serve + HTTPS am iPad final glätten** — im neuen Tailnet erledigt/bestätigt.
   Reststolpersteine bleiben iPad-seitig: iCloud Private Relay aus, URL frisch
   tippen (nicht aus Verlauf), notfalls Chrome statt Safari.

---

## Schnellstart nächste Session

Lokal arbeiten (Standard):
```
bash scripts/launch_lab.command            # read-only, Router+MCP lokal
bash scripts/launch_lab.command write      # schreibfähig
```

Remote (iPad) — Serve/HTTPS (aktuell erprobter Weg, kein Neustart nötig):
```
bash scripts/launch_lab.command                                        # nur falls Router noch nicht läuft
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve --bg 8080
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve status      # zeigt die .ts.net-URL
# iPad: https://macbook-pro-von-hans-werner.tail08de73.ts.net
```

Remote (iPad) — Direct-Bind/IP (Fallback, braucht Server-Neustart):
```
pkill -f llama-server
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve reset
LAB_BIND=tailscale bash scripts/launch_lab.command
# iPad: http://100.89.16.112:8080
```

Modellwahl: bei „Server unavailable" / langsamem Laden im UI-Dropdown das
leichteste Modell nehmen — `JetBrains/Mellum2-…-Q4_K_M:Q4_K_M`. Große Modelle
(`Qwen3.6-27B`, `gemma-4-26B`) können beim On-demand-Laden hängen/OOM auslösen.

---

## Wichtige Fakten / Referenzen

- Repo: Branch `main` (von `master` umbenannt), mit `origin`-Remote.
- Tailnet: `tail08de73.ts.net` (privat, Owner `hf9hsgw9th@`). **Vorher**
  geschäftlich: `tail7f9148.ts.net` / `plan2-hw@dobben-united.de` — durch die
  Account-Migration komplett neues Tailnet: Suffix, alle 100.x-IPs, Tags und
  Policy sind neu bzw. leer.
- Geräte (neu): `macbook-pro-von-hans-werner` (100.89.16.112), `ipad165`
  (100.112.7.40), `iphone181` (100.106.12.65).
- Tailscale-CLI-Pfad (macOS): `/Applications/Tailscale.app/Contents/MacOS/Tailscale`
  (kein `tailscale` im PATH; ggf. Alias in `~/.zshrc`).
- MagicDNS + HTTPS-Certificates: im neuen Tailnet aktiv (Serve lieferte gültiges
  HTTPS-Cert auf Anhieb). Falls je „Serve not enabled" → einmal bestätigen, danach
  läuft's.
- Serve abschalten: `tailscale serve reset` (bzw. `tailscale serve --https=443 off`).
- MCP-Server-Lebenscheck: `curl http://127.0.0.1:8787/mcp` → „Not Acceptable /
  text/event-stream" bzw. 406 = läuft.
- Router-Lebenscheck: `curl -sI http://127.0.0.1:8080/health` → 200.

---

## Betriebsnotizen / Stolpersteine (aus dieser Session)

- **Account-Migration = neues Tailnet (2026-07-22):** Wechsel geschäftlich→privat
  erzeugt ein frisches Tailnet — Suffix, alle Geräte-IPs, Tags und Policy sind
  neu/leer. Vor Remote-Zugriff immer `tailscale status` (+ `serve status`) prüfen,
  nicht auf notierte IPs verlassen. Serve aktiviert sich beim ersten `serve --bg`
  im neuen Tailnet selbst („Serve is not enabled" → „Success").
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
