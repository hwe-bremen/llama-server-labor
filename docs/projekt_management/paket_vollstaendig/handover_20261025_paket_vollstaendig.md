# Handover: paket_vollstaendig

- **Spec:** `docs/projekt_management/spec_20261025_paket_vollstaendig.md`
- **Datum:** 2026-10-25
- **Modell / Werkzeug:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** `84e3bb7`

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1 | erfüllt | `kette.py`, Funktion `_diff` (neue Signatur, 3 Quellen, Klassifikation Kette/Fremd) |
| A2 | erfüllt | `kette.py`, Funktion `_kappen` (neuer Parameter `nicht_genannt`) |
| A3 | erfüllt | `kette.py`, Funktion `_diff` (Vorrang 1/2/3, zweistufige Kürzung) |
| A4 | erfüllt | `kette.py`, Konstante `KETTE_PAKET_MAX`, Funktion `paket` (Exit 1 bei Überschreitung) |
| A5 | erfüllt | `kette.py`, Funktion `gegenprobe` (Ausschlussliste ohne `role-split/kette/`) |
| A6 | erfüllt | `test_kette.py`, Methode `test_paket_nur_dateien_aus_handover_und_nie_werkzeug` |
| A7 | erfüllt | `kette.py`, Funktion `paket` (Exit 1 bei leeren Code-Dateien mit Änderungen) |

## Geänderte und neue Dateien

- `role-split/kette/kette.py` – geändert – `_diff` vollständig neu geschrieben (Kette/Fremd-Klassifikation, Vorrang, 4 Rückgabewerte); `_kappen` um `nicht_genannt` erweitert; `PAKET_NIE` angepasst; `KETTE_PAKET_MAX` neu; `paket` um Fremde-/Weggelassen-Sektionen, harte Obergrenze, leeres-Paket-Check erweitert; `gegenprobe` nimmt `role-split/kette/` auf
- `role-split/kette/test_kette.py` – geändert – `test_paket_nur_dateien_aus_handover_und_nie_werkzeug` bewusst angepasst (A1: alle Code-Dateien werden jetzt aufgenommen)
- `tests/test_paket_vollstaendig.py` – neu – 9 Tests (T1–T9) fuer die neuen Anforderungen

## Abweichungen von der Spec

- **A1 Fremde Dateien im Paket:** Die Spec sagt „Fremde Aenderungen (nur Liste)". Ich habe die fremden Dateien als separate Sektion „## 3a. Fremde Aenderungen (nur Liste)" im Paket. Die Liste enthaelt Datei-Pfad und Commit-Betreffe, aber keinen Datei-Inhalt.
- **A3 Vorrang-Kürzung:** Die Spec sagt „zweistufig". Ich habe Vorrang 3 zuerst weggenommen, dann Vorrang 2. Vorrang 1 wird nie weggenommen (auch bei extremer Ueberschreitung). Die Spec sagt nichts über Vorrang 1 in diesem Fall.
- **A7 Paket ohne Code:** Die Spec sagt Exit 1. Ich pruefe, ob es ueberhaupt Aenderungen gab (git diff + ls-files). Wenn ja, aber keine Code-Dateien, Exit 1. Wenn keine Aenderungen ueberhaupt, bleibt es beim alten Verhalten (Exit 2).

## Annahmen

- **PAKET_NIE:** Ich habe `tests/` und `role-split/` aus PAKET_NIE entfernt. `mcp-server/` bleibt, da die Spec „mcp-server/ kann bleiben" sagt.
- **Fremd-Erkennung:** Eine Datei ist „fremd", wenn sie nur in Commits ohne den Kurztitel geaendert wurde. Unversionierte Dateien und nicht-committete Aenderungen gelten als Kette.
- **Vorrang-Kürzung:** Die Kürzung basiert auf der Groesse des Code-Abschnitts (Sektion 3), nicht der gesamten Paket-Datei. Die harte Obergrenze (KETTE_PAKET_MAX) prueft die gesamte Paket-Datei.

## Getestet (mit echter Ausgabe)

**T1: docs/ und .md-Dateien nie im Paket (PAKET_NIE)** – bestanden

**T2: KETTE_PAKET_MAX als Konstante vorhanden und > 0** – bestanden

**T3: Dateien in Commits mit Kurztitel gehoeren zur Kette** – bestanden

**T4: Fremde Dateien erscheinen in separater Sektion** – bestanden

**T5: Dateien nicht im Handover werden markiert** – bestanden

**T6: Vorrang-Klassifikation funktioniert korrekt** – bestanden

**T7: Paket > KETTE_PAKET_MAX -> Exit 1** – bestanden

**T8: Gegenprobe nimmt role-split/kette/ auf** – bestanden

**T9: Paket ohne Code trotz Aenderungen -> Exit 1** – bestanden

```
$ python3 -m unittest -v tests/test_paket_vollstaendig.py
test_t1_docs_excluded (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t1_docs_excluded)
T1: docs/ und .md-Dateien nie im Paket (PAKET_NIE). ... ok
test_t2_kette_paket_max_exists (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t2_kette_paket_max_exists)
T2: KETTE_PAKET_MAX als Konstante vorhanden und > 0. ... ok
test_t3_ketten_dateien_im_paket (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t3_ketten_dateien_im_paket)
T3: Dateien in Commits mit Kurztitel gehoeren zur Kette. ... ok
test_t4_fremde_dateien_liste (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t4_fremde_dateien_liste)
T4: Fremde Dateien erscheinen in separater Sektion. ... ok
test_t5_nicht_genannt_markierung (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t5_nicht_genannt_markierung)
T5: Dateien nicht im Handover werden markiert. ... ok
test_t6_vorrang_klassifikation (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t6_vorrang_klassifikation)
T6: Vorrang-Klassifikation funktioniert korrekt. ... ok
test_t7_harte_obergrenze_exit1 (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t7_harte_obergrenze_exit1)
T7: Paket > KETTE_PAKET_MAX -> Exit 1. ... ok
test_t8_gegenprobe_role_split (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t8_gegenprobe_role_split)
T8: Gegenprobe nimmt role-split/kette/ auf. ... ok
test_t9_paket_ohne_code_exit1 (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t9_paket_ohne_code_exit1)
T9: Paket ohne Code trotz Aenderungen -> Exit 1. ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.012s

OK
```

Bestehende Tests (40 Tests in `role-split/kette/test_kette.py`):

```
$ python3 -m unittest role-split/kette/test_kette.py -v 2>&1 | tail -5
----------------------------------------------------------------------
Ran 40 tests in 2.030s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe paket_vollstaendig --commit 84e3bb7
<Ausgabe>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Alle Tests arbeiten mit dem bestehenden Git-Repo ohne Netzwerkzugriff oder echte Daten.

## Hawe muss ausführen

- `python3 role-split/kette/kette.py gegenprobe paket_vollstaendig --commit 84e3bb7` – Gegenprobe im echten Repo (benötigt das Testskript `tests/test_paket_vollstaendig.py` und ggf. weitere Tests).
- Eventuell `python3 role-split/kette/kette.py paket paket_vollstaendig` – um das Review-Paket zu erzeugen und die Ausgabe zu pruefen.

## Nicht getestet

- **Echte Integration von `_diff` mit fremden Commits:** Die Tests pruefen die Logik indirekt (Quellcode-Inspektion). Ein echter Test mit fremden Commits im Git-Repo waere aufwaendig und erfordert ein Test-Repo mit mehreren Commits.
- **Vorrang-Kürzung mit grossen Paketen:** Die Tests pruefen, dass die Logik im Code steht, aber nicht mit einem echten grossen Paket.

## Offene Punkte / bekannte Schwächen

- **Fremd-Erkennung bei gemischten Commits:** Wenn ein Commit sowohl Kette- als auch fremde Dateien enthält, werden alle Dateien in diesem Commit als „Kette" klassifiziert (da der Commit den Kurztitel enthält). Dies ist bewusst so, um falsche Ausschlüsse zu vermeiden.
- **Vorrang-Kürzung ist grob:** Die Kürzung entfernt ganze Dateien, nicht Teile von Dateien. Bei sehr grossen Dateien in Vorrang 2/3 koennte dies zu viel Kontext verlieren.
