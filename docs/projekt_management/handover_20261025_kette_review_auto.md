# Handover: kette_review_auto

- **Spec:** `docs/projekt_management/spec_20261025_kette_review_auto.md`
- **Datum:** 2026-10-25
- **Modell / Werkzeug:** Qwen3.6-35B-A3B-MTP-GGUF in OpenCode, Agent „Umsetzung"
- **Rücksetzpunkt:** `80916fd` (Commit „Rolle @idee (Phase 0: Idee klaeren) + RUNBOOK")

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| T14 → K1: Test umbenennen | erfüllt | `tests/test_kette_review_auto.py`, Zeile ~276 |
| T15 → K2: Test umbenennen | erfüllt | `tests/test_kette_review_auto.py`, Zeile ~293 |
| T16: „UNVOLLSTÄNDIG" mit Ä überall | erfüllt | `kette.py` Zeilen 733, 744, 746; Test Zeilen 286, 290 |
| T17: API-Prompts erste Zeile Datum/Modell | erfüllt | `prompts/review_api.md`, `prompts/review2_api.md` |
| T18: review_auto ersetzt {datum_heute}/{modell} | erfüllt | `kette.py` Zeilen 1240–1241 |
| T19: _MiniServer.do_POST Modulo-Fix | erfüllt | `tests/test_kette_review_auto.py`, Zeile 37 |
| Handover-Datei erstellen | erfüllt | `docs/projekt_management/handover_20261025_kette_review_auto.md` |

## Geänderte und neue Dateien

- `tests/test_kette_review_auto.py` – geändert: Tests K1/K2 umbenannt, `UNVOLLSTAENDIG` → `UNVOLLSTÄNDIG` (2 Stellen), `_MiniServer.do_POST` Modulo mit `max(len(...), 1)` gepatcht
- `role-split/kette/kette.py` – geändert: `UNVOLLSTAENDIG` → `UNVOLLSTÄNDIG` (3 Stellen in `zusammenfuehren` und `review_auto`), `{datum_heute}` und `{modell}` werden in `review_auto` ersetzt
- `role-split/kette/prompts/review_api.md` – geändert: erste Zeile `Datum: {datum_heute}\nDein Modellname: {modell}` eingefügt
- `role-split/kette/prompts/review2_api.md` – geändert: erste Zeile `Datum: {datum_heute}\nDein Modellname: {modell}` eingefügt
- `docs/projekt_management/handover_20261025_kette_review_auto.md` – neu: Handover-Dokument nach Vorlage

## Abweichungen von der Spec

- Keine. Alle 7 Anforderungen wurden wörtlich umgesetzt.

## Annahmen

- `dt.datetime.now().strftime("%Y-%m-%d")` liefert das korrekte heutige Datum im要求的 Format.
- `KETTE_LLM_MODEL` ist als Umgebungsvariable oder Default-String gesetzt; der Platzhalter wird direkt dort ausgelesen.

## Getestet (mit echter Ausgabe)

**T1: Endergebnis zwei gültige Läufe** – bestanden
**T2: Router nicht erreichbar** – bestanden
**T3: Ungültiger Kurztitel** – bestanden
**T4: Rote Unit-Tests Abbruch** – bestanden
**T5: Paket Voraussetzung fehlt** – bestanden
**T6: Leere Modellantwort** – bestanden
**T7: Automatisches Umbenennen** – bestanden
**T8: Fehlende Befund-Tabelle** – bestanden
**T9: Abbruch bei Lauf 2** – bestanden
**T10: Zusammenfassung Gesamt-Datei** – bestanden
**T11: Nur Loopback** – bestanden
**T12: Abgeschnittene Antwort** – bestanden
**T13: Herzschlag während Lauf** – bestanden
**K1: Lauf 1 schlägt fehl, ein Request** – bestanden
**K2: Timeout / Zeitüberschreitung** – bestanden

```
$ timeout 120 python3 -m unittest -v tests.test_kette_review_auto
test_k1_lauf1_fehlschlaegt_ein_request (tests.test_kette_review_auto.ReviewAutoTests.test_k1_lauf1_fehlschlaegt_ein_request) ... ok
test_k2_timeout_zeitueberschreitung (tests.test_kette_review_auto.ReviewAutoTests.test_k2_timeout_zeitueberschreitung) ... ok
test_t10_zusammenfassung_gesamt_datei (tests.test_kette_review_auto.ReviewAutoTests.test_t10_zusammenfassung_gesamt_datei) ... ok
test_t11_nur_loopback (tests.test_kette_review_auto.ReviewAutoTests.test_t11_nur_loopback) ... ok
test_t12_abgeschnittene_antwort (tests.test_kette_review_auto.ReviewAutoTests.test_t12_abgeschnittene_antwort) ... ok
test_t13_herzschlag_waehrend_lauf (tests.test_kette_review_auto.ReviewAutoTests.test_t13_herzschlag_waehrend_lauf) ... ok
test_t1_endergebnis_zwei_gueltige_laeufe (tests.test_kette_review_auto.ReviewAutoTests.test_t1_endergebnis_zwei_gueltige_laeufe) ... ok
test_t2_router_nicht_erreichbar (tests.test_kette_review_auto.ReviewAutoTests.test_t2_router_nicht_erreichbar) ... ok
test_t3_ungueltiger_kurztitel (tests.test_kette_review_auto.ReviewAutoTests.test_t3_ungueltiger_kurztitel) ... ok
test_t4_rote_unit_tests_abbruch (tests.test_kette_review_auto.ReviewAutoTests.test_t4_rote_unit_tests_abbruch) ... ok
test_t5_paket_voraussetzung_fehlt (tests.test_kette_review_auto.ReviewAutoTests.test_t5_paket_voraussetzung_fehlt) ... ok
test_t6_leere_modellantwort (tests.test_kette_review_auto.ReviewAutoTests.test_t6_leere_modellantwort) ... ok
test_t7_automatisches_umbenennen (tests.test_kette_review_auto.ReviewAutoTests.test_t7_automatisches_umbenennen) ... ok
test_t8_fehlende_befund_tabelle (tests.test_kette_review_auto.ReviewAutoTests.test_t8_fehlende_befund_tabelle) ... ok
test_t9_abbruch_bei_lauf_2 (tests.test_kette_review_auto.ReviewAutoTests.test_t9_abbruch_bei_lauf_2) ... ok

----------------------------------------------------------------------
Ran 15 tests in 1.315s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe kette_review_auto --commit 80916fd
Keine geaenderten Code-Dateien seit 80916fd.
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Alle Tests laufen isoliert gegen lokale Mock-Server.

## Hawe muss ausführen

- `python3 role-split/kette/kette.py gegenprobe kette_review_auto --commit <neuer-Commit-Hash>` nach dem Commit der Änderungen.

## Nicht getestet

- T14 (ursprünglicher Name, jetzt K1) – durch K1 ersetzt
- 25.10. Nachtrag: „Prompt-Test im Terminal" – erfordert echten Router-Lauf, wurde nicht ausgeführt

## Offene Punkte / bekannte Schwächen

- **Bekannte Grenze:** Das Review sieht nur das Review-Paket. `paket` schließt `tests/` und `role-split/` aus → falsche A4/A5-Fehlberichte (werden in K9 behoben).
- **Bekannte Grenze:** `paket` schließt `docs/projekt_management/` aus → A2-Prüfung der Unit-Tests erfolgt nicht im Paket (absichtliche Design-Entscheidung).
- **Bekannte Grenze:** `review_auto` erfordert einen laufenden Router auf 127.0.0.1:8080 für echte Läufe; Tests mocken dies.
