<!-- Schritt D, Lauf 2 (anderer Blickwinkel), start_eval, NEUER Chat. Liest Lauf 1 nicht. Danach: kette.py zusammenfuehren. -->
@review Zweites Review zu „{kurztitel}" – Blickwinkel BETRIEB. Ein erstes Review hat Code und Spec schon gegen die Anforderung geprüft; du suchst gezielt, was dabei typischerweise übersehen wird.
Lies NUR {paket}. Höchstens drei gezielte Nachlesungen (search_files oder Zeilenbereich). Verdikte liest du nicht.
Nur falls das Paket fehlt: Anforderung {anforderung}, Spec docs/projekt_management/spec_{datum}_{kurztitel}.md, Diff gegen {commit} – gezielt, nicht vollständig.

1. Echte Abhängigkeiten statt Attrappen: Wo ersetzen die Tests eine echte Abhängigkeit (LLM/Modell, Netz, Server, Postfach, Dateisystem, Schlüsselbund, Uhrzeit)? Was liefert die echte Abhängigkeit anders als die Attrappe (Format und Zusatztext, Fehler, Zeitüberschreitung, Langsamkeit, Sonderzeichen)? Spiel für jede solche Stelle durch, was der Code dann tut. Läuft das Werkzeug mit der echten Abhängigkeit überhaupt durch?
2. Wiederkehrende Fehler: Gibt es eine Eingabe, die bei JEDEM Lauf erneut scheitert (einen kaputten oder ungewöhnlichen Datensatz)? Bleibt sie dann für immer hängen, ohne dass der Nutzer sie zu sehen bekommt? Wird ein vorübergehender Fehler (Netz) anders behandelt als ein dauerhafter (unbrauchbarer Inhalt)?
3. Anforderung Satz für Satz: Nimm jeden Satz der Anforderung (auch die Antworten auf Rückfragen). Widersprechen sich zwei Sätze in einem Fall? Stimmt jeder Satz nach einem normalen Lauf, einem Wiederholungslauf und einem Fehlerlauf noch?
4. Erster echter Einsatz: Was muss der Nutzer beim ersten Start mit echten Daten vorher einrichten, und was passiert, wenn es fehlt (Ordner, Konfigurationsdatei, Schlüsselbund-Eintrag, Port, TLS)? Ist die Fehlermeldung dann verständlich?
Was die Spec unter „Nicht-Ziele" ausschließt, ist kein Befund. Wiederhole keine reinen Stilfragen.

Verdikt KNAPP (Richtwert 40 Zeilen; nie löschen, kürzen oder neu schreiben), Form nach _vorlage_verdict.md (Ergebnis, Befunde mit den Spalten Datenverlust / Unbemerkt / Harte Vorgabe, Nicht geprüft). Speichern: erst write_file (Kopf, Ergebnis, Befunde), dann append_file für weitere Abschnitte.
Datei: docs/projekt_management/verdict_{datum}_{kurztitel}_<modellkürzel>_betrieb.md
