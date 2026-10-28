# Handover: paket_vollstaendig

- **Spec:** `docs/projekt_management/spec_20261025_paket_vollstaendig.md`
- **Datum:** 2026-10-26
- **Modell / Werkzeug:** Erstumsetzung + NB1 + NB2 (abgebrochen): unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL in OpenCode. **Rest von NB2: Claude (Übernahme nach RUNBOOK-Regel, Hawe hat zugestimmt).**
- **Rücksetzpunkt:** Commit „Spec paket_vollstaendig" (`kette.py` findet ihn selbst). `1b2e74c` ist ein Checkpoint, den OpenCode trotz „Kein Commit" selbst angelegt hat.

## Warum Übernahme

NB2 lief ~4,5 h (ab 17:00) ohne Abschluss. Dabei war `_is_chain_file()` entstanden, das `role-split/` pauschal zur Kette zählte (gegen Spec A1/A5), T1/T4/T5/T9 waren rot, die Tests nicht nach Spec nummeriert und mit Python 3.10 nicht lauffähig (f-Strings mit Backslash).

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1 | erfüllt | `kette.py`: `_git`, `_aenderungen` (3 Quellen: Commits seit Rücksetzpunkt, nicht committet, unversioniert; Kurztitel als ganzes Wort), `_diff` |
| A2 | erfüllt | `kette.py`: `_diff`/`_kappen` (Marker „nicht in der Uebergabe genannt") |
| A3 | erfüllt | `kette.py`: `_vorrang`, Kürzung in `paket` (erst V3, dann V2, Dateiweise, bis Gesamtpaket ≤ 80 000; V1 nie) |
| A4 | erfüllt | `kette.py`: `KETTE_PAKET_MAX` (Env, Standard 150 000), Exit 1 **vor** dem Schreiben |
| A5 | erfüllt | `kette.py`: `gegenprobe` nutzt dieselbe Auswahl `_aenderungen` (inkl. `role-split/kette/`, ohne fremde Dateien) |
| A6 | erfüllt | `test_kette.py`: ein Test bewusst ersetzt (s. u.), sonst unverändert aus `84e3bb7` |
| A7 | erfüllt | `kette.py`: `paket` – Exit 1 „Paket ohne Code trotz Aenderungen", wenn nur fremde Änderungen vorliegen |
| A8 | offen | Abnahme T10 durch Hawe |
| Zusatz | erfüllt | `max_tokens` (`KETTE_LLM_MAX_TOKENS`, Standard 8000) im API-Aufruf – jetzt mit Test K3 |

## Geänderte und neue Dateien

- `role-split/kette/kette.py` – geändert – `_is_chain_file` u. a. ersetzt durch `_git`, `_aenderungen`, `_vorrang`, neues `_diff`; `paket` mit Abschnitten 3a/3b, Kürzung, A4/A7; `gegenprobe` auf gemeinsame Auswahl umgestellt.
- `role-split/kette/test_kette.py` – geändert – Stand `84e3bb7`; `test_paket_nur_dateien_aus_handover_und_nie_werkzeug` ersetzt durch `test_paket_alle_kette_dateien_mit_markierung_und_fremde_liste` (A1 verlangt jetzt alle Kette-Dateien).
- `tests/test_paket_vollstaendig.py` – neu geschrieben – T1–T9 nach Spec plus K1 (nur docs/ → Exit 0), K2 (Kurztitel als ganzes Wort); Verhaltenstests mit Wegwerf-Git-Repos, Python ≥ 3.10.
- `tests/test_kette_review_auto.py` – geändert – `_MiniServer` merkt sich Request-Bodies; Test K3 `max_tokens`.

## Abweichungen von der Spec

- **Nicht committete/unversionierte Dateien zählen immer zur Kette** (Spec A1). Folge: Wer ein Paket für eine *alte* Kette baut, während andere Arbeit uncommittet herumliegt, bekommt diese Arbeit mit ins Paket. Probe: `paket mail_server_test` mit uncommittetem K9-Stand → 175 161 Zeichen → Exit 1. **Vor T10 also K9 committen.**
- Keine Code-Änderung überhaupt (nur docs/) → Exit 0 mit „Geaenderte Code-Dateien: keine" (wie bisher), nicht Exit 1.

## Annahmen

- Vorrang 1 = in der Übergabe genannt **oder** außerhalb `tests/`; Vorrang 2 = `.py/.sh/.command` unter `tests/`; Vorrang 3 = übrige Testdaten.
- Die Übergabe-Liste kommt aus dem neuesten Handover der Kette.

## Getestet (mit echter Ausgabe)

Testtitel **exakt wie in der Spec**.

**T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)** – bestanden

**T2: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte** – bestanden

**T3: Handover-Datei ohne Markierung, fremde Datei mit Markierung** – bestanden

**T4: Vorrang-Kürzung – Vorrang 3 wird weggelassen** – bestanden

**T5: KETTE_PAKET_MAX überschritten → Exit 1** – bestanden

**T6: Gegenprobe berücksichtigt role-split/kette/** – bestanden

**T7: Bestehende Tests in test_kette.py bleiben grün** – bestanden

**T8: Fremde Commits nur als Liste** – bestanden

**T9: Paket ohne Code trotz Änderungen → Exit 1** – bestanden

```
$ python3 -m unittest -v tests.test_paket_vollstaendig
K1: Nur docs/ geaendert -> Exit 0, 'keine Code-Dateien' ... ok
K2: Kurztitel 'g' trifft nicht 'gross' -> Datei aus 'gross init' ist fremd ... ok
T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel) ... ok
T2: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte ... ok
T3: Handover-Datei ohne Markierung, fremde Datei mit Markierung ... ok
T4: Vorrang-Kürzung – Vorrang 3 wird weggelassen ... ok
T5: KETTE_PAKET_MAX überschritten → Exit 1 ... ok
T6: Gegenprobe berücksichtigt role-split/kette/ ... ok
T7: Bestehende Tests in test_kette.py bleiben grün ... ok
T8: Fremde Commits nur als Liste ... ok
T9: Paket ohne Code trotz Änderungen → Exit 1 ... ok
Ran 11 tests in 0.833s
OK

$ python3 -m unittest tests.test_kette_review_auto
Ran 16 tests in 1.053s

OK

$ python3 role-split/kette/test_kette.py
Ran 40 tests in 0.553s

OK
```

**Probelauf am K7-Stand** (Wegwerf-Klon, K9 dort committet): `paket mail_server_test` → Exit 0, 137 634 Zeichen (~39k Token), Warnung > 80 000; 10 fremde Dateien nur gelistet (u. a. `kette.py`, `mcp-server/…`); weggelassen: `tests/mail_server_test/einliefern.py` (V2, nicht in der Übergabe). Die 16 Mails bleiben drin, weil der K7-Handover sie nennt (V1).

## Nicht getestet

- **T10: Abnahme – echter Lauf am K7-Stand (Hawe, manuell)** – braucht Router + 35B, macht Hawe.

## Offene Punkte

- Phase G: Messwerte 27B (Erstumsetzung 2 h 45, NB1 ~4,5 h, NB2 ~4,5 h ohne Abschluss) und OpenCode-Selbstcommit `1b2e74c` in die Learnings.
- Nach K9: `experiments/k8_paket_ergaenzen.py` löschen.
