# Anforderung: k10b_nachtraege

## Aufgabe

> Vier kleine Nachträge aus der K10-Abnahme in `role-split/kette/kette.py`:
> 1. Der Umsetzer-Prompt (`umsetzung-auto`) nennt für jede Test-ID der Spec die Pflichtzeile `**Tn: Titel** – bestanden | fehlgeschlagen` für den Handover.
> 2. `abgleich` zählt Bereiche wie „T1–T5“ unter „Nicht getestet“ nicht als Einzelnennung.
> 3. Protokoll und Zusammenfassung von `umsetzung-auto` zeigen zusätzlich die Token-Spitze eines einzelnen Schritts.
> 4. `zusammenfuehren` zählt Befundzeilen, die das Modell selbst zurückgezogen hat („Korrekt.“ / „Befund entfällt.“ am Ende), nicht als hoch – die Zeilen bleiben aber im Gesamtbefund sichtbar.
> Sonst nichts an `kette.py` ändern.

## Zweck

- Erster echter Einsatz von `umsetzung-auto` (35B-A3B), kleine gezielte Änderungen in einer großen Datei (R43).
