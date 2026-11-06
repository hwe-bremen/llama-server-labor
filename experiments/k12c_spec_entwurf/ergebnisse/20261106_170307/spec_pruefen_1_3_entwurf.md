# Spec: spec_pruefen

- **Datum:** 2026-11-04
- **Modell:** lokales Modell (Messung K12c)
- **Betroffene Dateien:** role-split/kette/kette.py, role-split/kette/test_kette.py
- **Änderungsstellen:** 4

## Ziel

Einen mechanischen Prüfbefehl `kette.py spec-pruefen` implementieren, der eine Spec auf Vollständigkeit und Formatübereinstimmung prüft, bevor Tests oder Umsetzung beginnen. Der Befehl darf keine Modelle aufrufen. Alte Specs ohne die neue Zeile „Änderungsstellen" müssen einen Befund melden, aber keinen Exit 1 verursachen.

## Nicht-Ziele

- Prüfung der inhaltlichen Korrektheit von Anforderungen oder Fehlerpfaden (das ist Aufgabe des Reviews).
- Prüfung der Größe der Spec (R59) als Fehler; diese bleibt ein Hinweis mit Exit 0.
- Integration in `kette.py pruefen` oder `kette.py gegenprobe` in dieser Kette.

## Schreibbereich

- `role-split/kette/kette.py`
- `role-split/kette/test_kette.py`
- `tests/test_spec_pruefen.py` (Vorgabe-Tests)

## Vorgabe-Tests

- `tests/test_spec_pruefen.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts
- **Technische Sperre für Tests:** Der Befehl `spec-pruefen` liest nur lokale Dateien. Es gibt keine Netz- oder Dateisystem-Sperre nötig, da keine Änderungen geschrieben werden.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py spec-pruefen <kurztitel>` | T1 |
| `role-split/kette/test_kette.py` | `python3 -m unittest role-split/kette/test_kette.TestSpecPruefen` | T2, T3, T4, T5, T6, T7, T8 |

## Quellen

- `role-split/kette/kette.py` def main – Registrierung der Subparser und Aufruf der Logik
- `role-split/kette/kette.py` def _block – Extrahieren von Markdown-Blöcken nach Überschrift
- `role-split/kette/kette.py` def abschnitt – Hilfsfunktion zum Finden von Abschnitten im Text
- `role-split/kette/kette.py` def datei_suchen – Finden der Spec-Datei im Ablageordner
- `role-split/kette/kette.py` def _schreibbereich – Parsen des „Schreibbereich"-Abschnitts (Vorlage für das Parsen von Listen)
- `role-split/kette/test_kette.py` TestSpecSchreibbereich – Referenz für das Testen von Parser-Funktionen

## Anforderungen

### A1: Mechanischer Befehl `spec-pruefen`
- **Anforderung:** Der Befehl `kette.py spec-pruefen <kurztitel>` muss existieren, die Spec-Datei laden und auf Pflichtabschnitte prüfen.
- **Stelle:** `role-split/kette/kette.py`, Funktion `spec_pruefen` (neu), Eintrag in `main` als Subparser.
- **Akzeptanz:** Der Befehl endet mit Exit 0, wenn alle Pflichtabschnitte da sind. Er endet mit Exit 1, wenn ein Pflichtabschnitt fehlt oder „Offene Fragen" den Inhalt „Keine" haben.

### A2: Prüfung der Pflichtabschnitte
- **Anforderung:** Folgende Abschnitte müssen in der Spec vorhanden sein: „## Ziel", „## Nicht-Ziele", „## Schreibbereich", „## Quellen", „## Anforderungen", „## Fehlerpfade", „## Testplan".
- **Stelle:** `role-split/kette/kette.py`, Funktion `spec_pruefen`.
- **Akzeptanz:** Fehlt einer dieser Abschnitte, wird eine Fehlermeldung ausgegeben und Exit 1 zurückgegeben.

### A3: Prüfung der Platzhalter
- **Anforderung:** Die Kopfzeilen der Spec dürfen nur die wörtlichen Platzhalter der Vorlage enthalten: `<kurztitel>`, `<JJJJ-MM-TT>`, `<Modellname aus dem System-Prompt>`, `<nur Dateien, die du gelesen hast>`, `<1–3 Sätze>`, `<…>`, `<… oder „Keine">`, `<Datei, Funktion>`, `<prüfbar formuliert>`, `<beobachtbares Ergebnis>`. Keine anderen Platzhalter (wie `<Beschreibung>`) sind erlaubt.
- **Stelle:** `role-split/kette/kette.py`, Funktion `spec_pruefen`.
- **Akzeptanz:** Enthält die Spec unbekannte Platzhalter, wird Exit 1 zurückgegeben.

### A4: Prüfung der Änderungsstellen
- **Anforderung:** Die Spec muss eine Zeile `- **Änderungsstellen:** <Zahl>` enthalten. Der Wert muss eine positive ganze Zahl sein. Ist er nicht vorhanden, wird ein Befund „Änderungsstellen fehlen" ausgegeben, aber Exit 0 bleibt (sofern keine anderen Fehler vorliegen).
- **Stelle:** `role-split/kette/kette.py`, Funktion `spec_pruefen`.
- **Akzeptanz:** Fehlt die Zeile, wird die Meldung „Fehlende Pflichtzeile: Änderungsstellen" ausgegeben. Exit 0, wenn sonst alles passt. Ist die Zahl ungültig (z. B. Text), wird Exit 1 zurückgegeben.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Kurztitel existiert nicht | | Exit 2, Meldung „Spec oder Handover fehlt" (oder spezifisch „Spec nicht gefunden") | T1 |
| A2 | Pflichtabschnitt „## Ziel" fehlt | | Exit 1, Meldung „Fehlender Abschnitt: Ziel" | T2 |
| A2 | Alle Pflichtabschnitte vorhanden | | Exit 0, keine Fehlermeldung zu Abschnitten | T3 |
| A3 | Platzhalter `<Beschreibung>` im Text | | Exit 1, Meldung „Unbekannter Platzhalter: <Beschreibung>" | T4 |
| A3 | Alle Platzhalter bekannt | | Exit 0 | T5 |
| A4 | Zeile „Änderungsstellen" fehlt | | Exit 0, Meldung „Fehlende Pflichtzeile: Änderungsstellen" | T6 |
| A4 | Zeile „Änderungsstellen: abc" | | Exit 1, Meldung „Ungültige Zahl bei Änderungsstellen" | T7 |
| A4 | Zeile „Änderungsstellen: 3" | | Exit 0 (wenn sonst alles passt) | T8 |

## Testplan

Alle Tests werden als `tests/test_spec_pruefen.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.

### T1: Prüft A1, Fehlerpfad „Kurztitel existiert nicht"
- **Prüft:** A1
- **Aufbau:** Ruf `spec_pruefen("nicht_existent")` auf.
- **Erwartung:** Exit 2, Ausgabe enthält „Spec nicht gefunden".
- **Warum misst der Test das Richtige?** Der Test prüft, dass der Befehl robust auf fehlende Eingaben reagiert, bevor er die Spec parst.
- **Gegenprobe:** keine (neuer Code)

### T2: Prüft A2, Fehlerpfad „Pflichtabschnitt fehlt"
- **Prüft:** A2
- **Aufbau:** Erstelle eine temporäre Spec-Datei mit nur „## Ziel". Ruf `spec_pruefen` mit dieser Datei (oder einem Mock) auf.
- **Erwartung:** Exit 1, Ausgabe enthält „Fehlender Abschnitt: Nicht-Ziele" (oder der erste fehlende Abschnitt).
- **Warum misst der Test das Richtige?** Der Test prüft, dass die Liste der Pflichtabschnitte korrekt abgearbeitet wird.
- **Gegenprobe:** keine (neuer Code)

### T3: Prüft A2, Normalfall
- **Prüft:** A2
- **Aufbau:** Erstelle eine temporäre Spec mit allen Pflichtabschnitten. Ruf `spec_pruefen` auf.
- **Erwartung:** Exit 0.
- **Warum misst der Test das Richtige?** Der Test bestätigt, dass korrekte Specs akzeptiert werden.
- **Gegenprobe:** keine (neuer Code)

### T4: Prüft A3, Fehlerpfad „Unbekannter Platzhalter"
- **Prüft:** A3
- **Aufbau:** Erstelle eine Spec mit dem Platzhalter `<Beschreibung>`. Ruf `spec_pruefen` auf.
- **Erwartung:** Exit 1, Ausgabe enthält „Unbekannter Platzhalter: <Beschreibung>".
- **Warum misst der Test das Richtige?** Der Test prüft die Whitelist der erlaubten Platzhalter.
- **Gegenprobe:** keine (neuer Code)

### T5: Prüft A3, Normalfall
- **Prüft:** A3
- **Aufbau:** Erstelle eine Spec nur mit bekannten Platzhaltern. Ruf `spec_pruefen` auf.
- **Erwartung:** Exit 0.
- **Warum misst der Test das Richtige?** Der Test bestätigt, dass bekannte Platzhalter durchgehen.
- **Gegenprobe:** keine (neuer Code)

### T6: Prüft A4, Fehlerpfad „Änderungsstellen fehlt"
- **Prüft:** A4
- **Aufbau:** Erstelle eine Spec ohne Zeile „Änderungsstellen". Ruf `spec_pruefen` auf.
- **Erwartung:** Exit 0, Ausgabe enthält „Fehlende Pflichtzeile: Änderungsstellen".
- **Warum misst der Test das Richtige?** Der Test prüft, dass das Fehlen der Zeile einen Hinweis, aber keinen Fehler (Exit 1) auslöst.
- **Gegenprobe:** keine (neuer Code)

### T7: Prüft A4, Fehlerpfad „Ungültige Zahl"
- **Prüft:** A4
- **Aufbau:** Erstelle eine Spec mit „- **Änderungsstellen:** abc". Ruf `spec_pruefen` auf.
- **Erwartung:** Exit 1, Ausgabe enthält „Ungültige Zahl bei Änderungsstellen".
- **Warum misst der Test das Richtige?** Der Test prüft die Formatvalidierung des Werts.
- **Gegenprobe:** keine (neuer Code)

### T8: Prüft A4, Normalfall
- **Prüft:** A4
- **Aufbau:** Erstelle eine Spec mit „- **Änderungsstellen:** 3" und allen anderen korrekten Abschnitten. Ruf `spec_pruefen` auf.
- **Erwartung:** Exit 0.
- **Warum misst der Test das Richtige?** Der Test bestätigt, dass eine korrekte Zahl akzeptiert wird.
- **Gegenprobe:** keine (neuer Code)

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
