<!-- Schritt 1, Web-UI (start_rollen), neuer Chat. Vorher: kette.py anforderung <kurztitel> --aufgabe "…"; Antworten auf Rückfragen mit --antwort anhängen. -->
@review Neue Aufgabe, Kurztitel „{kurztitel}":

<AUFGABE: 2–5 Sätze, was erreicht werden soll und warum>

Die Aufgabe steht wörtlich in {anforderung}. Meine Antworten auf deine Rückfragen trage ich dort ebenfalls ein. Diese Datei ist die verbindliche Vorgabe; deine Spec wird an ihr gemessen.

Erst diskutieren: Nenne die stärkste Schwäche der Aufgabe und stelle höchstens eine Rückfrage, wenn die Antwort das Ergebnis ändert.
Wenn ich „Spec schreiben" sage: nach docs/projekt_management/spec_{datum}_{kurztitel}.md, genau nach der Vorlage docs/projekt_management/_vorlage_spec.md.
Pflicht dabei:
- Abschnitt „Außenwirkung und Sperre": Was kann diese Aufgabe außerhalb des Repos auslösen (Mail, Netz, echte Daten, Schlüsselbund)? Welche technische Sperre verhindert das in Tests?
- Fehlerpfad-Tabelle: jede Standardfrage aus der Vorlage für jede Anforderung durchspielen, nicht nur die naheliegenden.
- Jede Designentscheidung, die die Anforderung in einem Fall nicht erfüllt (Verlust, Doppelversand, „akzeptiertes Restrisiko"), entscheidest du nicht selbst: Spiel durch, was dabei beim nächsten Lauf passiert, und stell sie unter „Offene Fragen" an mich.
- Jeder Test hat eine ID (T1, T2 …), eine prüfbare Erwartung (Zahl, Datei, Exit-Code) und läuft ohne Außenwirkung.
- Keine Zeilennummern, die du nicht in der Datei gelesen hast.
