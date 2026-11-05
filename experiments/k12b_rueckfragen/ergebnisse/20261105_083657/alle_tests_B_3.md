<!-- alle_tests Variante B Wiederholung 3: 12.3 s, prompt 5427, antwort 594, Form: ok -->

F1: Sollen die Vorgabe-Tests explizit prüfen, dass ein einzelner, isoliert fehlschlagender Test den Gesamt-Exit-Code auf ungleich 0 setzt, auch wenn andere Tests durchlaufen?
  Optionen: Ja (Testfall: ein Test schlägt fehl, Hauptscript exit != 0) | Nein (nur der Normalfall grüner Durchlauf wird getestet)
  Warum: R12 verlangt den Erfolgsfall, aber R20 und R50 betonen, dass Exit-Code zählt. Ohne diesen Test ist unklar, ob das Skript nur `sys.exit()` aufruft oder den Aggregator der Testergebnisse korrekt auswertet. Ein Test, der nur grüne Fälle prüft, beweist nicht, dass ein Fehler auch zum Abbruch führt.

F2: Soll das Skript nur die Tests der aktuellen Kette ausführen oder explizit „alle Testdateien“ im Repo (oder im `tests/`-Ordner) durchlaufen?
  Optionen: Nur Tests der aktuellen Kette | Alle Testdateien im Repo/Ordner
  Warum: R50 spricht von „Nach jedem Lauf **alle** Testdateien laufen lassen“. Die Aufgabe nennt „alle Testdateien“. Diese Unterscheidung ändert die Parameter für den Testaufruf (z. B. `pytest tests/` vs. `pytest tests/test_neu.py`) und damit die Spec zur Pfadbestimmung.

F3: Wie soll das Skript mit Tests umgehen, die lange dauern oder blockieren (z. B. Netzaufrufe, die nicht gemockt sind)?
  Optionen: Zeitlimit erzwingen (z. B. `timeout 120`) und abbrechen | Keine Begrenzung (Verlass auf korrekte Mocks)
  Warum: R36 verlangt Zeitlimits für Tests mit Servern/Netz. R14 betont echte Läufe. Wenn das Skript „alle“ Tests läuft, ist ein fehlendes Timeout ein Risiko für Hänger (R36). Die Entscheidung ändert, ob das Skript `subprocess` mit Timeout-Argumenten aufruft oder nur `pytest` delegiert.

Annahmen:
- das Skript wird als Shell-Skript (z. B. Python oder Bash) im `llama-server`-Repo implementiert.
- Es wird angenommen, dass `pytest` als Testrunner im Repo verfügbar ist (Standard in Python-Projekten).
- Die „Testdateien“ sind `.py`-Dateien im `tests/`-Ordner (oder im Root, wenn keine Struktur vorgegeben ist).
- Das Skript soll direkt ausführbar sein (z. B. `./pruef_skript.py` oder `python pruef_skript.py`).
