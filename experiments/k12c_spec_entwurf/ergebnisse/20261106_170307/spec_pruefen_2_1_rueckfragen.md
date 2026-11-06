<!-- 9.6 s, prompt 6804, antwort 483, Form: ok -->

F1: Soll der Befund „Änderungsstellen fehlen“ bei alten Specs (vor Commit ba1668c) als „NACHBESSERN“ (Exit 1) gewertet werden, obwohl Hawe sagte „keine Ausnahme nach Datum“, oder ist das Ausbleiben der Zeile bei alten Specs toleriert (Exit 0), da die Pflicht erst mit der Vorlagen-Einführung galt?
  Optionen: A) Streng: Fehlende Zeile = NACHBESSERN (Exit 1) | B) Pragmatisch: Alte Specs ohne Zeile = OK (Exit 0), neue Specs mit Pflichtzeile prüfen | C) Hybrid: Alte Specs ohne Zeile = Warnung (Exit 0), neue Specs ohne = NACHBESSERN (Exit 1)
  Warum: Hawe sagte „keine Ausnahme nach Datum“, was auf A hindeutet, aber „alte Specs“ impliziert oft Bestandschutz. Die Konsequenz ist Exit 1 (NACHBESSERN) vs. Exit 0.

Annahmen:
- keine

Quellen:
- `role-split/kette/kette.py` def pruefen – Haupteinstieg für den Befehl
- `role-split/kette/kette.py` def _schreibbereich – Prüfung des Schreibbereichs
- `role-split/kette/kette.py` def _pruefung_kurz – Formatierung des Prüfergebnisses
- `role-split/kette/kette.py` BESTAND – Konstante für Bestandstests
- `role-split/kette/kette.py` GIT_SCHUTZ – Liste geschützter Dateien
- `docs/projekt_management/_vorlage_spec.md` – Vorlage für Pflichtabschnitte und Platzhalter
- `tests/test_kette_review_auto.py` – Beispiel für Struktur von Prüfungsaufgaben
- `tests/test_vorgabe_tests.py` – Beispiel für Validierung von Tests
- `tests/test_umsetzung_auto.py` – Beispiel für Validierung von Umsetzung
- `tests/test_scout_bericht_ueberschreiben.py` – Beispiel für Fehlerpfade
- `tests/test_mail_planung.py` – Beispiel für Anforderungsprüfung
- `tests/test_mcp_kette.py` – Beispiel für Schnittstellenprüfung
