Verdict: pruefen_venv

- **Spec:** `spec_20261107_pruefen_venv.md`
- **Handover:** `handover_20261107_pruefen_venv.md`
- **Datum:** 2026-11-07
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `tests/test_pruefen_venv.py`

## Ergebnis

**PASS** – Die Implementierung in `kette.py` entspricht exakt der Spec. Die Funktion `test_python` sucht korrekt aufwaerts bis `ROOT` und gibt den relativen Pfad zurueck, ohne ihn aufzuloesen. Die Aufrufe in `tests_laufen` und `unittest_lauf` sind korrekt angepasst. Alle 6 Tests bestanden.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1 | A1: `test_python` Auswahl des Pythons | erfuellt | `kette.py:392-412` |
| 2 | A2: Testläufe mit `test_python` | erfuellt | `kette.py:417`, `kette.py:624-627` |

## Handover gegen Code

- Keine Abweichung gefunden.
- Behauptete Tests (T1-T6) sind im Skript vorhanden und liefen gruene.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `kette.py:400` | Symlink-Verhalten | `test_python` gibt den Pfad nicht aufloest, was gewollt ist. Falls `.venv/bin/python` ein Symlink ist, bleibt der Symlink-Pfad erhalten. Dies ist laut Spec korrekt ("nicht aufgelöst"). Kein Fehler. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** `kette.py pruefen pruefen_venv` im echten Projektkontext mit aktivem `.venv`.
- **Braucht externe Quelle:** Keine.

## Abweichende Meinung

Keine.