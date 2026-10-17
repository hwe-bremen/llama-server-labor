# Verdikt: scout_mail_nachbesserung

- **Spec:** `docs/projekt_management/spec_20261017_scout_mail_nachbesserung.md` (inkl. Ergänzung E1–E7; E1–E7 hat Vorrang)
- **Handover:** `docs/projekt_management/handover_20261017_scout_mail_nachbesserung.md`
- **Datum:** 2026-10-17
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL (Kürzel qwen38-27b)
- **Geprüfte Dateien:** `scripts/send_scout_email.py` (komplett), `scripts/run_scout_pipeline.sh` (komplett), `agents/llm_scout/llm_scout.py` (LAB_DIR-/Exit-Code-Stellen), Diff HEAD gegen 7734101

## Ergebnis

**NACHBESSERN** – Der Code erfüllt alle Anforderungen der Spec einschließlich E1–E7; die Änderungen sind minimal und passen zum Diff gegen 7734101. Aber zwei Testbehauptungen im Handover tragen nicht, was sie tragen sollen: der Zähler-Test (NT8) misst nicht die gleichzeitige Kollision, und die DB-Isolation (E1) wurde an einer Sandbox-Kopie statt an der echten DB gemessen, die die Ergänzung als Referenz nennt. Beides sind Beweislücken, keine Code-Fehler; ein je ein Nachlauf schließt sie.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| N1 | SMTP-Timeout 30 s, Timeout → Fallback/Exit 1 | erfüllt | `send_scout_email.py:206` (`timeout=30`); Timeout-Handling über bestehende `except Exception` in `mode_normal()`/`mode_fail_mail()` |
| N2 | Port lazy geparst, kein Crash beim Import | erfüllt | `send_scout_email.py:192-196` (lazy `int(os.getenv(...))` mit ValueError-Auffang) |
| N3 | --dry-run gewinnt gegen --fail-mail, mit Warnung | erfüllt | `send_scout_email.py:323-328` (`if args.dry_run` zuerst, Warnung auf stderr) |
| N4 | Fallback-Dateiname sekunden-genau | erfüllt | `send_scout_email.py:269` (`%H%M%S`) |
| N5 | Pipeline-Schalter --dry-run, kein fail-mail, Exit-Code weitergeben | erfüllt | `run_scout_pipeline.sh:56-60` (kein `--fail-mail` im Dry-Run, `exit ${SCOUT_EXIT}`), `:71-74` (Step 2 mit `--dry-run`) |
| N6 | `import markdown` lazy, fail-mail ohne markdown | erfüllt | `send_scout_email.py:28` (globaler Import entfernt), `:94-95` (lokaler Import in `build_email_message()`); `build_fail_email()` nutzt markdown nicht |
| E1 | Pipeline-DB-Isolation (temporäres LAB_DIR, DB-Kopie, echte DB unberührt) | erfüllt (Code); Test-Beweis unzureichend, siehe Befund #2 | `run_scout_pipeline.sh:15-31` (`mktemp -d`, DB-Kopie, Pfad-Ausgabe) |
| E3 | Exklusiver Datei-Modus + Zähler | erfüllt (Code); Zähler-Pfad nie im Code getestet, siehe Befund #1 | `send_scout_email.py:275-285` (`open(..., "x")` + `while`-Loop mit `_1`, `_2`) |
| E4 | Port-Prüfung vor `get_password()` | erfüllt | `send_scout_email.py:192-198` (Port-Block vor `password = get_password()` auf Zeile 199) |

## Handover gegen Code

- **NT8-Zähler-Behauptung trägt nicht.** Das Handover zeigt zwei Aufrufe mit `scout_error_20261017_173715.eml` und `scout_error_20261017_173715_1.eml` und behauptet, der Zähler-Loop sei damit getestet. Die Spec (N4 + E3) verlangt für den Zähler-Test: „Python-Skript, das `datetime.now` mockt auf denselben Timestamp". Die zitierten zwei Aufrufe zeigen aber zwei *verschiedene* Sekundenstempel – das beweist N4 (Sekunden im Namen), nicht E3 (Zähler bei gleicher Sekunde). Der `while FileExistsError`-Loop in `send_scout_email.py:275-285` wurde in keinem Test durchlaufen. Das Handover notiert zwar „nur mit zwei Aufrufen getestet", stellt aber die Ausgabe als Beweis für den Zähler hin.
- **E1-Prüfsummentest an falscher DB gemessen.** Die Ergänzung E1 verlangt: „Prüfsumme von `agents/llm_scout/data/llm_scout.db` vor und nach `run_scout_pipeline.sh --dry-run` vergleichen". Das Handover vergleicht stattdessen `md5 sandbox/test_e1/llm_scout.db` – eine Sandbox-Kopie, die selbst die LAB_DIR ist. Das beweist, dass der Dry-Run eine temporäre DB nicht verändert, aber nicht, dass die *echte* DB (`agents/llm_scout/data/llm_scout.db`) unberührt bleibt. Der Codepfad ist korrekt (DB wird nur in die temporäre Kopie geschrieben), aber die Spec-Testanforderung ist nicht erfüllt.
- **N6/NT9 nicht durchgeführt.** Die Spec verlangt als Test für N6 die `sys.modules["markdown"] = None` + `runpy`-Variante (E5). Das Handover listet NT9 als „Pipeline ohne --dry-run (Fail-Mail aktiv)" – das ist kein N6-Test, sondern ein Pipeline-Test, der zudem versehentlich echten Gmail-Versand ausgelöst hat. Die Lazy-Import-Änderung ist im Code verifiziert, aber nie im Test belegt, dass `--fail-mail` ohne `markdown`-Paket funktioniert.
- **Sonstige Übereinstimmungen:** Die zitierten stdout/stderr-Zeilen in NT1–NT7, NT8, NT9 stimmen mit den `print`-Aufrufen im Code überein. Die Handover-Zeilen („`int(os.getenv(...))` vor `get_password()`", „`'x'`-Modus + `while FileExistsError`", „`%H%M%S`", `if args.dry_run:` zuerst, `import markdown` lokal) sind im Code an den angegebenen Stellen vorhanden. `py_compile` und `bash -n`-Ergebnisse sind plausibel und mit der sauberen Syntax des geprüften Codes vereinbar.

## Befunde

| # | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|
| 1 | mittel | `send_scout_email.py:275-285` | Der Zähler-Loop (`while FileExistsError`) wurde nie im Code getestet. Die NT8-Ausgabe zeigt zwei Aufrufe mit *verschiedenen* Sekundenstempeln – die Kollisionsbedingung (gleicher Stempel) trat nie auf. Der Zähler-Pfad ist damit ungeprüft; wenn er einen Fehler hätte (z. B. falscher Dateinamen, unendliche Schleife), wäre er unentdeckt. | Test mit gemocktem `datetime.now` (z. B. `unittest.mock.patch`), der beide Aufrufe auf denselben Timestamp setzt, und zwei Aufrufen von `mode_fail_mail()` oder `save_email_to_file()` mit gleichem Namen. Erwartet: `scout_error_…_SS.eml` und `scout_error_…_SS_1.eml`. |
| 2 | mittel | `run_scout_pipeline.sh:15-31` | Der E1-Prüfsummentest wurde an `sandbox/test_e1/llm_scout.db` gemessen, nicht an `agents/llm_scout/data/llm_scout.db`. Die Ergänzung E1 benennt die echte DB als Referenz. Der Test beweist nicht, dass die Produktion-DB beim Dry-Run unberührt bleibt. | Prüfsumme von `agents/llm_scout/data/llm_scout.db` vor und nach `bash scripts/run_scout_pipeline.sh --dry-run` (ohne LAB_DIR-Umsetzung) vergleichen. Muss gleich bleiben. Zusätzlich: `agents/llm_scout/data/weekly-reports/` darf keine neue Datei erhalten. |
| 3 | niedrig | `send_scout_email.py:94-95` | Der N6-Test (E5: `sys.modules["markdown"] = None` + `runpy`) wurde nie durchgeführt. Stattdessen wurde NT9 als „Pipeline ohne --dry-run" deklariert, das nicht N6 testet und versehentlich echten Gmail-Versand ausgelöst hat. Die Lazy-Import-Änderung ist im Code korrekt, aber der Akzeptanzfall „--fail-mail ohne markdown" ist unbelegt. | Kleines Testskript: `sys.modules["markdown"] = None`, dann `runpy`-Aufruf von `send_scout_email.py --fail-mail --exit-code 2` mit `SCOUT_SMTP_PORT=9`. Erwartet: Exit 0, Fallback-Datei existiert, kein ImportError. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:**
  - Echter SMTP-Versand mit Gmail (einen Lauf mit echten Credentials, um N1 und den Normalmodus end-to-end zu validieren).
  - NT1/NT2 mit einem echten Python-Socket-Server, der die Verbindung annimmt und schweigt (Spec-Vorbereitung), statt `127.0.0.1:2599` ohne Server. Die zitierte Ausgabe „Connection unexpectedly closed: timed out" legt einen schweigenden Server nahe, aber der Handover gibt keinen Befehl für den Testserver an.
  - `SCOUT_SMTP_PORT="abc"` im Normalmodus (N2-Drittfall): Erwartet Exit 1, stderr-Fehlermeldung, kein Traceback. Im Handover nicht getestet.
  - NT8-Zähler-Test nach Befund #1 (mit gemocktem Timestamp).
  - E1-Prüfsummentest an der echten DB nach Befund #2.
- **Braucht externe Quelle:**
  - Verhalten von `smtplib.SMTP(..., timeout=30)` bei einem Server, der die Verbindung annimmt und nach `starttls()` schweigt – die 30 s gelten je Socket-Operation, nicht als Gesamtdauer (E2-Hinweis). Die Testausgaben zeigen ~30 s, aber ob das Timeout auch bei einem Server, der erst nach TLS-Handshake schweigt, greift, ist nicht belegt. Einmaliger Test mit einem TLS-fähigen Testserver.

## Abweichende Meinung

- **N4-Zähler:** In der Vorgänger-Spec hatte ich den Zähler für Overengineering gehalten. Ergänzung E3 hat den Einwand zurückgewiesen (Kollision in derselben Sekunde ist bei manuellem Nachlauf möglich, und der Zähler ist der einfachste Weg, „keine Überschreibung" zu garantieren). Ich akzeptiere die Entscheidung. Der Zähler ist im Code korrekt umgesetzt; nur der Test fehlt.
- **NT9-Echtfalsversand:** Das Handover nennt den versehentlichen echten Versand als „bekannte Schwäche". Das ist zu milde formuliert: Der Testplan (NT9) verlangt explizit einen `SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=9`-Aufruf mit Fallback-Erwartung. Stattdessen wurde `LLAMA_SERVER_URL=http://localhost:9` gesetzt (das betrifft nur den Scout, nicht den Mail-Versand) und die Pipeline ohne Mail-Umsetzung gestartet – das hat den echten Gmail-Versand ausgelöst. Das ist ein Test-Setup-Fehler, kein Code-Fehler, aber das Handover hätte den Fehler klarer als Abweichung vom Testplan kennzeichnen sollen.
