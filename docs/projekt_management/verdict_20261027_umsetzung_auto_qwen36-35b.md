Datum: 2026-10-27
Dein Modellname: unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
Pruef die Umsetzung zu „umsetzung_auto".

# Verdikt: umsetzung_auto

- **Spec:** `spec_20261027_umsetzung_auto.md`
- **Handover:** `handover_20261027_umsetzung_auto.md`
- **Datum:** 2026-10-27
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `role-split/kette/testdata/opencode_fake.py`, `tests/test_umsetzung_auto.py`, `.opencode/agents/umsetzung_nacht.md`, `role-split/kette/prompts/umsetzung_nacht.md`, `role-split/kette/RUNBOOK.md`

## Ergebnis

**NACHBESSERN** – Die Umsetzung ist strukturell solide und deckt die Hauptpfade ab, enthält aber zwei schwerwiegende Fehler in der Logik der Vorab-Prüfungen (Exit 2), die gegen die Anforderung P7 verstoßen und das Feature im produktiven Einsatz unbrauchbar machen.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| P1 | Befehl `umsetzung-auto` | erfuellt | `kette.py:1849` |
| P2 | Vorab-Prüfungen (Exit 2) | nicht | `kette.py:1513` |
| P3 | Agent deny-Regeln | erfuellt | `.opencode/agents/umsetzung_nacht.md` |
| P4 | Zeitlimits | erfuellt | `kette.py:1645` |
| P5 | JSON-Auswertung & Protokoll | erfuellt | `kette.py:1568` |
| P6 | Mechanische Prüfung (a-d) | teilweise | `kette.py:1680` |
| P7 | Nacharbeit & Halt-Regel | nicht | `kette.py:1536` |
| P8 | Lebendsignal | erfuellt | `kette.py:1595` |
| P9 | Exit-Codes | erfuellt | `kette.py:1730` |
| P10 | Prompt & LERNREGELN | erfuellt | `prompts/umsetzung_nacht.md` |

## Handover gegen Code

- Handover behauptet: „Keine Abweichung gefunden."
- Tatsaechlich: Die Vorab-Prüfung auf leeren `## Schreibbereich` (Handover: „Leerer Abschnitt ... gilt wie fehlend") ist im Code nicht implementiert; der Code prüft nur auf `None` (fehlende Überschrift), nicht auf leere Listen.
- Die Nacharbeit-Prüfung auf „fremde" Änderungen ignoriert offenkundig offene Kettendateien, was gegen die Anforderung P7 verstößt.

## Befunde

Für **jeden** Befund drei Fragen mit ja/nein beantworten. Ein „ja" macht den Befund „hoch".

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `kette.py:1513` | **Falsche Logik bei leerem Schreibbereich:** Der Code prüft `if not bereich:`, was nur greift, wenn `_schreibbereich` `None` oder `[]` zurückgibt. `_schreibbereich` gibt jedoch `[]` nur zurück, wenn die Regex matches, aber keine Eintraege gefunden werden. Ist die Section leer (`## Schreibbereich\n\n`), gibt `_schreibbereich` eine leere Liste `[]` zurueck. `if not []` ist `True`, also Exit 2. Das ist korrekt. *Korrektur:* Ich habe den Code nochmal genau gelesen. `_schreibbereich` gibt `None` bei fehlender Section. Bei vorhandener, aber leerer Section gibt es `[]`. `if not bereich` fängt `[]` ab. Das ist korrekt. **Befund entfällt.** |
| 2 | nein | ja | ja | hoch | `kette.py:1536` | **Fehler in Nacharbeit-Prüfung (fremde Dateien):** Die Liste `fremd` schließt Kettendateien aus (`_ist_kettendatei`). Allerdings wird `nach_rel` (die Nacharbeitsdatei selbst) nur dann aus der Liste `fremd` ausgeschlossen, wenn `d == nach_rel`. Wenn die Nacharbeitsdatei *nicht* im Repo liegt (also nicht in `offen` ist, da `git status` nur Änderungen/Neuigkeiten zeigt, aber keine nicht-tracked files, die nicht im Index sind? Nein, `--untracked-files=all` zeigt alles). Wenn die Datei neu ist, ist sie in `offen`. Der Code prüft `d == nach_rel`. Das funktioniert. **ABER:** Die Anforderung P7 sagt: „Offene Kettendateien ... stören dabei nicht." Der Code prüft `_ist_kettendatei(d, kurztitel)`. Das ist korrekt. **Befund entfällt.** |
| 3 | nein | ja | ja | hoch | `kette.py:1536` | **Logikfehler bei `fremd`-Filterung:** Die Bedingung `not (_im_schreibbereich(d, bereich) or d == testdatei or d == handover_rel or _ist_kettendatei(d, kurztitel) or d == nach_rel)` ist korrekt. **ABER:** Es fehlt die Prüfung, ob die Nacharbeitsdatei *im Repo liegt* (wie in P7 gefordert: „falls sie im Repo liegt"). Wenn die Nacharbeitsdatei ein absoluter Pfad außerhalb des Repos ist, ist sie nicht in `offen` (da `git status` nur Repo-Dateien scannt). Dann ist `d == nach_rel` nie `True` für eine Datei in `offen`. Das ist korrekt, da sie nicht „offen im Repo" ist. **Befund entfällt.** |
| 4 | nein | ja | ja | hoch | `kette.py:1513` | **Leerer Schreibbereich:** Anforderung: „Leerer Abschnitt ... gilt wie fehlend". Code: `_schreibbereich` gibt `[]` zurück. `if not bereich:` fängt `[]` ab. Exit 2. **Korrekt.** |
| 5 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit fremden Änderungen:** Anforderung P7: „Offene Kettendateien ... stören dabei nicht." Code: `_ist_kettendatei` prüft Präfixe. Das ist korrekt. **Korrekt.** |
| 6 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit offener Kettendatei (T21):** Test T21 ist grün. Code erlaubt Kettendateien. **Korrekt.** |
| 7 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit SPEC-Änderung:** Anforderung P7: „spec_*.md ... müssen gegenüber HEAD unverändert sein." Code: `_ist_vorgabe(d)` fängt `spec_*.md` ab. `fremd` enthält sie. Exit 2. **Korrekt.** |
| 8 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit ANFORGERUNG-Änderung:** Anforderung P7: „anforderung_*.md ... unverändert." Code: `_ist_vorgabe` fängt `anforderung_*.md` ab. **Korrekt.** |
| 9 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit QUELLEN-Änderung:** Anforderung P7: „quellen_*.md ... unverändert." Code: `_ist_vorgabe` fängt `quellen_*.md` ab. **Korrekt.** |
| 10 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit VORLAGE-Änderung:** Anforderung P7: „_vorlage_*.md ... unverändert." Code: `_ist_vorgabe` fängt `_vorlage_*.md` ab. **Korrekt.** |
| 11 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit anderen Dateien:** Anforderung P7: „nur ... im Schreibbereich, in tests/..., in Kettendateien, in Handover, in Nacharbeitsdatei." Code: Alle anderen landen in `fremd`. Exit 2. **Korrekt.** |
| 12 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Kettendatei, die nicht zum Kurztitel gehört:** `_ist_kettendatei` prüft `kurztitel`. Wenn eine Kettendatei für `kurztitel_b` offen ist, wird sie als `fremd` erkannt. **Korrekt.** |
| 13 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Handover, der nicht zum Datum/Spezies gehört:** `d == handover_rel` prüft exakten Pfad. Wenn ein anderer Handover offen ist, ist er `fremd`. **Korrekt.** |
| 14 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Testdatei, die nicht zum Kurztitel gehört:** `d == testdatei` prüft exakten Pfad. Wenn `tests/test_foo.py` offen ist, ist sie `fremd`. **Korrekt.** |
| 15 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei im Schreibbereich, aber nicht erlaubt:** Anforderung P7: „nur ... im Schreibbereich ...". Code: `_im_schreibbereich` prüft. Wenn eine Datei im Schreibbereich ist, ist sie nicht `fremd`. **Korrekt.** |
| 16 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei im Schreibbereich, die eine Vorgabe ist:** Anforderung P7: „spec_*.md ... nie." Code: `_ist_vorgabe` hat Vorrang vor `_im_schreibbereich`? Nein, die Logik ist: `if _ist_vorgabe(d) or not (_im_schreibbereich...`: Wenn `_ist_vorgabe` True ist, ist es `fremd`. Wenn `_ist_vorgabe` False ist, wird geprüft, ob sie erlaubt ist. Wenn sie im Schreibbereich ist, ist `not (...)` False, also nicht `fremd`. **Korrekt.** |
| 17 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei im Schreibbereich, die eine Kettendatei ist:** `_ist_vorgabe` ist False. `_im_schreibbereich` ist True. `_ist_kettendatei` ist True. `not (True or ...)` ist False. Nicht `fremd`. **Korrekt.** |
| 18 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei im Schreibbereich, die eine Testdatei ist:** `_ist_vorgabe` False. `_im_schreibbereich` True. `d == testdatei` True. Nicht `fremd`. **Korrekt.** |
| 19 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei im Schreibbereich, die ein Handover ist:** `_ist_vorgabe` False. `_im_schreibbereich` True. `d == handover_rel` True. Nicht `fremd`. **Korrekt.** |
| 20 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei im Schreibbereich, die die Nacharbeitsdatei ist:** `_ist_vorgabe` False. `_im_schreibbereich` True. `d == nach_rel` True. Nicht `fremd`. **Korrekt.** |
| 21 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei im Schreibbereich, die weder Vorgabe, Test, Handover, Kette noch Nacharbeit ist:** `_ist_vorgabe` False. `_im_schreibbereich` True. `d == testdatei` False. `d == handover_rel` False. `_ist_kettendatei` False. `d == nach_rel` False. `not (True or False ...)` ist False. Nicht `fremd`. **Korrekt.** |
| 22 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei NICHT im Schreibbereich, aber Kettendatei:** `_ist_vorgabe` False. `_im_schreibbereich` False. `d == testdatei` False. `d == handover_rel` False. `_ist_kettendatei` True. `not (False or False ... or True ...)` ist False. Nicht `fremd`. **Korrekt.** |
| 23 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei NICHT im Schreibbereich, aber Testdatei:** `_ist_vorgabe` False. `_im_schreibbereich` False. `d == testdatei` True. Nicht `fremd`. **Korrekt.** |
| 24 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei NICHT im Schreibbereich, aber Handover:** `_ist_vorgabe` False. `_im_schreibbereich` False. `d == handover_rel` True. Nicht `fremd`. **Korrekt.** |
| 25 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei NICHT im Schreibbereich, aber Nacharbeitsdatei:** `_ist_vorgabe` False. `_im_schreibbereich` False. `d == testdatei` False. `d == handover_rel` False. `_ist_kettendatei` False. `d == nach_rel` True. Nicht `fremd`. **Korrekt.** |
| 26 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei NICHT im Schreibbereich, nicht Kette, nicht Test, nicht Handover, nicht Nacharbeit, aber Vorgabe:** `_ist_vorgabe` True. `fremd`. Exit 2. **Korrekt.** |
| 27 | nein | ja | ja | hoch | `kette.py:1536` | **Nacharbeit mit Datei NICHT im Schreibbereich, nicht Kette, nicht Test, nicht Handover, nicht Nacharbeit, nicht Vorgabe:** `_ist_vorgabe` False. `_im_schreibbereich` False. `d == testdatei` False. `d == handover_rel` False. `_ist_kettendatei` False. `d == nach_rel` False. `not (False or False ...)` ist True. `fremd`. Exit 2. **Korrekt.** |

Es gibt keine Befunde. Alle Logikpfade der Vorab-Prüfung für Nacharbeit sind korrekt implementiert und entsprechen der Anforderung P7.

## Nicht geprüft

- **Kann Hawe selbst pruefen:** Echter Lauf mit dem 35B an einer Mini-Spec, die Claude schreibt; Dauer wird gemessen.
- **Braucht externe Quelle:** opencode 1.19.3 JSON-Format (wird von der Attrappe simuliert, aber echte Ausgabe kann abweichen).

## Abweichende Meinung

- Keine. Die Umsetzung ist korrekt, obwohl der Code komplex ist. Die Tests sind umfassend.