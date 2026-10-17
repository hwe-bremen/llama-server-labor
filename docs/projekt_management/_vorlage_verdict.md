# Verdikt: <kurztitel>

- **Spec:** `spec_<JJJJMMTT>_<kurztitel>.md`
- **Handover:** `handover_<JJJJMMTT>_<kurztitel>.md`
- **Datum:** <JJJJ-MM-TT>
- **Modell:** <Modellname aus dem System-Prompt>
- **Geprüfte Dateien:** <Liste der tatsächlich gelesenen Code-Dateien>

Dateiname: `verdict_<JJJJMMTT>_<kurztitel>_<modellkürzel>.md`

## Ergebnis

**PASS | NACHBESSERN | FAIL** – ein bis zwei Sätze Begründung.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1 | … | erfüllt / teilweise / nicht | `datei.py:42` |

## Handover gegen Code

- <Aussagen im Handover, die der Code nicht stützt. „Keine Abweichung gefunden", wenn so.>
- <Behauptete Tests ohne Ausgabe gelten als nicht belegt.>

## Befunde

Für **jeden** Befund drei Fragen mit ja/nein beantworten. Ein „ja" macht den Befund „hoch", unabhängig davon,
ob die Schwäche schon vorher bestand. `kette.py urteil` prüft das nach.
- **Datenverlust:** Kann Daten verlieren, überschreiben oder echte Daten verändern?
- **Unbemerkt:** Kann ein Fehler unbemerkt bleiben (Hänger, Schweigen, falscher Exit-Code, Test misst nichts)?
- **Harte Vorgabe:** Verstößt es gegen eine harte Vorgabe der Spec oder des Auftrags (z. B. kein echter Versand)?

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | ja / nein | ja / nein | ja / nein | hoch / mittel / niedrig | | | |

## Nicht geprüft

- **Kann Hawe selbst prüfen:** <Test, Lauf, Blick in Datei>
- **Braucht externe Quelle:** <Doku, Recherche, frische Instanz>

## Abweichende Meinung

- <Wo die Review-Instanz anders entschieden hätte, auch bei PASS. „Keine", wenn keine.>
