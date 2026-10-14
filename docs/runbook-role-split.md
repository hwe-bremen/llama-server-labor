# Runbook — role-split (Rollen-Proxy, Review/Umsetzung)

Experiment: Tragen lokale Modelle eine Trennung zwischen Review-Instanz (Web-UI)
und Umsetzungs-Instanz (OpenCode) in einer echten Projektstruktur? Übergabe über
Markdown in `docs/projekt_management/`. Hintergrund und Testplan: `role-split/README.md`.
Alle Befehle aus dem Projekt-Root (`~/PycharmProjects/llama-server`).

## Kette

```
Browser 127.0.0.1:8092 ─► role-split (Rollen-Prompt) ─► 8091 local-memory (Gedächtnis) ─► 8080 Router ─► Modell
                                                                     MCP-Tools: 8787 (mit MCP_WRITE_ROOTS)
```

| Port | Was | Gestartet von |
|---|---|---|
| 8092 | Rollen-Proxy `role-split/role_proxy.py` | `launch_lab_roles.command` (oder einzeln `bash role-split/role.command`) |
| 8091 | Gedächtnis-Proxy | Launcher mit `LAB_MEMORY=1` |
| 8080 | Router | Launcher |
| 8787 | Lab-MCP mit Schreibgrenze | Launcher mit `write` und `MCP_WRITE_ROOTS=…` |

## Start (Standard) — ein Fenster

```bash
bash scripts/launch_lab_roles.command      # Doppelklick geht nach einmalig chmod +x
# Browser: http://127.0.0.1:8092           (127.0.0.1, nicht localhost)
```

Der Starter setzt `MCP_WRITE_ROOTS=docs/projekt_management,docs/research` und `LAB_MEMORY=1`,
startet den Rollen-Proxy im Hintergrund und das Lab (`launch_lab.command write`) im Vordergrund.
Ctrl+C stoppt alles, auch den Rollen-Proxy.

**Fail-loud:** Läuft auf 8787 schon ein MCP-Server ohne genau diese Schreibgrenze
(oder read-only), bricht der Starter mit `ABBRUCH: …` ab und nennt die PID. Dann den alten
Server beenden und neu starten. Ein falsch gestarteter Server wird also nicht mehr
stillschweigend weiterbenutzt (Befund 14.10.: genau das war passiert).

Im Banner steht danach: `WRITE_ROOTS : docs/projekt_management,docs/research`.

### Start von Hand (zwei Terminals, gleiches Ergebnis ohne Abbruch-Prüfung)

```bash
# Terminal 1
MCP_WRITE_ROOTS=docs/projekt_management,docs/research LAB_MEMORY=1 bash scripts/launch_lab.command write
# Terminal 2, nach "[lm] Proxy auf http://127.0.0.1:8091"
bash role-split/role.command
```

Achtung: `launch_lab.command write` **ohne** die Variable, `launch_lab_write.command` per Doppelklick
oder ein aus dem Verlauf geholter Befehl starten den MCP-Server **ohne** Schreibgrenze.

## Alle Befehle

```bash
bash scripts/launch_lab_roles.command   # alles in einem Fenster (empfohlen)
bash role-split/role.command            # nur Rollen-Proxy (Standard: serve)
bash role-split/role.command test       # 21 Tests (Trigger, @aus, Streaming, gzip)
bash role-split/role.command check      # Rollen anzeigen + Trockenlauf, ohne Server

ROLE_UPSTREAM=http://127.0.0.1:8080 bash role-split/role.command   # ohne Gedächtnis, direkt auf den Router
ROLE_PORT=8093 bash role-split/role.command                        # anderer Port

tail -5 role-split/results/role_log.jsonl   # welche Rolle hatte welche Anfrage? ("rolle": null = keine)

# Schreibgrenze des laufenden MCP-Servers prüfen
PID=$(lsof -ti :8787 -sTCP:LISTEN); ps eww -p $PID | tr ' ' '\n' | grep -E 'MCP_(READONLY|WRITE_ROOTS)'
#   erwartet: MCP_READONLY=0 und MCP_WRITE_ROOTS=docs/projekt_management,docs/research
#   fehlt MCP_WRITE_ROOTS: kill $PID, Lab mit launch_lab_roles.command neu starten
```

## Im Chat

| Eingabe am Anfang einer Nachricht | Wirkung |
|---|---|
| `@review …` | Review-Instanz: Konzept, Spec, ADR, Verdikt; begründeter Widerspruch; schreibt nur nach `docs/projekt_management/` |
| `@research …` | Recherche-Instanz: belegt / Wissensstand / Vermutung, `web_search` mit URL; schreibt nur nach `docs/research/` |
| `@aus …` | Rolle ab; der Proxy setzt einen Hinweis, dass frühere Rollenangaben nicht mehr gelten |
| ohne Trigger | die zuletzt gesetzte Rolle im Verlauf gilt weiter |

- Rollen sind Dateien in `role-split/roles/<name>.md`, Trigger `@<name>`. Neu anlegen oder
  ändern wirkt bei der nächsten Nachricht, ohne Neustart.
- Neuer Durchlauf = **neuer Chat** (bei ~11 Token/s wird ein langer Verlauf schnell langsam).
- Der Trigger wird entfernt, bevor Modell und Gedächtnis-Retrieval die Nachricht sehen.

## Einmalig

- `chmod +x scripts/launch_lab_roles.command` (für Doppelklick; per MCP geschriebene Dateien sind 100644).
- Unter 8092 den MCP-Eintrag neu anlegen (Browser-Speicher pro Adresse): `http://127.0.0.1:8787/mcp`,
  dann per Stift-Icon „use llama-server proxy" AN. Den Kirby-Eintrag (8788) hier nicht anlegen.
- OpenCode: Agent liegt in `.opencode/agents/umsetzung.md`; im TUI mit Tab wählen.
  OpenCode nutzt seine eigenen Datei-Tools, nicht den eingeschränkten MCP.

## Ablauf eines Durchlaufs

1. Web-UI `@review`: Vorhaben besprechen → „Speichere die Spec als `spec_<JJJJMMTT>_<titel>.md`".
2. OpenCode, Agent „umsetzung": „Setz `docs/projekt_management/spec_<…>.md` um."
   → Code + `handover_<…>.md` (Vorlage `_vorlage_handover.md`).
3. Web-UI `@review`: „Prüf `handover_<…>.md` gegen Spec und Code, speichere das Verdikt."
   → `verdict_<…>.md`, Ergebnis PASS / NACHBESSERN / FAIL.
4. NACHBESSERN → zurück zu 2. PASS → Hawe committet (die Review-Instanz kann es nicht:
   `git_commit` ist bei gesetzter Schreibgrenze abgeschaltet).

## Prüfungen (Probe-Satz, ~2 Minuten)

| Nachricht | Erwartet |
|---|---|
| `@review hallo, welche Rolle hast du?` | Review-Instanz, Log `"rolle": "review"` |
| `Liste den Ordner docs/projekt_management auf.` | Tool-Aufruf, zwei Vorlagen |
| `Schreib eine Testdatei nach sandbox/x.md mit dem Inhalt "test".` | Versuch ohne Einwand, **scheitert** an MCP_WRITE_ROOTS, ehrliche Meldung. `ls sandbox/x.md` → nicht vorhanden |
| `@aus Welche Rolle hast du jetzt?` | keine Rolle, Log `"rolle": null` |

## Troubleshooting

- **`ABBRUCH: Auf Port 8787 läuft bereits ein MCP-Server …`:** gewollt (fail-loud). Alten Server
  beenden (Ctrl+C im alten Launcher-Fenster oder `kill <PID>` aus der Meldung), Starter neu aufrufen.
- **`Error: gzip is not supported by this browser` auf 8092:** alter Proxy-Stand
  (vor `1d637c0`). Stand prüfen, Rollen-Proxy neu starten.
- **Modell schreibt nach `sandbox/` o.ä.:** Schreibgrenze nicht aktiv. Prüfbefehl oben.
  Ursache am 14.10.: Lab war ohne `MCP_WRITE_ROOTS` neu gestartet worden. Mit
  `launch_lab_roles.command` starten.
- **Nach `@aus` nennt sich das Modell weiter Review-Instanz:** alter Proxy-Stand
  (vor `49cf0c3`) oder Rollen-Proxy nicht neu gestartet. Log prüfen: `"rolle": null`?
- **Rolle wirkt nicht / Antwort ohne Rollenverhalten:** Seite über 8091 oder 8080
  statt 8092 geöffnet. Log `role-split/results/role_log.jsonl` bekommt dann keinen Eintrag.
- **Gedächtnis fehlt in der Antwort:** local-memory muss mit `system_mode=merge` laufen
  (steht im `[lm]`-Banner); sonst ersetzt es den Rollen-Prompt.
- **`[role-split] "GET /models/sse …" 200`** im Terminal: normal, das ist der
  Statusstrom der Web-UI (bleibt offen).
- **502 „Upstream nicht erreichbar"**: 8091 läuft (noch) nicht — der Gedächtnis-Proxy startet erst,
  wenn der Router antwortet (bis 3 Minuten). Warten auf `[lm] Proxy auf …8091`, oder ohne
  Gedächtnis: `ROLE_UPSTREAM=http://127.0.0.1:8080`.
