# Lab – Kurzanleitung

Zwei Startbefehle, sonst nichts. Beide starten alles in **einem** Fenster: Router + Chat-UI,
Gedächtnis-Proxy (8091), Rollen-Proxy (8092), MCP-Server (8787) **mit Schreibrechten**
(nur in `docs/projekt_management/` und `docs/research/`), Tailscale Serve fürs
iPad/iPhone/Mini und `caffeinate` gegen Ruhezustand.
Ausführlich: `RUNBOOK.md` und `runbook-role-split.md`.

## 1. Starten (Fenster 1 – bleibt offen)

```bash
cd ~/PycharmProjects/llama-server
git status --short                       # sollte leer sein, sonst erst committen
pkill -f lab_mcp_server; pkill -f lm.proxy; pkill -f role_proxy; sleep 1   # Reste vom letzten Lauf
```

| Ich will … | Befehl (auch per Doppelklick) |
|---|---|
| **normal arbeiten** – chatten, `@review`, `@research`, mit Gedächtnis | `bash start_rollen.command` |
| **Modelle vergleichen** (Review-Eval) | `bash start_eval.command` |

Fertig, wenn nach 1–3 Min. `Starte Gedaechtnis-Proxy … 8091` und die `.ts.net`-URL erscheinen.
**Stoppen:** Ctrl+C in Fenster 1. **Wechseln:** erst Ctrl+C, dann den anderen Befehl.
Steht `ABBRUCH: … MCP-Server …` da: alten Server beenden (`kill <PID>` aus der Meldung), neu starten.

## 2. Öffnen

| Wo | Adresse | Was |
|---|---|---|
| iPad / iPhone / Mini | `https://macbook-pro-von-hans-werner.tail08de73.ts.net` | wie 8092 |
| am Mac | `http://127.0.0.1:8092` | Rollen + Gedächtnis (Standard) |
| am Mac | `http://127.0.0.1:8091` | nur Gedächtnis |
| am Mac | `http://127.0.0.1:8080` | Modell pur (Kontrollgruppe) |

Im Eval-Lauf geht 8092 direkt auf 8080 – ohne Gedächtnis, damit Modelle fair verglichen werden.

## 2b. Datei-Tools (MCP) in der Web-UI

Seit llama.cpp 0.6.0: **+ unter dem Chat-Eingabefeld → „MCP servers"** → Server hinzufügen,
URL **`http://127.0.0.1:8787/mcp`**, „use llama-server proxy" **AN**.
Gleiche URL am Mac, im Büro, am iPad. Nicht `…:8080` (das ist das Modell → `404 File Not Found`).
Der Eintrag gilt nur für **diese Adresse in diesem Browser** – immer dasselbe Lesezeichen nutzen.
Settings → Tools zeigt nur eingebaute Tools („Browser"); die für Eval-Läufe ausschalten.

## 3. Rollen im Chat (Web-UI)

| Am Anfang der Nachricht | Wirkung |
|---|---|
| `@review …` | prüft, widerspricht begründet, schreibt Specs/Verdikte nach `docs/projekt_management/` |
| `@research …` | recherchiert, markiert belegt / Wissensstand / Vermutung |
| `@aus …` | Rolle ab |
| ohne Trigger | zuletzt gesetzte Rolle gilt weiter |

Neuer Vorgang = **neuer Chat**. Die Rollen schreiben **nie** Code; das macht OpenCode (Abschnitt 6).

## 4. Prüfen (Fenster 2, ⌘N)

```bash
curl -s http://127.0.0.1:8091/lm/status | head -c 120; echo        # "k": 4 → Gedächtnis aktiv
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve status    # proxy …:8092 → iPad/Mini gehen
tail -1 role-split/results/role_log.jsonl                            # welche Rolle hatte die letzte Anfrage?
```
Gedächtnis leer → von Hand: `cd ~/PycharmProjects/local-memory && bash lm.command proxy`.
`.ts.net` tot → Lab lief nicht mit einem der zwei Startbefehle oder der Mac schläft.

## 5. Gedächtnis füttern (morgens)

Der Nachtlauf (03:30) bereitet Vorschläge vor. Dann:
```bash
cd ~/PycharmProjects/local-memory
bash lm.command pending                  # ansehen
bash lm.command accept                   # übernehmen  (oder: edit / reject)
```
Von Hand statt Nachtlauf: `bash lm.command memorize`, dann wie oben.
Etwa monatlich aufräumen: `bash lm.command review`, dann `pending`.

## 6. Code ändern lassen (OpenCode)

`opencode` im Projektordner, mit **Tab** den Agenten „umsetzung" wählen:
„Setz `docs/projekt_management/spec_<…>.md` um." → Code + Handover → in der Web-UI `@review` prüfen lassen.
OpenCode darf im ganzen Projekt Dateien ändern; Shell-Befehle fragt es vorher
(außer Syntax-Checks, Tests, `git status/diff/log`). **Vorher committen.** Committen nach dem Review: du.

## 7. Modelle testen (selten)

```bash
python3 role-split/eval/halluzination/probe.py --modelle "<id>"     # Halluzinations-Vortest, Lab läuft
```
Review-Eval mit `start_eval.command`, Ablauf in `role-split/eval/README.md`.

## Merksätze

- Jeder Befehlsblock beginnt mit `cd …` – auf den Ordner im Prompt achten.
- Zwei Fenster: 1 = Launcher (nichts eintippen), 2 = Befehle.
- Die Web-UI-Modelle schreiben nur Dokumente (`docs/projekt_management/`, `docs/research/`), keinen Code.
- Antworten ohne Beleg (Datei, URL, Testausgabe) gelten als **ungeprüft** – nachfragen: „Woher? Zeig die Stelle."
- Nach MCP-Neustart: MCP-Eintrag aus/an, Seite neu laden, **neuen Chat**.
