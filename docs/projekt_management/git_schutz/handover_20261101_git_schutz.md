# Handover: git_schutz

- **Spec:** `docs/projekt_management/git_schutz/spec_20261101_git_schutz.md`
- **Datum:** 2026-11-01
- **Modell / Werkzeug:** Qwen3.6-35B-A3B-MTP-GGUF in unbeaufsichtigtem Nachtlauf
- **Rücksetzpunkt:** 7f95f7d

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1: Git-Verzeichnis bestimmen | erfüllt | `kette.py`: `GIT_SCHUTZ` (Zeile 1627), `_git_verzeichnis()` (neue Funktion vor `PROTOKOLL_RE`) |
| A2: Schnappschuss der geschützten Teile | erfüllt | `kette.py`: `_git_schutz()` (neue Funktion direkt hinter `_git_verzeichnis`) |
| A3: Einbau in `umsetzung_auto` | erfüllt | `kette.py`: `umsetzung_auto()` – Schnappschuss vor Start, nach Lauf, Befund, Protokollzeilen, Schlusszeile |
| A4: git nach dem Lauf nicht benutzbar | erfüllt | `kette.py`: `umsetzung_auto()` – `head_nach` über `subprocess.run` (kein `check=True`), Skip-Logik für (c)/(d) |

## Geänderte und neue Dateien

- `role-split/kette/kette.py` – geändert: Konstante `GIT_SCHUTZ` nach `ABGELEHNT_TEXTE`, zwei neue Funktionen `_git_verzeichnis()` und `_git_schutz()` vor `PROTOKOLL_RE`, Einbau in `umsetzung_auto()` (Schnappschuss, Befund, Protokoll, Schluss, sichere `head_nach`, Skip-Logik). Keine Zeile der Datei wurde durch Neuschreiben ersetzt.

## Abweichungen von der Spec

- Keine. Alle Anforderungen A1–A4 wurden wie spezifiziert umgesetzt.
- Die Spec nennt als Einbaustelle für A3.1 „unmittelbar vor `head_vor = …`". Die Umsetzung fügt `gitdir = _git_verzeichnis()` und `schutz_vor = _git_schutz(gitdir)` exakt davor ein – wie verlangt.
- Die Spec fordert für A4, dass `head_nach` nicht mehr über `_git()` geht. Die Umsetzung verwendet `subprocess.run` mit `check=False` und prüft `returncode == 0`.

## Annahmen

- Keine eigenen Annahmen getroffen. Konstanten, Formate und Schnittstellen ausschließlich aus Spec, Quellen und bestehendem Code übernommen.

## Getestet (mit echter Ausgabe)

**T1: Unverändertes Git-Verzeichnis – Lauf OK, Zeile „Git-Schutz: unverändert"** – bestanden

**T2: git config user.name Test (Fall vom 27.10.) – lauter Befund, Exit 1, nichts zurückgesetzt** – bestanden

**T3: hooks/ – neuer Hook, nur ausführbar gemacht, Symlink, gelöscht** – bestanden

**T4: info/ und Unterordner – auch im Nacharbeit-Lauf** – bestanden

**T5: Änderungen in .git/ außerhalb von config/hooks/info – kein Git-Schutz-Befund** – bestanden

**T6: config kaputt – kein Absturz, Befund, Protokollzeile, (c)/(d) übersprungen** – bestanden

**T7: Git-Verzeichnis – Worktree nutzt das des Hauptrepos; nicht bestimmbar → Exit 2, kein Start** – bestanden

**T8: Standardwerte im echten Pfad – GIT_SCHUTZ, echtes Git-Verzeichnis, nur lesend** – bestanden

```
$ python3 -m unittest -v tests/test_git_schutz.py
test_t1_unveraendertes_git_verzeichnis_lauf_ok (tests.test_git_schutz.GitSchutzTests.test_t1_unveraendertes_git_verzeichnis_lauf_ok)
T1: Unverändertes Git-Verzeichnis – Lauf OK, Zeile „Git-Schutz: unverändert" ... ok
test_t2_git_config_user_name_test_fall_vom_27_10 (tests.test_git_schutz.GitSchutzTests.test_t2_git_config_user_name_test_fall_vom_27_10)
T2: git config user.name Test (Fall vom 27.10.) – lauter Befund, Exit 1, nichts zurückgesetzt ... ok
test_t3_hooks_neu_ausfuehrbar_symlink_geloescht (tests.test_git_schutz.GitSchutzTests.test_t3_hooks_neu_ausfuehrbar_symlink_geloescht)
T3: hooks/ – neuer Hook, nur ausführbar gemacht, Symlink, gelöscht ... ok
test_t4_info_exclude_und_unterordner_auch_in_der_nacharbeit (tests.test_git_schutz.GitSchutzTests.test_t4_info_exclude_und_unterordner_auch_in_der_nacharbeit)
T4: info/ und Unterordner – auch im Nacharbeit-Lauf ... ok
test_t5_aenderungen_ausserhalb_der_geschuetzten_teile_kein_befund (tests.test_git_schutz.GitSchutzTests.test_t5_aenderungen_ausserhalb_der_geschuetzten_teile_kein_befund)
T5: Änderungen in .git/ außerhalb von config/hooks/info – kein Git-Schutz-Befund ... ok
test_t6_config_unlesbar_kein_absturz (tests.test_git_schutz.GitSchutzTests.test_t6_config_unlesbar_kein_absturz)
T6: config kaputt – kein Absturz, Befund, Protokollzeile, (c)/(d) übersprungen ... ok
test_t7_git_verzeichnis_worktree_und_fehlt (tests.test_git_schutz.GitSchutzTests.test_t7_git_verzeichnis_worktree_und_fehlt)
T7: Git-Verzeichnis – Worktree nutzt das des Hauptrepos; nicht bestimmbar → Exit 2, kein Start ... ok
test_t8_standardwerte_im_echten_pfad (tests.test_git_schutz.GitSchutzTests.test_t8_standardwerte_im_echten_pfad)
T8: Standardwerte im echten Pfad – GIT_SCHUTZ, echtes Git-Verzeichnis, nur lesend ... ok

----------------------------------------------------------------------
Ran 8 tests in 1.559s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe git_schutz --commit 7f95f7d
<Ausgabe>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Alle Tests bauen temporäre Git-Repos und biegen `kette.ROOT` dorthin um.

## Hawe muss ausführen

- `python3 role-split/kette/kette.py gegenprobe git_schutz --commit 7f95f7d`

## Nicht getestet

- Nichts. Alle 8 Tests (T1–T8) bestanden.

## Offene Punkte / bekannte Schwächen

- Vorher/Nachher-Vergleich erkennt keine Änderung, die der Umsetzer vor Laufende selbst zurücknimmt (bewusst offen, siehe Spec „Abweichende Meinung").
- Globale Git-Konfiguration (`~/.gitconfig`) wird nicht geschützt (bewusst nicht im Auftrag).
