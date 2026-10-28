# Handover: lauf_status

- **Spec:** `docs/projekt_management/spec_20261028_lauf_status.md`
- **Datum:** 2026-10-28
- **Modell / Werkzeug:** Qwen3.6-35B, unbeaufsichtigt (Nachtlauf)
- **Rücksetzpunkt:** c9469ed

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| C1: Größenprüfung | erfüllt | `automatik.py`, Funktion `groesse()` |
| C2: `lauf(kurztitel) -> int` | erfüllt | `automatik.py`, Funktion `lauf()` |
| C3: `stand(kurztitel) -> dict` | erfüllt | `automatik.py`, Funktion `stand()` |
| C4: `status(kurztitel) -> int` | erfüllt | `automatik.py`, Funktion `status()` |
| C5: Subparser `lauf`/`status` in `kette.py` | erfüllt | `kette.py`, `main()` |

## Geänderte und neue Dateien

- `role-split/kette/automatik.py` – neu; enthält `groesse()`, `stand()`, `status()`, `lauf()` nach Spec C1–C4
- `role-split/kette/kette.py` – zwei Subparser (`lauf`, `status`) und Weiterleitung in `main()` ergänzt (C5)

## Abweichungen von der Spec

- Keine. Alle Anforderungen der Spec umgesetzt.

## Annahmen

- Keine.

## Nachbesserung 1

Zwei Fehler in der ursprünglichen Umsetzung von `automatik.py` korrigiert:

1. **C3 – Review-Wert `UNVOLLSTÄNDIG`:** `stand()` suchte nach `**UNVOLLSTAENDIG**` (ohne Umlaut). `review-auto` schreibt `**UNVOLLSTÄNDIG**` mit Ä. Geändert auf `**UNVOLLSTÄNDIG**` (Zeile 65).
2. **C4 – Zeile `Spec:`:** Dort stand der ganze Pfad. Geändert auf `Path(s['spec']).name` für den Dateinamen (Zeile 122).

## Getestet (mit echter Ausgabe)

**T1: lauf – ohne Commit „Spec <kt>“ kein Start** – bestanden

```
$ python3 -m unittest -v tests/test_lauf_status.py
test_t8_main_lauf_und_status (tests.test_lauf_status.Einstieg.test_t8_main_lauf_und_status)
T8: main – lauf und status über kette.py ... ok
test_t4_lauf_ok_bis_halt (tests.test_lauf_status.LaufAblauf.test_t4_lauf_ok_bis_halt)
T4: lauf – Umsetzung und Review grün, Halt an Hawes Entscheidung ... ok
test_t5_lauf_umsetzung_rot (tests.test_lauf_status.LaufAblauf.test_t5_lauf_umsetzung_rot)
T5: lauf – Umsetzung nicht in Ordnung, kein Review ... ok
test_t6_lauf_review_nicht_pass (tests.test_lauf_status.LaufAblauf.test_t6_lauf_review_nicht_pass)
T6: lauf – Review nicht PASS ergibt Exit 1 ... ok
test_t1_lauf_ohne_spec_commit (tests.test_lauf_status.LaufVorab.test_t1_lauf_ohne_spec_commit)
T1: lauf – ohne Commit „Spec <kt>“ kein Start ... ok
test_t2_lauf_ohne_vorgabe_tests (tests.test_lauf_status.LaufVorab.test_t2_lauf_ohne_vorgabe_tests)
T2: lauf – ohne Abschnitt Vorgabe-Tests kein Start ... ok
test_t3_lauf_zu_gross (tests.test_lauf_status.LaufVorab.test_t3_lauf_zu_gross)
T3: lauf – Größenprüfung hält bei Überschreitung, an der Schwelle läuft es ... ok
test_t7_status_naechster_schritt (tests.test_lauf_status.Status.test_t7_status_naechster_schritt)
T7: status – Stand und nächster Schritt aus den Dateien ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.524s

OK
```

**T2: lauf – ohne Abschnitt Vorgabe-Tests kein Start** – bestanden

**T3: lauf – Größenprüfung hält bei Überschreitung, an der Schwelle läuft es** – bestanden

**T4: lauf – Umsetzung und Review grün, Halt an Hawes Entscheidung** – bestanden

**T5: lauf – Umsetzung nicht in Ordnung, kein Review** – bestanden

**T6: lauf – Review nicht PASS ergibt Exit 1** – bestanden

**T7: status – Stand und nächster Schritt aus den Dateien** – bestanden

**T8: main – lauf und status über kette.py** – bestanden

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe lauf_status --commit <rücksetzpunkt>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt.

## Hawe muss ausführen

- `python3 role-split/kette/kette.py gegenprobe lauf_status --commit c9469ed`
- `git add role-split/kette/automatik.py role-split/kette/kette.py && git commit -m "K11b lauf_status"`

## Nicht getestet

- Nichts.

## Offene Punkte / bekannte Schwächen

- Keine.
