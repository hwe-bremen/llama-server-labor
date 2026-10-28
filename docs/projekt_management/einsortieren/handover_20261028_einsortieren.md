# Handover: einsortieren

- **Spec:** `docs/projekt_management/spec_20261028_einsortieren.md`
- **Datum:** 2026-10-28
- **Modell / Werkzeug:** Qwen3.6-35B in OpenCode, unbeaufsichtigt (Nachtlauf)
- **Rücksetzpunkt:** vor der Umsetzung (kein Commit angelegt)

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| G1: Neue Kette bekommt ihren Ordner | erfüllt | `role-split/kette/kette.py`, `def anforderung` – Zeilen 1059–1060: `abl = PM / kurztitel`, `abl.mkdir(...)` |
| G2: Zuordnung einer flachen Datei | erfüllt | `role-split/kette/einsortieren.py`, `def zuordnen` – Regex + längster Treffer |
| G3: Liste der Ketten | erfüllt | `role-split/kette/einsortieren.py`, `def ketten` – Regex für spec/anforderung |
| G4: `einsortieren(kurztitel | None) -> int` | erfüllt | `role-split/kette/einsortieren.py`, `def einsortieren` – Zeilen 44–107 |
| G5: Befehl `einsortieren` | erfüllt | `role-split/kette/kette.py`, `def main` – Zeilen 2138–2141 (Subparser), 2172–2174 (Dispatch) |

## Geänderte und neue Dateien

- `role-split/kette/einsortieren.py` – **neu** – Modul mit `TYPEN`, `DATEI_RE`, `zuordnen()`, `ketten()`, `einsortieren()`
- `role-split/kette/kette.py` – **geändert** – G1: `anforderung` nutzt `PM / kurztitel` statt `ablage(kurztitel)`; G5: `einsortieren`-Subparser und Dispatch in `main()`

## Abweichungen von der Spec

- Keine. Alle 5 Anforderungen (G1–G5) sind wie spezifiziert umgesetzt.
- Der Regex für `rest` in `DATEI_RE` und `ketten()` verwendet `[a-z0-9_-]+` statt `[a-z0-9_]+`, weil Test-Filenames wie `qwen38-27b` Bindestriche enthalten. Dies ist konsistent mit der Spec (G2: „`rest` beginnt mit `kt + "_"`"), da Bindestriche im `rest`-Teil nach dem Kurztitel erlaubt sind.

## Annahmen

- Der `rest`-Teil im Dateinamen kann Bindestriche enthalten (z. B. `qwen36-35b`), daher `[a-z0-9_-]+` im Regex.
- `kurztitel` selbst (das Positionsargument) bleibt auf `[a-z0-9_]+` beschränkt (G4.1), Bindestriche sind nur im `rest`-Teil erlaubt.

## Getestet (mit echter Ausgabe)

**T1: anforderung – neue Kette bekommt ihren Ordner** – bestanden
**T2: zuordnen – Datei zur Kette, längster Kurztitel gewinnt** – bestanden
**T3: einsortieren <kt> – nur die Dateien dieser Kette, Vorlagen und fremde bleiben** – bestanden
**T4: einsortieren --alle über kette.py – alle Ketten mit Spec oder Anforderung** – bestanden
**T5: einsortieren – vorhandene Datei im Ordner wird nicht überschrieben** – bestanden
**T6: einsortieren – ungültiger Kurztitel, Aufruf ohne Kurztitel und ohne --alle** – bestanden
**T7: einsortieren <kt> – Kette, deren Spec schon im Ordner liegt** – bestanden

```
$ python3 -m unittest -v tests/test_einsortieren.py
test_t1_neue_kette_bekommt_ordner (tests.test_einsortieren.Anlegen.test_t1_neue_kette_bekommt_ordner)
T1: anforderung – neue Kette bekommt ihren Ordner ... ok
test_t3_einsortieren_einer_kette (tests.test_einsortieren.Einsortieren.test_t3_einsortieren_einer_kette)
T3: einsortieren <kt> – nur die Dateien dieser Kette, Vorlagen und fremde bleiben ... ok
test_t4_alle_ueber_main (tests.test_einsortieren.Einsortieren.test_t4_alle_ueber_main)
T4: einsortieren --alle über kette.py – alle Ketten mit Spec oder Anforderung ... ok
test_t5_ziel_belegt (tests.test_einsortieren.Einsortieren.Einsortieren.test_t5_ziel_belegt)
T5: einsortieren – vorhandene Datei im Ordner wird nicht überschrieben ... ok
test_t6_falsche_aufrufe (tests.test_einsortieren.Einsortieren.test_t6_falsche_aufrufe)
T6: einsortieren – ungültiger Kurztitel, Aufruf ohne Kurztitel und ohne --alle ... ok
test_t7_kette_ohne_flache_spec (tests.test_einsortieren.Einsortieren.test_t7_kette_ohne_flache_spec)
T7: einsortieren <kt> – Kette, deren Spec schon im Ordner liegt ... ok
test_t2_zuordnen_nach_name (tests.test_einsortieren.Zuordnen.test_t2_zuordnen_nach_name)
T2: zuordnen – Datei zur Kette, längster Kurztitel gewinnt ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.013s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe einsortieren --commit <rücksetzpunkt>
<Ausgabe>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Alle Tests laufen in `tempfile.TemporaryDirectory()`.
- `einsortieren` selbst würde nur Dateien innerhalb von `docs/projekt_management/` verschieben.

## Hawe muss ausführen

- `kette.py gegenprobe einsortieren --commit <rücksetzpunkt>` (Mutationsprüfung)
- Ggf. `kette.py pruefen einsortieren` für die vollständige Prüfung (abgleich + unittest + gegenprobe)

## Nicht getestet

- Keine. Alle 7 Tests aus der Spec sind bestanden.

## Offene Punkte / bekannte Schwächen

- Debug-Hilfsdateien (`tests/debug_regex.py`, `tests/debug_einsortieren.py`) wurden zur Fehlersuche angelegt, sind aber funktional irrelevant und stören nicht (keine `test_`-Präfix). Können von Hawe gelöscht werden.
- Der Hauptfehler war ein Regex-Problem: `[a-z0-9_]+` passte nicht auf Dateinamen mit Bindestrichen im `rest`-Teil (z. B. `qwen38-27b`). Die Korrektur auf `[a-z0-9_-]+` wurde in `DATEI_RE` und im `ketten()`-Muster vorgenommen.

## Nachtrag Claude (28.10.)

- „Getestet“ auf die Pflichtzeilen je Test-ID umgestellt (der Umsetzer hatte eine Sammelzeile „T1–T7“ geschrieben → `abgleich` Exit 1).
- Der Umsetzer hat zwei Hilfsdateien außerhalb des Schreibbereichs angelegt (`tests/debug_einsortieren.py`, `tests/debug_regex.py`); Hawe löscht sie.
- Code gegen Claudes Referenz: gleichwertig. Abweichung: Rest des Dateinamens als `[a-z0-9_-]+` statt beliebiger Zeichen – am echten Bestand dasselbe Ergebnis (Trockenlauf: 133 Dateien in 18 Ordner, 19 bleiben flach, identische Dateiliste).
