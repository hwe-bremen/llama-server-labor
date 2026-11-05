<!-- alle_tests Variante A Wiederholung 1: 5.6 s, prompt 420, antwort 266, Form: ok -->

F1: Sollen die Exit-Codes der einzelnen Testläufe aggregiert werden, sodass ein einzelner Fehler den gesamten Skript-Aufruf mit einem nicht-Null-Exit-Code beendet (Fail-Fast), oder soll das Skript alle Tests durchlaufen und am Ende eine Zusammenfassung mit dem Gesamtstatus ausgeben?
  Optionen: Fail-Fast (Stop bei erstem Fehler) | Alle testen (Aggregierte Ausgabe am Ende)
  Warum: Dies bestimmt die Kontrollfluss-Logik im Skript und die Art der Ausgabe, was sich direkt auf die Implementierung und die erwartete Nutzung durch den Reviewer auswirkt.

F2: Soll das Skript nur die Dateien im Verzeichnis `tests/` (oder einem vergleichbaren Standard-Pfad) durchsuchen, oder explizit alle Dateien mit der Endung `_test.py` (oder `.spec.js` etc., je nach Sprache) im gesamten Projektbaum?
  Optionen: Nur Standard-Testverzeichnis | Rekursiv alle Dateien mit Test-Endung
  Warum: Dies definiert den Suchbereich (Globs/Paths) und damit, welche Dateien als "Testdateien" für die Prüfung identifiziert werden, was die Spec für die Dateisuche bestimmt.

Annahmen:
- keine
