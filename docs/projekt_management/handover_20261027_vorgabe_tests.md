# Handover: vorgabe_tests

- **Spec:** `docs/projekt_management/spec_20261027_vorgabe_tests.md`
- **Datum:** 2026-10-28
- **Modell / Werkzeug:** Claude (Referenzlösung per `tmp/k11a/einbau_k11a.py`); Erstlauf des 35B (27.10., 22:10) verworfen, siehe Abweichungen
- **Rücksetzpunkt:** 39ce6aa

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1 | erfüllt | `role-split/kette/kette.py`, `_vorgabe_tests` |
| A2 | erfüllt | `role-split/kette/kette.py`, `tests_pruefen` |
| A3 | erfüllt | `role-split/kette/kette.py`, `umsetzung_auto` (Vorab-Prüfung nach A2.4, Prüfung (b)) |
| A4 | erfüllt | `role-split/kette/kette.py`, `_umsetzung_prompt` |
| A5 | erfüllt | `role-split/kette/kette.py`, `main` und Moduldocstring |

## Geänderte und neue Dateien

- `role-split/kette/kette.py` – geändert – Block „tests-pruefen (K11a)“, drei Stellen in `umsetzung_auto`/`_umsetzung_prompt`, Subparser, Docstring

## Abweichungen von der Spec

- Keine im Code. Ablauf: Der Erstlauf des 35B hat (1) `tests/test_vorgabe_tests.py` neu geschrieben, obwohl die Spec das unter Nicht-Ziele ausschließt, (2) `tests_pruefen` anders verstanden (führt Tests aus und verlangt grün statt rot vorab, keine Abdeckungs-/Ladeprüfung), (3) die Prüfung in jeden `umsetzung-auto`-Lauf eingebaut – auch ohne `## Vorgabe-Tests` –, wodurch 22 von 37 bestehenden Tests rot wurden, (4) A3-Verstoß und A4-Prompt nicht umgesetzt. Gegen die echten Vorgabe-Tests: 1/8 grün. Deshalb `git restore` beider Dateien und Einbau der Referenz.
- Beim Erstlauf galt noch der alte Prompt („Die Tests der Spec schreibst du …“) – Widerspruch zur Spec. Der Befund (1) ist daher nur ein halber Beleg; die eigentliche Messung folgt mit K11b unter dem neuen Prompt.

## Annahmen

- Keine.

## Getestet (mit echter Ausgabe)

**T1: tests-pruefen – alle Vorgabe-Tests vorhanden und rot vorab** – bestanden
**T2: tests-pruefen – Test-ID ohne Methode** – bestanden
**T3: tests-pruefen – Test ohne Umsetzung schon grün** – bestanden
**T4: tests-pruefen – Testskript lädt nicht** – bestanden
**T5: tests-pruefen – Testdatei oder Spec fehlt** – bestanden
**T6: umsetzung-auto – Erstlauf startet nur mit bestandener Testprüfung** – bestanden
**T7: umsetzung-auto – Änderung an Vorgabe-Tests ist ein Verstoß** – bestanden
**T8: umsetzung-auto – Nacharbeit prüft nicht auf rot vorab, Prompt nennt Vorgabe** – bestanden

```
$ python3 -m unittest -v tests/test_vorgabe_tests.py
test_t1_tests_pruefen_rot_vorab_ok (tests.test_vorgabe_tests.TestsPruefen)
T1: tests-pruefen – alle Vorgabe-Tests vorhanden und rot vorab ... ok
test_t2_tests_pruefen_test_fehlt (tests.test_vorgabe_tests.TestsPruefen)
T2: tests-pruefen – Test-ID ohne Methode ... ok
test_t3_tests_pruefen_gruen_ohne_umsetzung (tests.test_vorgabe_tests.TestsPruefen)
T3: tests-pruefen – Test ohne Umsetzung schon gruen ... ok
test_t4_tests_pruefen_laedt_nicht (tests.test_vorgabe_tests.TestsPruefen)
T4: tests-pruefen – Testskript laedt nicht ... ok
test_t5_tests_pruefen_voraussetzung_fehlt (tests.test_vorgabe_tests.TestsPruefen)
T5: tests-pruefen – Testdatei oder Spec fehlt ... ok
test_t6_erstlauf_nur_mit_rot_vorab (tests.test_vorgabe_tests.UmsetzungMitVorgabe)
T6: umsetzung-auto – Erstlauf startet nur mit bestandener Testpruefung ... ok
test_t7_vorgabe_tests_geaendert (tests.test_vorgabe_tests.UmsetzungMitVorgabe)
T7: umsetzung-auto – Aenderung an Vorgabe-Tests ist ein Verstoss ... ok
test_t8_nacharbeit_ohne_rot_vorab (tests.test_vorgabe_tests.UmsetzungMitVorgabe)
T8: umsetzung-auto – Nacharbeit prueft nicht auf rot vorab, Prompt nennt Vorgabe ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.730s

OK
```

Zusätzlich grün: `tests/test_umsetzung_auto.py`, `tests/test_k10b_nachtraege.py`, `role-split/kette/test_kette.py` (zusammen 85 Tests, Python 3.10 in Claudes Kopie).

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

Läuft in `kette.py pruefen vorgabe_tests` mit. In Claudes Kopie mit dem alten `kette.py`: 8/8 rot.

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt.

## Hawe muss ausführen

- Nichts außer den Befehlen aus dem Chat (restore, Einbau, pruefen, commit).

## Nicht getestet

- Fehlerpfad „Testskript hängt“ (`ZEIT`) – nur über die vorhandene Timeout-Logik von `tests_laufen`.

## Offene Punkte / bekannte Schwächen

- `_vorlage_spec.md` und RUNBOOK kennen `## Vorgabe-Tests` noch nicht (Claude ergänzt getrennt).
