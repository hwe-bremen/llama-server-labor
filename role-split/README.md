# role-split – Review- und Umsetzungs-Instanz mit lokalen Modellen

**Frage des Experiments:** Tragen lokale Modelle über llama-server eine Rollentrennung in einer echten Projektstruktur? Eine Review-Instanz in der Web-UI konzipiert und prüft, eine Umsetzungs-Instanz in OpenCode baut, und beide übergeben über Markdown-Dateien in `docs/projekt_management/`. Gemessen wird, ob der Reviewer widerspricht, ob er nichts erfindet und ob er echte Fehler findet.

Stand: 15.10.2026 · im Einsatz (erste Durchläufe: llm_scout-Automatisierung, Scout-Mailversand). Neu: zweite Review-Stimme mit anderem Modell.

## Was wo liegt

| Pfad | Zweck |
|---|---|
| `role-split/roles/review.md` | Rollen-Prompt Review: eigene Meinung, begründeter Widerspruch, keine erfundenen Fakten, Verdikt PASS / NACHBESSERN / FAIL, Verdikt-Datei mit Modellkürzel |
| `role-split/roles/research.md` | Rollen-Prompt Recherche: Kennzeichnung belegt / Wissensstand / Vermutung |
| `role-split/role_proxy.py` | Rollen-Proxy auf :8092 (nur Standardbibliothek): erkennt `@review`, `@research`, `@aus` (auch mit Doppelpunkt) und setzt den passenden System-Prompt plus heutiges Datum und Modellname |
| `role-split/test_role_proxy.py` | 28 Tests: Trigger-Logik, Modellkürzel und ein echter Durchlauf mit Fake-Upstream inkl. Streaming |
| `role-split/role.command` | Launcher: `serve` (Standard), `check` (Trockenlauf), `test` |
| `.opencode/agents/umsetzung.md` | OpenCode-Agent „umsetzung“ für die Umsetzungs-Instanz |
| `docs/projekt_management/_vorlage_*.md` | Vorlagen für Handover und Verdikt |
| `role-split/results/` | Log der Rollenwechsel (`role_log.jsonl`: Rolle, Modell, Tools), nicht im Git, weil es Chat-Anfänge enthält |

## Kette und Rollenwechsel

```
Web-UI  →  :8092 role-split  →  :8091 local-memory  →  :8080 Router  →  llama-server
```

- Eine Nutzernachricht, die mit `@review` (oder `@review:`) beginnt, schaltet die Rolle ein. Der Trigger wird entfernt, bevor das Modell und das Gedächtnis-Retrieval die Nachricht sehen.
- Die Rolle gilt weiter, bis ein anderer Trigger oder `@aus` kommt. Der Proxy hält dafür keinen Zustand: Die UI schickt den ganzen Verlauf mit, der Proxy sucht darin den letzten Trigger.
- Neue Rolle: `roles/<name>.md` anlegen, Trigger `@<name>`. Dateien werden bei jeder Anfrage neu gelesen, kein Neustart nötig.
- Ein System-Prompt des Clients bleibt unter dem Rollen-Prompt erhalten.
- Der Proxy schreibt den Modellnamen aus dem Feld `model` der Anfrage in den System-Prompt („Du läufst als Modell: …, Kürzel für Dateinamen: gemma“). Lokale Modelle kennen ihren eigenen Namen nicht zuverlässig.
- Antwort-Header `X-Lab-Role` zeigt die aktive Rolle.
- Ohne Gedächtnis: `ROLE_UPSTREAM=http://127.0.0.1:8080 bash role-split/role.command`.

## Start

```bash
bash scripts/launch_lab_roles.command                  # Mac, alles in einem Fenster
LAB_BIND=serve bash scripts/launch_lab_roles.command   # zusätzlich iPad/Büro
# Browser: http://127.0.0.1:8092   (127.0.0.1, nicht localhost)
```

Details, Start von Hand und Remote: `docs/runbook-role-split.md`.

`MCP_WRITE_ROOTS` begrenzt `write_file` und `delete_file` des Web-UI-MCP-Servers auf die genannten Ordner und schaltet `git_commit` ab. Damit kann die Review-Instanz nur Specs, ADRs, Verdikte und Recherchen schreiben, keinen Code, und nichts committen. Das steht nicht nur im Prompt, sondern wird im Server durchgesetzt. Claude Desktop und der Harness laufen als eigene stdio-Prozesse und sind davon nicht betroffen.

**Einmalig in der Web-UI unter 8092:** Der MCP-Eintrag liegt im Browser-Speicher pro Adresse (siehe `docs/RUNBOOK.md`, Abschnitt 0). Unter `http://127.0.0.1:8092` muss der MCP-Server deshalb neu eingetragen werden: `http://127.0.0.1:8787/mcp`, danach per Stift-Icon „use llama-server proxy“ einschalten.

## Prüfen vor dem ersten Durchlauf

| Punkt | Wie |
|---|---|
| Proxy-Tests | `bash role-split/role.command test` und `check` |
| UI über 8092 | Seite lädt, Antwort streamt, Header `X-Lab-Role: review` in den Entwicklertools nach `@review hallo` |
| MCP über 8092 | `@review Liste docs/projekt_management auf` – Tool-Aufruf geht durch |
| Schreibgrenze | `@review Schreib eine Testdatei nach sandbox/x.md` – muss mit „außerhalb von MCP_WRITE_ROOTS“ scheitern |
| Gedächtnis + Rolle | `LM_SYSTEM_MODE=merge` gesetzt? Probe: `@review Welche Rolle hast du, und was steht über mich im Gedächtnis?` – beides muss in der Antwort vorkommen |
| OpenCode | im Repo starten, mit Tab muss Agent „umsetzung“ erscheinen. Format folgt der aktuellen OpenCode-Doku (`.opencode/agents/`), V2 hat andere Feldnamen. `"tools": {"subagent": false}` weiter beachten |

## Ablauf eines Durchlaufs

1. **Web-UI, `@review`:** Vorhaben besprechen. Wenn klar: „Speichere die Spec als `spec_<datum>_<titel>.md`.“
2. **OpenCode, Agent „umsetzung“:** „Setz `docs/projekt_management/spec_<…>.md` um.“ OpenCode nutzt seine eigenen Datei-Werkzeuge im Repo, nicht den eingeschränkten Web-UI-MCP.
3. **Web-UI, `@review`:** „Prüf `handover_<…>.md` gegen Spec und Code, speichere das Verdikt.“ → `verdict_<datum>_<titel>_<modellkürzel>.md`
4. Bei NACHBESSERN zurück zu 2 mit Verweis auf das Verdikt. Bei PASS committet Hawe.

Einen neuen Chat pro Durchlauf verwenden, sonst wird der Verlauf bei 2–3 Minuten pro Antwort schnell lang und langsam.

## Zweite Stimme (anderes Modell, gleicher Prompt)

Qwen prüft Qwen trennt nur die Kontexte, nicht die blinden Flecken. Deshalb prüft ein zweites Modell aus einer anderen Familie **dasselbe Handover mit demselben Review-Prompt**. Keine eigene Rolle: Ein anderer Prompt würde den Unterschied der Prompts messen statt den der Modelle.

1. Neuer Chat, Modell **Qwen3.6 27B**: `@review Prüf docs/projekt_management/handover_<…>.md gegen Spec und Code, speichere das Verdikt.` → `verdict_<…>_qwen.md`
2. Neuer Chat, Modell **gemma-4-26B-A4B**: exakt derselbe Satz. → `verdict_<…>_gemma.md`
3. Beide Verdikte nebeneinander lesen. Im Log steht pro Anfrage das Modell (`"modell"`).

| Messpunkt | Wie prüfen |
|---|---|
| Werkzeugtreue | Hat das Modell Spec, Handover **und** Code per Tool gelesen (Tool-Aufrufe in der UI, „Geprüfte Dateien“ im Verdikt)? Oder geraten? |
| Gemeinsame Befunde | Was finden beide → wahrscheinlich echt |
| Nur einer findet | Prüfen, wer recht hat → blinder Fleck des anderen oder Erfindung |
| Erfindungen | Befunde ohne Fundstelle im Code, falsche Zeilennummern, nicht existierende Pfade |
| Urteil | Gleiches Verdikt (PASS/NACHBESSERN/FAIL)? |
| Zeit | Sekunden bis zum Verdikt je Modell |

Nicht geprüft: ob beide Modelle gleichzeitig in die 48 GB passen. Sonst lädt der Router um (kostet Zeit, kein Fehler); bei OOM-Meldung zwischen den Läufen umschalten.

## Testplan

Erste Aufgabe: **`scripts/pm_status.py`** listet in `docs/projekt_management/`, welche Specs noch kein Handover haben und welche Handovers noch kein Verdikt.

| Messpunkt | Wie prüfen | Bestanden, wenn |
|---|---|---|
| Widerspruch | In Schritt 1 bewusst einen schwachen Vorschlag machen, z. B. „Ergebnisse als JSON mit eingebetteten Zeilenumbrüchen“ | Reviewer widerspricht mit Begründung, nicht als Frage |
| Kein Scheinwiderspruch | Einen guten Vorschlag machen | Zustimmung mit Begründung, kein erfundener Einwand |
| Faktentreue | Spec und Verdikt auf Pfade, Optionen, Versionen durchsehen | Nichts erfunden, Ungeprüftes als „nicht geprüft“ markiert |
| Gegenprobe | Nach dem Handover von Hand einen Fehler einbauen, Handover unverändert lassen | Verdikt findet den Fehler mit Datei:Zeile |
| Handover-Treue | Handover gegen Code und `git diff` lesen | Keine behaupteten Tests ohne Ausgabe, Abweichungen genannt |
| Zeit | Sekunden pro Antwort | Notieren |

## Notiz nach dem Lauf

Was getestet? Ergebnis je Messpunkt? Weiterverfolgen?
