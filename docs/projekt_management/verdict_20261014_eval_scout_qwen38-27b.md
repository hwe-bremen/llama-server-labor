# Verdikt: eval scout

- **Spec:** keine – das Handover nennt als Quelle eine Spec-Datei, die im Repo nicht existiert; die Anforderungen kamen direkt von Hawe. Maßstab ist daher die Anforderungstabelle des Handovers selbst.
- **Handover:** `role-split/eval/scout_20261014/handover_20261014_llm_scout_automation.md`
- **Datum:** 2026-10-16
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `role-split/eval/scout_20261014/llm_scout.py`, `llm_scout.plist`, `logs/llm_scout_out.log`, `logs/llm_scout_err.log` (jeweils im genannten Ordner; gleichnamige Dateien anderswo im Repo bewusst nicht geprüft) plus das Handover als Prüfbestandteil

Dateiname: `verdict_20261014_eval_scout_qwen38-27b.md`

## Ergebnis

**PASS** – Alle im Code prüfbaren Anforderungen sind erfüllt, die Zeilenreferenzen des Handovers sind exakt, die Abweichungen sind dokumentiert und nachvollziehbar begründet. Die Befunde (Markierung vor Evaluation, stiller RSS-Ausfall, Handover-/Log-Widerspruch) verändern den Erfüllungsstatus der Anforderungen nicht, sind aber zu kennen (Befunde 1–2).

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1a | os.makedirs vor Report-Schreiben | erfüllt | `llm_scout.py:304` (`os.makedirs(REPORT_DIR, exist_ok=True)` in `main()`, vor `open(filepath, 'w')` in Zeilen 309–310); Zeilenreferenz des Handovers exakt. Zusätzlich bereits `REPORT_DIR.mkdir` auf Modul-Ebene (`llm_scout.py:25`) |
| 1b | sys.exit(0) bei Erfolg, sys.exit(1) bei Fehler | erfüllt | `llm_scout.py:296` und `:314` (exit 0), `llm_scout.py:318` (exit 1 im `except` von `main()`, Zeile 316). Randfall: Ein LLM-Fehler (Timeout) führt nicht zu exit 1, weil `call_llm_for_evaluation` die Exception schluckt und eine Fehler-String zurückgibt (`llm_scout.py:262–264`) – das Skript beendet mit exit 0 und Fehler-Report. Das Handover dokumentiert genau dieses Verhalten als beabsichtigtes, bestehendes Verhalten |
| 1c | Shebang | erfüllt | `llm_scout.py:1` (`#!/usr/bin/env python3`) |
| 2 | chmod +x | erfüllt (Beleg eingeschränkt) | `ls -la`-Ausgabe im Handover zeigt `-rwxr-xr-x` (Dateigröße 10833 B = identisch zur eingefrorenen Kopie); die Ausgabe bezieht sich jedoch auf den Originalpfad `agents/llm_scout/llm_scout.py`. Execute-Bit der eingefrorenen Kopie ist mit den mir verfügbaren Werkzeugen nicht prüfbar (Befund 4) |
| 3 | launchd plist | erfüllt | `llm_scout.plist`: Label `de.hawe.lab.llm_scout`, venv-Interpreter + Skript als ProgramArguments, absoluter WorkingDirectory, `StartCalendarInterval` Weekday=1/Hour=8/Minute=0 (Montag 08:00), stdout/stderr nach `logs/llm_scout_{out,err}.log`. Stimmt key- für key mit der PlistBuddy-Ausgabe im Handover überein; Datei selbst gelesen, wohlgeformtes XML |
| 4 | logs/ Ordner | erfüllt | `logs/` existiert mit beiden Logdateien; Logs sind ins Git übernommen (Commit `b3eb852`) |

## Handover gegen Code

- **Widerspruch: „Nicht getestet – End-to-End-Ausführung: Das Skript wurde nicht durchlaufen.“** `logs/llm_scout_out.log` zeigt eine komplette Durchführung (Start → Fetch → Deduplizierung → LLM-Abfrage → „Bericht gespeichert unter: …/llm_scout_kw42_2026.md“ → sauberes Beenden). `kw42` = ISO-Woche 42/2026 = 12.–18.10.2026, also die Woche des Handovers. Die 48 Zeilen „(bereits verarbeitet)“ belegen zusätzlich, dass mindestens ein früherer Lauf die DB befüllt hatte. Zwei Lesarten: (a) Lauf vor dem 14.10. → Aussage des Handovers falsch; (b) Lauf zwischen 14.10. und dem Einfrieren → Aussage zum Stichtag wahr, aber der eingefrorene Ordner enthält eine Durchführung, die das Handover nicht erwähnt. Der Zeitstempel des Logs ist hier nicht bestimmbar (nicht Teil der Dateiliste) – Klärung durch Hawe nötig (Befund 1). Mildernd zeigt das Log mehr getestetes als behauptetes, nicht weniger.
- **„Getestet: py_compile“** – Ausgabe im Handover vorhanden; der reale Lauf im Log ist ohnehin der stärkere Beleg für syntaktische Korrektheit.
- **„Getestet: PlistBuddy“** – Ausgabe vorhanden und mit der eingefrorenen plist exakt übereinstimmend (alle Keys selbst verifiziert).
- **„Getestet: ls -la“** – Ausgabe vorhanden, bezieht sich auf den Originalpfad (siehe Anforderung 2).
- **Abweichung venv-Interpreter statt Shebang** – im plist konsistent; Begründung fachlich korrekt (launchd setzt keine benutzerbezogene `$PATH`, der System-Python hätte `feedparser`/`requests` nicht). Kein Einwand (siehe „Abweichende Meinung“).
- **Annahme LAB_DIR-Fallback `~/lab`** – vom Log bestätigt: „Bericht gespeichert unter: /Users/hans-wernereberhardt/lab/weekly-reports/llm_scout_kw42_2026.md“.
- **„chmod +x in git: der Commit steht noch aus“** – vom Handover selbst offengelegt; die Automatisierungs-Arbeit ist heute im Repo (Commit `cce3bc5`).
- Sonstige Abweichungen: keine gefunden.

## Befunde

| # | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|
| 1 | mittel | `handover_20261014_llm_scout_automation.md` (Abschnitt „Nicht getestet“) vs. `logs/llm_scout_out.log` | Das Handover behauptet, das Skript sei nicht durchlaufen; das Log im eingefrorenen Ordner zeigt eine komplette Durchführung in der ISO-Woche des Handovers (einschließlich DB-Spuren mindestens eines früheren Laufs). Zeitstempel des Logs hier nicht bestimmbar. | Klären, wann der Log-Lauf stattfand (z. B. `stat logs/llm_scout_out.log` auf der Maschine); fand er vor dem 14.10. statt, den „Nicht getestet“-Abschnitt der eingefrorenen Kopie berichtigen bzw. beim Einfrieren eine Anmerkung ergänzen. |
| 2 | mittel | `llm_scout.py:287` (Markierung im Filter-Durchlauf, vor dem LLM-Call Zeile 301 und vor dem Speichern Zeilen 309–310) | Neue Items werden vor der Evaluation und vor dem Speichern des Reports als verarbeitet markiert. Der Log-Lauf zeigt die Konsequenz: Das einzige neue Item wurde von der per Timeout fehlgeschlagenen LLM-Abfrage konsumiert (`logs/llm_scout_err.log`: ReadTimeout), der „Report“ enthält nur den Fehler-Text, und im nächsten Lauf wird das Item als „bereits verarbeitet“ übersprungen – seine Evaluation ist verloren. Kein Verstoß gegen die genannten Anforderungen (das Handover stuft den Fehler-Report ausdrücklich als bestehendes Verhalten ein), aber ein Korrektheitsproblem für den unbeaufsichtigten Montag-Lauf. Hinweis: Der Git-Log des Repos zeigt einen späteren Commit (`5065ba4`, „erst nach gespeichertem Bericht markieren“), der genau das in der Produktversion behebt – stützt die Einschätzung. | Items erst markieren, nachdem der Report erfolgreich geschrieben wurde (z. B. zweiter Durchlauf nach dem Datei-Write; oder nur die Items markieren, die tatsächlich bewertet werden konnten). |
| 3 | niedrig | `llm_scout.py:146–173` (Funktion `fetch_github_releases`), `feedparser.parse` Zeile 155 | Im einzigen im Log gezeigten Lauf lieferten alle drei GitHub-RSS-Feeds 0 Einträge – ohne jede Warnung. `feedparser` wirft bei Lese-Fehlern keine Exception, sondern liefert ein leeres Feed; der Code prüft `feed.bozo` nicht, daher bliebe ein Abruf-Fehler (z. B. SSL) still. Da Hugging Face im selben Log 49 Items lieferte, war das Netzwerk als solches up. Der Git-Log zeigt später einen Commit (`dbf90ac`), der das Feed-Holen ersetzt und die llama.cpp-URL korrigiert (ggml-org) – Vermutung: die Feeds waren in dieser Version tatsächlich defekt bzw. veraltet. Liegt außerhalb der Anforderungen des Handovers (bestehender Code), schwächt aber den eigentlichen Zweck des Scouts. | Feed-Status prüfen und `feed.bozo`/HTTP-Fehler als Warnung ausgeben; Repo-URLs auf Korrektheit prüfen (llama.cpp ist nach ggml-org gezogen). |
| 4 | niedrig | `llm_scout.py` (Execute-Bit) | Anforderung 2 ist nur über die `ls -la`-Ausgabe im Handover belegt, und diese bezieht sich auf den Originalpfad; das Execute-Bit der eingefrorenen Kopie ist mit den mir verfügbaren Werkzeugen nicht prüfbar. Funktionsal für launchd irrelevant, da die plist den venv-Interpreter direkt aufruft. | Falls relevant: Execute-Bit in `ls -l` für beide Dateien im Repo prüfen und die Rechteänderung committen. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:** Zeitstempel der beiden Logdateien (`stat`/`ls -l`); Inhalt des erzeugten Reports `~/lab/weekly-reports/llm_scout_kw42_2026.md` (enthält er nur den Fehler-Text?); Execute-Bit von `role-split/eval/scout_20261014/llm_scout.py` (`ls -l`); Existenz des venv-Interpreter-Pfads aus der plist auf dem M4; ob der Job geladen ist (`launchctl list | grep llm_scout`).
- **Braucht externe Quelle:** ein echter launchd-Lauf (braucht manuelles `launchctl load`/`kickstart` auf dem M4); eine echte LLM-Bewertung mit laufendem llama-server, um zu belegen, dass ein echter Report erzeugt wird (der einzige Log-Lauf endete im Timeout); ob die GitHub-RSS-Feeds wirklich leer sind oder das Holen fehlschlägt (Netzwerk/SSL auf dem M4).

## Abweichende Meinung

- **Markierung vor Evaluation (Befund 2):** Hätte ich als Teil der Automatisierung behoben – oder zumindest als offenen Punkt mit Empfehlung benannt. Grund: Das neue Automatisierungs-Szenario (unbeaufsichtigt montags 08:00) macht einen LLM-Ausfall deutlich wahrscheinlicher, und dessen Konsequenz (stiller Verlust der Wochen-Daten) ist schwerwiegender als der vom Handover dokumentierte Fehler-Report.
- **Exit-Code bei LLM-Fehler:** Ein Fehler-Report ist kein Erfolg; ein nicht-Null-Exit-Code würde den Fehlschlag in launchd/Monitoring sichtbar machen. Ich akzeptiere das Framing des Handovers (als bestehendes Verhalten dokumentiert) – halte es aber für einen ADR-würdigen Punkt.
- **venv-Interpreter-Abweichung:** kein Einwand – fachlich korrekt und besser als die Shebang-Variante der Spec. Die genannte System-Python-Version (3.9.6) ist nicht verifiziert, das Argument trägt aber ohne die konkrete Version.
