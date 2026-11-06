# Spec: spec_pruefen

- **Datum:** 2026-11-04
- **Modell:** lokales Modell (Messung K12c)
- **Betroffene Dateien:** role-split/kette/kette.py, role-split/kette/test_kette.py, tests/test_spec_pruefen.py
- **Änderungsstellen:** 8

## Ziel

Einen mechanischen Befehl `spec-pruefen` in `kette.py` implementieren, der eine Spec auf formale Vollständigkeit und Korrektheit prüft (Pflichtabschnitte, Platzhalter, Änderungsstellen-Zeile, Stelle/Prüft-Struktur), ohne ein Modell zu nutzen.

## Nicht-Ziele

- Prüfung der inhaltlichen Konsistenz von Anforderungen und Fehlerpfaden (das macht der Review).
- Prüfung von Spec-Dateien, die vor der Einführung der Vorlage (Commit ba1668c) erstellt wurden (Ausnahme für Bestandschutz laut Hawe-Antwort, aber Befund „Änderungsstellen fehlen“ nur als Hinweis, nicht als Fehler).
- Änderung der Prompt-Generierung (`prompt`-Befehl) oder des Review-Prozesses.

## Schreibbereich

- `role-split/kette/kette.py`
- `tests/test_spec_pruefen.py`

## Vorgabe-Tests

Mit diesem Abschnitt ist `tests/test_spec_pruefen.py` Vorgabe: Sie wird mit der Spec committet, vor dem Erstlauf von `kette.py tests-pruefen spec_pruefen` geprüft (je Test-ID eine Methode, Skript lädt, jeder Test rot vorab) und darf von der Umsetzung nicht geändert werden. Tests für bestehendes Verhalten tragen `(Bestand)` im Titel und müssen vorab grün sein (R49).

- `tests/test_spec_pruefen.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts
- **Technische Sperre für Tests:** Keine nötig, da nur Datei-Lesen und String-Verarbeitung.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py spec-pruefen <kurztitel>` | T1, T2, T3, T4, T5, T6 |
| `tests/test_spec_pruefen.py` | `python3 -m unittest tests.test_spec_pruefen` | T1, T2, T3, T4, T5, T6 (Bestand) |

## Quellen

Jede Konstante, jedes Dateiformat, jede Schnittstelle oder Option, die die Umsetzung braucht, als Fundstelle im Repo – **nichts aus dem Gedächtnis**.

- `role-split/kette/kette.py` def pruefen (Zeilen 615–642) – Referenz für Exit-Codes (0, 1, 2) und Fehlermeldungen (`kurztitel ungueltig`, `Kein Commit gefunden`).
- `role-split/kette/kette.py` def ablage (Zeilen 1576–1579) – Pfad zur Projektmanagement-Datei, um Spec zu finden.
- `role-split/kette/kette.py` def abschnitt (Zeilen 1600–1605) – Hilfsfunktion zum Extrahieren von Markdown-Abschnitten.
- `role-split/kette/kette.py` def _schreibbereich (Zeilen 1630–1639) – Referenz für Regex zur Erkennung von Schreibbereich-Einträgen.
- `role-split/kette/kette.py` def main (Zeilen 1700–1750) – Referenz für Befehlsstruktur und Argument-Parsing.
- `tests/test_vorgabe_tests.py` (Zeilen 1–174) – Referenz für Test-Struktur und Umgang mit `kette.ROOT`/`kette.PM` in Tests.
- `docs/projekt_management/_vorlage_spec.md` (Zeilen 1–100) – Vorlage für Pflichtabschnitte und Platzhalter.
- `role-split/kette/test_kette.py` – Referenz für bestehende Tests, die ggf. angepasst werden müssen (Bestand).

## Anforderungen

### A1: Mechanischer Befehl `spec-pruefen`
- **Anforderung:** `kette.py` muss den Befehl `spec-pruefen <kurztitel>` unterstützen. Er liest die Spec-Datei, prüft sie gegen die Vorlage und gibt einen Exit-Code zurück (0 = OK, 1 = Abweichung, 2 = Format-/Dateifehler).
- **Stelle:** `role-split/kette/kette.py` (neue Funktion `def spec_pruefen(kurztitel: str) -> int` und Eintrag in `main`).
- **Akzeptanz:** Aufruf `python3 role-split/kette/kette.py spec-pruefen spec_pruefen` endet mit Exit 0, wenn die Spec korrekt ist.

### A2: Prüfung auf Pflichtabschnitte und Platzhalter
- **Anforderung:** Der Befehl prüft, ob alle in der Vorlage (`_vorlage_spec.md`) definierten Überschriften vorhanden sind (`# Spec:`, `## Ziel`, `## Nicht-Ziele`, `## Schreibbereich`, `## Außenwirkung und Sperre`, `## Einstiegspunkte`, `## Quellen`, `## Anforderungen`, `## Fehlerpfade`, `## Testplan`, `## Offene Fragen`, `## Abweichende Meinung`). Zudem wird geprüft, ob die Platzhalter `<...>` noch im Text stehen (außer bei `<Modellname aus dem System-Prompt>`, das erlaubt ist).
- **Stelle:** `role-split/kette/kette.py` in `def spec_pruefen`.
- **Akzeptanz:** Fehlt ein Abschnitt oder steht ein Platzhalter `<...>` im Text (außer Modellname), ist der Exit-Code 1. Die Ausgabe enthält die Zeile `FEHLT: <Abschnitt>` oder `PLATZHALTER: <Text>`.

### A3: Prüfung auf Änderungsstellen-Zeile
- **Anforderung:** Der Kopf der Spec muss eine Zeile `- **Änderungsstellen:** <Zahl>` enthalten. Fehlt diese Zeile, ist der Exit-Code 1 (auch bei alten Specs, laut Hawe-Antwort „keine Ausnahme nach Datum“, aber nur als Befund, nicht als Ausschluss).
- **Stelle:** `role-split/kette/kette.py` in `def spec_pruefen`.
- **Akzeptanz:** Fehlt die Zeile `- **Änderungsstellen:**`, ist der Exit-Code 1. Die Ausgabe enthält `FEHLT: - **Änderungsstellen:**`.

### A4: Prüfung auf Stelle/Prüft-Struktur
- **Anforderung:** Jede Anforderung (`### A...`) muss die Unterpunkte `- **Stelle:**` und `- **Akzeptanz:**` enthalten. Jeder Test (`### T...`) muss den Unterpunkt `- **Prüft:**` enthalten. Fehlt einer dieser Punkte, ist der Exit-Code 1.
- **Stelle:** `role-split/kette/kette.py` in `def spec_pruefen`.
- **Akzeptanz:** Fehlt `- **Stelle:**` oder `- **Akzeptanz:**` bei einer Anforderung, oder `- **Prüft:**` bei einem Test, ist der Exit-Code 1. Die Ausgabe enthält `FEHLT: - **Stelle:**` oder `FEHLT: - **Prüft:**`.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Kurztitel ungültig (Sonderzeichen, leer) | | Exit 2, Ausgabe: `Kurztitel '...' ungueltig` | T1 |
| A1 | Spec-Datei nicht gefunden | | Exit 2, Ausgabe: `Spec nicht gefunden: ...` | T2 |
| A2 | Pflichtabschnitt fehlt | | Exit 1, Ausgabe: `FEHLT: ## Ziel` | T3 |
| A2 | Platzhalter `<...>` steht noch im Text | | Exit 1, Ausgabe: `PLATZHALTER: <...>` | T4 |
| A3 | Zeile `- **Änderungsstellen:**` fehlt | | Exit 1, Ausgabe: `FEHLT: - **Änderungsstellen:**` | T5 |
| A4 | Unterpunkt `- **Stelle:**` fehlt bei Anforderung | | Exit 1, Ausgabe: `FEHLT: - **Stelle:**` | T6 |
| A4 | Unterpunkt `- **Prüft:**` fehlt bei Test | | Exit 1, Ausgabe: `FEHLT: - **Prüft:**` | T6 |
| A4 | Unterpunkt `- **Akzeptanz:**` fehlt bei Anforderung | | Exit 1, Ausgabe: `FEHLT: - **Akzeptanz:**` | T6 |

## Testplan

Alle Tests werden als `tests/test_spec_pruefen.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung. Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.

### T1: Ungültiger Kurztitel
- **Prüft:** A1
- **Aufbau:** Aufruf von `kette.spec_pruefen` mit Kurztitel `../x`.
- **Erwartung:** Exit-Code 2. Ausgabe enthält `ungueltig`.
- **Warum misst der Test das Richtige?** Der Test prüft, ob die Eingabevalidierung greift, bevor die Spec gelesen wird.
- **Gegenprobe:** Keine (neue Funktion).

### T2: Spec nicht gefunden
- **Prüft:** A1
- **Aufbau:** Aufruf von `kette.spec_pruefen` mit einem Kurztitel, für den keine Spec existiert.
- **Erwartung:** Exit-Code 2. Ausgabe enthält `Spec nicht gefunden`.
- **Warum misst der Test das Richtige?** Der Test prüft, ob das Fehlen der Eingabedatei korrekt abgefangen wird.
- **Gegenprobe:** Keine (neue Funktion).

### T3: Pflichtabschnitt fehlt
- **Prüft:** A2
- **Aufbau:** Spec-Text ohne `## Ziel`.
- **Erwartung:** Exit-Code 1. Ausgabe enthält `FEHLT: ## Ziel`.
- **Warum misst der Test das Richtige?** Der Test prüft, ob die Regex für Pflichtabschnitte funktioniert.
- **Gegenprobe:** Keine (neue Funktion).

### T4: Platzhalter noch im Text
- **Prüft:** A2
- **Aufbau:** Spec-Text mit `<JJJJ-MM-TT>` im Datum-Feld.
- **Erwartung:** Exit-Code 1. Ausgabe enthält `PLATZHALTER: <JJJJ-MM-TT>`.
- **Warum misst der Test das Richtige?** Der Test prüft, ob Platzhalter erkannt werden.
- **Gegenprobe:** Keine (neue Funktion).

### T5: Änderungsstellen-Zeile fehlt
- **Prüft:** A3
- **Aufbau:** Spec-Text ohne `- **Änderungsstellen:**`.
- **Erwartung:** Exit-Code 1. Ausgabe enthält `FEHLT: - **Änderungsstellen:**`.
- **Warum misst der Test das Richtige?** Der Test prüft, ob die neue Pflichtzeile erkannt wird.
- **Gegenprobe:** Keine (neue Funktion).

### T6: Stelle/Prüft-Struktur fehlerhaft
- **Prüft:** A4
- **Aufbau:** Spec-Text mit Anforderung ohne `- **Stelle:**` und Test ohne `- **Prüft:**`.
- **Erwartung:** Exit-Code 1. Ausgabe enthält `FEHLT: - **Stelle:**` und `FEHLT: - **Prüft:**`.
- **Warum misst der Test das Richtige?** Der Test prüft, ob die Struktur der Anforderungen und Tests validiert wird.
- **Gegenprobe:** Keine (neue Funktion).

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
