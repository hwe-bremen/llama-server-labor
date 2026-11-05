<!-- alle_tests Variante D Wiederholung 3: 16.6 s, prompt 8221, antwort 491, Form: ok -->

F1: Sollen die Tests für bestehendes Verhalten (`(Bestand)`) explizit von der Prüfung ausgeschlossen werden, oder müssen sie ebenfalls erfolgreich durchlaufen?
  Optionen: Alle Tests inkl. `(Bestand)` müssen grün sein | Nur neue Tests müssen grün sein, `(Bestand)` ignoriert
  Warum: Bestimmt die Logik im Skript: Muss es den Testplan auf `(Bestand)` filtern oder alle `test_*`-Methoden ausführen? Dies beeinflusst die Spec unter „Anforderung" und „Testplan".

F2: Wie soll das Skript mit Testdateien umgehen, die syntaktisch fehlerhaft sind oder beim Import abstürzen?
  Optionen: Fehler protokollieren und als fehlgeschlagen markieren | Skript mit Exit-Code 2 (Fehler) abbrechen
  Warum: Bestimmt das Fehlerbehandlungsverhalten (Exit-Codes) und die Ausgabe im Protokoll, was in der Spec als „Akzeptanz" und „Fehlerpfade" definiert wird.

F3: Sollen nur Dateien im Verzeichnis `tests/` geprüft werden, oder auch Testdateien in anderen Verzeichnissen, die dem Pattern `test_*.py` folgen?
  Optionen: Nur `tests/*.py` | Alle `test_*.py` im Repo
  Warum: Definiert den Suchbereich des Skripts. Da die Kette oft in `tests/` arbeitet, ist dies eine Standardannahme, die aber explizit festgelegt werden muss, um Pfade in der Spec korrekt anzugeben.

Annahmen:
- Das Skript durchsucht rekursiv das gesamte Repository nach Dateien, die auf `test_*.py` enden (Standard-Verhalten von `unittest`/`pytest`, wenn kein Pfad gegeben ist, aber hier explizit als „alle Testdateien" interpretiert).
- Das Skript ist als CLI-Tool (`python3 ...`) konzipiert, das keine externen Abfragen (LLM) stellt, sondern nur die Ausführung der Python-Testskripte steuert.
- Exit-Code 0 bedeutet „Alle Tests bestanden", Exit-Code 1 bedeutet „Ein oder mehrere Tests fehlgeschlagen", Exit-Code 2 bedeutet „Skript-/Importfehler".
