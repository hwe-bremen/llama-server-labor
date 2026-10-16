# Runbook — role-split (Rollen-Proxy, Review/Umsetzung)

Experiment: Tragen lokale Modelle eine Trennung zwischen Review-Instanz (Web-UI)
und Umsetzungs-Instanz (OpenCode) in einer echten Projektstruktur? Übergabe über
Markdown in `docs/projekt_management/`. Hintergrund und Testplan: `role-split/README.md`.
Alle Befehle aus dem Projekt-Root (`~/PycharmProjects/llama-server`).

## Kette

```
Mac:          Browser 127.0.0.1:8092 ─┐
iPad / Büro:  https://<mac>.ts.net ───┤ (Tailscale Serve, nur mit LAB_BIND=serve)
                                      ▼
              8092 role-split (Rollen-Prompt) ─► 8091 local-memory (Gedächtnis) ─► 8080 Router ─► Modell
                                                         MCP-Tools: 8787 (mit MCP_WRITE_ROOTS)
```

| Port | Was | Gestartet von |
|---|---|---|
| 8092 | Rollen-Proxy `role-split/role_proxy.py` | `launch_lab_roles.command` (oder einzeln `bash role-split/role.command`) |
| 8091 | Gedächtnis-Proxy | Launcher mit `LAB_MEMORY=1` |
| 8080 | Router | Launcher |
| 8787 | Lab-MCP mit Schreibgrenze | Launcher mit `write` und `MCP_WRITE_ROOTS=…` |
| 443 (.ts.net) | Tailscale Serve → 8092 | `LAB_BIND=serve` bzw. `launch_lab_roles_remote.command` |

## Start — genau zwei Befehle (ab 16.10.)

Beide: MCP mit Schreibrechten (Grenze `docs/projekt_management`, `docs/research`), Rollen-Proxy 8092,
Tailscale Serve → 8092 (Mac, iPad, Mac mini), Mac bleibt wach. Ctrl+C stoppt alles.

| Befehl (Projekt-Root, auch per Doppelklick) | Wofür | Unterschied |
|---|---|---|
| `bash start_rollen.command` | normale Arbeit mit `@review` / `@research` | Gedächtnis 8091 an, `git_log` an |
| `bash start_eval.command` | Modellvergleich (`role-split/eval/`) | direkt auf 8080, 1 Modell, `git_log` aus |

Wechsel zwischen beiden: erst Ctrl+C, dann den anderen starten. Läuft noch ein MCP-Server aus dem
anderen Modus, bricht der Starter mit `ABBRUCH` ab (fail-loud) — dann den alten beenden.
Alle anderen `scripts/launch_*.command` sind Bausteine dieser beiden; direkt nur noch für Sonderfälle.

## Start (Standard) — ein Fenster

```bash
bash scripts/launch_lab_roles.command                  # nur am Mac
LAB_BIND=serve bash scripts/launch_lab_roles.command   # Mac + iPad/Büro (Serve wird beim Beenden zurückgesetzt)
bash scripts/launch_lab_roles_remote.command           # Büro-Tag: Serve bleibt, MacBook schläft nicht
# Browser Mac:  http://127.0.0.1:8092   (127.0.0.1, nicht localhost)
# iPad/Büro:    die .ts.net-URL aus dem Lab-Banner
```

Der Starter setzt `MCP_WRITE_ROOTS=docs/projekt_management,docs/research` und `LAB_MEMORY=1`,
startet den Rollen-Proxy im Hintergrund und das Lab (`launch_lab.command write`) im Vordergrund.
Mit `LAB_BIND=serve` zeigt Serve auf **8092** (statt 8091 wie beim normalen Büro-Launcher).
Ctrl+C stoppt alles, auch den Rollen-Proxy.

**Fail-loud:** Läuft auf 8787 schon ein MCP-Server ohne genau diese Schreibgrenze
(oder read-only), bricht der Starter mit `ABBRUCH: …` ab und nennt die PID. Dann den alten
Server beenden und neu starten. Ein falsch gestarteter Server wird also nicht mehr
stillschweigend weiterbenutzt (Befund 14.10.: genau das war passiert).

Im Banner steht danach: `WRITE_ROOTS : docs/projekt_management,docs/research`, im
serve-Modus außerdem `Starte Tailscale Serve fuer Port 8092` und
`(fuehrt ueber Port 8092 (LAB_SERVE_PORT) …)`.

### Start von Hand (zwei Terminals, gleiches Ergebnis ohne Abbruch-Prüfung)

```bash
# Terminal 1 (remote zusätzlich: LAB_BIND=serve LAB_SERVE_PORT=8092 davor)
MCP_WRITE_ROOTS=docs/projekt_management,docs/research LAB_MEMORY=1 bash scripts/launch_lab.command write
# Terminal 2, nach "[lm] Proxy auf http://127.0.0.1:8091"
bash role-split/role.command
```

Achtung: `launch_lab.command write` **ohne** die Variable, `launch_lab_write.command` per Doppelklick
oder ein aus dem Verlauf geholter Befehl starten den MCP-Server **ohne** Schreibgrenze.

## Remote (iPad, Mac mini im Büro)

- Gleiche Voraussetzungen wie Runbook Szenario D (Tailscale, MagicDNS/HTTPS, MacBook wach).
- Der Rollen-Proxy bleibt auf `127.0.0.1`; nach außen öffnet nur Serve, im Tailnet. Nie
  `ROLE_HOST=0.0.0.0` setzen.
- **MCP-Eintrag auf dem iPad bleibt gültig:** Die Adresse im Browser ist weiter die `.ts.net`-URL,
  nur das Ziel dahinter ist jetzt 8092. Falls noch keiner da ist: `http://127.0.0.1:8787/mcp` +
  Proxy-Schalter, wie überall.
- Schreibgrenze gilt auch für Chats vom iPad — die Review-Instanz kann remote nur nach
  `docs/projekt_management/` und `docs/research/` schreiben.
- **OpenCode am Mini** mit `baseURL` `https://….ts.net/v1` läuft dann ebenfalls über 8092.
  Ohne Trigger reicht der Rollen-Proxy alles unverändert durch (auch Tool-Aufrufe, laut Tests);
  am Mini selbst noch nicht geprüft. Soll OpenCode sicher am Rollen-Proxy vorbei, den
  normalen Büro-Launcher (`launch_lab_remote.command`, Serve → 8091) nehmen.
- Gegenprobe vom iPad: Seite lädt, `@review hallo, welche Rolle hast du?` → Review-Instanz,
  und am Mac `tail -1 role-split/results/role_log.jsonl` zeigt `"rolle": "review"`.

## Alle Befehle

```bash
bash scripts/launch_lab_roles.command          # alles in einem Fenster, nur Mac (empfohlen)
LAB_BIND=serve bash scripts/launch_lab_roles.command   # dito + Tailscale Serve -> 8092
bash scripts/launch_lab_roles_remote.command   # Büro-Tag mit Rollen (Serve bleibt, caffeinate)
bash role-split/role.command            # nur Rollen-Proxy (Standard: serve)
bash role-split/role.command test       # 21 Tests (Trigger, @aus, Streaming, gzip)
bash role-split/role.command check      # Rollen anzeigen + Trockenlauf, ohne Server

python3 role-split/eval/halluzination/probe.py --alle --kein-denken   # Halluzinations-Vortest aller Modelle (Lab läuft)
python3 role-split/eval/halluzination/test_probe.py                   # Selbsttest der Probe, ohne Modell

ROLE_UPSTREAM=http://127.0.0.1:8080 bash role-split/role.command   # ohne Gedächtnis, direkt auf den Router
ROLE_PORT=8093 bash role-split/role.command                        # anderer Port

tail -5 role-split/results/role_log.jsonl   # welche Rolle hatte welche Anfrage? ("rolle": null = keine)

# Schreibgrenze des laufenden MCP-Servers prüfen
PID=$(lsof -ti :8787 -sTCP:LISTEN); ps eww -p $PID | tr ' ' '\n' | grep -E 'MCP_(READONLY|WRITE_ROOTS)'
#   erwartet: MCP_READONLY=0 und MCP_WRITE_ROOTS=docs/projekt_management,docs/research
#   fehlt MCP_WRITE_ROOTS: kill $PID, Lab mit launch_lab_roles.command neu starten

# Wohin zeigt Serve gerade?
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve status    # erwartet: proxy http://127.0.0.1:8092
```

## Halluzinations-Probe (Vortest vor jedem neuen Modell)

Misst, wie oft ein Modell Lücken füllt statt „kenne ich nicht" zu sagen: 11 feste Fragen
(erfundene Begriffe, Fragen zu einem Text, die der Text nicht beantwortet, feste Fakten) direkt
an den Router 8080, ohne Tools, je ohne und mit Rolle `research`.

```bash
python3 role-split/eval/halluzination/probe.py --modelle "<id>"         # ein Modell, Thinking laut Preset
python3 role-split/eval/halluzination/probe.py --alle --kein-denken     # alle, schneller Vortest
```

- Ergebnis: `role-split/eval/halluzination/ergebnisse/<datum>_uebersicht.md` (Tabelle + alle Antworten).
- `✓?`/`✗?` ist nur Vorsortierung über Stichworte; das Urteil beim Lesen der Antworten fällen.
- Wichtigste Spalten: „Erfundenes abgelehnt" und „Texttreue". `ohne` vs. `research` zeigt, ob die
  Rollen-Regeln wirken.
- Grenze: misst eine Neigung, schützt nicht im Alltag. Dort: Beleg (Datei/URL) verlangen, unbelegte
  Details als ungeprüft behandeln, bei Wichtigem eine zweite Stimme. Details: `role-split/eval/halluzination/README.md`.

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

- `chmod +x scripts/launch_lab_roles.command scripts/launch_lab_roles_remote.command`
  (für Doppelklick; per MCP geschriebene Dateien sind 100644), danach eigener Commit.
- Unter 8092 den MCP-Eintrag neu anlegen (Browser-Speicher pro Adresse): `http://127.0.0.1:8787/mcp`,
  dann per Stift-Icon „use llama-server proxy" AN. Den Kirby-Eintrag (8788) hier nicht anlegen.
- **Ab llama.cpp 0.6.0** (Update 15.10.): MCP-Einträge liegen nicht mehr in den Settings, sondern
  hinter dem **+ unter dem Chat-Eingabefeld → „MCP servers"**. Alte Einträge waren nach dem Update
  weg (Vermutung: neues Speicherformat) — pro Adresse (8092, 8091, 8080, iPad) neu anlegen.
  Settings → Tools zeigt nur die eingebauten Tools („Browser": get_datetime, get_info).
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
- **iPad: `@review` wirkt nicht, Log bekommt keinen Eintrag:** Serve zeigt nicht auf 8092
  (`tailscale serve status`). Häufig: mit `launch_lab_remote.command` statt
  `launch_lab_roles_remote.command` gestartet, oder ein altes Serve-Mapping ist stehen geblieben
  (`LAB_KEEP_SERVE=1`). Lösung: `tailscale serve reset`, Rollen-Starter mit `LAB_BIND=serve` neu.
- **iPad: Seite lädt nicht / 502:** Serve steht, aber 8092 oder 8091 laufen (noch) nicht — Rollen-Proxy
  läuft nur, solange sein Starter-Fenster offen ist; der Gedächtnis-Proxy braucht bis zu 3 Minuten.
- **`Error: gzip is not supported by this browser` auf 8092:** alter Proxy-Stand
  (vor `1d637c0`). Stand prüfen, Rollen-Proxy neu starten.
- **Modell schreibt nach `sandbox/` o.ä.:** Schreibgrenze nicht aktiv. Prüfbefehl oben.
  Ursache am 14.10.: Lab war ohne `MCP_WRITE_ROOTS` neu gestartet worden. Mit
  `launch_lab_roles.command` starten.
- **Nach `@aus` nennt sich das Modell weiter Review-Instanz:** alter Proxy-Stand
  (vor `49cf0c3`) oder Rollen-Proxy nicht neu gestartet. Log prüfen: `"rolle": null`?
- **Rolle wirkt nicht / Antwort ohne Rollenverhalten (Mac):** Seite über 8091 oder 8080
  statt 8092 geöffnet. Log `role-split/results/role_log.jsonl` bekommt dann keinen Eintrag.
- **Gedächtnis fehlt in der Antwort:** local-memory muss mit `system_mode=merge` laufen
  (steht im `[lm]`-Banner); sonst ersetzt es den Rollen-Prompt.
- **`[role-split] "GET /models/sse …" 200`** im Terminal: normal, das ist der
  Statusstrom der Web-UI (bleibt offen).
- **502 „Upstream nicht erreichbar"**: 8091 läuft (noch) nicht — der Gedächtnis-Proxy startet erst,
  wenn der Router antwortet (bis 3 Minuten). Warten auf `[lm] Proxy auf …8091`, oder ohne
  Gedächtnis: `ROLE_UPSTREAM=http://127.0.0.1:8080`.

### llama.cpp 0.6.0 (seit 15.10.)

- **Keine MCP-Tools in der Web-UI:** Eintrag neu anlegen über das + unter dem Eingabefeld
  (siehe „Einmalig"). Router, `--webui-mcp-proxy` und 8787 waren am 15.10. intakt.
- **`--tools` / `--agent` (neu in 0.6.0) nicht aktivieren:** eingebaute Server-Tools wie
  `exec_shell_command`, `write_file`, `edit_file` laufen am Scope-Guard und an `MCP_WRITE_ROOTS`
  vorbei. Gehören nicht in `config/models.ini`.
- **`--mcp-servers-config`** kann laut README nur stdio-Server (llama-server startet sie als
  Kindprozess) — passt nicht zum HTTP-MCP auf 8787. Vorerst nicht genutzt.
- **Rückweg auf Build 9850:** liegt noch unter `/opt/homebrew/Cellar/llama.cpp/9850`, aber ggml
  wurde mit aktualisiert (0.15.3 → 0.27.0). Vor einem Rückweg prüfen:
  `otool -L /opt/homebrew/Cellar/llama.cpp/9850/bin/llama-server | grep ggml` — zeigt es auf
  `…/opt/ggml/…`, läuft der alte Build gegen das neue ggml (Rückweg unsicher).
- **`search_files` meldet „Keine Treffer" bei einer Einzeldatei:** bis 16.10. ein Fehler (`rglob`
  auf einer Datei findet nichts). Behoben; die Meldung nennt jetzt die Zahl durchsuchter Dateien.
