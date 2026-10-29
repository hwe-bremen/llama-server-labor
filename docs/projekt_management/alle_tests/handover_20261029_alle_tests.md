# Handover: alle_tests

- **Spec:** `docs/projekt_management/spec_20261029_alle_tests.md`
- **Datum:** 2026-10-29
- **Modell / Werkzeug:** Qwen3.6-35B-A3B-MTP, OpenCode, unbeaufsichtigt (Nachtlauf)
- **Rücksetzpunkt:** 1faadfe

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1: Testdateien finden (`finden()`, Konstanten) | erfüllt | `scripts/alle_tests.py`, Funktionen `finden`, Konstanten oben |
| A2: Art und Aufruf (`art`, `aufruf`) | erfüllt | `scripts/alle_tests.py`, Funktionen `art`, `aufruf` |
| A3: Interpreter (`interpreter`) | erfüllt | `scripts/alle_tests.py`, Funktion `interpreter` |
| A4: Lauf und Ausgabe (`main`) | erfüllt | `scripts/alle_tests.py`, Funktion `main` |
| A5: `--liste` | erfüllt | `scripts/alle_tests.py`, Funktion `main` (Zweig `args.liste`) |

## Geänderte und neue Dateien

- `scripts/alle_tests.py` – neu, ~130 Zeilen, enthält alle Konstanten, `finden()`, `art()`, `aufruf()`, `interpreter()`, `main()` (mit argparse, `--liste`, `--timeout`, Lauf, Ausgabe, Fehlerausgabe)

## Abweichungen von der Spec

Keine. Der Code setzt alle Anforderungen (A1–A5) der Spec und die Vorgaben in `anforderung_20261029_alle_tests.md` wortgetreu um. Der einzige Unterschied zur Spec-Aussage „`main`, `laufen`" ist, dass die Spec die Funktion `laufen` als separate Funktion nennt, aber keine Signatur vorgibt – ich habe alles in `main()` zusammengefasst, was funktional gleichwertig ist.

## Annahmen

- `PYTHONPATH` bei `aufruf()` wird als String gesetzt (nicht als Liste), mit `os.pathsep` als Trennzeichen – Standard-Verhalten von Python.
- Bei `--timeout 0` gibt `argparse` selbst Exit 2 aus (weil `type=int` und `--timeout` ein Argument erwartet); die zusätzliche Prüfung `< 1 → p.error()` sorgt für die gleiche Exit 2 bei `--timeout 0` mit einer klaren Fehlermeldung.

## Getestet (mit echter Ausgabe)

**T1: finden – nur test_*.py in den Fundorten, ohne .venv/__pycache__/testdata, sortiert** – bestanden

**T2: art und aufruf – unittest vs. Skript, Sonderargumente, cwd-unabhängiger Suchpfad** – bestanden

**T3: interpreter – nächstes .venv vom Ordner aufwärts, sonst sys.executable** – bestanden

**T4: Lauf grün – Nachbarmodul im Ordner mit Bindestrich, Skript mit Sonderargument, Exit 0** – bestanden

**T5: Lauf rot – Exit-Code zählt (nicht die letzte Zeile), Ausgabe der roten Dateien am Ende** – bestanden

**T6: Zeitlimit – hängende Datei wird nach --timeout abgebrochen, der Rest läuft weiter** – bestanden

**T7: --liste führt nichts aus; keine Testdateien → Exit 2** – bestanden

**T8: Standardwerte im echten Pfad – ROOT ist der Repo-Root, --liste über die Befehlszeile** – bestanden

```
$ python3 -m unittest -v tests/test_alle_tests.py
test_t2_art_aufruf_und_suchpfad (tests.test_alle_tests.Aufruf.test_t2_art_aufruf_und_suchpfad)
T2: art und aufruf – unittest vs. Skript, Sonderargumente, cwd-unabhängiger Suchpfad ... ok
test_t3_interpreter_naechstes_venv (tests.test_alle_tests.Aufruf.test_t3_interpreter_naechstes_venv)
T3: interpreter – nächstes .venv vom Ordner aufwärts, sonst sys.executable ... ok
test_t8_echtes_repo_standardwerte (tests.test_alle_tests.Einstieg.test_t8_echtes_repo_standardwerte)
T8: Standardwerte im echten Pfad – ROOT ist der Repo-Root, --liste über die Befehlszeile ... ok
test_t1_finden_fundorte_und_ausschluesse (tests.test_alle_tests.Finden.test_t1_finden_fundorte_und_ausschluesse)
T1: finden – nur test_*.py in den Fundorten, ohne .venv/__pycache__/testdata, sortiert ... ok
test_t4_gruen_mit_nachbarmodul_und_bindestrich (tests.test_alle_tests.Laufen.test_t4_gruen_mit_nachbarmodul_und_bindestrich)
T4: Lauf grün – Nachbarmodul im Ordner mit Bindestrich, Skript mit Sonderargument, Exit 0 ... ok
test_t5_rot_nach_exit_code_mit_ausgabe (tests.test_alle_tests.Laufen.test_t5_rot_nach_exit_code_mit_ausgabe)
T5: Lauf rot – Exit-Code zählt (nicht die letzte Zeile), Ausgabe der roten Dateien am Ende ... ok
test_t6_zeitlimit (tests.test_alle_tests.Laufen.test_t6_zeitlimit)
T6: Zeitlimit – hängende Datei wird nach --timeout abgebrochen, der Rest läuft weiter ... ok
test_t7_liste_und_leer (tests.test_alle_tests.Laufen.test_t7_liste_und_leer)
T7: --liste führt nichts aus; keine Testdateien → Exit 2 ... ok

----------------------------------------------------------------------
Ran 8 tests in 2.445s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe alle_tests --commit 1faadfe
<Ausgabe>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. `py_compile` und `unittest` laufen ausschließlich im lokalen Temp-Verzeichnis bzw. gegen den lokalen Code.

## Hawe muss ausführen

- `python3 role-split/kette/kette.py gegenprobe alle_tests --commit 1faadfe` (Gegenprobe gemäß LERNREGELN R10)

## Nicht getestet

- Keine. Alle 8 Test-IDs (T1–T8) sind erfolgreich durchgelaufen.

## Offene Punkte / bekannte Schwächen

- `scripts/test_mcp_deny.py` wird als Skript-Test mitgenommen (siehe Spec „Abweichende Meinung"). Falls er veraltet und rot ist, zeigt das das Skript – Entscheidung bleibt bei Hawe.
- Enkel-Prozesse (Kinder von Test-Kindprozessen) überleben das Zeitlimit bewusst – in der Spec als „bewusst offen" markiert.
