# Anforderung: abnahme_k10

## Aufgabe

> Abnahme von `kette.py umsetzung-auto` (K10) an einer kleinen, in sich geschlossenen Aufgabe:
> Ein Kommandozeilen-Werkzeug `experiments/abnahme_k10/mdstat.py` zählt in einer Markdown-Datei Zeilen,
> Wörter, Überschriften und Codeblöcke (Inhalt von Codeblöcken zählt nicht als Wörter oder Überschriften)
> und gibt das als Text oder mit `--json` als JSON aus. Fehlt die Datei: Meldung auf stderr, Exit 2.
> Nur Standardbibliothek, keine Änderung an bestehenden Dateien.

## Zweck der Abnahme

- Läuft `umsetzung-auto` unbeaufsichtigt durch (reason: stop, Handover, pruefen grün)?
- Dauer, Werkzeugaufrufe, Tokens je Modell (35B-A3B und 27B, gleiche Spec).
- Greifen die deny-Regeln des Agenten (Abschnitt „abgelehnt“ in Ausgabe und Rohdaten)?
