# Spec: ablage_ordner

- **Datum:** 2026-10-28
- **Modell:** Claude (Spec, Vorgabe-Tests, Referenzlösung); Umsetzung durch den lokalen Umsetzer per `kette.py lauf`
- **Betroffene Dateien:** `role-split/kette/kette.py` (drei neue kleine Funktionen, rund 20 Pfadstellen), `role-split/role_proxy.py` (zwei Stellen)

## Ziel

Jede Kette kann ihre Dateien in einem eigenen Ordner `docs/projekt_management/<kurztitel>/` haben. Regel: **Gibt es den Ordner, liest und schreibt die Kette dort; gibt es ihn nicht, bleibt alles flach wie bisher.** Damit bleiben alle alten Ketten und Tests unverändert lauffähig. Diese Kette baut nur die Pfadlogik; das Anlegen des Ordners für neue Ketten und das Verschieben der alten folgen in K13b.

## Nicht-Ziele

- **`tests/test_ablage_ordner.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Kein Anlegen von Ordnern, kein Verschieben von Dateien (K13b).
- Vorlagen `_vorlage_*.md` bleiben in `docs/projekt_management/` und werden nie in einen Ordner umgebogen.
- Keine Änderung an `prompts/`, `automatik.py`, Tests oder Dokumentation.
- Keine Änderung am Verhalten, wenn kein Ordner existiert.

## Schreibbereich

- `role-split/kette/kette.py`
- `role-split/role_proxy.py`

## Vorgabe-Tests

- `tests/test_ablage_ordner.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts.
- **Technische Sperre für Tests:** T1–T3, T5–T7 arbeiten in `tempfile.TemporaryDirectory()` mit umgebogenem `kette.ROOT`/`kette.PM`; T4 nutzt `Basis` aus `tests/test_umsetzung_auto.py` (Temp-Git-Repo, Attrappe mit Temp-Sperre, Prüfung, dass das echte Repo unverändert ist). T7 ersetzt `shutil.which` (kein `pbcopy`) und `_pruefen_teile` (keine Unit-Tests im Unterprozess).

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | als Modul (`ablage`, `datei_suchen`, `anforderung`, `quellen`, `pruefen`, `paket`, `prompt`, `zusammenfuehren`, `umsetzung_auto`, `_ist_kettendatei`) | T1–T5, T7 |
| `role-split/role_proxy.py` | als Modul (`capture_task`) | T6 |

## Quellen

- `role-split/kette/kette.py` def datei_suchen – Suche nach `<typ>_<datum>_<kt>.md` (E2)
- `role-split/kette/kette.py` def pruefen – Ziel `pruefung_…` (E3)
- `role-split/kette/kette.py` def paket – Ziel `review_paket_…` (E3)
- `role-split/kette/kette.py` def zusammenfuehren – Ziel `gesamt_…`, Tupel in `zeilen` (E3, E6)
- `role-split/kette/kette.py` def anforderung – Ziel `anforderung_…` (E3)
- `role-split/kette/kette.py` def quellen – Ziel der Quellen-Datei (E3)
- `role-split/kette/kette.py` def prompt – Pfade im Prompt (E4)
- `role-split/kette/kette.py` def _freier_verdiktpfad – Verdikt-Pfad (E3)
- `role-split/kette/kette.py` def review_auto – Paket-, Verdikt- und Gesamt-Pfade (E3)
- `role-split/kette/kette.py` def _ist_kettendatei – Ordnerprüfung (E5)
- `role-split/kette/kette.py` def _umsetzung_prompt – Pfade im Umsetzer-Prompt (E4)
- `role-split/kette/kette.py` def umsetzung_auto – `handover_rel`, `protokoll_p` (E3)
- `role-split/role_proxy.py` def capture_task – Spec-Auftrag im System-Prompt (E4)

## Anforderungen

### E1: Ablage-Funktionen
- **Anforderung:** Direkt vor `def datei_suchen` drei Funktionen in `kette.py`:
  - `ablage(kurztitel) -> Path`: `PM / kurztitel`, wenn das ein Ordner ist (`is_dir()`), sonst `PM`.
  - `_ablage_rel(kurztitel) -> str`: `ablage(kurztitel)` relativ zu `ROOT` als `as_posix()`, also `docs/projekt_management` oder `docs/projekt_management/<kt>`.
  - `_ablage_text(text, kurztitel) -> str`: ersetzt in `text` jedes `docs/projekt_management/`, auf das **nicht** `_vorlage` folgt, durch `_ablage_rel(kurztitel) + "/"` (`re.sub` mit `(?!_vorlage)`).
- **Akzeptanz:** T1, T6.

### E2: Suchen in der Ablage
- **Anforderung:** `datei_suchen` sucht in beiden Zweigen (mit und ohne Datum) in `ablage(kurztitel)` statt in `PM`. Existiert der Ordner, werden flache Dateien derselben Kette nicht mehr gefunden.
- **Akzeptanz:** T2.

### E3: Schreiben in der Ablage
- **Anforderung:** Jede Stelle, die eine Datei einer Kette unter `PM / …` anlegt oder erwartet, nimmt `ablage(<kurztitel>) / …`:
  `pruefen` (`pruefung_`), `paket` (`review_paket_`), `zusammenfuehren` (beide `gesamt_`-Stellen, mit `ablage(kurz)`), `anforderung` (`anforderung_`), `quellen` (`quellen_`), `_freier_verdiktpfad` (beide Zweige), `review_auto` (`paket_pfad`, beide Verdikt-Rückfallpfade `pfad1`/`pfad2`, beide `gesamt_pfad`), `umsetzung_auto` (`protokoll_p`). In `umsetzung_auto` wird `handover_rel` zu `f"{_ablage_rel(kurztitel)}/handover_{datum}_{kurztitel}.md"`.
- **Akzeptanz:** T3, T4, T7 (die `review_auto`-Stellen: – , kein eigener Test, siehe Fehlerpfade).

### E4: Pfade in Prompts
- **Anforderung:**
  - `prompt` und `_umsetzung_prompt`: den Vorlagentext **zuerst** mit `_ablage_text(…, kurztitel)` umbiegen, **danach** die Platzhalter ersetzen (sonst entsteht `…/<kt>/<kt>/`). Selbst gebaute Pfade (`paket_pfad`, `anf_pfad`, `{quellen}`, der Handover im Nachbesserungs-Teil) beginnen mit `_ablage_rel(kurztitel)` statt mit `docs/projekt_management`.
  - `role_proxy.py` `capture_task`: den Spec-Auftrag (Vorlage `spec.md`) ebenfalls zuerst mit `k._ablage_text(t, kurztitel)` umbiegen; `{anforderung}` wird `f"{k._ablage_rel(kurztitel)}/{anf.name}"`.
- **Akzeptanz:** T4, T6, T7.

### E5: Kettendateien im Ordner
- **Anforderung:** `_ist_kettendatei(pfad, kurztitel)` akzeptiert als Ordner `docs/projekt_management` **oder** `_ablage_rel(kurztitel)`; alles andere wie bisher.
- **Akzeptanz:** T5.

### E6: Absturz in `zusammenfuehren` (Nebenfund beim Testen)
- **Anforderung:** Hat ein Verdikt keine erkennbare Befundtabelle, legt `zusammenfuehren` heute ein Tupel mit **fünf** Werten in `zeilen` ab; die spätere Schleife erwartet sechs → `ValueError`. Das Tupel bekommt als sechsten Wert `False` (nicht zurückgezogen).
- **Akzeptanz:** T3.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| E1 | kein Ordner | – | alles flach wie bisher | T1, T2, T5, T6 |
| E1 | Ordner einer anderen Kette | – | zählt nicht | T1 |
| E2 | Ordner und flache Datei | – | nur der Ordner zählt | T2 |
| E3 | Handover an der flachen Stelle, Ordner vorhanden | Lauf ist gelaufen | gilt nicht als geschrieben (Exit ≠ 0) | T4 |
| E3 | `review_auto` mit Ordner | – | Pfade in der Ablage | – (braucht Server/API; `zusammenfuehren` darunter ist in T3 getestet) |
| E4 | Vorlagen `_vorlage_*` im Prompt | – | bleiben flach | T4, T6 |
| E4 | doppelter Ordner `…/<kt>/<kt>/` | – | kommt nicht vor | T4, T6 |
| E6 | Verdikt ohne Befundtabelle | – | kein Absturz, Gesamtbefund geschrieben | T3 |

## Testplan

Die Tests stehen in `tests/test_ablage_ordner.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. Jede Methode ist vorab rot (geprüft: 7/7). Mutationsprüfung der Referenz: 22 von 23 Mutanten gefangen (übrig: `review_auto`-Gesamtpfad, siehe Fehlerpfade).

### T1: ablage – Ordner der Kette, wenn vorhanden, sonst flach
- **Prüft:** E1
- **Aufbau:** Temp-Verzeichnis; erst ohne, dann mit Ordner `k`.
- **Erwartung:** `ablage("k")` erst `PM`, dann `PM/k`; `_ablage_rel` entsprechend; `ablage("andere")` bleibt `PM`.
- **Warum misst der Test das Richtige?** Prüft beide Zweige und dass der Ordner nur für seine Kette gilt.
- **Gegenprobe:** alter `kette.py` → rot (Funktion fehlt).

### T2: datei_suchen – sucht in der Ablage der Kette
- **Prüft:** E2
- **Aufbau:** flache Spec; dann Ordner mit eigener Spec.
- **Erwartung:** ohne Ordner die flache, mit Ordner die im Ordner (mit und ohne Datum); kein Handover → `None`.
- **Warum misst der Test das Richtige?** Beide Zweige von `datei_suchen`, und die flache Datei darf den Ordner nicht überdecken.
- **Gegenprobe:** alter `kette.py` → rot.

### T3: anforderung, Verdikt-Pfad und Gesamtbefund landen in der Ablage
- **Prüft:** E3, E6
- **Aufbau:** Ordner `k`; `anforderung(--aufgabe)`, `_freier_verdiktpfad`, `zusammenfuehren` mit einem Verdikt (intern) und mit zwei Verdikten ohne Befundtabelle.
- **Erwartung:** Dateien im Ordner, nicht flach; kein Absturz.
- **Warum misst der Test das Richtige?** Je ein Beispiel für Anlegen, Pfadwahl und beide `gesamt_`-Stellen.
- **Gegenprobe:** alter `kette.py` → rot.

### T4: umsetzung-auto – Prompt, Handover und Protokoll in der Ablage, Vorlagen bleiben
- **Prüft:** E3, E4
- **Aufbau:** `Basis`; Spec, Anforderung, Quellen per `git mv` in den Ordner `g`, committet; Lauf mit Handover im Ordner; danach Lauf mit Handover an der flachen Stelle; `_umsetzung_prompt` mit Nachbesserung.
- **Erwartung:** Exit 0, Protokoll im Ordner, Prompt nennt `docs/projekt_management/g/spec_…` und `…/g/handover_…`, nicht die flache Spec, kein `…/g/_vorlage`, kein `…/g/g/`; flacher Handover → Exit ≠ 0; Nachbesserungs-Teil nennt den Handover im Ordner.
- **Warum misst der Test das Richtige?** Der echte Ablauf über die Attrappe, inklusive der beiden typischen Fehler (Vorlage umgebogen, doppelter Ordner).
- **Gegenprobe:** alter `kette.py` → rot.

### T5: _ist_kettendatei – Kettendateien im Ordner der Kette zählen
- **Prüft:** E5
- **Aufbau:** Ordner `k`; Pfade im Ordner, in fremdem Ordner, flach.
- **Erwartung:** Prüfung/Verdikt im Ordner ja, Spec nein, fremder Ordner nein, flach weiter ja.
- **Warum misst der Test das Richtige?** Sonst blockiert eine Nacharbeit wegen „fremder“ offener Kettendateien.
- **Gegenprobe:** alter `kette.py` → rot.

### T6: role_proxy – Spec-Auftrag nennt Pfade in der Ablage
- **Prüft:** E1 (`_ablage_text`), E4 (`role_proxy`)
- **Aufbau:** `_ablage_text` ohne und mit Ordner; `role_proxy.capture_task` mit „Neue Aufgabe k: …“ bei vorhandenem Ordner.
- **Erwartung:** Vorlage bleibt flach; Anforderung im Ordner angelegt; Auftrag nennt `…/k/anforderung_…` und `…/k/spec_…`, kein `…/k/k/`.
- **Warum misst der Test das Richtige?** Der Chat-Weg (Phase A) muss dieselben Pfade nennen wie `kette.py`.
- **Gegenprobe:** alter Stand → rot.

### T7: pruefen, quellen, paket und prompt – Ausgaben und Pfade in der Ablage
- **Prüft:** E3, E4
- **Aufbau:** Temp-Git-Repo mit Ordner `k` (Spec mit Quelle, Anforderung, `src/m.py`), Commit „Spec k“; `quellen`, `pruefen` (Teile ersetzt), `paket` nach Codeänderung, `prompt("umsetzung")` ohne `pbcopy`.
- **Erwartung:** `quellen_`, `pruefung_`, `review_paket_` im Ordner (Paket nicht flach); Prompt nennt die Spec im Ordner, nicht flach.
- **Warum misst der Test das Richtige?** Deckt die übrigen schreibenden Befehle und den Hand-Prompt ab.
- **Gegenprobe:** alter `kette.py` → rot.

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
