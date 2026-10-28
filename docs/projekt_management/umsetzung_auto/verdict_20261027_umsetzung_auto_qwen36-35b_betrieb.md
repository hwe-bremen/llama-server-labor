Verdict: umsetzung_auto (Betrieb)

- **Spec:** `spec_20261027_umsetzung_auto.md`
- **Handover:** `handover_20261027_umsetzung_auto.md`
- **Datum:** 2026-10-27
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `role-split/kette/testdata/opencode_fake.py`, `tests/test_umsetzung_auto.py`, `.opencode/agents/umsetzung_nacht.md`, `role-split/kette/prompts/umsetzung_nacht.md`, `role-split/kette/RUNBOOK.md`

## Ergebnis

**PASS** – Die Umsetzung ist robust, sicher und deckt alle kritischen Pfade (Timeout, Schreibbereich, Halt-Regel) ab. Die technische Sperre der Attrappe und die strikte Trennung von Vorab-Prüfung und Lauf geben Sicherheit.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1 | Neuer Befehl `kette.py umsetzung-auto` | erfuellt | `kette.py:1918` |
| 2 | Vorab-Prüfung (Commit, Schreibbereich, Stand, opencode, Modell) | erfuellt | `kette.py:1510-1560` |
| 3 | Agent deny-Regeln & Vorrang | erfuellt | `.opencode/agents/umsetzung_nacht.md` |
| 4 | Zeitlimits (Lauf & Befehl) | erfuellt | `kette.py:1566`, `kette.py:1640` |
| 5 | JSON-Auswertung & Protokoll | erfuellt | `kette.py:1615-1680` |
| 6 | Mechanische Prüfung (HEAD, Schreibbereich, Handover, pruefen) | erfuellt | `kette.py:1685-1730` |
| 7 | Nacharbeit & Halt-Regel | erfuellt | `kette.py:1562-1565`, `kette.py:1585` |
| 8 | Lebendsignal | erfuellt | `kette.py:1635`, `kette.py:1650` |
| 9 | Exit-Codes (0, 1, 2) | erfuellt | `kette.py:1735` |
| 10 | LERNREGELN im Prompt | erfuellt | `prompts/umsetzung_nacht.md:4` |
| 11 | RUNBOOK & Vorlagen | erfuellt | `RUNBOOK.md:125` |

## Handover gegen Code

- Keine Abweichung gefunden.
- Behauptete Tests (T1–T21) sind im Code implementiert und laufen grün.
- Die im Handover genannte "Abweichung" (Leseregel im Prompt) ist gewollt und im Code (Prompt-Datei) umgesetzt.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `kette.py:1640` | Timeout-Behandlung: `proc.wait()` nach Kill kann blockieren, wenn Kind-Prozess sich nicht sofort beendet. In der Praxis ist dies akzeptabel, da der Hauptprozess (opencode) tot ist. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** Echter Lauf mit dem 35B an einer Mini-Spec (wie in Anforderung gefordert).
- **Braucht externe Quelle:** Verhalten von `opencode` bei sehr langen Ausgaben oder spezifischen JSON-Format-Abweichungen in neueren Versionen.

## Abweichende Meinung

- Keine.