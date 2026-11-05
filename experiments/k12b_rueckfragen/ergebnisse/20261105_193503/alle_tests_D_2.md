<!-- alle_tests Variante D Wiederholung 2: 15.3 s, prompt 8221, antwort 432, Form: ok -->

F1: Sollen die Tests mit `python3 -m unittest discover -s tests -p 'test_*.py'` (Standard-Lauf) oder explizit `python3 -m unittest tests/<datei>.py` (einzeln) ausgeführt werden, um sicherzustellen, dass auch Tests ohne `TestSuite`-Integration laufen?
  Optionen: A) `discover` (rekursiv, standard) | B) explizite Liste aller Dateien | C) Glob-Pattern `tests/test_*.py`
  Warum: Ändert die Implementierung des Skripts (wie die Testdateien gefunden und aufgerufen werden) und die Fehlerbehandlung (Exit-Code bei fehlenden Modulen vs. Import-Fehler).

F2: Soll das Skript auch die Exit-Codes der einzelnen Testläufe aggregieren und melden (z. B. „3 von 10 fehlgeschlagen"), oder reicht ein globaler Exit-Code (0 bei Erfolg, 1 bei beliebigem Fehler)?
  Optionen: A) Nur globaler Exit-Code (einfach) | B) Globale Summe der Fehler + Exit-Code 1 bei >0 Fehlern | C) Detaillierte Liste pro Datei im stdout
  Warum: Bestimmt die Ausgabeformatierung und die Logik zur Bestimmung des Exit-Codes (R50 verlangt „richtig aufrufen, Exit-Code zählt“; die Präzision der Rückmeldung ist Teil der Spezifikation).

F3: Dürfen temporäre Dateien oder Verzeichnisse (z. B. `__pycache__`, `.pyc`) vom Skript bereinigt werden, oder müssen sie unangetastet bleiben?
  Optionen: A) Bereinigung erlaubt | B) Keine Bereinigung (sauberer Zustand wird vorausgesetzt)
  Warum: Beeinflusst, ob das Skript Schreibzugriff auf systemnahe Verzeichnisse benötigt und ob es Nebenwirkungen auf den Repo-Zustand hat.

Annahmen:
- keine
