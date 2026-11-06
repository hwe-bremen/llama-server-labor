# Spec: spec_pruefen

- **Datum:** 2026-11-04
- **Modell:** lokales Modell (Messung K12c)
- **Betroffene Dateien:** role-split/kette/kette.py
- **Änderungsstellen:** 7

## Ziel

Einen mechanischen Prüf Befehl `spec-pruefen` in `kette.py` implementieren, der eine Spec-Datei validiert, bevor Tests oder Umsetzung beginnen. Er prüft Pflichtabschnitte, Platzhalter, Größe und Struktur, ohne ein LLM einzubinden.

## Nicht-Ziele

- Prüfung von Test-Code oder Umsetzungscode.
- Prüfung von Anforderungs-Dateien oder Handover-Dateien.
- Automatischer Aufruf in anderen Befehlen (z. B. `umsetzung-auto`); dies wird in einer späteren Kette geregelt.

## Schreibbereich

- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_spec_pruefen.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts
- **Technische Sperre für Tests:** keine (reine Datei- und String-Prüfung).

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `tests/test_spec_pruefen.py` | `python3 -m unittest tests.test_spec_pruefen` | T1 |

## Quellen

- `role-split/kette/kette.py` def ablage – wofür (Pfad zur Spec-Datei ermitteln)
- `role-split/kette/kette.py` def abschnitt – wofür (Inhalt von Markdown-Abschnitten extrahieren)
- `role-split/kette/kette.py` def _bloecke – wofür (Markdown-Blöcke parsen)
- `role-split/kette/kette.py` def _schreibbereich – wofür (Schreibbereich aus Spec lesen)
- `role-split/kette/kette.py` def main – wofür (Subcommand-Struktur und Argument-Parser)
- `role-split/kette/kette.py` GIT_SCHUTZ – wofür (Prüfen, dass keine geschützten Dateien verändert werden)
- `docs/projekt_management/_vorlage_spec.md` – wofür (Vorlage für Struktur und Platzhalter)

## Anforderungen

### A1: Pflichtabschnitte und Platzhalter
- **Anforderung:** `spec-pruefen` muss prüfen, dass alle in der Vorlage definierten Hauptabschnitte vorhanden sind und die wörtlichen Platzhalter (z. B. `<kurztitel>`, `<JJJJ-MM-TT>`) durch echte Werte ersetzt wurden.
- **Stelle:** `role-split/kette/kette.py` def spec_pruefen
- **Akzeptanz:** Exit-Code 1 mit Fehlermeldung "Platzhalter <Name> nicht ersetzt" oder "Fehlender Abschnitt <Name>".

### A2: Änderungsstellen-Zeile
- **Anforderung:** Die Spec muss eine Zeile `- **Änderungsstellen:** <Zahl>` im Kopf enthalten. Der Befehl prüft, dass diese Zeile existiert.
- **Stelle:** `role-split/kette/kette.py` def spec_pruefen
- **Akzeptanz:** Exit-Code 1 mit Meldung "Fehlende Zeile: Änderungsstellen".

### A3: Offene Fragen
- **Anforderung:** Der Abschnitt `## Offene Fragen` darf nicht den wörtlichen Inhalt "- Keine" oder "- <… oder „Keine">" enthalten, wenn er leer ist. Er muss entweder mit "- Keine" (wörtlich) oder mit konkreten Fragen gefüllt sein. Ist er leer oder enthält er nur Platzhalter-Text, ist das ein Befund.
- **Stelle:** `role-split/kette/kette.py` def spec_pruefen
- **Akzeptanz:** Exit-Code 1 mit Meldung "Offene Fragen sind nicht explizit als 'Keine' markiert".

### A4: Größe und Änderungsstellen
- **Anforderung:** Die Gesamtgröße der Spec-Datei wird geprüft. Ist sie zu groß (> 60.000 Zeichen), wird eine Warnung ausgegeben, aber der Befehl endet mit Exit 0 (sofern keine anderen Fehler vorliegen). Die Zahl der Änderungsstellen wird ausgegeben, aber nicht als Fehler gewertet.
- **Stelle:** `role-split/kette/kette.py` def spec_pruefen
- **Akzeptanz:** Exit-Code 0, Warnung auf stdout "Warnung: Spec-Größe > 60.000 Zeichen".

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Abschnitt fehlt | | Exit 1, Meldung "Fehlender Abschnitt Ziel" | T1 |
| A1 | Platzhalter bleibt | | Exit 1, Meldung "Platzhalter <kurztitel> nicht ersetzt" | T1 |
| A2 | Zeile fehlt | | Exit 1, Meldung "Fehlende Zeile: Änderungsstellen" | T2 |
| A3 | Offene Fragen leer | | Exit 1, Meldung "Offene Fragen sind nicht explizit als 'Keine' markiert" | T3 |
| A4 | Spec zu groß | | Exit 0, Warnung auf stdout | T4 |

## Testplan

Alle Tests werden als `tests/test_spec_pruefen.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.

### T1: Pflichtabschnitte und Platzhalter
- **Prüft:** A1
- **Aufbau:** Spec-Text mit fehlendem Abschnitt "Ziel" und/oder verbliebenem Platzhalter `<kurztitel>` im Titel.
- **Erwartung:** Exit-Code 1, Ausgabe enthält "Fehlender Abschnitt Ziel" oder "Platzhalter <kurztitel> nicht ersetzt".
- **Warum misst der Test das Richtige?** Der Test zeigt, dass die Regex-Prüfung auf Abschnittstitel und Platzhalter-Werte greift.
- **Gegenprobe:** Keine (neuer Code).

### T2: Änderungsstellen-Zeile
- **Prüft:** A2
- **Aufbau:** Spec-Text ohne Zeile `- **Änderungsstellen:**`.
- **Erwartung:** Exit-Code 1, Ausgabe enthält "Fehlende Zeile: Änderungsstellen".
- **Warum misst der Test das Richtige?** Der Test zeigt, dass die Pflichtzeile im Kopf erkannt wird.
- **Gegenprobe:** Keine (neuer Code).

### T3: Offene Fragen
- **Prüft:** A3
- **Aufbau:** Spec-Text mit leerem Abschnitt `## Offene Fragen` (nur Überschrift, kein Inhalt).
- **Erwartung:** Exit-Code 1, Ausgabe enthält "Offene Fragen sind nicht explizit als 'Keine' markiert".
- **Warum misst der Test das Richtige?** Der Test zeigt, dass leere Abschnitte als Fehler erkannt werden.
- **Gegenprobe:** Keine (neuer Code).

### T4: Größe der Spec
- **Prüft:** A4
- **Aufbau:** Spec-Text mit > 60.000 Zeichen, aber sonst gültig.
- **Erwartung:** Exit-Code 0, Ausgabe enthält "Warnung: Spec-Größe > 60.000 Zeichen".
- **Warum misst der Test das Richtige?** Der Test zeigt, dass die Größenprüfung nur warnt, nicht abbricht.
- **Gegenprobe:** Keine (neuer Code).

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
