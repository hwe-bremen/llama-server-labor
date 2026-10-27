# Spec: abnahme_k10

- **Datum:** 2026-10-27
- **Modell:** Claude (Abnahme-Aufgabe für `kette.py umsetzung-auto`, bewusst klein)
- **Betroffene Dateien:** keine bestehenden; neu `experiments/abnahme_k10/mdstat.py`, `tests/test_abnahme_k10.py`

## Ziel

Ein eigenständiges Kommandozeilen-Werkzeug `mdstat.py`, das für eine Markdown-Datei Zeilen, Wörter, Überschriften und Codeblöcke zählt und als Text oder JSON ausgibt. Die Aufgabe dient als Abnahme von `umsetzung-auto`: eine neue Datei, rund 80 Zeilen, fünf Tests.

## Nicht-Ziele

- Keine Änderung an bestehenden Dateien, insbesondere nicht an `role-split/kette/`.
- Kein Markdown-Parser aus einer Bibliothek; nur Standardbibliothek.
- Keine Auswertung von Tabellen, Links oder Listen.

## Schreibbereich

- `experiments/abnahme_k10/`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts – das Werkzeug liest nur die übergebene Datei und schreibt auf stdout/stderr.
- **Technische Sperre für Tests:** Tests schreiben ihre Eingabedateien nur in `tempfile.TemporaryDirectory()`.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `experiments/abnahme_k10/mdstat.py` | von Hand: `python3 experiments/abnahme_k10/mdstat.py <datei> [--json]` | T4, T5 |
| `experiments/abnahme_k10/mdstat.py` | als Modul importiert (`zaehle`) | T1–T3 |

## Quellen

- `docs/projekt_management/_vorlage_handover.md` – Gliederung des Handovers

## Anforderungen

### A1: Funktion `zaehle(text: str) -> dict`
- **Anforderung:** Gibt ein Dict mit genau den Schlüsseln `zeilen`, `woerter`, `ueberschriften`, `codebloecke` (alle `int`) zurück.
  - `zeilen` = Anzahl Zeilen laut `text.splitlines()`.
  - `woerter` = Anzahl der durch Leerraum getrennten Teile (`str.split()`) über alle Zeilen **außerhalb** von Codeblöcken; die Zaun-Zeilen selbst zählen nicht.
  - `codebloecke` = Anzahl abgeschlossener Codeblöcke. Ein Codeblock beginnt mit einer Zeile, die (nach `lstrip()`) mit drei Backticks beginnt, und endet mit der nächsten solchen Zeile. Ein nicht geschlossener Block am Dateiende zählt nicht als Codeblock, seine Zeilen gelten aber als Code (keine Wörter, keine Überschriften).
  - `ueberschriften` = Zeilen außerhalb von Codeblöcken, die dem Muster `^#{1,6} ` entsprechen (1–6 Rauten, dann ein Leerzeichen).
- **Stelle:** `experiments/abnahme_k10/mdstat.py`, `def zaehle`
- **Akzeptanz:** T1–T3.

### A2: Kommandozeile
- **Anforderung:** `python3 mdstat.py <datei>` gibt vier Zeilen aus, genau in diesem Format und dieser Reihenfolge:
  `zeilen: <n>`, `woerter: <n>`, `ueberschriften: <n>`, `codebloecke: <n>`; Exit 0.
  Mit `--json` stattdessen eine Zeile JSON mit denselben vier Schlüsseln; Exit 0.
  Die Datei wird als UTF-8 gelesen.
- **Stelle:** `experiments/abnahme_k10/mdstat.py`, `def main(argv=None) -> int`, Aufruf über `if __name__ == "__main__": sys.exit(main())`.
- **Akzeptanz:** T4.

### A3: Fehlende Datei
- **Anforderung:** Existiert `<datei>` nicht, schreibt das Werkzeug `Datei nicht gefunden: <datei>` auf stderr, nichts auf stdout, Exit 2.
- **Stelle:** `def main`
- **Akzeptanz:** T5.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Gegenstelle antwortet nicht oder schweigt | n. a. (keine Gegenstelle) | – | – |
| A1 | Eingabe leer | nichts | alle vier Werte 0 | T1 |
| A1 | nicht geschlossener Codeblock | nichts | zählt nicht als Block, Inhalt nicht als Wörter/Überschriften | T3 |
| A2 | Ziel existiert schon | n. a. (schreibt keine Datei) | – | – |
| A2 | Schalter kombiniert | n. a. (nur `--json`) | – | – |
| A3 | Datei fehlt | nichts | stderr-Meldung, stdout leer, Exit 2 | T5 |
| A1–A3 | Absturz mitten im Lauf | nichts (nur Lesen) | – | – |

## Testplan

Alle Tests werden als `tests/test_abnahme_k10.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.
Neue Funktionen im Test **in der Methode** importieren (z. B. über `runpy.run_path` oder `importlib` mit dem Pfad `experiments/abnahme_k10/mdstat.py`), nicht am Dateianfang.

### T1: Leerer Text
- **Prüft:** A1, Fehlerpfad „Eingabe leer“
- **Aufbau:** `zaehle("")`
- **Erwartung:** `{"zeilen": 0, "woerter": 0, "ueberschriften": 0, "codebloecke": 0}`
- **Warum misst der Test das Richtige?** Fehlt ein Schlüssel oder ist ein Wert ≠ 0, schlägt der Vergleich mit dem ganzen Dict fehl.
- **Gegenprobe:** ohne `mdstat.py` rot (Datei fehlt).

### T2: Überschriften und Wörter außerhalb von Code
- **Prüft:** A1
- **Aufbau:** `zaehle("# Titel\nEin kurzer Satz hier.\n##Keine\n###### Tief\n\n")`
- **Erwartung:** `{"zeilen": 5, "woerter": 9, "ueberschriften": 2, "codebloecke": 0}`. Wörter: `#`, `Titel` (2) + Satz (4) + `##Keine` (1) + `######`, `Tief` (2) = 9; Rauten zählen als Wort, weil `str.split()` sie nicht abtrennt.
- **Warum misst der Test das Richtige?** `##Keine` (ohne Leerzeichen) darf nicht als Überschrift zählen; ein zu großzügiges Muster macht `ueberschriften` 3.
- **Gegenprobe:** ohne `mdstat.py` rot.

### T3: Codeblöcke
- **Prüft:** A1, Fehlerpfad „nicht geschlossener Codeblock“
- **Aufbau:** Im Test `ZAUN = chr(96) * 3` (drei Backticks), dann `zaehle(f"Text davor\n{ZAUN}\n# kein Titel\nx = 1\n{ZAUN}\n  {ZAUN}python\n# auch kein Titel\n")` – der zweite, eingerückte Zaun öffnet einen Block, der nie geschlossen wird.
- **Erwartung:** `{"zeilen": 7, "woerter": 2, "ueberschriften": 0, "codebloecke": 1}`.
- **Warum misst der Test das Richtige?** Zählt der Code Überschriften oder Wörter im Codeblock oder den offenen Block mit, weicht mindestens ein Wert ab.
- **Gegenprobe:** ohne `mdstat.py` rot.

### T4: Kommandozeile Text und JSON
- **Prüft:** A2
- **Aufbau:** temporäre Datei (UTF-8) mit `"# Titel\nEin kurzer Satz über Größe.\n##Keine\n###### Tief\n\n"` (erwartet: zeilen 5, woerter 10, ueberschriften 2, codebloecke 0), Aufruf mit `subprocess.run([sys.executable, <pfad zu mdstat.py>, <datei>])` und einmal mit `--json`.
- **Erwartung:** Exit 0; Textausgabe genau vier Zeilen in der Reihenfolge aus A2 mit den Werten aus `zaehle`; JSON-Ausgabe lässt sich mit `json.loads` lesen und ist gleich dem Ergebnis von `zaehle` für denselben Text.
- **Warum misst der Test das Richtige?** Startet wie im Betrieb über die Kommandozeile; falsches Format, falsche Reihenfolge oder falsches Encoding fällt auf.
- **Gegenprobe:** ohne `mdstat.py` rot.

### T5: Fehlende Datei
- **Prüft:** A3
- **Aufbau:** Aufruf über `subprocess.run` mit einem Pfad im temporären Verzeichnis, der nicht existiert.
- **Erwartung:** Exit 2; stderr enthält `Datei nicht gefunden: ` und den Pfad; stdout ist leer.
- **Warum misst der Test das Richtige?** Ein Traceback (Exit 1) oder eine Ausgabe auf stdout lässt den Test scheitern.
- **Gegenprobe:** ohne `mdstat.py` rot.

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
