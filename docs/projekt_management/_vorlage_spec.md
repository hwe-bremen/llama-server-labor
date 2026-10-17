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

### T1: <Titel>
- **Prüft:** A1, Fehlerpfad „…"
- **Aufbau:** <Testserver, temporäres Verzeichnis, Umgebungsvariablen>
- **Erwartung:** <prüfbare Bedingung: Exit-Code, Datei existiert, Dauer ≥ x s …>
- **Warum misst der Test das Richtige?** <ein Satz: woran würde der Test scheitern, wenn die Anforderung NICHT erfüllt ist?>

## Offene Fragen

- <… oder „Keine">

## Abweichende Meinung

- <… oder „Keine">
