# Verdikt: scout_bericht_ueberschreiben

- **Datum:** 2026-10-19
- **Modell:** Qwen3-Coder-Next-80B-A3B, qwen3-80b
- **Spec:** `docs/projekt_management/spec_20261018_scout_bericht_ueberschreiben.md`
- **Handover:** `docs/projekt_management/handover_20261018_scout_bericht_ueberschreiben.md`
- **Rücksetzpunkt:** 818aa5d

## Verdikt

**FAIL**

## Befunde

| Datei / Stelle | Schwere | Datenverlust | Unbemerkt | Harte Vorgabe | Begründung | Lösungsweg |
|---|---|---|---|---|---|---|
| `scripts/send_scout_email.py` Zeile 363–372 | hoch | nein | ja | ja | `mode_normal()` ruft `record_sent_week(next_lauf)` **vor** `send_email_smtp()`, wie in A3 gefordert. Jedoch testet **T3 nicht, ob `record_sent_week()` VOR dem SMTP-Aufruf steht**, sondern nur, dass zwei Zustandszeilen geschrieben wurden. Der Test misst das Ergebnis, nicht die Reihenfolge der Aufrufe. | T3 muss `record_sent_week()` und `send_email_smtp()` in der gleichen `try`-Zone prüfen und sicherstellen, dass `record_sent_week()` vor dem `sendmail()`-Aufruf aufgerufen wird. |
| `scripts/send_scout_email.py` Zeile 363–372 | hoch | nein | ja | ja | T3 simuliert den SMTP-Fehler **nach** `record_sent_week()` aufruft. Der Test erwartet, dass `sendmail()` genau einmal aufgerufen wird. Aber: Wenn `record_sent_week()` **nach** `sendmail()` aufgerufen würde, würde der SMTP-Fehler **beim ersten Versuch** die Zustandszeile nicht schreiben, und beim zweiten Aufruf von `mode_normal()` würde erneut gesendet. Da der Test erwartet, dass nach einem SMTP-Fehler beim zweiten Aufruf kein zweiter Versand stattfindet, **misst T3 implizit die Reihenfolge** – aber nur indirekt und nicht explizit prüfbar. | T3 sollte `send_email_smtp` mocken und direkt prüfen, dass `record_sent_week()` **vor** dem `sendmail()`-Aufruf steht (z. B. durch Counter-Zählung in der gleichen Funktion). |
| `scripts/send_scout_email.py` Zeile 347–354 | hoch | nein | ja | ja | A2 verlangt: „Wie viele Berichts-Läufe hat die aktuelle Bericht-Datei?“ → `count_report_runs()`. Der Test T3 prüft mit zwei Läufen (Erstbericht + ein Nachtrag) die Logik, **aber misst nicht, ob die Datei korrekt geparst wird**, sondern nur die Zustandsdatei. Wenn `count_report_runs()` fehlerhaft ist (z. B. falscher Header-Zähler), bleibt der Fehler unbemerkt. | T3 muss den Inhalt der Bericht-Datei explizit auf mehrere Nachträge prüfen und sicherstellen, dass `count_report_runs()` korrekt zählt. |
| `scripts/send_scout_email.py` Zeile 265–280 | hoch | nein | ja | ja | `get_last_sent_lauf_nr()` filtert nach `parts[0] == current_key`, aber prüft **nicht**, ob `parts[1]` eine gültige Zahl ist, bevor `int(parts[1])` aufgerufen wird. Wenn die Datei beschädigt ist (z. B. `2026_42 abc 2026-10-19`), wirft `int()` einen `ValueError`. Der Test T3 simuliert keine beschädigte Zustandsdatei. | T5 oder eine neue Testmethode muss eine beschädigte Zustandsdatei mit ungültiger `lauf_nr` erzeugen und prüfen, dass `get_last_sent_lauf_nr()` fehlerfrei bleibt (z. B. gibt 0 zurück). |
| `scripts/send_scout_email.py` Zeile 265–280 | mittel | nein | ja | ja | `get_last_sent_lauf_nr()` überspringt Zeilen mit `len(parts) >= 2`, aber prüft **nicht**, ob die Zeile **mit** dem aktuellen Key **beginnt** (nur `parts[0] == current_key`). Wenn die Datei `2026_41 2 2026-10-19\n2026_42 1 2026-10-19` enthält und aktuell `2026_42` ist, wird Zeile 1 fälschlicherweise ignoriert – korrekt. Aber wenn die Zeile `2026_42_extra 1 2026-10-19` ist, wird `parts[0] == current_key` **falsch**, weil `2026_42_extra != 2026_42`. Das ist korrekt. **Aber**: Wenn die Zeile `2026_42 1 2026-10-19_extra` ist, wird `parts[0] == current_key` **wahr**, aber die Zeile ist nicht gültig. `int(parts[1])` funktioniert, aber das Datum ist beschädigt. `get_last_sent_lauf_nr()` gibt `lauf` zurück, aber es gibt **keinen Test**, der beschädigte Datumsformate prüft. | T5 muss eine Zustandsdatei mit beschädigtem Datum erzeugen und prüfen, dass `get_last_sent_lauf_nr()` dennoch den korrekten `lauf_nr` zurückgibt (ignoriert beschädigte Zeilen). |
| `scripts/send_scout_email.py` Zeile 282–289 | hoch | ja | ja | ja | `count_report_runs()` zählt mit `content.count("## Nachtrag KW")`. Das ist unsicher: Wenn im LLM-Output oder im Erstbericht der Text `## Nachtrag KW` vorkommt (z. B. als Beispiel, Kommentar, oder im Footer), wird fälschlicherweise ein Nachtrag gezählt. Der Test T3/T4/T5 prüft die Bericht-Dateiinhalte, aber **nicht**, ob der Zähler falsch schlägt, wenn `## Nachtrag KW` im Text erscheint. | `count_report_runs()` muss prüfen, ob die Zeile **exakt** mit `## Nachtrag KW` beginnt (nicht nur enthält), z. B. `content.startswith("## Nachtrag KW", pos)`. |
| `scripts/send_scout_email.py` Zeile 291–296 | hoch | ja | ja | ja | `record_sent_week(lauf_nr)` prüft `line.startswith(f"{current_key} {lauf_nr}")`, um doppelte Einträge zu vermeiden. Aber: Wenn `current_key="2026_42"` und `lauf_nr=12` ist, wird geprüft auf `line.startswith("2026_42 12")`. Wenn die Datei `2026_42 1 2026-10-19` enthält, wird `line.startswith("2026_42 12")` **falsch** – korrekt. Aber wenn die Datei `2026_42 120 2026-10-19` ist, wird `line.startswith("2026_42 12")` **wahr**, weil `"2026_42 120".startswith("2026_42 12")` wahr ist. Das bedeutet: `lauf_nr=12` wird fälschlicherweise als bereits gesendet erkannt, obwohl `lauf_nr=120` gesendet wurde. Der Test T4 prüft mit zwei Zeilen, aber **nicht**, ob die Prüfung auf `lauf_nr` exakt ist (kein Präfix-Übereinstimmungsfehler). | `record_sent_week()` muss prüfen, ob nach `lauf_nr` ein Leerzeichen oder Zeilenende kommt: `line.startswith(f"{current_key} {lauf_nr} ")` oder `line == f"{current_key} {lauf_nr} {datum}"`. |
| `tests/test_scout_bericht_ueberschreiben.py` Zeile 111–123 | mittel | nein | ja | ja | T3 simuliert den SMTP-Fehler mit `sendmail`-Mock, der `smtplib.SMTPException` wirft. Aber: Der Test prüft **nicht**, ob `sendmail()` **genau einmal** aufgerufen wurde, sondern nur `sendmail_call_count[0] == 1`. Wenn der Mock nicht korrekt ist (z. B. wird `sendmail()` nicht aufgerufen, aber der Test denkt, er sei aufgerufen worden), bleibt der Fehler unbemerkt. Der Test sollte `smtp_instance.sendmail.assert_called_once()` verwenden, um sicherzustellen, dass der Mock korrekt aufgerufen wurde. | T3 sollte `unittest.mock.assert_called_once()` verwenden, um die Mock-Aufrufe zu verifizieren. |
| `scripts/run_scout_pipeline.sh` | mittel | nein | ja | ja | A4 verlangt, dass die Pipeline den Exit-Code unverändert weitergibt. T7 prüft nur die Syntax (`bash -n`), nicht die Laufzeit-Logik. Es gibt **keinen Test**, der den echten Pipeline-Lauf simuliert (z. B. `bash -c 'source ... && exit_code=...; echo $exit_code'`). Wenn die Pipeline `llm_scout.py` mit Exit 2 und `send_scout_email.py` mit Exit 3 aufruft, muss die Pipeline Exit 3 weitergeben. T7 prüft **nicht**, dass `run_scout_pipeline.sh` Exit-Codes korrekt weitergibt. | T7 muss einen Subprozess aufrufen, der `run_scout_pipeline.sh` mit gesteuerten Umgebungsvariablen ausführt (z. B. tote `LLAMA_SERVER_URL`, fehlender Bericht) und den Exit-Code prüft. |
| `scripts/send_scout_email.py` Zeile 265–280 | mittel | nein | ja | ja | `get_last_sent_lauf_nr()` nutzt `max_lauf`, aber `max_lauf` wird **nicht** auf `0` initialisiert, wenn `content` leer ist (Zeile 270). Wenn `content` leer ist (`""`), wird `max_lauf = 0` gesetzt. Das ist korrekt. Aber: Wenn `content` nur Whitespace enthält (z. B. `"\n\n"`), wird `content.splitlines()` `["", ""]` liefern, `line.strip()` ergibt `""`, `if not line` ist wahr, und die Zeile wird übersprungen. Das ist korrekt. Der Test T3/T4/T5 prüft **nicht**, ob `content` nur Whitespace ist. | T5 sollte eine Zustandsdatei mit nur Whitespace erzeugen und prüfen, dass `get_last_sent_lauf_nr()` `0` zurückgibt. |

## Anforderungserfüllung

| Anforderung | Status | Fundstelle / Begründung |
|---|---|---|
| A1 | **teilweise erfüllt** | `save_report()` in `llm_scout.py` hängt korrekt an (Erstbericht bleibt byte-identisch, Nachtrag mit Header). **Aber**: Kein Test prüft, was passiert, wenn der Zweitlauf eine Datei mit **teilweisem Nachtrag** (Crash) vorfindet (A1 Fehlerpfad „Absturz mitten im Lauf“). Das ist ein **bekanntes Restrisiko**, aber es bleibt unbemerkt. |
| A2 | **nicht erfüllt** | `count_report_runs()` zählt mit `content.count("## Nachtrag KW")`, was **falsch** ist, wenn der Text `## Nachtrag KW` vorkommt (nicht nur Header). `get_last_sent_lauf_nr()` prüft `parts[0] == current_key`, aber prüft **nicht**, ob `parts[1]` eine gültige Zahl ist (ValueError bei beschädigter Datei). T3/T4/T5 prüfen die Logik, aber **nicht die Grenzfälle** (beschädigte Dateien, Text-Übereinstimmungen). |
| A3 | **teilweise erfüllt** | `record_sent_week()` wird vor `sendmail()` aufgerufen (Kernanforderung). Aber: **Kein Test misst die Reihenfolge**, sondern nur das Ergebnis (zwei Zustandszeilen). T3 simuliert einen SMTP-Fehler, aber **nicht, ob `record_sent_week()` VOR dem SMTP-Aufruf steht** (nur das Ergebnis). Der Test misst, dass nach einem SMTP-Fehler beim zweiten Aufruf kein zweiter Versand stattfindet, aber **nicht, warum** (weil `record_sent_week()` vor dem Versand steht oder weil `get_last_sent_lauf_nr()` korrekt ist). |
| A4 | **nicht erfüllt** | T7 prüft nur die Syntax (`bash -n`), nicht die Laufzeit-Logik. Es gibt **keinen Test**, der den echten Pipeline-Lauf simuliert und prüft, dass Exit-Codes korrekt weitergegeben werden. |
| A5 | **teilweise erfüllt** | `mode_dry_run()` berührt die Zustandsdatei nicht (Bestand). T5 prüft, dass nach Dry-Run die Zustandsdatei unverändert bleibt (Szenario a/b). Aber: **Kein Test prüft**, ob Dry-Run **keine** SMTP-Verbindung öffnet (nur Mock). T5 nutzt einen SMTP-Mock, aber der Test prüft nicht, ob `sendmail()` **nicht** aufgerufen wird. |

## Nicht geprüft

- **Reihenfolge von `record_sent_week()` und `sendmail()`**: T3 prüft das Ergebnis (Zustandszeilen), aber **nicht**, ob `record_sent_week()` VOR dem SMTP-Aufruf steht.
- **Grenzfälle von `count_report_runs()`**: Wenn `## Nachtrag KW` im LLM-Output erscheint, wird fälschlicherweise ein Nachtrag gezählt.
- **Grenzfälle von `get_last_sent_lauf_nr()`**: Beschädigte Zustandsdateien mit ungültiger `lauf_nr` oder beschädigtem Datum.
- **Grenzfälle von `record_sent_week()`**: Präfix-Übereinstimmungsfehler (`lauf_nr=12` vs `lauf_nr=120`).
- **Pipeline-Exit-Code-Weitergabe**: T7 prüft nur Syntax, nicht Laufzeit.
- **SMTP-Mock-Validität**: T3 prüft `sendmail_call_count[0]`, aber nicht, ob der Mock korrekt aufgerufen wurde (`assert_called_once()`).

## Abweichende Meinung

- **A2 – Zähler-Logik**: `count_report_runs()` mit `content.count("## Nachtrag KW")` ist **unsicher**, da es auf Teilstring-Übereinstimmung basiert. Besser wäre `content.startswith("## Nachtrag KW", pos)` oder ein Regex `^## Nachtrag KW`. Die Spec verlangt „Erstbericht + Anzahl der `## Nachtrag KW`-Header“, aber `count()` zählt alle Vorkommen, nicht nur Header-Zeilen. **Meinung**: Das ist ein kritischer Bug, der zu falschen Zählungen führt (z. B. wenn der LLM-Output `## Nachtrag KW` erwähnt).
- **A3 – Test-Logik**: T3 misst das Ergebnis (Zustandszeilen), aber **nicht die Reihenfolge** der Aufrufe. Die Spec verlangt explizit: „`record_sent_week()` wird **vor** `send_email_smtp()` aufgerufen“ (A3). Ein Test, der nur das Ergebnis prüft, garantiert nicht, dass die Reihenfolge stimmt. **Meinung**: T3 ist **nicht ausreichend**, um A3 zu verifizieren.
- **A4 – Pipeline-Test**: T7 prüft nur die Syntax (`bash -n`), nicht die Laufzeit-Logik. Die Spec verlangt: „Pipeline gibt den Exit-Code unverändert weiter“ (A4). Ein Syntax-Check garantiert nicht, dass der Exit-Code weitergegeben wird. **Meinung**: T7 ist **nicht ausreichend**, um A4 zu verifizieren.
- **A5 – SMTP-Mock**: T5 nutzt einen SMTP-Mock, aber der Test prüft nicht, ob `sendmail()` **nicht** aufgerufen wird. Die Spec verlangt: „Dry-Run sendet nie per SMTP“ (A5). Wenn der Mock nicht korrekt ist, könnte SMTP dennoch aufgerufen werden. **Meinung**: T5 ist **nicht ausreichend**, um A5 zu verifizieren.

## Mechanisches Urteil (kette.py)

_2026-10-19 08:18_

```
Modell-Urteil:       nicht gefunden
Regel-Urteil:        NACHBESSERN
Es gilt:             NACHBESSERN
  Befunde hoch: ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
  Korrektur: Befund ?: als 'mittel' eingestuft, aber ja bei Unbemerkt, Harte Vorgabe -> hoch
  Korrektur: Befund ?: als 'mittel' eingestuft, aber ja bei Unbemerkt, Harte Vorgabe -> hoch
  Korrektur: Befund ?: als 'mittel' eingestuft, aber ja bei Unbemerkt, Harte Vorgabe -> hoch
  Korrektur: Befund ?: als 'mittel' eingestuft, aber ja bei Unbemerkt, Harte Vorgabe -> hoch
```
