# Handover: lauf_spec_pruefen

- **Spec:** `docs/projekt_management/lauf_spec_pruefen/spec_20261106_lauf_spec_pruefen.md`
- **Datum:** 2026-11-06
- **Modell / Werkzeug:** Qwen3.6-35B, unbeaufsichtigt (Nachtlauf)
- **Rücksetzpunkt:** 2b63547

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1: lauf ruft spec-pruefen vor der Umsetzung | erfüllt | `role-split/kette/automatik.py`, `lauf`, Zeilen 159–165 |
| A2: Größen-Halt entfällt | erfüllt | `role-split/kette/automatik.py`, Modul-Docstring (Zeilen 1–5), Konstanten (entfernt), Docstring `lauf` (Zeile 136), Größenblock ersetzt (Zeilen 159–165) |

## Geänderte und neue Dateien

- `role-split/kette/automatik.py` – geändert: Modul-Docstring (K12a2, groesse nur zählt), GROESSE_DATEIEN/GROESSE_ANFORDERUNGEN/GROESSE_TESTS entfernt, Docstring `lauf` aktualisiert, Größenblock durch `spec_pruefen.spec_pruefen(kurztitel)` ersetzt (lokaler Import im Funktionsrumpf). `groesse()` unverändert. `stand()`, `status()` unverändert.

## Abweichungen von der Spec

- Keine. Alle 4 Änderungsstellen aus der Spec (Modul-Docstring, Konstanten, Docstring `lauf`, Größenblock) wurden exakt umgesetzt.
- Die Vorgabe-Tests `tests/test_lauf_spec_pruefen.py` wurden nicht geändert (wie gefordert).

## Annahmen

- Keine.

## Getestet (mit echter Ausgabe)

**T1: Befunde halten vor der Umsetzung** – bestanden
**T2: Größe nur noch Hinweis** – bestanden
**T3: Ausgabe wie der Einzelbefehl** – bestanden
**T4: Vorbedingungen und Exit 2** – bestanden
**T5: Standardwerte und echter Aufruf** – bestanden
**T6: Trockenlauf am echten Bestand** – bestanden

```
$ python3 -m unittest -v tests/test_lauf_spec_pruefen.py
test_t3_ausgabe_wie_einzelbefehl (tests.test_lauf_spec_pruefen.Ablauf.test_t3_ausgabe_wie_einzelbefehl)
T3: lauf – gültige Spec: Ausgabe wie spec-pruefen, danach Umsetzung und Review ... ok
test_t4_vorbedingungen_und_exit_2 (tests.test_lauf_spec_pruefen.Ablauf.test_t4_vorbedingungen_und_exit_2)
T4: lauf – Vorbedingungen vor der Spec-Prüfung, Exit 2 der Spec-Prüfung durchgereicht ... ok
test_t6_trockenlauf_echter_bestand (tests.test_lauf_spec_pruefen.Bestand.test_t6_trockenlauf_echter_bestand)
T6: Trockenlauf am echten Bestand – alte Spec hält, saubere Spec läuft, nichts geschrieben ... ok
test_t5_standardwerte_und_echter_aufruf (tests.test_lauf_spec_pruefen.Einstieg.test_t5_standardwerte_und_echter_aufruf)
T5: Standardwerte – alte Schwellen weg, groesse bleibt, lauf und spec-pruefen über kette.main in frischem Prozess ... ok
test_t1_befunde_halten_vor_der_umsetzung (tests.test_lauf_spec_pruefen.Halt.test_t1_befunde_halten_vor_der_umsetzung)
T1: lauf – Befunde aus spec-pruefen halten mit Exit 3 vor der Umsetzung ... ok
test_t2_groesse_nur_hinweis (tests.test_lauf_spec_pruefen.Halt.test_t2_groesse_nur_hinweis)
T2: lauf – Größe über den alten Schwellen und über R59 hält nicht mehr an ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.460s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe lauf_spec_pruefen --commit 2b63547
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt.

## Hawe muss ausführen

- `python3 role-split/kette/kette.py gegenprobe lauf_spec_pruefen --commit 2b63547`
- `python3 scripts/alle_tests.py` (alle Tests grün, Altlast `test_scout_kw_doppelversand.py` bleibt rot)
- RUNBOOK (Abschnitt `lauf`, Exit 3) anpassen – nicht Teil des Schreibbereichs, wird von Claude nach dem Lauf erledigt.

## Nicht getestet

- Nichts. Alle 6 Tests laufen grün.

## Offene Punkte / bekannte Schwächen

- Keine.
