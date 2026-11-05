<!-- alle_tests Variante D Wiederholung 1: 16.0 s, prompt 8221, antwort 468, Form: ok -->

F1: Sollen die Tests der aktuellen Kette explizit in die Prüfung einbezogen werden, oder ist das Skript strikt auf den allgemeinen „Health Check“ aller anderen Testdateien (`tests/test_*.py`) beschränkt, um die in R50 beschriebene „nächste Kette“ zu validieren?
  Optionen: Ja, alle `tests/test_*.py` einschließen | Nein, nur Tests außerhalb der aktuellen Kette (oder alle außer der aktuellen)
  Warum: Dies bestimmt, ob das Skript eine Fehlermeldung ausgibt, wenn die aktuellen Tests noch nicht grün sind (was bei R50 als „Messung des neuen Mechanismus“ kritisch sein kann), oder ob es sich einfach durchläuft. Es ändert die Logik der Schleife über `glob`/`os.listdir`.

F2: Soll das Skript nur den Exit-Code der einzelnen Testläufe prüfen und protokollieren, oder auch aggregieren, dass das gesamte Skript nur dann mit Exit 0 endet, wenn *alle* aufgerufenen Tests grün waren?
  Optionen: Nur Protokollierung pro Test (Exit 0 des Skripts ignoriert einzelne rote Tests) | Aggregiert (Exit 1 des Skripts, wenn mindestens ein Test rot ist)
  Warum: R50 sagt „Exit-Code zählt“. Wenn das Skript nur loggt, aber immer Exit 0 gibt, ist die Automation (z.B. CI oder `kette.py pruefen`) blind für Fehler. Die Entscheidung bestimmt die finale Logik am Ende des Skripts.

F3: Wie soll mit Testdateien umgegangen werden, die syntaktisch fehlerhaft sind oder beim Import abstürzen (z.B. durch fehlende Abhängigkeiten)?
  Optionen: Als Fehler zählen (Exit 1 für diesen Test) | Ignorieren und nur grüne/rote Tests zählen
  Warum: R50 fordert „alle Testdateien laufen lassen“. Ein Importfehler ist kein Testfehler im Sinne der Logik, blockiert aber den Lauf. Die Entscheidung ändert die `try/except`-Struktur um die Testausführung.

Annahmen:
- keine
