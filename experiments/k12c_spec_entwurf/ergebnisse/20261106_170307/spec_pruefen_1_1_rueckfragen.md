<!-- 19.7 s, prompt 6804, antwort 549, Form: ok -->

F1: Soll „Änderungsstellen" als eigener Abschnitt unter „Schreibbereich" oder als neue Liste unter „Testplan" (oder ähnlich) eingefügt werden?
  Optionen: Als neuer Unterabschnitt in „Schreibbereich" | Als neuer Abschnitt parallel zu „Schreibbereich" | Als neuer Abschnitt nach „Testplan"
  Warum: Die Struktur der Vorlage muss eindeutig sein, damit der Parser die Zeile maschinell findet; Hawe entscheidet über die logische Einordnung.

Annahmen:
- Der Parser sucht nach dem Abschnittstitel „Änderungsstellen" und wertet den Text dahinter mechanisch aus (Existenz + Format).

Quellen:
- `role-split/kette/kette.py` def abgleich – Mechanismus zum Vergleichen von Spec und Handover, relevant für die Logik von Exit-Codes und Befunden
- `role-split/kette/kette.py` def pruefen – Hauptfunktion für mechanische Prüfungen, zeigt Struktur der Befundtabellen
- `role-split/kette/kette.py` def _ist_hoch – Logik, wie ein Befund als „hoch" (Exit 1) gewertet wird
- `role-split/kette/kette.py` def _befunde – Parsen von Befundtabellen, relevant für die Struktur der Ausgabe
- `role-split/kette/kette.py` def _schreibbereich – Parsen des „Schreibbereich"-Abschnitts, zeigt, wie Platzhalter extrahiert werden
- `role-split/kette/kette.py` def _testplan_kurz – Parsen des Testplans, zeigt, wie Tests und ihre Unterpunkte identifiziert werden
- `role-split/kette/kette.py` def _block – Hilfsfunktion zum Extrahieren von Markdown-Blöcken, zentral für das Finden von Abschnitten
- `role-split/kette/kette.py` def main – Einstiegspunkt, zeigt, wie Befehle registriert und aufgerufen werden
- `role-split/kette/kette.py` def gegenprobe – Referenz für die Nutzung von Exit-Codes und mechanischer Prüfung
- `role-split/kette/kette.py` def tests_pruefen – Referenz für die Prüfung von Tests, zeigt Struktur der Test-IDs
- `role-split/kette/kette.py` def _rot_aus_pruefung – Logik für das Erkennen von Fehlern in der Prüfung
- `role-split/kette/kette.py` def _git_schutz – Referenz für die Integration von git_schutz, um Fehlalarme zu vermeiden
