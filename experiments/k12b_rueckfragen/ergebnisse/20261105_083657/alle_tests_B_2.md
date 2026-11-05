<!-- alle_tests Variante B Wiederholung 2: 7.6 s, prompt 5427, antwort 351, Form: ok -->

F1: Soll das Skript explizit die Testdateien der aktuellen Kette (`kette_<kurztitel>.md` oder entsprechende Ordnerstruktur) priorisieren oder alle `.py`-Dateien im Repo scannen, die als Tests konfiguriert sind (z.B. über `unittest`-Discovery oder `pytest`-Konventionen)?
  Optionen: Nur Tests der aktuellen Kette (definiert durch Datei-/Ordnername) | Alle im Repo gefundenen Testdateien
  Warum: Ändert die Logik der Dateisuche und damit die Spec zur Implementierung des Scanners.

F2: Ist das Skript dazu gedacht, nur die Tests der aktuellen Kette auszuführen, oder auch die Tests aller anderen Ketten im Repo (`kette_*.md`), um globale Regressionen zu prüfen (wie in R50 gefordert)?
  Optionen: Nur aktuelle Kette | Alle Ketten im Repo
  Warum: Bestimmt den Umfang der Ausführung und damit die Komplexität der Aufruflogik und die Fehlerbehandlung bei fehlgeschlagenen Tests anderer Ketten.

F3: Wie soll das Skript mit Testdateien umgehen, die nicht direkt ausgeführt werden können (z.B. fehlende Abhängigkeiten, falsche Struktur), ohne den gesamten Lauf abzubrechen?
  Optionen: Fehler protokollieren, aber weitermachen (Exit != 0 bei Fehlern) | Fehler protokollieren und Lauf stoppen (Exit != 0)
  Warum: Ändert die Fehlerbehandlungslogik und die Definition von „Exit-Code zählt“ (R50).

Annahmen:
- keine
