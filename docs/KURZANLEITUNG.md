# Lab – Kurzanleitung

Zwei Startbefehle, sonst nichts. Beide starten alles in **einem** Fenster: Router + Chat-UI,
Gedächtnis-Proxy (8091), Rollen-Proxy (8092), MCP-Server (8787) **mit Schreibrechten**
(nur in `docs/projekt_management/` und `docs/research/`), Tailscale Serve fürs
iPad/iPhone/Mini und `caffeinate` gegen Ruhezustand.
Ausführlich: `RUNBOOK.md` und `runbook-role-split.md`. Kette Schritt für Schritt: `role-split/kette/FAHRPLAN.md`.

## 1. Starten (Fenster 1 – bleibt offen)

```bash
cd ~/PycharmProjects/llama-server
git status --short                       # sollte leer sein, sonst erst committen
pkill -f lab_mcp_server; pkill -f lm.proxy; pkill -f role_proxy; sleep 1   # Reste vom letzten Lauf
```

| Ich will … | Befehl (auch per Doppelklick) |
|---|---|
| **normal arbeiten** – chatten, `@review`, `@research`, Spec schreiben, mit Gedächtnis | `bash start_rollen.command` |
| **Modelle vergleichen / Review einer Kette** (ohne Gedächtnis, `git_log` aus) | `bash start_eval.command` |

Fertig, wenn nach 1–3 Min. die `.ts.net`-URL erscheint (Rollen-Lauf zusätzlich `Starte Gedaechtnis-Proxy … 8091`;
im Eval-Lauf startet 8091 nicht – OpenCode dann auf Provider „M4 direkt (8080)" stellen, sonst „Cannot connect to API").
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

**Modell zuerst wählen** (Dropdown, vor der ersten Nachricht): Kettenstart/Spec = **Qwen3.8**, Review/Verdikt = **Qwen3.6-35B-A3B**
(eigener, neuer Chat im Eval-Lauf). Bei beiden Reasoning **aus**.

| Am Anfang der Nachricht | Wirkung |
|---|---|
| `@review Neue Aufgabe <kurztitel>: <Text>` | **neue Kette starten** – Modell **Qwen3.8**, Reasoning aus. Proxy schreibt deinen Text wörtlich nach `anforderung_<datum>_<kurztitel>.md`, jede spätere Antwort im Chat wird mitgeschrieben, Spec-Anweisungen kommen automatisch mit |
| `@review …` | prüft, widerspricht begründet, schreibt Specs/Verdikte nach `docs/projekt_management/` (Review einer Kette: Qwen3.6-35B-A3B) |
| `@research …` | recherchiert, markiert belegt / Wissensstand / Vermutung |
| `@aus …` | Rolle ab |
| ohne Trigger | zuletzt gesetzte Rolle gilt weiter |

Kurztitel: nur Kleinbuchstaben, Ziffern, `_`, danach Doppelpunkt – sonst wird nichts mitgeschrieben.
Neuer Vorgang = **neuer Chat**. Die Rollen schreiben **nie** Code; das macht OpenCode (Abschnitt 6).
Reasoning an lässt den 64K-Kontext beim Speichern langer Specs/Verdikte überlaufen.

## 4. Prüfen (Fenster 2, ⌘N)

```bash
curl -s http://127.0.0.1:8091/lm/status | head -c 120; echo        # "k": 4 → Gedächtnis aktiv
/Applications/Tailscale.app/Contents/MacOS/Tailscale serve status    # proxy …:8092 → iPad/Mini gehen
tail -1 role-split/results/role_log.jsonl                            # welche Rolle hatte die letzte Anfrage?
ls docs/projekt_management/anforderung_*                             # Mitschrift der neuen Aufgabe da?
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

`opencode` im Projektordner, mit **Tab** den Agenten wählen (Modell: **Qwen3.6**):

| Agent | Wann |
|---|---|
| `umsetzung` | normal, du bist dabei – fragt bei Shell-Befehlen außer Syntax-Checks, Tests, `git status/diff/log` |
| `umsetzung_nacht` | unbeaufsichtigt – keine Rückfragen, Shell nur Positivliste, alles andere wird abgelehnt; entscheidet selbst und begründet im Handover |

Prompt kommt aus `kette.py prompt umsetzung …` (Abschnitt 6b). **Vorher committen** (Spec-Commit = Rücksetzpunkt).
OpenCode darf im ganzen Projekt Dateien ändern. Committen nach Review und Gegenprüfung: du.

## 6b. Kette mit Prüfbefehlen (Spickzettel – Details im FAHRPLAN)

Spitze Klammern sind Platzhalter, nie mit eintippen. Den Kurztitel schreibst du immer **ausgeschrieben** hin
(z. B. `search_results_verbessern`) – keine `$K`/`$R`-Variablen mehr nötig.

```bash
cd ~/PycharmProjects/llama-server
# 1 Spec: start_rollen, Modell Qwen3.8 (Reasoning aus), Web-UI "@review Neue Aufgabe <kurztitel>: …",
#         Rückfragen beantworten, "Spec schreiben"
python3 role-split/kette/kette.py quellen <kurztitel>                 # Fundstellen der Spec wörtlich holen
git add docs/projekt_management/*_<kurztitel>.md && git commit -m "Spec <kurztitel>"   # = Rücksetzpunkt
python3 role-split/kette/kette.py prompt umsetzung <kurztitel>        # → OpenCode (Qwen3.6)
# 2 Nach jeder Umsetzung/Nachbesserung – EIN Befehl statt drei:
python3 role-split/kette/kette.py pruefen <kurztitel>
#   = abgleich + unittest + gegenprobe; Rücksetzpunkt findet es selbst (Commit "Spec <kurztitel>");
#   Ausgabe landet in docs/projekt_management/pruefung_<datum>_<kurztitel>.md → Claude nur Bescheid sagen
# 3 Review: start_eval, NEUER Chat, Modell Qwen3.6-35B-A3B (Reasoning aus); optional 2. Lauf: prompt review <kurztitel> --lauf 2
python3 role-split/kette/kette.py prompt review <kurztitel>
python3 role-split/kette/kette.py urteil docs/projekt_management/verdict_<…>.md --anhaengen
# dann externe Gegenprüfung (Claude) → PASS: commit | NACHBESSERN: Befunde an OpenCode, dann wieder 2
```

Wichtig: Die Commit-Nachricht muss genau `Spec <kurztitel>` lauten, sonst findet `pruefen` den Rücksetzpunkt nicht
(dann: `pruefen <kurztitel> --commit <hash>`, Hash aus `git log --oneline -10`).

Weitere Befehle:
- `kette.py anforderung <kurztitel> --aufgabe "…"` / `--antwort "…" --frage "…"` – Anforderung ohne Web-UI anlegen bzw. ergänzen.
- `kette.py prompt spec <kurztitel>` – Spec-Prompt ohne Web-UI-Mitschrift (dann ebenfalls mit Qwen3.8).
- Einzeln weiterhin möglich: `kette.py abgleich <kurztitel>`, `kette.py gegenprobe <kurztitel> --commit <hash>`.

Hat die Aufgabe Außenwirkung (Mail, Netz, echte Daten): **Sperre vor der Umsetzung**. Ablauf: `role-split/kette/README.md`.

## 7. Modelle testen (selten)

```bash
python3 role-split/eval/halluzination/probe.py --modelle "<id>"     # Halluzinations-Vortest, Lab läuft
```
Review-Eval mit `start_eval.command`, Ablauf in `role-split/eval/README.md`. Welches Modell für welche Rolle:
Projektdokument `modellwahl-tabelle.md` (Kettenstart/Spec Qwen3.8, Umsetzung Qwen3.6-27B, Review Qwen3.6-35B-A3B).

Qwen3-Coder-Next 80B (Slipstream, ruht): `bash scripts/launch_qwen3next.command` (Port 8083, Lab vorher beenden,
bei Speichermangel `sudo purge`). Stand: Projektdokument `slipstream-stand.md`.

## Merksätze

- Jeder Befehlsblock beginnt mit `cd …` – auf den Ordner im Prompt achten.
- Zwei Fenster: 1 = Launcher (nichts eintippen), 2 = Befehle.
- Codeblöcke über das Kopier-Symbol kopieren (sonst landet z. B. `sh` mit im Terminal).
- Modell: Kettenstart/Spec **Qwen3.8**, Umsetzung **Qwen3.6-27B**, Review **Qwen3.6-35B-A3B** – vor der ersten Nachricht im Dropdown wählen.
- Die Web-UI-Modelle schreiben nur Dokumente (`docs/projekt_management/`, `docs/research/`), keinen Code.
- Antworten ohne Beleg (Datei, URL, Testausgabe) gelten als **ungeprüft** – nachfragen: „Woher? Zeig die Stelle."
- Nach MCP-Neustart: MCP-Eintrag aus/an, Seite neu laden, **neuen Chat**.
- Speichern des Verdikts/der Spec bricht mit „Failed to parse tool call arguments" ab → Kontext voll: neuer Chat, Reasoning aus.
