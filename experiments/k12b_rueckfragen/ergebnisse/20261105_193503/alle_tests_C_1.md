<!-- alle_tests Variante C Wiederholung 1: 15.6 s, prompt 3948, antwort 554, Form: ok -->

F1: Sollen die Tests explizit in der Reihenfolge der Testdateinamen (alphabetisch) oder der Test-ID (z. B. T1, T2) ausgeführt werden, oder ist die Reihenfolge egal, solange alle Dateien geparst werden?
  Optionen: Alphabetisch nach Dateiname | Explizit nach Test-ID (T1, T2...) | Keine feste Reihenfolge (beliebig)
  Warum: Die Spec muss definieren, wie die "Kette" der Tests durchlaufen wird, falls die Reihenfolge für die Fehlerauswertung (Exit-Code zählen) relevant ist. Bei "Exit-Code zählt" ist oft nur das Endergebnis (0 oder 1) wichtig, aber die Spezifikation des Parsing-Logik (Datei für Datei vs. Test für Test) hängt davon ab. Wenn die ID-Reihenfolge für die Lesbarkeit der Fehlermeldung wichtig ist, muss sie spezifiziert werden.

F2: Soll das Skript nur die Existenz und syntaktische Gültigkeit der Testdateien prüfen, oder auch deren tatsächliche Ausführbarkeit (Importierbarkeit/Loadability) ohne Ausführung der Tests selbst sicherstellen?
  Optionen: Nur Dateiexistenz und Syntax (AST-Prüfung) | Import-Prüfung (ladet das Modul ohne Test-Lauf) | Vollständige Ausführung mit Zeitlimit
  Warum: "Richtig aufrufen" kann bedeuten, dass das Skript `unittest`-Discovery aufruft. Ein reiner Syntaxcheck reicht oft nicht, um "richtig aufgerufen" im Sinne von `kette.py`-Integration zu garantieren, da Importfehler oft erst beim Laden auftreten. Die Spec muss klarstellen, bis zu welcher Tiefe die Validierung geht, um unnötige Laufzeiten zu vermeiden, aber genug Sicherheit zu bieten.

F3: Wie soll mit Testdateien verfahren werden, die keine `unittest.TestCase`-Subklassen enthalten, aber im `tests/`-Ordner liegen (z. B. reine Hilfsdateien oder Skripte)?
  Optionen: Ignorieren (nur Dateien mit TestCase-Klassen) | Fehler melden (Exit 2) | Als "leerer Test" zählen (0 Tests, OK)
  Warum: Die Spec muss den Suchbereich eingrenzen. Wenn `kette.py` alle `.py`-Dateien im `tests/`-Verzeichnis durchsucht, muss definiert sein, wie nicht-testbare Dateien behandelt werden, um False-Positives oder -Negatives bei der "Prüfung aller Testdateien" zu vermeiden.

Annahmen:
- keine
