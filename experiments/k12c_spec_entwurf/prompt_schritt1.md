Du bereitest eine Spec für die Kette vor. In diesem Schritt schreibst du noch keine Spec und keinen Code.

## Kontext

Die Kette baut Werkzeuge im Repo llama-server: Hawe gibt eine Aufgabe vor → eine Spec wird geschrieben → Claude schreibt Vorgabe-Tests → ein lokales Modell setzt um → mechanische Prüfungen → Review → Hawe entscheidet über den Commit. Zentrales Skript: role-split/kette/kette.py.

{projekt}

## Auftrag

**Teil 1 – Rückfragen an Hawe.** Hawe ist Auftraggeber, kein Entwickler. Frag nur Entscheidungen, die ein Auftraggeber trifft: was passieren soll, Umfang, Verhalten im Fehlerfall, was ausdrücklich nicht dazugehört. Wie etwas programmiert wird (Funktion, Mechanismus, Datenformat, Testaufbau) fragst du **nicht** – das entscheidest du später selbst und nennst es unter „Annahmen“. Was Aufgabe oder Antworten schon festlegen, fragst du nicht.
- Höchstens 4 Fragen, die wichtigste zuerst; jede mit 2–3 Optionen.
- Gibt es keine solche Frage: genau „Keine Rückfragen.“ und darunter ein Satz Begründung.

**Teil 2 – Quellen.** Welche Stellen im Repo musst du lesen, um die Spec zu schreiben (Einbaustelle, Funktionen, die du nutzt, Konstanten, Formate)? Höchstens 12 Zeilen. Nur Dateien aus der Dateiliste und Namen aus der Funktionsliste oben – nichts erfinden. Form je Zeile genau so:
- `pfad/datei.py` def name – wofür
- `pfad/datei.py` Zeilen 10–40 – wofür
- `pfad/datei.md` – wofür (ganze Datei, nur bei kleinen Dateien)

Ausgabe genau in dieser Form, nichts davor, nichts danach:

F1: <Frage in einem Satz>
  Optionen: <A> | <B> [| <C>]
  Warum: <was sich je nach Antwort am Ergebnis ändert>

Annahmen:
- <technische Entscheidung, die du selbst triffst> (oder „- keine“)

Quellen:
- `…` …

## Aufgabe (wörtlich von Hawe, Kurztitel „{kurztitel}“)

{aufgabe}

## Antworten von Hawe

{antworten}
