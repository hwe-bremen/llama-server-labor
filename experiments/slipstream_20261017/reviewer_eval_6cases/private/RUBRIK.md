# Vorab festgelegte Bewertung

Diese Datei, answer_key.json und verify_cases.py bleiben außerhalb aller Prompts.
Fälle und Kriterien werden vor Modellantworten gehasht und nicht nachträglich
an Antworten angepasst. Weitere reale Befunde dürfen separat anerkannt werden,
wenn Auslöser/Auswirkung anhand des unveränderten Codes überprüfbar sind.

Für Fälle01–04 jeweils separat:

- **Gefunden:** primärer bekannter Fehler mit korrekter Kausalkette und konkreter
  Datei/Stelle beschrieben. Eine andere präzise Zeile derselben Fehlerkette genügt.
- **Teilweise:** relevanter Mechanismus erkannt, aber Auslöser, Wirkung oder
  zentrale Ursache fehlen oder werden nicht sauber verbunden.
- **Übersehen:** primärer Fehler fehlt oder eine andere/falsche Ursache wird behauptet.
- Zusätzlich Ursache richtig/teilweise/falsch, Ort richtig/ungenau/falsch,
  Vermutungen gekennzeichnet ja/nein/nicht anwendbar protokollieren.

Für Fälle05–06: Kein absichtlich eingebauter Fehler. Jeder belastbar behauptete
Fehler wird einzeln geprüft. Vertragsgemäß erlaubte Verhaltensweisen gelten nicht
als Fehler. Plausible, ausdrücklich konditionale Designhinweise sind getrennt von
falschen Gewissheiten zu zählen. Bloße Stilwünsche nicht als Fehler zählen.
Ein zusätzlicher belegter echter Fehler ist ein Problem der Aufgabenkonstruktion;
er wird anerkannt, ohne stillschweigend die Musterlösung umzuschreiben.

Für alle Fälle:

- Unbelegte/falsche Befunde mit Wortlaut und Gegenbeleg einzeln auflisten.
- Fehlenden, nicht gelieferten Kontext niemals gegen das Modell auslegen.
- Bei finish_reason=length, fehlendem [DONE], Übertragungsfehler oder
  eindeutig abgebrochenem Satz als **unvollständig** kennzeichnen. Erwähnte Funde
  dürfen beschrieben werden; fehlende Funde dann nicht als sichere Modellschwäche zählen.
- Laufzeit separat, keine scheinpräzise Gesamtnote. Für diese kleine Prüfserie
  vorab festgelegte Orientierung: <=180s/Antwort für interaktives Review brauchbar;
  180–360s eher asynchron brauchbar; >360s für kleine Fälle unpraktisch.
  Diese Grenzen sind Arbeitspräferenzen, keine universellen Benchmarks.
- Keine Schlussfolgerung auf Haiku-Niveau, größere Modelle oder allgemeine Qualität.
- Aufgaben und Bewertung stammen vom selben Assistenten; begrenzte Unabhängigkeit,
  sechs handgefertigte Fälle und je ein Lauf, keine repräsentative Statistik.
