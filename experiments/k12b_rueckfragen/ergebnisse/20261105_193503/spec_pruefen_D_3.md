<!-- spec_pruefen Variante D Wiederholung 3: 17.2 s, prompt 8725, antwort 491, Form: ok -->

F1: Soll `spec-pruefen` auch prüfen, dass `## Vorgabe-Tests` (falls vorhanden) eine existierende Datei referenziert und dass jede Test-ID als Methodennamen im Testskript vorkommt?
  Optionen: Ja (um R48/R49 vorab zu sichern) | Nein (nur Struktur und Quellen prüfen)
  Warum: Ändert den Umfang der mechanischen Prüfung und die benötigten Quellen/Parsing-Logik. Ohne diesen Check laufen fehlerhafte Vorgabe-Tests erst bei `tests-pruefen` auf, was die Kette verzögert.

F2: Soll `spec-pruefen` prüfen, ob die `## Fehlerpfade`-Tabelle für jede Anforderung mindestens eine Zeile enthält, oder reicht die strukturelle Existenz der Tabelle?
  Optionen: Mindestens eine Zeile pro A1..An | Nur strukturelle Existenz der Tabelle
  Warum: Ändert die Validierungslogik. Eine leere Tabelle ist nach R01 wertlos, aber die mechanische Prüfung auf „mindestens eine Zeile" ist einfacher als die semantische Prüfung auf Vollständigkeit.

F3: Soll `spec-pruefen` prüfen, ob `## Quellen` nur Dateien aus dem Repo referenziert, die tatsächlich existieren (`os.path.exists`)?
  Optionen: Ja | Nein
  Warum: Ändert die Abhängigkeiten (nur Standardbibliothek, kein Git-Call nötig). Nach R02 sind erfundene Quellen ein Fehler. Die Prüfung auf Existenz ist einfach, aber die Spec könnte auch externe Quellen (unter „Offene Fragen") haben, die nicht im Repo sind.

Annahmen:
- Die Prüfung erfolgt strikt gegen die Spec-Datei, die als Argument übergeben wird.
- Es werden keine externen Tools (wie `git diff`) verwendet, nur Python-Standardbibliothek.
- „Trockenlauf an git_schutz und alle_tests" bedeutet: Die Funktion wird in die Kette integriert und muss bestehen, ohne dass neue Spezifikationen für `git_schutz` oder `alle_tests` geschrieben werden (nur Integrationstests für `spec-pruefen` selbst).
- Die Spec-Vorlage ist stabil und folgt der im Kontext gegebenen Vorlage.
