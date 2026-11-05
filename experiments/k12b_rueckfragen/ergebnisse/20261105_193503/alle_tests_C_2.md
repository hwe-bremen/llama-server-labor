<!-- alle_tests Variante C Wiederholung 2: 8.0 s, prompt 3948, antwort 374, Form: ok -->

F1: Sollen die Tests in `tests/test_<kurztitel>.py` explizit mit `unittest.main()` gestartet werden, oder erwartet das Skript, dass es die Test-Module direkt importiert und `unittest.TextTestRunner` aufruft?
  Optionen: A) Skript startet die Dateien als `python3`-Prozesse (Subprocess) | B) Skript importiert die Module als Python-Module
  Warum: Bestimmt die Architektur des Skripts (Prozess-Management vs. Import-Handling) und die Fehlerbehandlung (Exit-Code aus Subprocess vs. Exception im Import).

F2: Soll das Skript nur grüne/rote Ergebnisse zählen, oder auch Tests melden, die wegen Importfehlern oder Syntaxfehlern gar nicht erst gestartet werden konnten?
  Optionen: A) Nur erfolgreiche Test-Läufe (grün/rot) | B) Auch nicht-startbare Tests als Fehler
  Warum: Ändert die Logik zur Fehlererkennung und die Ausgabe des Skripts (ob ein fehlendes Modul als "Test fehlgeschlagen" oder "Skript-Fehler" gewertet wird).

F3: Wie soll mit Tests umgegangen werden, die in Unterverzeichnissen von `tests/` liegen (z.B. `tests/subdir/test_foo.py`)?
  Optionen: A) Nur Dateien direkt in `tests/` | B) Rekursiv alle `test_*.py`-Dateien | C) Nur Dateien, die in der Spec unter „Schreibbereich“ oder „Tests“ aufgeführt sind
  Warum: Bestimmt die Dateisuchlogik (glob Rekursion vs. flaches Glob) und ob das Skript eine Konfiguration benötigt.

Annahmen:
- keine
