# Spec: lauf_status

- **Datum:** 2026-10-28
- **Modell:** Claude (Spec und Referenzlösung); Vorgabe-Tests: Messung 27B gegen Claudes Referenztests; Umsetzung durch den lokalen Umsetzer per `kette.py lauf`
- **Betroffene Dateien:** neu `role-split/kette/automatik.py`; in `role-split/kette/kette.py` nur zwei Subparser und die Weiterleitung in `main`

## Ziel

Ein Befehl `kette.py lauf <kurztitel>` führt die Kette ab fertiger, committeter Spec mit Vorgabe-Tests bis zum Halt an Hawes Entscheidung: Größenprüfung mit Umsetzer-Vorschlag → `umsetzung-auto` → `review-auto` → Status mit nächstem Schritt. `kette.py status <kurztitel>` zeigt den Stand der Kette aus den vorhandenen Dateien, ohne etwas auszuführen. Der Ablauf liegt im neuen Modul `automatik.py`, damit `kette.py` klein bleibt (R43).

## Nicht-Ziele

- **`tests/test_lauf_status.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Keine Nacharbeit aus `lauf` heraus (der Nacharbeitsauftrag kommt von Claude; `umsetzung-auto --nacharbeit` bleibt der Weg).
- Keine eigene Zustandsdatei: `status` leitet alles aus Spec, Protokoll `umsetzung_*`, Gesamtbefund `gesamt_*` und `git status` ab.
- Keine Rückfragen im Lauf (kein `input()`), keine weiteren Schalter.
- In `kette.py` nichts außer C5 ändern; `umsetzung_auto`, `review_auto` usw. bleiben unverändert.
- Kein Lauf aller Testdateien (R50) im Werkzeug – `status` nennt ihn als Schritt vor dem Commit.

## Schreibbereich

- `role-split/kette/automatik.py`
- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_lauf_status.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** `lauf` startet über `umsetzung-auto` opencode (lokales Modell) und über `review-auto` zwei API-Läufe am lokalen Server – beides wie bisher, nichts Neues nach außen.
- **Technische Sperre für Tests:** Jeder Test arbeitet in `tempfile.TemporaryDirectory()` mit eigenem Temp-Git-Repo und umgebogenem `kette.ROOT`/`kette.PM`. `kette.umsetzung_auto` und `kette.review_auto` werden per `mock.patch.object` durch Attrappen ersetzt – deshalb muss `automatik.py` sie **über das Modul** aufrufen (`kette.umsetzung_auto(...)`), nie per `from kette import ...`.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `kette.py lauf <kt>`, `kette.py status <kt>` (über `main`) | T8 |
| `role-split/kette/automatik.py` | als Modul (`lauf`, `status`), importiert `kette` | T1–T7 |

## Quellen

- `role-split/kette/kette.py` def _schreibbereich – Einträge des Schreibbereichs (C1)
- `role-split/kette/kette.py` def abschnitt – Inhalt unter einer `##`-Überschrift (C1)
- `role-split/kette/kette.py` def tests_finden – Test-IDs der Spec (C1)
- `role-split/kette/kette.py` def datei_suchen – Kettendateien zum Kurztitel (C2, C3)
- `role-split/kette/kette.py` def spec_commit – Commit „Spec <kt>“ (C2, C3)
- `role-split/kette/kette.py` def _vorgabe_tests – Abschnitt `## Vorgabe-Tests` (C2, C3)
- `role-split/kette/kette.py` def _datum_aus – Datum aus dem Spec-Dateinamen (C3)
- `role-split/kette/kette.py` def umsetzung_auto – Exit 0/1/2 (C2)
- `role-split/kette/kette.py` def review_auto – Exit 0/1/2, schreibt `gesamt_<datum>_<kt>.md` (C2, C3)
- `role-split/kette/kette.py` def main – Subparser (C5)

## Anforderungen

### C1: Größenprüfung
- **Anforderung:** In `automatik.py` Konstanten `GROESSE_DATEIEN = 2`, `GROESSE_ANFORDERUNGEN = 6`, `GROESSE_TESTS = 8` (vorläufig) und `UMSETZER_VORSCHLAG = "35B"`. Funktion `groesse(spec_text) -> dict` mit `dateien` (Einträge aus `kette._schreibbereich`, keiner → 0), `anforderungen` (Überschriften `### <Buchstabe(n)><Zahl>:` **nur im Abschnitt `## Anforderungen`**) und `tests` (Anzahl `kette.tests_finden`). Zu groß ist eine Spec, wenn **ein** Wert seine Schwelle **überschreitet** (an der Schwelle nicht).
- **Stelle:** `automatik.py`
- **Akzeptanz:** T3.

### C2: `lauf(kurztitel) -> int`
- **Anforderung:** in dieser Reihenfolge:
  1. Kurztitel nicht `[a-z0-9_]+` → Exit 2. Keine Spec oder kein Commit „Spec <kt>“ (`kette.spec_commit`) → Meldung, die `Spec <kt>` nennt, Exit 2. Spec ohne `## Vorgabe-Tests` → Meldung mit `Vorgabe-Tests` und Hinweis auf R48, Exit 2. In diesen Fällen wird nichts gestartet.
  2. Zeile `Größe: <d> Datei(en), <a> Anforderungen, <t> Tests (Schwellen 2/6/8, vorläufig)`. Zu groß → Zeile `HALT – zu groß für den lokalen Umsetzer: Spec teilen oder Claude übernimmt (R43).`, Exit 3, nichts gestartet.
  3. Zeile `Umsetzer: 35B`; dann `kette.umsetzung_auto(kurztitel)` (genau ein Argument). Nur bei Exit 0 danach `kette.review_auto(kurztitel)`.
  4. Leerzeile, Ausgabe von `status(kurztitel)` (C3/C4), dann Zeile `HALT – Entscheidung Hawe.`
  5. Rückgabe: 0, wenn Umsetzung und Review 0 waren; 2, wenn der zuletzt gelaufene Schritt 2 lieferte; sonst 1.
- **Stelle:** `automatik.py`
- **Akzeptanz:** T1, T2, T3, T4, T5, T6.

### C3: Stand aus Dateien
- **Anforderung:** Funktion `stand(kurztitel) -> dict` mit:
  - `spec` (Pfad oder `None`, `kette.datei_suchen("spec", kt, None)`), `spec_commit` (`kette.spec_commit` oder `None`), `vorgabe` (bool),
  - `laeufe`: Liste `(art, exit)` aus `PM/umsetzung_<spec-datum>_<kt>.md`, **nur Zeilen, die mit `- **` beginnen**, je Treffer von `art: (erst|nb\d+), Exit: (\d+)` (Unterzeilen mit fremdem Text zählen nicht),
  - `review`: `PASS` / `NACHBESSERN` / `UNVOLLSTÄNDIG` aus der ersten Zeile `**<WERT>**` in `kette.datei_suchen("gesamt", kt, None)`, sonst `None`,
  - `offen`: Pfade aus `git -C <ROOT> status --porcelain`.
- **Stelle:** `automatik.py`
- **Akzeptanz:** T7.

### C4: `status(kurztitel) -> int` und nächster Schritt
- **Anforderung:** Kurztitel ungültig → Exit 2. Ausgabe (Einrückung zwei Leerzeichen, Werte ab Spalte 17 wie gezeigt):
  ```
  Status <kt>
    Spec:          <dateiname oder fehlt>
    Spec-Commit:   <hash oder fehlt>
    Vorgabe-Tests: <ja|nein>
    Umsetzung:     <"erst Exit 1, nb1 Exit 0" oder keiner>
    Review:        <PASS|NACHBESSERN|UNVOLLSTÄNDIG oder keins>
    Offen:         <n> Datei(en)
  Nächster Schritt: <text>
  ```
  Nächster Schritt, erste zutreffende Regel:
  1. keine Spec → Text mit „Spec fehlt“;
  2. kein Spec-Commit → `Spec committen: git commit -m "Spec <kt>"`;
  3. keine Läufe → `kette.py lauf <kt>`;
  4. letzter Lauf Exit ≠ 0 → Text, der „Nacharbeit“ und „Übernahme durch Claude“ nennt;
  5. kein Review → `kette.py review-auto <kt>`;
  6. Review nicht `PASS` → Text mit dem Review-Wert und „gegenprüfen“;
  7. offene Dateien → Text mit „alle Testdateien laufen lassen (R50), dann committen“;
  8. sonst → `Abgeschlossen – nichts offen.`
  Rückgabe 0, wenn eine Spec existiert, sonst 2.
- **Stelle:** `automatik.py`
- **Akzeptanz:** T7.

### C5: Befehle in `kette.py`
- **Anforderung:** Subparser `lauf` und `status`, je mit `kurztitel`. In `main`: bei `lauf`/`status` `import automatik` **in der Verzweigung** (nicht am Dateianfang, sonst Kreisimport) und Rückgabe von `automatik.lauf(kt)` bzw. `automatik.status(kt)`.
- **Stelle:** `def main`
- **Akzeptanz:** T8.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| C2 | Kurztitel ungültig | nichts | Exit 2 | T1 |
| C2 | kein Commit „Spec <kt>“ | nichts | Exit 2, nichts gestartet | T1 |
| C2 | ohne `## Vorgabe-Tests` | nichts | Exit 2, nichts gestartet | T2 |
| C1/C2 | Tests, Anforderungen oder Dateien über der Schwelle | nichts | Exit 3, nichts gestartet | T3 |
| C1/C2 | genau an der Schwelle | – | Lauf startet | T3 |
| C2 | Umsetzung Exit 1 / 2 | Protokoll von umsetzung-auto | kein Review, Exit 1 / 2, HALT-Zeile | T5 |
| C2 | Review Exit 1 | Verdikte, Gesamtbefund | Exit 1 | T6 |
| C3 | Unterzeile im Protokoll mit „art: …, Exit: …“ | – | zählt nicht als Lauf | T7 |
| C4 | jede Regel 1–8 | – | passender nächster Schritt | T7 (Regel 2: – kein Test, gleiche Bedingung wie in `lauf`) |
| C2 | Absturz in umsetzung-auto/review-auto | dort beschrieben | Ausnahme geht durch (kein eigenes Abfangen) | – |

## Testplan

Die Tests stehen in `tests/test_lauf_status.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. `automatik` wird in jeder Methode importiert, damit jeder Test vorab rot ist.

### T1: lauf – ohne Commit „Spec <kt>“ kein Start
- **Prüft:** C2.1
- **Aufbau:** Temp-Git-Repo, Spec mit Vorgabe-Tests unter anderer Commit-Nachricht committet; `lauf("k")`; danach `lauf("K-ungueltig")`.
- **Erwartung:** Exit 2, Ausgabe enthält `Spec k`, keine Attrappe aufgerufen; ungültiger Kurztitel Exit 2.
- **Warum misst der Test das Richtige?** Ohne die Prüfung würde die Umsetzung ohne Rücksetzpunkt starten.
- **Gegenprobe:** ohne `automatik.py` rot.

### T2: lauf – ohne Abschnitt Vorgabe-Tests kein Start
- **Prüft:** C2.1
- **Aufbau:** Spec ohne `## Vorgabe-Tests` als „Spec k“ committet.
- **Erwartung:** Exit 2, Ausgabe enthält `Vorgabe-Tests`, keine Attrappe aufgerufen.
- **Warum misst der Test das Richtige?** R48: ohne Vorgabe-Tests schreibt der Umsetzer seine eigenen.
- **Gegenprobe:** ohne `automatik.py` rot.

### T3: lauf – Größenprüfung hält bei Überschreitung, an der Schwelle läuft es
- **Prüft:** C1, C2.2
- **Aufbau:** Spec mit 9 Test-IDs im Testplan (`### T1:` … `### T9:`); dann 7 Anforderungen (`### A1:` … unter `## Anforderungen`); dann 3 Schreibbereich-Einträgen (Pfad in Backticks); dann genau 2/6/8. *(präzisiert 28.10.: „Tests“ = Test-IDs im Testplan, nicht Einträge unter `## Vorgabe-Tests`)*
- **Erwartung:** dreimal Exit 3 (erste Ausgabe enthält `9 Tests` und `teilen`, keine Attrappe aufgerufen); an der Schwelle Exit 0 und `2 Datei(en), 6 Anforderungen, 8 Tests`.
- **Warum misst der Test das Richtige?** Jede der drei Größen allein muss halten; die Schwelle selbst darf nicht halten; Testplan-Überschriften zählen nicht als Anforderungen.
- **Gegenprobe:** ohne `automatik.py` rot.

### T4: lauf – Umsetzung und Review grün, Halt an Hawes Entscheidung
- **Prüft:** C2.3–C2.5
- **Aufbau:** gültige Spec; beide Attrappen Exit 0.
- **Erwartung:** Exit 0; Aufrufe genau `umsetzung_auto("k")` (ohne Nacharbeit), dann `review_auto("k")`; Ausgabe enthält `Umsetzer: 35B`, `Nächster Schritt:` und `HALT – Entscheidung Hawe.`
- **Warum misst der Test das Richtige?** Prüft Reihenfolge und Argumente, nicht nur den Exit-Code.
- **Gegenprobe:** ohne `automatik.py` rot.

### T5: lauf – Umsetzung nicht in Ordnung, kein Review
- **Prüft:** C2.3, C2.5
- **Aufbau:** Attrappe Umsetzung Exit 1, danach Exit 2.
- **Erwartung:** Exit 1, nur der Umsetzungsaufruf, HALT-Zeile; mit Exit 2 der Umsetzung Exit 2.
- **Warum misst der Test das Richtige?** Ein Review auf roter Umsetzung ist verschwendet; Exit 2 (Voraussetzung) darf nicht zu 1 werden.
- **Gegenprobe:** ohne `automatik.py` rot.

### T6: lauf – Review nicht PASS ergibt Exit 1
- **Prüft:** C2.5
- **Aufbau:** Umsetzung Exit 0, Review Exit 1.
- **Erwartung:** Exit 1, Aufrufe Umsetzung dann Review.
- **Warum misst der Test das Richtige?** Ein NACHBESSERN darf nicht als „alles gut“ enden.
- **Gegenprobe:** ohne `automatik.py` rot.

### T7: status – Stand und nächster Schritt aus den Dateien
- **Prüft:** C3, C4 (Regeln 1, 3–8)
- **Aufbau:** Temp-Git-Repo nacheinander: ohne Spec; Spec committet; Protokoll mit einer Laufzeile im Format von `umsetzung-auto` (`- **2026-10-28 10:00** – … art: erst, Exit: 1`, plus Unterzeile `  - … art: nb9, Exit: 0`) *(präzisiert 28.10.: Format wie C3)*; Protokoll `erst Exit 1`, `nb1 Exit 0`; `gesamt_…` mit `**NACHBESSERN**`; mit `**PASS**` (Dateien offen); alles committet.
- **Erwartung:** Exit 2 und `Spec:          fehlt`; dann Exit 0, `Vorgabe-Tests: ja`, `Nächster Schritt: kette.py lauf k`; `Umsetzung:     erst Exit 1`, kein `nb9`, Schritt nennt „Nacharbeit“; `Nächster Schritt: kette.py review-auto k`; `Review:        NACHBESSERN` und „gegenprüfen“; Schritt nennt „committen“; zuletzt „Abgeschlossen“. Keine Attrappe aufgerufen.
- **Warum misst der Test das Richtige?** Jede Regel wird durch genau die Datei ausgelöst, die sie lesen soll; die Unterzeile prüft den Protokoll-Filter.
- **Gegenprobe:** ohne `automatik.py` rot.

### T8: main – lauf und status über kette.py
- **Prüft:** C5
- **Aufbau:** `automatik.lauf`/`automatik.status` durch Attrappen ersetzt (Rückgabe 3 bzw. 0); `kette.main(["lauf", "k"])`, `kette.main(["status", "k"])`.
- **Erwartung:** Rückgaben 3 und 0, Attrappen mit `k` aufgerufen.
- **Warum misst der Test das Richtige?** Prüft, dass `main` den Rückgabewert durchreicht und beide Befehle verdrahtet sind.
- **Gegenprobe:** alter `kette.py` → rot.

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
