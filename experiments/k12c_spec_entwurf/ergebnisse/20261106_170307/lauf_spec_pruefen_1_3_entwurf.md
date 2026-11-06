# Spec: lauf_spec_pruefen

- **Datum:** 2026-11-06
- **Modell:** lokales Modell (Messung K12c)
- **Betroffene Dateien:** `role-split/kette/kette.py`
- **Änderungsstellen:** 2

## Ziel

`kette.py pruefen` nutzt `spec-pruefen` statt `groesse` für die mechanische Prüfung der Spec-Struktur. Die Befunde der mechanischen Prüfung halten vor der Umsetzung an (Exit 2 bei Fehlern), die alte `groesse`-Prüfung wird zum reinen Hinweis degradiert. Alte Specs mit `groesse`-Problemen erhalten keinen Sonderweg mehr, sondern scheitern an den neuen Regeln.

## Nicht-Ziele

- Änderung der Testlogik oder des Handover-Formats.
- Anpassung der Prompt-Vorlagen (diese lesen die Spec, nicht die Funktion).
- Migration alter Specs in der Ablage.

## Schreibbereich

- `role-split/kette/kette.py`
- `role-split/kette/spec_pruefen.py`
- `tests/test_lauf_spec_pruefen.py`

## Vorgabe-Tests

- `tests/test_lauf_spec_pruefen.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts
- **Technische Sperre für Tests:** keine (keine Netz-, Datei- oder Prozessaufriffe außerhalb des Testprozesses).

## Einstiegspunkte

Keine neuen Einstiegspunkte. `kette.py pruefen` wird über die CLI aufgerufen.

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py pruefen lauf_spec_pruefen` | T1, T2 |

## Quellen

- `role-split/kette/kette.py` def pruefen – Hauptfunktion für die Prüfung, muss `spec-pruefen` integrieren
- `role-split/kette/spec_pruefen.py` def pruefe – Mechanische Prüfung der Spec-Struktur (Ziel, Schreibbereich, Quellen etc.)
- `role-split/kette/spec_pruefen.py` PFLICHT – Liste der Pflichtabschnitte, die geprüft werden müssen

## Anforderungen

### A1: Mechanische Prüfung vor der Umsetzung
- **Anforderung:** `pruefen` ruft `spec_pruefen.pruefe` auf. Wenn `pruefe` Befunde zurückgibt, bricht `pruefen` sofort mit Exit-Code 2 ab und gibt die Befunde aus.
- **Stelle:** `role-split/kette/kette.py` def pruefen, Zeile 626 (vor dem Aufruf von `_pruefen_teile`)
- **Akzeptanz:** Exit-Code 2, Ausgabe enthält die Befunde aus `spec_pruefen.pruefe`.

### A2: Groesse als Hinweis
- **Anforderung:** Die Größe der Spec (`_groesse` aus `spec_pruefen`) wird nicht mehr als Fehler gewertet. Das Ergebnis wird als Hinweis in die Ausgabe aufgenommen, aber der Exit-Code nicht davon beeinflusst.
- **Stelle:** `role-split/kette/kette.py` def pruefen, Zeile 634 (Kurz-Zeile), Zeile 640 (Zieldatei)
- **Akzeptanz:** Exit-Code bleibt 0 oder 1, solange keine anderen Fehler vorliegen. Die Ausgabe enthält einen Hinweis zur Größe.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Spec hat Platzhalter aus der Vorlage | `spec_pruefen.pruefe` erkennt Platzhalter | Exit 2, Befund: "Platzhalter aus der Vorlage: ..." | T1 |
| A1 | Spec hat offene Fragen | `spec_pruefen.pruefe` erkennt offene Fragen | Exit 2, Befund: "Offene Fragen nicht geklärt..." | T1 |
| A1 | Spec hat falschen Schreibbereich | `spec_pruefen.pruefe` erkennt falschen Schreibbereich | Exit 2, Befund: "Schreibbereich falsch..." | T1 |
| A1 | Spec hat falsche Quellen | `spec_pruefen.pruefe` erkennt falsche Quellen | Exit 2, Befund: "Quellen falsch..." | T1 |
| A2 | Spec ist zu groß | `spec_pruefen._groesse` berechnet große Größe | Exit 0 oder 1, Hinweis in Ausgabe | T2 |
| A2 | Spec ist zu klein | `spec_pruefen._groesse` berechnet kleine Größe | Exit 0 oder 1, Hinweis in Ausgabe | T2 |

## Testplan

Alle Tests werden als `tests/test_lauf_spec_pruefen.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.

### T1: Mechanische Prüfung bei Fehlern
- **Prüft:** A1
- **Aufbau:** Temporäres Spec-File mit Platzhalter oder offenen Fragen.
- **Erwartung:** Exit-Code 2, Ausgabe enthält den entsprechenden Befund.
- **Warum misst der Test das Richtige?** Der Test prüft, dass `pruefen` bei mechanischen Fehlern sofort abbricht und nicht weiterläuft.
- **Gegenprobe:** Die Spec muss vor der Umsetzung fehlerhaft sein.

### T2: Groesse als Hinweis
- **Prüft:** A2
- **Aufbau:** Temporäres Spec-File mit großer Größe.
- **Erwartung:** Exit-Code 0 oder 1, Ausgabe enthält Hinweis zur Größe.
- **Warum misst der Test das Richtige?** Der Test prüft, dass die Größe nicht zum Fehler führt, sondern nur ein Hinweis ist.
- **Gegenprobe:** Die Spec muss vor der Umsetzung groß sein.

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
