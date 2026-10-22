<!-- Schritt D, start_eval, NEUER Chat, Qwen3.6, Reasoning aus. kette.py baut vorher das Review-Paket. Danach: urteil. -->
@review Prüf die Umsetzung zu „{kurztitel}".
Lies NUR {paket}. Darin stehen Anforderung (verbindlich), Spec-Auszug, Code-Diff gegen {commit}, Testliste, Abweichungen aus dem Handover und die maschinelle Prüfung. Ganze Dateien liest du nicht; höchstens drei gezielte Nachlesungen (search_files oder ein Zeilenbereich), wenn eine Frage anders nicht zu klären ist. Ältere Verdikte liest du nicht.
Nur falls das Paket fehlt: Anforderung {anforderung}, Spec docs/projekt_management/spec_{datum}_{kurztitel}.md, Handover docs/projekt_management/handover_{datum}_{kurztitel}.md, Diff gegen {commit} – dann gezielt, nicht vollständig lesen.

1. Spec gegen Anforderung: Widerspricht eine Designentscheidung oder ein „akzeptiertes Restrisiko" der Anforderung? Das ist ein Befund (Harte Vorgabe: ja), auch wenn der Code die Spec korrekt umsetzt.
2. Für JEDE Anforderung beantwortest du diese fünf Pflichtfragen mit Fundstelle (Datei:Zeile):
   a) Erzwungen oder nur verlangt? Steht das Verlangte nur in einem Prompt an ein LLM, in einem Kommentar oder in der Spec – oder erzwingt der Code es auch dann, wenn das LLM, der Feed oder die Eingabe sich nicht daran hält?
   b) Leerer und abweichender Fall: Was passiert konkret, wenn die Eingabe leer ist (keine Einträge, leere Datei, leere Antwort) oder anders aussieht als erwartet (andere Überschrift, andere Schreibweise, fehlendes Feld)? Spiel es mit einem konkreten Beispiel durch.
   c) Markiert, aber nie gezeigt? Wird etwas als erledigt, verarbeitet oder gesendet markiert, das der Nutzer nie zu sehen bekommt? Das ist IMMER ein Befund „hoch" (Unbemerkt: ja) – auch wenn es beabsichtigt oder im Handover begründet wirkt.
   d) Läuft die Absicherung selbst ins Leere? Gibt es einen Pfad, in dem eine Prüf- oder Nachtrags-Logik nichts tut, obwohl ihre Bedingung erfüllt ist (z. B. Bedingung prüft lose, Ersetzung sucht exakt)?
   e) Widersprüchliche Anweisungen: Enthält ein Prompt an ein LLM, eine Konfiguration oder ein Kommentar Anweisungen, die einander oder der Anforderung widersprechen (z. B. zwei Regeln, die nicht gleichzeitig erfüllbar sind)? Dann folgt das LLM zufällig einer davon – Befund.
   Jede Antwort mit „nur verlangt", „verloren", „verschluckt", „unbemerkt", „läuft ins Leere" oder „widerspricht" ist ein Befund – in der Befundtabelle, nicht nur in der Anforderungstabelle. Was die Spec unter „Nicht-Ziele" ausschließt, ist kein Befund.
3. Tests: Für jeden GRUEN- oder ANDERS-Test steht sein Code im Paket. Sag je Test, ob er bewusst Bestehendes prüft (in Ordnung) oder die neue Logik, die sein Titel nennt, gar nicht ausführt (Befund). Fehlt für eine Pflichtfrage mit Befund ein Test, ist auch das ein Befund.

Verdikt KNAPP, höchstens 40 Zeilen, Form nach _vorlage_verdict.md (Abschnitte Ergebnis, Anforderungen einzeln, Befunde mit den Spalten Datenverlust / Unbemerkt / Harte Vorgabe, Nicht geprüft). Keine Wiederholung des Pakets.
Speichern in Abschnitten, damit bei vollem Kontext nichts verloren geht:
- erst write_file: Kopf + „## Ergebnis" + „## Befunde" (Tabelle),
- dann append_file: „## Anforderungen einzeln",
- dann append_file: „## Nicht geprüft".
Datei: docs/projekt_management/verdict_{datum}_{kurztitel}_<modellkürzel>.md
