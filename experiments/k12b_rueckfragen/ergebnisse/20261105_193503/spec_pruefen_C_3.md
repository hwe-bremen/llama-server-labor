<!-- spec_pruefen Variante C Wiederholung 3: 14.4 s, prompt 3986, antwort 701, Form: ok -->

F1: Soll `spec-pruefen` nur die Struktur und Plausibilität der Spec prüfen, oder auch die technische Umsetzbarkeit der Anforderungen im Kontext des bestehenden Codes?
  Optionen: A) Struktur/Plausibilität (Syntax, Format, interne Konsistenz, Vorlage-Einhaltung) | B) Struktur + technische Umsetzbarkeit (Prüft, ob geforderte Funktionen/Schnittstellen im Repo existieren oder plausibel sind)
  Warum: Antwort A führt zu einem reinen Format-Check. Antwort B erfordert das Lesen bestehender Code-Dateien (z. B. `core/`, `agents/`) in `spec-pruefen`, was die Komplexität und Laufzeit erhöht, aber Fehler früher findet. Da die Aufgabe "Trockenlauf an git_schutz und alle_tests" betont und keine explizite Code-Analyse fordert, ist A der Standard, aber B ist für "mechanische Prüfung der Spec" im Sinne von "kann das gebaut werden?" relevant.

F2: Wie soll `spec-pruefen` mit fehlenden oder unvollständigen Abschnitten in der Spec umgehen (z. B. leere "Quellen" oder "Offene Fragen")?
  Optionen: A) Fehler (Exit 2), da die Spec unvollständig ist | B) Warnung (Exit 0 mit Hinweis), da "Offene Fragen" explizit erlaubt sind | C) Fehler nur bei fehlenden Pflichtfeldern (Schreibbereich, Ziel), Warnung bei optionalen
  Warum: Die Vorlage erlaubt "Offene Fragen: Keine". Wenn "Quellen" leer ist, ist die Umsetzung unmöglich. Die Unterscheidung zwischen "kritisch fehlend" und "bewusst offen" bestimmt, ob der Prozess blockiert wird.

F3: Sollen die "Vorgabe-Tests" (falls vorhanden) auf syntaktische Korrektheit und Existenz der Test-Datei geprüft werden, oder nur auf ihre Nennung in der Spec?
  Optionen: A) Nur Nennung in Spec prüfen | B) Syntaktische Prüfung der Test-Datei (lädt Skript, prüft Methoden) | C) Nur Existenz der Datei
  Warum: Die Aufgabe nennt "Trockenlauf an git_schutz und alle_tests". Wenn die Tests selbst Fehler haben (z. B. Importfehler), würde `alle_tests` später scheitern. Eine Prüfung der Test-Syntax in `spec-pruefen` entkoppelt Spec-Validierung von Code-Validierung. Antwort B erhöht die Komplexität, Antwort A ist minimal.

F4: Soll `spec-pruefen` prüfen, ob die in der Spec genannten "Schreibbereich"-Dateien tatsächlich existieren oder geändert werden können?
  Optionen: A) Ja (Existenz-Check der Dateien im Schreibbereich) | B) Nein (nur Format-Check der Liste)
  Warum: Ein Tippfehler im Schreibbereich (`pfad/falsch.py`) würde zu einem späteren Fehler führen. Ein Existenz-Check ist einfach, aber wenn die Datei noch nicht existiert (neue Datei), müsste man zwischen "Datei existiert nicht" und "Pfad falsch" unterscheiden. Antwort A erfordert klare Definition, ob neue Dateien erlaubt sind.

Annahmen:
- keine
