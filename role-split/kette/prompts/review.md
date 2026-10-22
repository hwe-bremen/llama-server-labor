<!-- Schritt D, start_eval, NEUER Chat, Qwen3.6, Reasoning aus. kette.py baut vorher das Review-Paket. Danach: urteil. -->
@review Prüf die Umsetzung zu „{kurztitel}".
Lies NUR {paket}. Darin stehen Anforderung (verbindlich), Spec-Auszug, Code-Diff gegen {commit}, Testliste, Abweichungen aus dem Handover und die maschinelle Prüfung. Ganze Dateien liest du nicht; höchstens drei gezielte Nachlesungen (search_files oder ein Zeilenbereich), wenn eine Frage anders nicht zu klären ist. Ältere Verdikte liest du nicht.
Nur falls das Paket fehlt: Anforderung {anforderung}, Spec docs/projekt_management/spec_{datum}_{kurztitel}.md, Handover docs/projekt_management/handover_{datum}_{kurztitel}.md, Diff gegen {commit} – dann gezielt, nicht vollständig lesen.

1. Spec gegen Anforderung: Widerspricht eine Designentscheidung oder ein „akzeptiertes Restrisiko" der Anforderung? Das ist ein Befund (Harte Vorgabe: ja), auch wenn der Code die Spec korrekt umsetzt.
2. Für JEDE Anforderung beantwortest du diese vier Pflichtfragen mit Fundstelle im Diff:
   a) Erzwungen oder nur verlangt? Steht das Verlangte nur in einem Prompt an ein LLM, in einem Kommentar oder in der Spec – oder erzwingt der Code es auch dann, wenn das LLM, der Feed oder die Eingabe sich nicht daran hält?
   b) Leerer und abweichender Fall: Was passiert konkret, wenn die Eingabe leer ist (keine Einträge, leere Datei, leere Antwort) oder anders aussieht als erwartet (andere Überschrift, andere Schreibweise, fehlendes Feld)? Spiel es mit einem konkreten Beispiel durch.
   c) Markiert, aber nie gezeigt? Wird etwas als erledigt, verarbeitet oder gesendet markiert, das der Nutzer nie zu sehen bekommt?
   d) Läuft die Absicherung selbst ins Leere? Gibt es einen Pfad, in dem eine Prüf- oder Nachtrags-Logik nichts tut, obwohl ihre Bedingung erfüllt ist (z. B. Bedingung prüft lose, Ersetzung sucht exakt)?
   Jede Antwort mit „nur verlangt", „verloren", „verschluckt", „unbemerkt" oder „läuft ins Leere" ist ein Befund.
3. Tests: Steht in der Prüfung ein GRUEN- oder ANDERS-Test, sag, ob er bewusst Bestehendes prüft (in Ordnung) oder nichts misst (Befund). Fehlt für eine Pflichtfrage mit Befund ein Test, ist auch das ein Befund.

Verdikt KNAPP, höchstens 40 Zeilen, Form nach _vorlage_verdict.md (Abschnitte Ergebnis, Anforderungen einzeln, Befunde mit den Spalten Datenverlust / Unbemerkt / Harte Vorgabe, Nicht geprüft). Keine Wiederholung des Pakets.
Speichern in Abschnitten, damit bei vollem Kontext nichts verloren geht:
- erst write_file: Kopf + „## Ergebnis" + „## Befunde" (Tabelle),
- dann append_file: „## Anforderungen einzeln",
- dann append_file: „## Nicht geprüft".
Datei: docs/projekt_management/verdict_{datum}_{kurztitel}_<modellkürzel>.md
