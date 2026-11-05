<!-- alle_tests Variante A Wiederholung 3: 4.5 s, prompt 420, antwort 210, Form: ok -->

F1: Sollen die Tests parallel oder sequentiell ausgeführt werden?
  Optionen: Parallel | Sequentiell
  Warum: Die Parallelisierung erfordert eine andere Struktur für das Skript (z.B. Nutzung von `asyncio` oder Multiprocessing) und beeinflusst die Zählung der Exit-Codes (muss alle Ergebnisse aggregieren). Bei sequentieller Ausführung ist die Logik einfacher und der Exit-Code ist direkt der des letzten oder eines fehlgeschlagenen Tests.

F2: Wie soll das Skript mit Testdateien umgehen, die keine expliziten Test-Funktionen enthalten oder nicht ausführbar sind?
  Optionen: Ignorieren | Fehler werfen | Als erfolgreich markieren
  Warum: Dies bestimmt die Fehlerbehandlungslogik im Skript. Ein Fehler würde den Exit-Code auf 1 setzen, Ignorieren würde die Datei überspringen, und "erfolgreich" würde sie als bestanden werten.

Annahmen:
- keine
