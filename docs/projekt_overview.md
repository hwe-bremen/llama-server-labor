# Projekt-Übersicht — llama-server Lab

Die *Landkarte* des Labs: was es ist, aus welchen Teilen es besteht und warum
sie so gebaut sind. Für Bedienung siehe `RUNBOOK.md`, für den aktuellen Stand
und offene Punkte siehe `session_kontext.md`.

---

## Zweck

Ein lokales Experimentierfeld für llama.cpp-Modelle: schnelles Lernen,
Iteration und Ideenvalidierung an lokalen Modellen — mit Werkzeugen, die den
Modellen kontrollierten Datei- und Git-Zugriff geben (via MCP), lokal wie
remote nutzbar. Reines Lab, klar getrennt von AskValentinAI (siehe unten).

---

## Komponenten

| Ordner / Datei              | Rolle                                                        |
|-----------------------------|-------------------------------------------------------------|
| `mcp-server/lab_mcp_server.py` | Der MCP-Server: bietet Datei- und Git-Tools im Scope an   |
| `core/mcp_agent.py`         | Wiederverwendbare Agenten-Basis (MCP-Client + Tool-Loop)    |
| `agents/llama_harness.py`   | Dünner Konsument von `core`: lokales Modell als MCP-Agent   |
| `agents/` (weitere)         | dev_agent, dev_agent_diff, excel_agent (ältere Experimente) |
| `scripts/launch_lab.command`| Orchestrator: startet MCP-Server + Router zusammen          |
| `scripts/launch_router.command` | llama-server im Router-Modus (Modelle on-demand)        |
| `config/models.ini`         | Router-Preset: Modelle + Sampling-Parameter                 |
| `config/tailscale-acl-example.json` | Vorlage für die Tag-basierte Tailscale-ACL          |
| `sandbox/`                  | Wegwerf-Experimente (von Agenten beschreibbar)              |
| `docs/`                     | RUNBOOK, session_kontext, diese Übersicht                   |

---

## Wie es zusammenspielt

Der **MCP-Server** ist das Herzstück: eine einzige Tool-Quelle (Datei lesen/
schreiben/suchen, Git), die von drei verschiedenen Clients genutzt wird. Die
Clients unterscheiden sich nur im Transport:

```
  Claude Desktop ──stdio──┐
  llama-Harness  ──stdio──┤
                          ├──> MCP-Server ──> Dateien + Git (im Scope-Ordner)
  Web-UI (Browser) ───────┘        (8787, streamable-http / stdio)
      │
      └── Browser lädt von: llama-server Router (8080)
              │  --ui-mcp-proxy leitet MCP-Anfragen serverseitig weiter
              └── Router lädt Modelle on-demand aus config/models.ini

  Remote-Client (iPad/iPhone)
      └── Tailscale (Serve = HTTPS  ODER  Direct-Bind = 100.x-IP) ──> Router (8080)
```

Kernidee: **Der MCP-Server bleibt immer auf localhost.** Kein Client spricht ihn
übers Netz direkt an — die Web-UI erreicht ihn über den `--ui-mcp-proxy` des
Routers (serverseitige Auflösung), und Remote-Clients erreichen nur den Router,
nie den Tool-Server. Kleinste Angriffsfläche.

---

## Design-Entscheidungen (das *Warum*)

- **Ein MCP-Server, zwei Transporte.** stdio für lokale Subprozess-Clients
  (Claude Desktop, Harness), streamable-http für den Browser (die Web-UI kann
  keinen stdio-Subprozess starten). Gleiche Tools, gleicher Scope-Guard.
- **Scope-Guard mit Traversal-Schutz.** Alle Pfade werden gegen einen festen
  Scope-Ordner aufgelöst; `..`, absolute Pfade und Symlink-Ausbrüche werden
  blockiert. `run_python` ist standardmäßig aus. Read-only ist der Default;
  Schreiben wird bewusst aktiviert.
- **`core/mcp_agent.py` als Basis, Agenten als dünne Konsumenten.** Session-
  Management, Tool-Konvertierung, Modell-Discovery und Tool-Loop liegen einmal
  zentral; der Harness ist nur noch Konfiguration + Aufruf. Neue Agenten erben
  dieselbe Basis.
- **Router-Modus statt festem Modell.** llama-server lädt Modelle on-demand aus
  `config/models.ini`; die Web-UI wählt per Dropdown. Ein Endpunkt, alle Modelle.
- **Remote via Tailscale Serve bevorzugt.** Serve hält llama-server auf
  localhost und terminiert HTTPS im signierten Tailscale-Daemon — umgeht die
  macOS-Berechtigungs-/Firewall-Fragen des Direct-Binds und bringt einen
  stabilen `.ts.net`-Namen. Der Direct-Bind (an die Tailscale-IP) bleibt als
  einfachere Alternative.
- **Tag-basierte ACL.** Rollen (`tag:llm-server`, `tag:llm-client`) statt
  Gerätenamen — neue Geräte (Mac Mini) brauchen nur den Tag, die Policy bleibt
  unverändert.

---

## Sicherheits-Prinzipien (eingebaut, nicht nachgerüstet)

- Traversal-geschützter Scope, Whitelist der Tools, kein freier Shell-Zugriff.
- Read-only als Default; Git-Commit als Rollback-Punkt vor schreibenden Läufen.
- Netz-Exposition nur im privaten Tailnet, mit ACL; llama-server hat keine
  native Auth, daher ist die ACL/Serve-Schicht davor Pflicht, nicht Kür.
- Keine echten personenbezogenen Daten in Testläufen — synthetisch bleiben.

---

## Die harte Grenze

Reines Lab. Kein AskValentinAI-Code, keine produktiven Repos, keine echten
Mandanten-/Kunden-/Geschäftsdaten. Sobald ein Vorhaben das berührt, gehört es
ins jeweilige AskValentinAI-Projekt (mit dessen eigenem Prozess) — nicht hierher.
