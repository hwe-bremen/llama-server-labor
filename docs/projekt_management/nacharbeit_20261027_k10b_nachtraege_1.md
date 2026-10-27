# Nacharbeit 1: k10b_nachtraege

Grundlage: Prüfung durch Claude am 27.10. (Diff und Tests gelesen, `pruefung_20261027_k10b_nachtraege.md`). Die Änderungen für A2, A3 und A4 in `kette.py` sind richtig und bleiben. Nachzubessern sind eine Stelle in A1 und vor allem die Tests. Ändere nur `role-split/kette/kette.py` (eine Stelle), `tests/test_k10b_nachtraege.py` und den Handover.

## 1. A1: Reihenfolge der Pflichtzeilen (kette.py)

In `_umsetzung_prompt` steht `for tid in sorted(spec_tests):`. `sorted` sortiert als Text: T1, T10, T11, T2 … Die Spec verlangt **Spec-Reihenfolge**. `tests_finden` liefert ein dict in Spec-Reihenfolge – also über `spec_tests.items()` laufen, ohne `sorted`. Sonst nichts an `kette.py` ändern.

## 2. Tests genau wie in der Spec – je Test-ID genau eine Methode

`pruefen` meldet für die Gegenprobe vier GRUEN-Tests (`test_t1_keine_test_ids`, `test_t2_bereichsangaben_entfernt`, `test_t2_einzelne_nennung_nicht_getestet`, `test_t4_hoch_bleibt_hoch`). Die Spec sagt: „Jeder Test muss mit dem alten `kette.py` rot werden; deshalb steht der Gegenfall jeweils **in derselben Methode**.“ Darum:

- Genau vier Testmethoden: `test_t1_…`, `test_t2_…`, `test_t3_…`, `test_t4_…`. Die Gegenfälle in dieselbe Methode, keine eigenen Methoden dafür.
- **T1:** wie in der Spec. Zusätzlich im selben Test: Spec mit `### T2: Zwei` vor `### T10: Zehn` – im Prompt muss die Zeile für T2 **vor** der Zeile für T10 stehen (prüft Punkt 1).
- **T2:** Aufbau genau wie in der Spec: Spec mit T1 und T2, im Handover unter Getestet nur `**T1: Erster** – bestanden`, unter „Nicht getestet“ `- Nichts, alle Tests (T1–T2) laufen grün.` Erwartung: Ausgabe enthält `FEHLT     T2`, enthält `NICHT GET` nicht, Rückgabe 1. Dann im selben Test die Einzelnennung `- T2: braucht einen echten Server.` → `NICHT GET T2`. Der jetzige Test (Bereich „T1–T2“, T1 getestet, Prüfung nur auf T1) kann mit altem Code nicht rot werden und misst nichts.
- **T3:** wie in der Spec über die Klasse `Basis` aus `tests/test_umsetzung_auto.py` (`from tests.test_umsetzung_auto import Basis, HANDOVER`, vorher Repo-Stamm in `sys.path`), Lauf `self.lauf(FAKE_HANDOVER=HANDOVER)`. Erwartung: Rückgabe **0**, `Tokens 150 (Spitze 100)` in der Ausgabe, `  - Tokens: input 130, output 18, reasoning 2, spitze 100` im Protokoll. Die Variablen `FAKE_TOTAL_1` usw. gibt es in der Attrappe nicht (siehe `role-split/kette/testdata/opencode_fake.py`) – weglassen. „Exit 0 oder 1 ist OK“ ist keine Prüfung.
- **T4:** Tabellenformat und Zeilen genau wie in der Spec (Kopf mit 8 Spalten wie in `verdict_20261027_umsetzung_auto_qwen36-35b_betrieb.md`, Dateinamen `verdict_20261027_k_qwen36-35b.md` und `verdict_20261027_k_qwen36-35b_betrieb.md`, Aufruf ohne `_internal`). Erwartung erster Aufruf: Rückgabe 0, `davon 0 hoch, 2 zurückgezogen -> PASS`, genau zweimal `| nein (zurückgezogen) |`, Text `Befund entfällt.` vorhanden. Zweiter Aufruf im selben Test: `davon 1 hoch -> NACHBESSERN`, Rückgabe 1.
- Den eigenen Aufbau `Basis` in der Testdatei ersetzen: T1, T2, T4 brauchen nur ein Temp-Verzeichnis mit `docs/projekt_management/` und umgebogenes `kette.ROOT`/`kette.PM` (kein Git, kein `pruefen`-Ersatz nötig).

## 3. Handover

- Unter „## Getestet“ genau die vier Pflichtzeilen aus dem Prompt (Titel wörtlich aus der Spec). `abgleich` meldet jetzt T2 und T3 als ANDERS, weil die Titel umformuliert wurden.
- Neuer Abschnitt `## Nachbesserung 1` mit den Punkten 1–3 und der echten Ausgabe von `python3 -m unittest -v tests/test_k10b_nachtraege.py`.
