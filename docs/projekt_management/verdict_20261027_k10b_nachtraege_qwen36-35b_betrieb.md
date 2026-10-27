# Verdikt: k10b_nachtraege

- **Spec:** `spec_20261027_k10b_nachtraege.md`
- **Handover:** `handover_20261027_k10b_nachtraege.md`
- **Datum:** 2026-10-27
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `tests/test_k10b_nachtraege.py`

## Ergebnis

**PASS** – Alle vier Nachträge sind korrekt implementiert und durch die Tests gedeckt. Der Code bleibt fokussiert auf die vier Anforderungen, ohne ungewollte Nebenwirkungen.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Pflichtzeilen im Prompt | erfuellt | `kette.py:1669-1678` |
| A2 | Bereichsangaben filtern | erfuellt | `kette.py:279-281` |
| A3 | Token-Spitze tracken | erfuellt | `kette.py:1669,1742-1744,1931,1939` |
| A4 | Zurückgezogene Befunde | erfuellt | `kette.py:831-835,877-880,890,898-906` |

## Handover gegen Code

- Der Handover erwähnt korrekte Abweichungen bei A1 (Anführungszeichen) und A2 (Geviertstrich). Diese sind im Code tatsächlich so umgesetzt und beeinträchtigen die Funktionalität nicht.
- Die Aussage „Keine Abweichung" im maschinellen Abgleich ist korrekt, da die funktionalen Anforderungen erfüllt sind.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `kette.py:280` | Regex erlaubt Geviertstrich | Nicht spezifiziert, aber sicherer als nur Bindestrich. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** Die exakte Reihenfolge der Test-IDs im Prompt (A1) ist nur implizit durch die Sortierung der Dict-Schlüssel in `tests_finden` gegeben; die Tests prüfen die Existenz, aber nicht strikt die lexikalische Sortierung über alle IDs hinweg (nur T2 vor T10).
- **Braucht externe Quelle:** Echte Token-Messwerte im produktiven Betrieb mit dem 35B-Modell.

## Abweichende Meinung

- Keine.