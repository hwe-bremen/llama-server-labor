# Handover: k10b_nachtraege

- **Spec:** `docs/projekt_management/spec_20261027_k10b_nachtraege.md`
- **Datum:** 2026-10-27
- **Modell / Werkzeug:** Code: Qwen3.6-35B-A3B-MTP per `kette.py umsetzung-auto` (Erstlauf + Nachbesserung 1, unbeaufsichtigt). Tests und dieser Handover: Claude (Übernahme nach R42, Nachbesserung 2).
- **Rücksetzpunkt:** `29060aa`

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1 Pflichtzeilen im Umsetzer-Prompt | erfüllt (nach NB1: Spec-Reihenfolge) | `kette.py`, `def _umsetzung_prompt` |
| A2 Bereiche unter „Nicht getestet“ | erfüllt | `kette.py`, `def abgleich` |
| A3 Token-Spitze | erfüllt | `kette.py`, `def _lauf`, Unterzeile und Zusammenfassung in `def umsetzung_auto` |
| A4 zurückgezogene Befunde | erfüllt | `kette.py`, `def _zurueckgezogen`, `def zusammenfuehren` |

## Geänderte und neue Dateien

- `role-split/kette/kette.py` – geändert – vier Stellen (A1–A4), vom 35B; keine andere Stelle berührt (Diff gelesen).
- `tests/test_k10b_nachtraege.py` – neu – vier Testmethoden T1–T4, von Claude (ersetzt die Fassung des Umsetzers).

## Abweichungen von der Spec

- A1: Zwischen Überschrift, Einleitungssatz und Pflichtzeilen stehen keine Leerzeilen; die schließenden Anführungszeichen sind `"` statt `“`. Inhaltlich wie verlangt; nicht nachgebessert.
- A2: Das Bereichsmuster erlaubt zusätzlich den Geviertstrich `—`. Unschädlich.

## Annahmen

- Keine.

## Getestet (mit echter Ausgabe)

**T1: Prompt nennt je Test-ID eine Pflichtzeile** – bestanden
**T2: abgleich – Bereich unter „Nicht getestet“ ist keine Einzelnennung** – bestanden
**T3: Tokens – Spitze je Schritt im Protokoll und auf stdout** – bestanden
**T4: zusammenfuehren – zurückgezogene „hoch“-Zeilen zählen nicht** – bestanden

Ausgabe: siehe `pruefung_20261027_k10b_nachtraege.md` nach dem nächsten `pruefen` (Claude hat die Tests gegen eine Kopie mit demselben Code laufen lassen: 4/4 grün, Gegenprobe 4/4 rot, Mutation `sorted(...)` in A1 macht T1 rot).

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe k10b_nachtraege --commit 29060aa
siehe pruefung_20261027_k10b_nachtraege.md
```

## Außenwirkung

- Keine. Alle Tests in temporären Verzeichnissen; T3 über die Attrappe mit Temp-Sperre und Prüfung des echten Repos (`Basis`).

## Hawe muss ausführen

- `pruefen`, `review-auto`, Commit.

## Nicht getestet

- Reihenfolge „Pflichtzeilen vor dem Nachbesserungs-Teil“ (A1) ist nicht eigens geprüft.

## Offene Punkte / bekannte Schwächen

- Messwerte 35B: Erstlauf 21:34 min (79 Werkzeugaufrufe), NB1 29:25 min (94 Aufrufe, Kontextspitze 58 118 Token von 64K). Code beide Male richtig bzw. nach Hinweis korrigiert; Tests beide Male nicht wie in der Spec.

## Nachbesserung 1

Vom 35B per `umsetzung-auto --nacharbeit` (Auftrag `nacharbeit_20261027_k10b_nachtraege_1.md`).

- Erledigt: A1 `sorted(spec_tests)` → `spec_tests.items()` (Spec-Reihenfolge).
- Nicht erledigt: Tests weiter in sieben Methoden statt vier (drei GRUEN in der Gegenprobe), T2 prüfte weiter nicht den Fall der Spec, T3 akzeptierte weiter Exit 0 oder 1, Handover-Titel weiter umformuliert – obwohl der Prompt die Pflichtzeilen erstmals mechanisch enthielt.
- Falsche Angaben im damaligen Handover (hier ersetzt, R40/R08): „Spec benötigt `## Schreibbereich` – hinzugefügt“ (nichts dergleichen geändert), „Verdikt-Dateinamen an Regex angepasst, `qwen36-35b` passt nicht“ (passt, siehe T4), Steuerung der Attrappe über `FAKE_TOTAL_1` usw. (gibt es nicht).

## Nachbesserung 2

Übernahme durch Claude nach R42 (zweiter Durchgang ohne Fortschritt bei den Tests, Spec-Vorgaben zu den Tests zweimal nicht befolgt).

- `tests/test_k10b_nachtraege.py` neu nach Spec: je Test-ID eine Methode, Gegenfall in derselben Methode, T1 zusätzlich mit Reihenfolge T2 vor T10, T3 über `Basis` mit Exit 0.
- Handover korrigiert (dieser Stand).
- `kette.py` unverändert gegenüber NB1.
