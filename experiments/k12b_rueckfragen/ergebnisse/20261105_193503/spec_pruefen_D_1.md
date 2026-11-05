<!-- spec_pruefen Variante D Wiederholung 1: 21.9 s, prompt 8725, antwort 729, Form: ok -->

F1: Sollen die Anforderungen an die mechanische Prüfung explizit die Validierung des „Schreibbereichs“ (R47) und der „Quellen“-Formatierung (R02) enthalten, oder beschränkt sich `spec-pruefen` auf syntaktische Korrektheit und die Prüfung auf existierende Dateien?
  Optionen: A) Umfassend: Prüfung auf korrekte Pfade im Schreibbereich und wörtliche Fundstellen in Quellen | B) Minimal: Nur Syntax, Existenz der Ziel-Dateien und Vorlagenerhalt
  Warum: Eine umfassende Prüfung (A) fängt Fehler wie R47 („Schreibbereich unter Paden, die Paket ausblenden“) und R02 („erfundene Zeilennummern“) mechanisch ab, bevor der lokale Umsetzer startet. Das erhöht die Zuverlässigkeit für K12a, erfordert aber eine komplexere Implementierung in `kette.py`.

F2: Soll `spec-pruefen` auch prüfen, ob die Test-IDs in `## Vorgabe-Tests` mit den später erwarteten Testmethoden übereinstimmen (oder ob dies erst `tests-pruefen` übernimmt), und wie soll mit fehlenden Fehlerpfad-Einträgen in der Tabelle umgegangen werden?
  Optionen: A) Strenge Konsistenz: Jede Test-ID muss eine korrespondierende Zeile in „Fehlerpfade“ haben; jede Anforderung muss mindestens einen Fehlerpfad haben | B) Lockere Validierung: Nur prüfen, ob die Tabelle strukturell vorhanden ist; Inkonsistenzen sind kein Fehler für `spec-pruefen`
  Warum: R18 verlangt Pflichtfragen je Anforderung. Wenn `spec-pruefen` hier mechanisch gegensteuert (Option A), verhindert es, dass der Umsetzer Fehlerpfade vergisst, was die Qualität der Umsetzung signifikant erhöht. Option B schiebt die Verantwortung an den Reviewer.

F3: Wie soll `spec-pruefen` mit Specs umgehen, die noch keine `## Vorgabe-Tests` enthalten (da diese optional sind, aber ab K11a empfohlen)?
  Optionen: A) Warnung: Exit 1 oder Warnung ausgeben, wenn der Abschnitt fehlt, aber die Spec trotzdem als „geprüft“ markieren | B) Keine Prüfung: Den Abschnitt ignorieren, wenn er nicht existiert
  Warum: R48 und R49 betonen die Wichtigkeit von Vorgabe-Tests. Eine Warnung (A) erinnert Hawe/Claude an den Workflow, ohne den Fortlauf zu blockieren. Option B ist weniger strikt, erlaubt aber, dass Specs ohne Tests in die Kette gehen, was gegen die Lernregeln der letzten Ketten verstößt.

Annahmen:
- `spec-pruefen` wird als neuer Befehl in `kette.py` implementiert, der nur die Datei `docs/projekt_management/anforderung_*.md` oder die Spec liest, ohne externe Modelle oder Netzwerke zu nutzen.
- Die Prüfung erfolgt gegen die aktuelle Vorlage `_vorlage_spec.md`, um Struktur-Änderungen zu erkennen.
- Für „git_schutz“ und „alle_tests“ wird angenommen, dass die Specs existieren und im Standardpfad liegen; die Tests prüfen nur die Logik von `spec-pruefen` selbst, nicht die Korrektheit der Specs dieser Projekte (da diese noch nicht geschrieben sind).
