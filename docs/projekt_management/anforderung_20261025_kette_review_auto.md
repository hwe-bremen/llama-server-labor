# Anforderung: kette_review_auto

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Ich will die Review-Phase nicht mehr von Hand machen. Ein Befehl kette.py review-auto <kurztitel> soll nacheinander:
> 1. pruefen laufen lassen. Sind die Unit-Tests rot, abbrechen mit dem Hinweis „direkt nachbessern, kein Review nötig".
> 2. Das Review-Paket bauen.
> 3. Review Lauf 1 und Lauf 2 über die API des Routers (127.0.0.1:8080) mit dem Modell Qwen3.6-35B-A3B ausführen, Reasoning aus. Beide Läufe bekommen das Paket direkt im Prompt und haben keine Werkzeuge. Die Prompts brauchen dafür eine Fassung ohne „lies Datei / write_file".
> 4. Die Antworten als Verdikt-Dateien mit den bisherigen Namen speichern. Vorhandene Verdikte nicht überschreiben.
> 5. Prüfen, dass jedes Verdikt eine auswertbare Befund-Tabelle enthält. Wenn nicht: laut abbrechen, kein Gesamtbefund mit nur einem Lauf.
> 6. zusammenfuehren und am Ende eine kurze Zusammenfassung ausgeben: Ergebnis, Anzahl hoher Befunde, Dateipfade.
> Fehlerfälle: Router nicht erreichbar, Zeitüberschreitung oder leere Antwort → Exit 1 mit klarer Meldung, keine halben Ergebnisse. Fortschritt live anzeigen, ein Lauf dauert 15–25 Minuten. Nur 127.0.0.1, die Modellantwort wird nur als Text gespeichert und nie ausgeführt.
> Testen mit einem simulierten Modell-Server. Zusätzlich ein echter Lauf am K7-Stand (mail_server_test), damit wir das Ergebnis mit dem K7-Schlüssel vergleichen können.
> Lies keine großen Dateien ganz. Erst search_files (liefert Zeilennummern), dann read_file mit start_line/end_line. Sag vorher, was du lesen willst und warum.

## Antworten auf Rueckfragen

**2026-10-25 12:16** — Frage: Für den Fall „Pfad für das Verdikt existiert schon": abbrechen mit klarer Meldung und Exit 1, oder automatisch umbenennen (`_lauf1`, `_lauf2`) und beide Läufe danach trotzdem zusammenführen? Die Antwort bestimmt den Ablauf des Fehlerlaufs.

> Im sinne es automatischen laufs fände ich automatisch umbennenen richtig

**2026-10-25 12:17** — Frage: Ich habe eine zweite, kleinere Rückfrage, weil sie den Ablauf des Fehlerlaufs ändert: **Fehlende Befund-Tabelle in einem Lauf** – die Anforderung sagt „laut abbrechen, kein Gesamtbefund mit nur einem Lauf". Soll das Skript dann (a) komplett abbrechen mit Exit 1, oder (b) die beiden Läufe trotzdem zu

> b
