<!-- 5.3 s, prompt 6985, antwort 265, Form: ok -->

F1: Soll `spec-pruefen` bei Fehlern (Exit 1) die Ausgabe anhalten und sofort mit Exit 1 enden, oder alle Befunde sammeln und am Ende zusammenfassen?
  Optionen: Sofortiger Abbruch bei erstem Fehler | Alle Fehler sammeln und auflisten
  Warum: Bei sofortigem Abbruch ist das Protokoll kürzer, aber Hawe sieht nicht auf einen Blick, ob noch andere Pflichtabschnitte fehlen. Bei Sammlung ist der Befund vollständiger, aber die Spec muss ggf. mehrmals korrigiert werden.

Annahmen:
- `spec-pruefen` gibt am Ende eine zusammengefasste Liste aller gefundenen Probleme aus (falls vorhanden), anstatt bei der ersten Abweichung zu stoppen.

Quellen:
- `role-split/kette/spec_pruefen.py` def pruefe – wie Befunde gesammelt werden
- `role-split/kette/spec_pruefen.py` PFLICHT – welche Abschnitte zwingend sind
- `role-split/kette/kette.py` def spec_pruefen – Aufrufmechanismus
- `role-split/kette/kette.py` def abgleich – Vergleichslogik (als Referenz für Konsistenz)
