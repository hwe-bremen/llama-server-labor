Du schreibst jetzt die Spec für die Kette. Kein Code, keine Testdatei – nur die Spec.

## Kontext

Die Kette baut Werkzeuge im Repo llama-server: Spec → Claude schreibt die Vorgabe-Tests nach deinem Testplan → ein lokales Modell (Qwen3.6-35B, 64K Kontext) setzt um → mechanische Prüfungen → Review → Hawe entscheidet. Die Spec ist die einzige Vorgabe für den Umsetzer: Was nicht drinsteht, macht er falsch oder gar nicht.

{projekt}

{lernregeln}

## Aufgabe (wörtlich von Hawe, Kurztitel „{kurztitel}“)

{aufgabe}

## Antworten von Hawe

{antworten}

## Deine Vorarbeit (Schritt 1)

Deine Rückfragen wurden **nicht** beantwortet. Was Aufgabe und Antworten nicht klären und ein Auftraggeber entscheiden muss, kommt unter „Offene Fragen“; technische Entscheidungen triffst du selbst.

{schritt1}

## Quellen (wörtlich aus dem Repo geholt, Stand vor der Aufgabe)

{quellen}

## Auftrag

Schreib die Spec genau nach der Vorlage oben (alle Abschnitte, Platzhalter ersetzen, HTML-Kommentare darfst du weglassen). Pflicht:
- Kopfzeilen: Datum {datum_iso}, Modell „lokales Modell (Messung K12c)“, Betroffene Dateien, `- **Änderungsstellen:** <Zahl>`.
- Zuschnitt für den Umsetzer: möglichst 1 Datei, höchstens 4 Anforderungen, höchstens 8 Tests, höchstens ~9 Änderungsstellen. Größere Aufgaben in ein eigenes Modul legen und in großen Dateien nur wenige Stellen ändern.
- Je Anforderung eine genaue Einbaustelle („Stelle:“ mit Datei und Funktion, die es in den Quellen gibt), Meldetexte wörtlich.
- `## Vorgabe-Tests` mit genau `tests/test_{kurztitel}.py`. Testplan mit T1, T2 …, je Test „Prüft:“ mit Anforderungs-IDs, Aufbau, Erwartung (Exit-Code, Datei, Meldung), ohne Außenwirkung. Bestehende Tests, die durch die Änderung brechen, nennen.
- `## Quellen` nur mit Fundstellen aus den Quellen oben oder der Dateiliste, Form wie dort.
- Keine Werte, Pfade, Funktionen oder Befehle aus dem Gedächtnis. Was du nicht weißt, kommt unter „Offene Fragen“.
- „Offene Fragen“ nur für Auftraggeber-Entscheidungen; sonst genau „- Keine“.

Ausgabe: nur die Spec in Markdown, erste Zeile `# Spec: {kurztitel}`, nichts davor, nichts danach.
