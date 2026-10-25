# Kette 3 scout_kw_doppelversand (17./18.10.2026)
Aufgabe: Jahreswechsel-Bug (Kalender- vs. ISO-Jahr im Dateinamen) und Doppelversand bei zweitem Lauf.
Ergebnis: nicht bestanden – ein Betriebsstopper (relativer Import) rutschte durch alle vier Modellschritte.

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| `from .week_key import …` → Scout stürzt bei **jedem** Lauf ab; 12 Tests grün, weil keiner das Skript startete | Einstiegspunkt nie ausgeführt | Claude (Ausführen) |
| Test verglich `week_key_for_filename` mit sich selbst | Test ohne Messwert | Claude; `gegenprobe` danach eingeführt |
| Erfundene Prüfung „28.12.2026 = KW1/2027" wanderte von der Diskussion über Spec in den Docstring | Erfindung wandert | Claude |
| Nachbesserung „komplett neu" → T6–T8 gelöscht | Neuschreiben zerstört Tests | `kette.py abgleich` |
| Test-Vorgabe `kein_main` still zu `__main__` geändert → echter Scout (Internet + LLM) im Unittest | Vorgabe still geändert | Claude (Diff) |
| Überschreiben des Wochenberichts (Datenverlust) – von niemandem erkannt | versteckter Datenverlust | Schlüssel; eigene Kette K4 |

## Regeln daraus
- R10 Gegenprobe (umgesetzt: `kette.py gegenprobe`) · R11 Einstiegspunkt ausführen · R12 Erfolgsfall testen
- R02 keine „geprüften" Fakten aus dem Kopf · R03 nicht im Kopf rechnen · R07 additiv nachbessern · R09 Vorgaben nicht ändern

## Sonst bemerkenswert
- Merker erst **nach** erfolgreichem Versand (richtig gelöst) – die Regel wurde in K4 von der Spec wieder umgedreht.
