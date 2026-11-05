<!-- alle_tests Variante A Wiederholung 2: 6.5 s, prompt 420, antwort 318, Form: ok -->

F1: Soll das Skript nur die Exit-Codes der Tests prüfen oder auch die Testausgabe (stdout/stderr) auf Fehlermuster (z.B. „FAILED“, „Traceback“) scannen?
  Optionen: Nur Exit-Code | Exit-Code + Ausgabe-Analyse
  Warum: Bei nur Exit-Code ist die Logik trivial (Exit != 0 ist Fehler). Bei Ausgabe-Analyse müssen Regex-Pattern definiert und die Ausgabe geparsed werden, was Spec, Tests und Umsetzung deutlich verändert.

F2: Wie soll das Skript mit Testdateien umgehen, die keine ausführbaren Skripte sind (z.B. reine Daten-Dateien .json oder .yaml), die im Test-Verzeichnis liegen?
  Optionen: Ignorieren | Fehler melden | Als fehlschlagen markieren
  Warum: Wenn nur Skripte ausgeführt werden sollen, muss das Skript eine Filterlogik (z.B. nach Extension oder Shebang) implementieren. Wenn alle Dateien versucht werden, führt das zu Abstürzen, die als Testfehler gewertet werden müssten.

F3: Sollen die Tests parallel ausgeführt werden oder nacheinander?
  Optionen: Nacheinander | Parallel
  Warum: Nacheinander ist einfach. Parallel erfordert Thread-Sicherheit oder Isolation der Testumgebung, eine Ergebnis-Aggregation für den Gesamt-Exit-Code und ggf. eine Limitierung der Prozessanzahl, was die Umsetzung komplexer macht.

Annahmen:
- keine
