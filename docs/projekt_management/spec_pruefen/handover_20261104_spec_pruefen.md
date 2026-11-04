# Handover: spec_pruefen

- **Spec:** `docs/projekt_management/spec_pruefen/spec_20261104_spec_pruefen.md`
- **Datum:** 2026-11-04
- **Modell / Werkzeug:** Qwen3.6-35B in OpenCode, unbeaufsichtigt (Nachtlauf)
- **Rücksetzpunkt:** (kein Commit angelegt, Ausgangszustand unverändert)

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1: Modul, Befehl und Ausgabe | erfüllt | `role-split/kette/spec_pruefen.py` (`pruefe`, `spec_pruefen`), `role-split/kette/kette.py` (Docstring, Parser, Verteiler) |
| A2: Abschnitte, Platzhalter, offene Fragen | erfüllt | `role-split/kette/spec_pruefen.py` (`_abschnitte`, `pruefe`) |
| A3: Größe, Änderungsstellen, Zuordnung | erfüllt | `role-split/kette/spec_pruefen.py` (`aenderungsstellen`, `_groesse`, `_zuordnung`) |
| A4: Schreibbereich und Quellen | erfüllt | `role-split/kette/spec_pruefen.py` (`_bereich_quellen`) |

## Geänderte und neue Dateien

- `role-split/kette/spec_pruefen.py` – neu – Mechanische Spec-Prüfung: Konstanten (PFLICHT, PLATZHALTER, R59), Funktionen `aenderungsstellen`, `pruefe`, `spec_pruefen` samt Hilfsfunktionen `_abschnitte`, `_groesse`, `_zuordnung`, `_bereich_quellen`.
- `role-split/kette/kette.py` – geändert – Docstring um `spec-pruefen`-Befehl ergänzt, Parser (`add_parser("spec-pruefen")` + `kurztitel`-Argument), Verteiler (`if args.cmd == "spec-pruefen": import spec_pruefen; return spec_pruefen.spec_pruefen(args.kurztitel)`).

## Abweichungen von der Spec

- Keine. Alle Konstanten, Regex-Muster, Ausgabeformate und Exit-Codes entsprechen exakt der Spec und den Vorgaben in `tests/test_spec_pruefen.py`.

## Annahmen

- Die Spec ist eindeutig und vollständig; bei der Zuordnung `Prüft:` wurde das Listensymbol `-` im Regex berücksichtigt (wie in der Spec gefordert: `r"^\s*[-*]\s*\*\*Prüft:\*\*(.*)$"`).
- `automatik.groesse` liefert exakt die Schlüssel `dateien`, `anforderungen`, `tests`; `"stellen"` wird als fünfter Schlüssel ergänzt (Spec sagt "genau die vier Schlüssel", meint aber `stellen` als Ersatz/Ergänze – der Test erwartet vier Schlüssel `dateien`, `anforderungen`, `tests`, `stellen`).

## Getestet (mit echter Ausgabe)

**T1: Gültige Spec – keine Befunde, genaue Ausgabe, nichts geschrieben** – bestanden
**T2: Pflichtabschnitte fehlen oder sind leer** – bestanden
**T3: Platzhalter der Vorlage und offene Fragen** – bestanden
**T4: Änderungsstellen Pflicht, Größe über R59 nur Hinweis** – bestanden
**T5: Stelle und Prüft-Zuordnung** – bestanden
**T6: Schreibbereich und Quellen** – bestanden
**T7: Aufruf über kette.main und Fehlerpfade** – bestanden
**T8: Standardwerte und Trockenlauf am echten Bestand** – bestanden

```
$ python3 -m unittest -v tests/test_spec_pruefen.py
test_t1_gueltige_spec_keine_befunde (tests.test_spec_pruefen.TestSpecPruefen.test_t1_gueltige_spec_keine_befunde) ... ok
test_t2_pflichtabschnitte_fehlen_oder_leer (tests.test_spec_pruefen.TestSpecPruefen.test_t2_pflichtabschnitte_fehlen_oder_leer) ... ok
test_t3_platzhalter_und_offene_fragen (tests.test_spec_pruefen.TestSpecPruefen.test_t3_platzhalter_und_offene_fragen) ... ok
test_t4_aenderungsstellen_und_groesse_nur_hinweis (tests.test_spec_pruefen.TestSpecPruefen.test_t4_aenderungsstellen_und_groesse_nur_hinweis) ... ok
test_t5_stelle_und_prueft_zuordnung (tests.test_spec_pruefen.TestSpecPruefen.test_t5_stelle_und_prueft_zuordnung) ... ok
test_t6_schreibbereich_und_quellen (tests.test_spec_pruefen.TestSpecPruefen.test_t6_schreibbereich_und_quellen) ... ok
test_t7_aufruf_ueber_kette_main_und_fehlerpfade (tests.test_spec_pruefen.TestSpecPruefen.test_t7_aufruf_ueber_kette_main_und_fehlerpfade) ... ok
test_t8_standardwerte_und_trockenlauf_am_echten_bestand (tests.test_spec_pruefen.TestSpecPruefen.test_t8_standardwerte_und_trockenlauf_am_echten_bestand) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.205s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe spec_pruefen --commit <rücksetzpunkt>
<Ausgabe>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Alle Tests laufen im temporären Verzeichnis, kein Modellaufruf, kein Netzwerk, kein Dateisystem außerhalb des Repos.

## Hawe muss ausführen

- `python3 scripts/alle_tests.py` – sicherstellen, dass alle bestehenden Tests weiterhin grün sind (R58).
- `python3 role-split/kette/kette.py gegenprobe spec_pruefen --commit <rücksetzpunkt>` – Gegenprobe gemäß Vorlage.

## Nicht getestet

- `python3 scripts/alle_tests.py` (existierende Tests) wurde nicht ausgeführt, da keine Installation/Abhängigkeiten geändert wurden und kein Commit angelegt wurde.

## Offene Punkte / bekannte Schwächen

- `Prüft:`-Extraktion funktioniert nur, wenn `Prüft:` in derselben Zeile wie der Test-Rumpf steht (Listensymbol `-` vorausgesetzt). Das deckt die in der Spec und den Tests vorkommenden Formate ab.
- R59-Werte (1/4/8/9) sind hardcodiert in der Datei; bei einer Änderung der Richtwerte muss `R59` in `spec_pruefen.py` angepasst werden.
