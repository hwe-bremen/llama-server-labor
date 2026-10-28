# Handover: vorgabe_nachtrag

- **Spec:** `docs/projekt_management/spec_20261028_vorgabe_nachtrag.md`
- **Datum:** 2026-10-28
- **Modell / Werkzeug:** Qwen3.6-35B-A3B, unbeaufsichtigter Nachtlauf
- **Rücksetzpunkt:** `404fefb`

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| B1: Bestand-Tests in `tests_pruefen` | erfüllt | `kette.py` Zeilen ~451-465 (neue Konstante + Funktion) und ~484-508 (Loop-Erweiterung) |
| B2: Bestand-Tests in `gegenprobe` | erfüllt | `kette.py` Zeilen ~418, ~434-445 (Bestand-Filter in `gruen` und `BESTAND`-Ausgabe) |
| B3: Nacharbeit mit offenen Vorgabe-Tests | erfüllt | `kette.py` Zeilen ~1903-1904 (Prüfung `testdatei in offen` vor `tests_pruefen`) |
| B4: Wirkungslose Ausnahme entfernen | erfüllt | `kette.py` Zeilen ~1972-1973 (List Comprehension Prüfung (b) bereinigt) |

## Geänderte und neue Dateien

- `role-split/kette/kette.py` – geändert; fünf gezielte Einfügungen/Änderungen (B1–B4), keine Umbenennungen, keine Neuformatierung

## Abweichungen von der Spec

- Keine. Alle fünf Anforderungen aus der Spec wurden exakt umgesetzt.

## Annahmen

- Bei B2 (gegenprobe) habe ich die Konvertierung von Methodennamen (z. B. `test_t2_bestand`) zu Test-IDs (z. B. `T2`) über einen regulären Ausdruck `test_(T2|…)(_|$)` realisiert, da `_bestand_ids` Test-IDs und nicht Methodennamen zurückgibt. Dies war nicht explizit in der Spec beschrieben, ergibt sich aber zwingend aus der Datenstruktur.

## Getestet (mit echter Ausgabe)

**T1: tests-pruefen – Bestand-Test grün ist in Ordnung; Spec ohne Test-ID ist Exit 2** – bestanden

**T2: tests-pruefen – Bestand-Test rot ist eine Abweichung; --timeout wird weitergereicht** – bestanden

**T3: gegenprobe – grüner Bestand-Test laut Spec ist keine Abweichung** – bestanden

**T4: umsetzung-auto – Nacharbeit startet nicht, solange die Vorgabe-Tests offene Änderungen haben** – bestanden

```
$ python3 -m unittest -v tests/test_vorgabe_nachtrag.py
test_t3_gegenprobe_bestand_gruen_zaehlt_nicht (tests.test_vorgabe_nachtrag.GegenprobeBestand.test_t3_gegenprobe_bestand_gruen_zaehlt_nicht)
T3: gegenprobe – gruener Bestand-Test laut Spec ist keine Abweichung ... ok
test_t4_nacharbeit_mit_offener_testdatei (tests.test_vorgabe_nachtrag.NacharbeitVorgabe.test_t4_nacharbeit_mit_offener_testdatei)
T4: umsetzung-auto – Nacharbeit startet nicht, solange die Vorgabe-Tests offene Aenderungen haben ... ok
test_t1_bestand_gruen_ok_und_spec_ohne_ids (tests.test_vorgabe_nachtrag.TestsPruefenBestand.test_t1_bestand_gruen_ok_und_spec_ohne_ids)
T1: tests-pruefen – Bestand-Test gruen ist in Ordnung; Spec ohne Test-ID ist Exit 2 ... ok
test_t2_bestand_rot_und_timeout_weitergereicht (tests.test_vorgabe_nachtrag.TestsPruefenBestand.test_t2_bestand_rot_und_timeout_weitergereicht)
T2: tests-pruefen – Bestand-Test rot ist eine Abweichung; --timeout wird weitergereicht ... ok

----------------------------------------------------------------------
Ran 4 tests in 1.126s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe vorgabe_nachtrag --commit 404fefb
<Ausgabe hier>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt.

## Hawe muss ausführen

- `python3 role-split/kette/kette.py gegenprobe vorgabe_nachtrag --commit 404fefb`
- `python3 role-split/kette/kette.py tests-pruefen vorgabe_nachtrag`
- Optional: `git diff 404fefb` zur visuellen Prüfung der 5 Änderungen

## Nicht getestet

- B4 (wirkungslose Ausnahme entfernen): Kein eigener Test in der Spec vorgesehen; kein beobachtbares Verhalten. `tests/test_vorgabe_tests.py` T7 bleibt grün (bestehend).

## Offene Punkte / bekannte Schwächen

- Keine.
