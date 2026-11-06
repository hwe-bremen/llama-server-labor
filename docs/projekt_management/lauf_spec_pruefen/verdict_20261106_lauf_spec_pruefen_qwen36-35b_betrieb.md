# Verdikt: lauf_spec_pruefen

- **Spec:** `spec_20261106_lauf_spec_pruefen.md`
- **Handover:** `handover_20261106_lauf_spec_pruefen.md`
- **Datum:** 2026-11-06
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/automatik.py`, `tests/test_lauf_spec_pruefen.py`

## Ergebnis

**PASS** – Die Umsetzung von K12a2 ist korrekt: Der alte Größen-Halt wurde entfernt, `spec_pruefen` wird vor der Umsetzung aufgerufen und hält bei Befunden (Exit 1) korrekt an. Keine Abweichungen von der Vorgabe.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1 | A1: lauf ruft spec-pruefen vor der Umsetzung | erfuellt | `automatik.py:159-165` |
| 2 | A2: Größen-Halt entfaellt (Konstanten weg, Docstrings) | erfuellt | `automatik.py:1-5, 133-135` |
| 3 | T1: Befunde halten vor der Umsetzung an (Exit 3) | erfuellt | `automatik.py:160-162` |
| 4 | T2: Größe nur noch Hinweis (Exit 0) | erfuellt | `automatik.py:164, 167` |
| 5 | T3: Ausgabe wie Einzelbefehl | erfuellt | `automatik.py:159` (Aufruf via Modul) |
| 6 | T4: Vorbedingungen und Exit 2 | erfuellt | `automatik.py:136-156` (unveraendert) |
| 7 | T5: Standardwerte und echter Aufruf | erfuellt | `automatik.py:13, 133` |
| 8 | T6: Trockenlauf am echten Bestand | erfuellt | `test_lauf_spec_pruefen.py:212` |

## Handover gegen Code

- „Keine Abweichung gefunden."
- Alle im Handover genannten Punkte (Löschung der Konstanten, Änderung der Docstrings, Insertion des `spec_pruefen`-Blocks) sind im Code exakt vorhanden.
- Der Hinweis „Nicht getestet: Nichts" ist korrekt; alle 6 Tests sind implementiert und laut maschineller Pruefung bestanden.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `automatik.py:159` | Import in Funktion | Der `import spec_pruefen` steht im Funktionsrumpf, um Zirkelimporte zu vermeiden. Dies ist gewollt und korrekt umgesetzt. |
| 2 | nein | nein | nein | niedrig | `automatik.py:160` | Exit-Code Pruefung | Die Pruefung `exit_spec == 1` ist spezifisch. Da `spec_pruefen` laut Spec nur Exit 0 (OK) und 1 (Befund) liefert, ist dies sicher. |
| – | nein | nein | nein | – | – | keine Befunde | – |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** Der echte Lauf mit einer Spec, die bewusst einen Befund ausloest, um die Ausgabezeile „HALT – Spec-Prüfung mit Befunden..." zu verifizieren.
- **Braucht externe Quelle:** Keine.

## Abweichende Meinung

- Keine.