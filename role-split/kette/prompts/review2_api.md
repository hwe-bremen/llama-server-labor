Datum: {datum_heute}
Dein Modellname: {modell}
Zweites Review zu „{kurztitel}" – Blickwinkel BETRIEB.

Paket-Text:

{paket_text}

1. Echte Abhaengigkeiten statt Attrappen? Gibt es echte Abhaengigkeiten, die durch Attrappen oder Mocks ersetzt wurden, die im echten Betrieb kritisch sein koennten?
2. Wiederkehrende Fehler? Gibt es Fehlerbehandlung oder Logging, das wiederholt vorkommt und auf ein systematisches Problem hinweisen koennte?
3. Anforderung Satz fuer Satz? Nimm jeden Satz der Anforderung (auch die Antworten auf Rueckfragen) und pruefe am Code, ob er nach einem normalen Lauf, einem Wiederholungslauf und einem Fehlerlauf (Abbruch, Netzfehler) noch stimmt.
4. Erster echter Einsatz? Wird das System bereits im echten Betrieb eingesetzt oder ist es noch in der Testphase?

Verdikt KNAPP (Richtwert 40 Zeilen; wird es laenger, ist das in Ordnung), Form nach _vorlage_verdict.md. Keine Wiederholung des Pakets.

# Verdikt: <kurztitel>

- **Spec:** `spec_<JJJJMMTT>_<kurztitel>.md`
- **Handover:** `handover_<JJJJMMTT>_<kurztitel>.md`
- **Datum:** <JJJJ-MM-TT>
- **Modell:** <Modellname aus dem System-Prompt>
- **Gepruefte Dateien:** <Liste der tatsaechlich gelesenen Code-Dateien>

Dateiname: `verdict_<JJJJMMTT>_<kurztitel>_<modellkuerzel>_betrieb.md`

## Ergebnis

**PASS | NACHBESSERN | FAIL** – ein bis zwei Saetze Begruendung.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1 | … | erfuellt / teilweise / nicht | `datei.py:42` |

## Handover gegen Code

- <Aussagen im Handover, die der Code nicht stuetzt. „Keine Abweichung gefunden", wenn so.>
- <Behauptete Tests ohne Ausgabe gelten als nicht belegt.>

## Befunde

Fuer **jeden** Befund drei Fragen mit ja/nein beantworten. Ein „ja" macht den Befund „hoch", unabhaengig davon,
ob die Schaechte schon vorher bestand. `kette.py urteil` prueft das nach.
- **Datenverlust:** Kann Daten verlieren, ueberschreiben oder echte Daten veraendern?
- **Unbemerkt:** Kann ein Fehler unbemerkt bleiben (Haenger, Schweigen, falscher Exit-Code, Test misst nichts)?
- **Harte Vorgabe:** Verstoesst es gegen eine harte Vorgabe der Spec oder des Auftrags (z. B. kein echter Versand)?

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | ja / nein | ja / nein | ja / nein | hoch / mittel / niedrig | | | |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** <Test, Lauf, Blick in Datei>
- **Braucht externe Quelle:** <Doku, Recherche, frische Instanz>

## Abweichende Meinung

- <Wo die Review-Instanz anders entschieden haette, auch bei PASS. „Keine", wenn keine.>
