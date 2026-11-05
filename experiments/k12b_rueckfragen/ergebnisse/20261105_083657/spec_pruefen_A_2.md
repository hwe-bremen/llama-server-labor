<!-- spec_pruefen Variante A Wiederholung 2: 6.5 s, prompt 439, antwort 320, Form: ok -->

F1: Soll „mechanische Prüfung“ auch die syntaktische Validität der Spec-Datei (z. B. JSON-Validierung) umfassen, oder nur die semantische Strukturierung (z. B. Vorhandensein von Pflichtfeldern)?
  Optionen: Ja, Syntax-Validierung einschließen | Nein, nur semantische Struktur prüfen
  Warum: Ändert die Implementierung der Prüflogik (Einbinden eines JSON-Parsers vs. reines String/Dict-Checking) und die Testfälle (ungültiges JSON vs. fehlende Felder).

F2: Definiert „ohne Fehlalarme“ bei `alle_tests`, dass bestehende, nicht von `kette.py` verwaltete Tests nicht angreifen dürfen, oder nur, dass `kette.py` selbst keine Fehler wirft?
  Optionen: Nur `kette.py` muss fehlerfrei sein | Alle Tests im Repo müssen grün bleiben
  Warum: Legt den Umfang der Integrationstests und die Fehlerbehandlung in `kette.py` fest (Abbruch bei fremden Fehlern vs. Ignorieren).

F3: Soll die mechanische Prüfung auch auf Konventionen wie Dateinamen-Konformität (z. B. `spec_*.md`) prüfen?
  Optionen: Ja, Dateinamen prüfen | Nein, nur Inhalt prüfen
  Warum: Ändert die Spec um Pfad-Validierungslogik und entsprechende Testfälle.

Annahmen:
- keine
