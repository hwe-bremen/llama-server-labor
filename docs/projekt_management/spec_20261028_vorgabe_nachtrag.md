# Spec: vorgabe_nachtrag

- **Datum:** 2026-10-28
- **Modell:** Claude (Spec, Vorgabe-Tests und Referenzlösung; Umsetzung durch den lokalen Umsetzer per `kette.py umsetzung-auto`, erstmals mit Vorgabe-Tests)
- **Betroffene Dateien:** `role-split/kette/kette.py` (fünf kleine Stellen); Vorgabe `tests/test_vorgabe_nachtrag.py` (schon geschrieben)

## Ziel

Nachträge aus der Gegenprüfung von K11a: Ein Test kann in der Spec als „(Bestand)“ gekennzeichnet werden – er prüft bewusst Bestehendes, muss vorab grün sein und zählt in der Gegenprobe nicht als Abweichung. Eine Nacharbeit startet nicht, solange die Vorgabe-Tests offene Änderungen haben. Die wirkungslose Ausnahme in Prüfung (b) entfällt.

## Nicht-Ziele

- **`tests/test_vorgabe_nachtrag.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Keine weitere Änderung an `kette.py` außer den Stellen unten. Nichts umbenennen, nichts neu formatieren, nichts löschen außer B4.
- `tests_laufen`, `abgleich`, `pruefen` bleiben unverändert.
- Tests ohne „(Bestand)“ verhalten sich in `tests_pruefen` und `gegenprobe` genau wie bisher.

## Schreibbereich

- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_vorgabe_nachtrag.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts.
- **Technische Sperre für Tests:** T1–T3 in `tempfile.TemporaryDirectory()` mit umgebogenem `kette.ROOT`/`kette.PM` (T3 mit eigenem Temp-Git-Repo). T4 nutzt `Basis` aus `tests/test_umsetzung_auto.py` (Temp-Git-Repo, Attrappe mit Temp-Sperre, Prüfung, dass das echte Repo unverändert ist).

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `kette.py tests-pruefen <kt> --timeout S` (über `main`) | T2 |
| `role-split/kette/kette.py` | als Modul importiert (`tests_pruefen`, `gegenprobe`, `umsetzung_auto`) | T1–T4 |

## Quellen

- `role-split/kette/kette.py` def tests_finden – {Test-ID: Titel} (B1, B2)
- `role-split/kette/kette.py` def datei_suchen – Spec zum Kurztitel finden (B1)
- `role-split/kette/kette.py` def _vorgabe_tests – Stelle für die neue Konstante und den Helfer (B1)
- `role-split/kette/kette.py` def tests_pruefen – Schleife über die Test-IDs (B1)
- `role-split/kette/kette.py` def gegenprobe – Liste `gruen` und Ausgabeschleife (B2)
- `role-split/kette/kette.py` def umsetzung_auto – Block „K11a: Vorgabe-Tests“, Liste `offen` (A2.4), Prüfung (b) (B3, B4)
- `tests/test_umsetzung_auto.py` class Basis – Testaufbau T4

## Anforderungen

### B1: Bestand-Tests in `tests_pruefen`
- **Anforderung:**
  - Neue Konstante `BESTAND = "(Bestand)"` und Funktion `_bestand_ids(kurztitel) -> set[str]`: die Test-IDs der Spec (`datei_suchen("spec", kurztitel, None)`, `tests_finden`), deren Titel `BESTAND` enthält; ohne Spec leere Menge. Beides direkt vor `def _vorgabe_tests`.
  - In der Schleife von `tests_pruefen` über die Test-IDs, nachdem die Methoden gefunden sind: Enthält der Titel der ID `BESTAND`, gilt die umgekehrte Regel – alle Methoden müssen Status `ok` haben → `  gruen     <ID>` (fünf Leerzeichen nach gruen); sonst `  NICHT GRUEN <ID>  <methoden>` mit dem Hinweis „Bestand-Test muss vorab grün sein“, Abweichung. Danach weiter mit der nächsten ID.
  - Alles andere in `tests_pruefen` bleibt.
- **Stelle:** vor `def _vorgabe_tests`; `def tests_pruefen`
- **Akzeptanz:** T1, T2.

### B2: Bestand-Tests in `gegenprobe`
- **Anforderung:** `gegenprobe` holt `_bestand_ids(kurztitel)`. Eine Testmethode ist Bestand, wenn ihr Name auf `test_<id klein>` gefolgt von `_` oder Ende passt. Bestand-Methoden, die mit keiner alten Datei rot werden, kommen **nicht** in die Liste `gruen` (kein Exit 1) und werden als `  BESTAND <methode>  (prueft laut Spec bewusst Bestehendes)` ausgegeben, an der Stelle, wo sonst `GRUEN`/`LADEN` stünde. Bestand-Methoden, die rot werden, erscheinen wie bisher als `rot`.
- **Stelle:** `def gegenprobe`
- **Akzeptanz:** T3.

### B3: Nacharbeit mit offenen Vorgabe-Tests
- **Anforderung:** Im Block „K11a: Vorgabe-Tests“ von `umsetzung_auto`, vor dem Aufruf von `tests_pruefen`: bei `--nacharbeit` und wenn `tests/test_<kt>.py` in `offen` (Liste aus A2.4) steht → Exit 2, kein Start, Meldung
  `Nacharbeit: Vorgabe-Tests tests/test_<kt>.py haben offene Aenderungen. Auf die Vorgabe zuruecksetzen (git restore tests/test_<kt>.py) oder eine bewusste Korrektur committen – kein Lauf.`
- **Stelle:** `def umsetzung_auto`
- **Akzeptanz:** T4.

### B4: Wirkungslose Ausnahme entfernen
- **Anforderung:** In Prüfung (b) die Bedingung `not (vorgabe and d == testdatei) and` samt Klammer um den Rest entfernen; der Ausdruck lautet wieder `if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d in (testdatei, handover_rel))`. Der eigene Befund „Vorgabe-Tests in diesem Lauf geändert“ bleibt. (Die Testdatei war im Ausdruck ohnehin immer erlaubt; die Ausnahme hatte keine Wirkung.)
- **Stelle:** `def umsetzung_auto`, Prüfung (b)
- **Akzeptanz:** kein eigener Test (kein beobachtbares Verhalten); `tests/test_vorgabe_tests.py` T7 bleibt grün.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| B1 | Bestand-Test vorab rot | nichts | `NICHT GRUEN`, Exit 1 | T2 |
| B1 | Spec ohne Test-ID | nichts | Exit 2 (bestehend, jetzt abgesichert) | T1 |
| B1 | `--timeout` über `main` | nichts | Wert kommt bei `tests_laufen` an (bestehend, jetzt abgesichert) | T2 |
| B2 | grüner Test ohne „(Bestand)“ | nichts | weiter `GRUEN`, Exit 1 | T3 (Gegenfall) |
| B3 | Nacharbeit, Testdatei offen | Handover, Nacharbeitsdatei | Exit 2, kein Start | T4 |
| B3 | Nacharbeit, Korrektur committet | – | Lauf startet, Prompt-Abschnitt vollständig zwischen Pflichtzeilen und Nachbesserung (bestehend, jetzt abgesichert) | T4 |
| B4 | – | – | Verhalten unverändert | – |
| B1–B4 | Absturz mitten im Lauf | n. a. | – | – |

## Testplan

Die Tests stehen schon in `tests/test_vorgabe_nachtrag.py` (Vorgabe, nicht ändern). Jede Methode enthält einen Teil, der mit dem alten `kette.py` rot wird; bestehendes Verhalten (Befunde 1, 4, 5 der Gegenprüfung) wird in derselben Methode mitgeprüft. Geprüft: alter Stand 4/4 rot, Referenz 4/4 grün.

### T1: tests-pruefen – Bestand-Test grün ist in Ordnung; Spec ohne Test-ID ist Exit 2
- **Prüft:** B1, Fehlerpfad „Spec ohne Test-ID“
- **Aufbau:** Spec `k` mit T1 und „T2: … (Bestand)“, Testdatei: T1 rot, T2 grün. Danach Spec ohne Testplan.
- **Erwartung:** Exit 0, `rot       T1`, `gruen     T2`, `Keine Abweichung.`; danach Exit 2 ohne `Keine Abweichung.`.
- **Warum misst der Test das Richtige?** Ohne B1 meldet der grüne Bestand-Test `NICHT ROT`.
- **Gegenprobe:** alter `kette.py` → rot.

### T2: tests-pruefen – Bestand-Test rot ist eine Abweichung; --timeout wird weitergereicht
- **Prüft:** B1, Fehlerpfade „Bestand vorab rot“, „--timeout“
- **Aufbau:** wie T1, aber T2 rot. Danach `main(["tests-pruefen", "k", "--timeout", "7"])` mit Attrappe für `tests_laufen`.
- **Erwartung:** Exit 1, `NICHT GRUEN T2`, `rot       T1`; Attrappe sieht Timeout 7, Exit 0.
- **Warum misst der Test das Richtige?** Ohne B1 zählt ein roter Bestand-Test als „rot“ und damit als in Ordnung.
- **Gegenprobe:** alter `kette.py` → rot.

### T3: gegenprobe – grüner Bestand-Test laut Spec ist keine Abweichung
- **Prüft:** B2, Gegenfall ohne Kennzeichnung
- **Aufbau:** Temp-Git-Repo mit `src/m.py`, Spec, Testdatei (T1 neu, T2 prüft Bestehendes); Commit; `src/m.py` erweitern. `gegenprobe` erst mit Spec ohne „(Bestand)“, dann mit.
- **Erwartung:** erst Exit 1 und `GRUEN test_t2_bestand`; dann Exit 0, `BESTAND test_t2_bestand`, kein `GRUEN test_t2_bestand`, `rot   test_t1_neu`.
- **Warum misst der Test das Richtige?** Ohne B2 bleibt der zweite Aufruf Exit 1; der Gegenfall zeigt, dass ohne Kennzeichnung nichts lockerer wird.
- **Gegenprobe:** alter `kette.py` → rot (zweiter Aufruf).

### T4: umsetzung-auto – Nacharbeit startet nicht, solange die Vorgabe-Tests offene Änderungen haben
- **Prüft:** B3, Fehlerpfade „Testdatei offen“, „Korrektur committet“
- **Aufbau:** `Basis`; Spec mit `## Vorgabe-Tests`, rote Testdatei committet; Nacharbeit vorbereiten; Testdatei ändern (nicht committet); Lauf mit `--nacharbeit`. Danach Änderung committen, erneut.
- **Erwartung:** erst Exit 2, nicht gestartet, Meldung nennt `tests/test_g.py` und `git restore`; dann gestartet, Exit 0, Prompt enthält `## Vorgabe-Tests` mit dem vollständigen Text aus K11a A4, nach `## Pflichtzeilen im Handover` und vor `## Nachbesserung 1`.
- **Warum misst der Test das Richtige?** Ohne B3 startet der erste Lauf und prüft gegen geschwächte Tests.
- **Gegenprobe:** alter `kette.py` → rot (erster Lauf startet).

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
