# Spec: einsortieren

- **Datum:** 2026-10-28
- **Modell:** Claude (Spec, Vorgabe-Tests, Referenzlösung); Umsetzung durch den lokalen Umsetzer per `kette.py lauf`
- **Betroffene Dateien:** neu `role-split/kette/einsortieren.py`; in `role-split/kette/kette.py` eine Zeile in `anforderung` und der Befehl `einsortieren` in `main`

## Ziel

Zweiter Teil der Ablage je Projekt (Ziel 3): Eine **neue** Kette bekommt ihren Ordner `docs/projekt_management/<kurztitel>/` beim ersten Schritt (`anforderung --aufgabe`), alles Weitere landet dank K13a automatisch dort. Der neue Befehl `kette.py einsortieren <kurztitel>` bzw. `--alle` verschiebt die flach liegenden Dateien bestehender Ketten in ihre Ordner – nichts wird überschrieben oder gelöscht.

## Nicht-Ziele

- **`tests/test_einsortieren.py` ist Vorgabe und wird nicht geändert – keine Zeile.** Auch `role-split/kette/test_kette.py` und `role-split/test_role_proxy.py` nicht (dort hat Claude zwei bzw. zwei Erwartungen auf den Ordner umgestellt; sie liegen außerhalb des Schreibbereichs).
- Kein `git mv`, kein Commit: `einsortieren` verschiebt nur im Dateisystem und nennt am Ende den git-Befehl.
- Dateien ohne passende Kette (Proben, Evals, `review_*`, Dateien ohne Datum) und Vorlagen `_vorlage_*` bleiben flach.
- Keine Änderung an `automatik.py`, Prompts, Doku.

## Schreibbereich

- `role-split/kette/einsortieren.py`
- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_einsortieren.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts. `einsortieren` verschiebt Dateien innerhalb von `docs/projekt_management/`.
- **Technische Sperre für Tests:** Jeder Test arbeitet in `tempfile.TemporaryDirectory()` mit umgebogenem `kette.ROOT`/`kette.PM`; kein Test berührt das echte `docs/projekt_management/`.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `kette.py einsortieren <kt>` / `--alle` (über `main`) | T4, T6 |
| `role-split/kette/einsortieren.py` | als Modul (`zuordnen`, `ketten`, `einsortieren`), importiert `kette` | T2, T3, T5–T7 |
| `role-split/kette/kette.py` | als Modul (`anforderung`) | T1 |

## Quellen

- `role-split/kette/kette.py` def anforderung – Ziel der Anforderung, Ordner anlegen (G1)
- `role-split/kette/kette.py` def ablage – Ordner der Kette (G1, G4)
- `role-split/kette/kette.py` def datei_suchen – findet Dateien im Ordner (G4)
- `role-split/kette/kette.py` def main – Subparser, Weiterleitung wie bei lauf/status (G5)

## Anforderungen

### G1: Neue Kette bekommt ihren Ordner
- **Anforderung:** In `anforderung` bei `--aufgabe`: Ziel ist immer `PM / kurztitel / anforderung_<d>_<kt>.md`; der Ordner `PM / kurztitel` wird vorher angelegt (`mkdir(parents=True, exist_ok=True)`). `--antwort` bleibt unverändert (findet die Datei über `datei_suchen`).
- **Stelle:** `def anforderung` (die zwei Zeilen `abl = ablage(kurztitel)` / `abl.mkdir(...)`)
- **Akzeptanz:** T1.

### G2: Zuordnung einer flachen Datei
- **Anforderung:** In `einsortieren.py`:
  - `TYPEN = ("spec", "spec_paket", "anforderung", "quellen", "handover", "pruefung", "review_paket", "verdict", "gesamt", "umsetzung", "nacharbeit")`.
  - `zuordnen(name, kurztitel_liste) -> str | None`: Der Name muss `<typ>_<JJJJMMTT>_<rest>.md` sein (Typ aus `TYPEN`, genau acht Ziffern). Passend sind Kurztitel `kt` mit `rest == kt` oder `rest` beginnt mit `kt + "_"`. Bei mehreren gewinnt der **längste**; keiner → `None`.
- **Akzeptanz:** T2.

### G3: Liste der Ketten
- **Anforderung:** `ketten() -> list[str]`: sortierte Kurztitel aller **flachen** Dateien `spec_<JJJJMMTT>_<kt>.md` oder `anforderung_<JJJJMMTT>_<kt>.md` (`kt` aus `[a-z0-9_]+`) in `kette.PM`.
- **Akzeptanz:** T4.

### G4: `einsortieren(kurztitel | None) -> int`
- **Anforderung:**
  1. Kurztitel (wenn angegeben) nicht `[a-z0-9_]+` → Exit 2.
  2. Ketten = `ketten()`, bei angegebenem Kurztitel zusätzlich dieser (auch wenn seine Spec schon im Ordner liegt).
  3. Für jede flache `*.md` in `kette.PM` (sortiert): `zuordnen`; keine Kette oder (bei angegebenem Kurztitel) eine andere → überspringen. Ziel `kette.PM / kt / name`: existiert es → Zeile `  ZIEL BELEGT <name> -> <kt>/ (nichts verschoben)`, nichts verschieben; sonst Ordner anlegen, Datei verschieben (`rename`), Zeile `  verschoben  <name> -> <kt>/` (zwei Leerzeichen nach „verschoben“).
  4. Abschluss nach einer Leerzeile: `<n> Datei(en) in <m> Ordner verschoben, <b> Ziel(e) belegt, <f> Datei(en) bleiben flach.` – `m` = Zahl der Ordner, in die verschoben wurde; `f` = flache `*.md` ohne `_vorlage_*` danach. Wurde etwas verschoben, eine Zeile mit dem git-Befehl `git add -A docs/projekt_management && git commit -m "Ablage: einsortiert"`.
  5. Exit 1, wenn ein Ziel belegt war, sonst 0.
- **Akzeptanz:** T3, T4, T5, T6, T7.

### G5: Befehl `einsortieren`
- **Anforderung:** Subparser `einsortieren` mit sich ausschließender Pflichtgruppe: Positionsargument `kurztitel` (`nargs="?"`) **oder** `--alle`. `main` ruft `einsortieren.einsortieren(None if args.alle else args.kurztitel)` – Import in der Verzweigung wie bei `lauf`/`status`.
- **Akzeptanz:** T4, T6.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| G4 | Ziel im Ordner existiert schon | andere Dateien sind evtl. schon verschoben | `ZIEL BELEGT`, Exit 1, beide Dateien unverändert | T5 |
| G4 | zweiter Lauf | alles verschoben | `0 Datei(en) …`, Exit 0 | T3 |
| G4 | Kurztitel ungültig | nichts | Exit 2 | T6 |
| G5 | weder Kurztitel noch `--alle`, oder beides | nichts | argparse-Fehler (Exit 2) | T6 |
| G2 | Kurztitel ist Präfix eines anderen | – | längster gewinnt; `kx` passt nicht zu `k` | T2 |
| G2 | Datei ohne Datum, `review_*`, Vorlage, Probe | – | bleibt flach | T2, T4 |
| G4 | Abbruch mitten im Verschieben | einzelne Dateien verschoben | erneuter Aufruf macht weiter (jede Datei einzeln) | – (folgt aus T3: zweiter Lauf) |

## Testplan

Die Tests stehen in `tests/test_einsortieren.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. Jede Methode ist vorab rot (7/7). Mutationsprüfung der Referenz: 14 von 16 gefangen, die zwei übrigen sind gleichwertig (Reihenfolge der Typen im Regex, `--alle` ohne Kurztitel).

### T1: anforderung – neue Kette bekommt ihren Ordner
- **Prüft:** G1
- **Aufbau:** Temp-Verzeichnis ohne Ordner; `anforderung("k", aufgabe)`, dann `--antwort`.
- **Erwartung:** Datei unter `PM/k/`, nicht flach; Antwort dort angehängt; `ablage("k")` ist der Ordner.
- **Warum misst der Test das Richtige?** Neue Ketten sollen ohne Handarbeit im Ordner landen.
- **Gegenprobe:** alter Stand → rot.

### T2: zuordnen – Datei zur Kette, längster Kurztitel gewinnt
- **Prüft:** G2
- **Aufbau:** Namen gegen `["scout_mail", "scout_mail_trockenlauf", "k"]`.
- **Erwartung:** wie in G2; `kx`, Vorlage, Datei ohne Datum (auch wenn ihr Kurztitel bekannt ist), `review_*`, Probe → `None`.
- **Warum misst der Test das Richtige?** Die echte Ablage hat Kurztitel, die Präfix eines anderen sind.
- **Gegenprobe:** alter Stand → rot.

### T3: einsortieren <kt> – nur die Dateien dieser Kette, Vorlagen und fremde bleiben
- **Prüft:** G4
- **Aufbau:** Spec, Handover, Verdikt von `k`, Spec von `andere`, eine Vorlage; zweimal `einsortieren("k")`.
- **Erwartung:** drei Dateien in `k/`, `andere` und Vorlage flach, kein Ordner `andere`; Zeile `verschoben  spec_… -> k/`, `3 Datei(en) in 1 Ordner verschoben`; zweiter Lauf `0 Datei(en) in 0 Ordner verschoben`, Exit 0.
- **Warum misst der Test das Richtige?** Ein Kurztitel darf nur seine Kette anfassen; der Befehl ist wiederholbar.
- **Gegenprobe:** alter Stand → rot.

### T4: einsortieren --alle über kette.py – alle Ketten mit Spec oder Anforderung
- **Prüft:** G3, G4, G5
- **Aufbau:** Kette `a` mit Spec, Kette `b` nur mit Anforderung, eine Probe-Datei, eine Vorlage; `main(["einsortieren", "--alle"])`.
- **Erwartung:** Exit 0; Dateien in `a/` und `b/`; Probe flach; Abschlusszeile genau `4 Datei(en) in 2 Ordner verschoben, 0 Ziel(e) belegt, 1 Datei(en) bleiben flach.`; `datei_suchen` findet die Spec im Ordner.
- **Warum misst der Test das Richtige?** Der echte Migrationsweg über die Befehlszeile.
- **Gegenprobe:** alter Stand → rot.

### T5: einsortieren – vorhandene Datei im Ordner wird nicht überschrieben
- **Prüft:** G4.3, G4.5
- **Aufbau:** Handover flach und gleichnamig schon im Ordner; Spec nur flach.
- **Erwartung:** Exit 1, `ZIEL BELEGT handover_… -> k/`, Ordner-Datei unverändert, flache bleibt; Spec trotzdem verschoben.
- **Warum misst der Test das Richtige?** Datenverlust durch Überschreiben ist der teuerste Fehler dieser Kette.
- **Gegenprobe:** alter Stand → rot.

### T6: einsortieren – ungültiger Kurztitel, Aufruf ohne Kurztitel und ohne --alle
- **Prüft:** G4.1, G5
- **Aufbau:** `einsortieren("K-x")`; `main(["einsortieren"])`; `main(["einsortieren", "k", "--alle"])`.
- **Erwartung:** Exit 2; zweimal `SystemExit` (Code 2 beim ersten).
- **Warum misst der Test das Richtige?** Ohne Pflichtgruppe würde ein vergessener Kurztitel still alles einsortieren.
- **Gegenprobe:** alter Stand → rot.

### T7: einsortieren <kt> – Kette, deren Spec schon im Ordner liegt
- **Prüft:** G4.2
- **Aufbau:** Spec im Ordner `k/`, Prüfung flach; `einsortieren("k")`.
- **Erwartung:** Exit 0, Prüfung im Ordner; `datei_suchen("pruefung", "k")` findet sie.
- **Warum misst der Test das Richtige?** Typischer Mischfall nach K13a: neue Dateien im Ordner, Reste flach.
- **Gegenprobe:** alter Stand → rot.

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
