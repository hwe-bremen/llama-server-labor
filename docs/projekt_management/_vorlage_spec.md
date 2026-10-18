# Spec: <kurztitel>

- **Datum:** <JJJJ-MM-TT>
- **Modell:** <Modellname aus dem System-Prompt>
- **Betroffene Dateien:** <nur Dateien, die du gelesen hast>

## Ziel

<1–3 Sätze>

## Nicht-Ziele

- <…>

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** <Mail, Netzwerk, echte Daten/DB, Schlüsselbund, launchd … oder „nichts">
- **Technische Sperre für Tests:** <z. B. Variable, die echten Versand erst erlaubt; temporäres Datenverzeichnis. Eine Regel im Prompt reicht nicht.>

## Einstiegspunkte

Welche geänderten Dateien werden **wie** gestartet (Pipeline, launchd, von Hand, als Modul importiert)?
Für jeden Einstiegspunkt gibt es einen Test, der ihn so startet wie im Betrieb (ohne Außenwirkung, z. B.
`runpy.run_path(…, run_name="kein_main")` für Imports, Ersatzskripte für Pipelines).
Anlass 18.10.: Ein relativer Import ließ den Scout bei jedem Lauf abstürzen; alle Funktionstests waren grün.

| Datei | Wie gestartet | Test |
|---|---|---|
| `pfad/skript.py` | `python3 pfad/skript.py` aus `run_x.sh` | T… |

## Anforderungen

### A1: <Titel>
- **Anforderung:** <prüfbar formuliert>
- **Stelle:** <Datei, Funktion>
- **Akzeptanz:** <beobachtbares Ergebnis>

## Fehlerpfade

Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Gegenstelle antwortet nicht oder schweigt (Netz, Server, Router) | | | T… |
| A1 | Eingabe leer oder ungültig (Variable, Datei, Argument) | | | |
| A1 | Ziel existiert schon (Datei, Eintrag) — wird etwas überschrieben? | | | |
| A1 | Schalter kombiniert (z. B. Trockenlauf + anderer Modus) | | | |
| A1 | Lauf ohne Testschalter / gegen echte Daten | | | |
| A1 | Absturz mitten im Lauf | | | |

## Testplan

Alle Tests werden als `tests/test_<kurztitel>.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.
Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.

### T1: <Titel>
- **Prüft:** A1, Fehlerpfad „…"
- **Aufbau:** <Testserver, temporäres Verzeichnis, Umgebungsvariablen>
- **Erwartung:** <prüfbare Bedingung: Exit-Code, Datei existiert, Dauer ≥ x s …>
- **Warum misst der Test das Richtige?** <ein Satz: woran würde der Test scheitern, wenn die Anforderung NICHT erfüllt ist?>
- **Gegenprobe:** <welche Datei bzw. welche Codezeile muss im alten Zustand sein, damit dieser Test rot wird? „keine" = Test prüft Bestehendes, dann begründen>

## Offene Fragen

- <… oder „Keine">

## Abweichende Meinung

- <… oder „Keine">
