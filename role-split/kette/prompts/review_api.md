Datum: {datum_heute}
Dein Modellname: {modell}
Pruef die Umsetzung zu „{kurztitel}".

Paket-Text:

{paket_text}

1. Spec gegen Anforderung: Widerspricht eine Designentscheidung oder ein „akzeptiertes Restrisiko" der Anforderung? Das ist ein Befund (Harte Vorgabe: ja), auch wenn der Code die Spec korrekt umsetzt.
2. Fuer JEDE Anforderung beantwortest du diese sechs Pflichtfragen mit Fundstelle (Datei:Zeile):
   a) Erzwungen oder nur verlangt? Steht das Verlangte nur in einem Prompt an ein LLM, in einem Kommentar oder in der Spec – oder erzwingt der Code es auch dann, wenn das LLM, der Feed oder die Eingabe sich nicht daran haelt?
   b) Leerer und abweichender Fall: Was passiert konkret, wenn die Eingabe leer ist (keine Eintraege, leere Datei, leere Antwort) oder anders aussieht als erwartet (andere Ueberschrift, andere Schreibweise, fehlendes Feld)? Spiel es mit einem konkreten Beispiel durch.
   c) Markiert, aber nie gezeigt? Wird etwas als erledigt, verarbeitet oder gesendet markiert, das der Nutzer nie zu sehen bekommt? Das ist IMMER ein Befund „hoch" (Unbemerkt: ja) – auch wenn es beabsichtigt oder im Handover begruendet wirkt.
   d) Laeuft die Absicherung selbst ins Leere? Gibt es einen Pfad, in dem eine Pruef- oder Nachtrags-Logik nichts tut, obwohl ihre Bedingung erfuellt ist (z. B. Bedingung prueft lose, Ersetzung sucht exakt)?
   e) Widerspruechliche Anweisungen: Enthaelte ein Prompt an ein LLM, eine Konfiguration oder ein Kommentar Anweisungen, die einander oder der Anforderung widersprechen (z. B. zwei Regeln, die nicht gleichzeitig erfuellbar sind)? Dann folgt das LLM zufaellig einer davon – Befund.
   f) Anforderung Satz fuer Satz: Nimm jeden Satz der Anforderung (auch die Antworten auf Rueckfragen) und pruefe am Code, ob er nach einem normalen Lauf, einem Wiederholungslauf und einem Fehlerlauf (Abbruch, Netzfehler) noch stimmt.
   Jede Antwort mit „nur verlangt", „verloren", „verschluckt", „unbemerkt", „laeuft ins Leere", „widerspricht" oder „stimmt nicht mehr" ist ein Befund – in der Befundtabelle, nicht nur in der Anforderungstabelle. Was die Spec unter „Nicht-Ziele" ausschliesst, ist kein Befund.
3. Tests: Fuer jeden GRUEN- oder ANDERS-Test sage, ob er bewusst Bestehendes prueft (in Ordnung) oder die neue Logik, die sein Titel nennt, gar nicht ausfuehrt (Befund). Fehlt fuer eine Pflichtfrage mit Befund ein Test, ist auch das ein Befund.

Verdikt KNAPP (Richtwert 40 Zeilen; wird es laenger, ist das in Ordnung), Form nach _vorlage_verdict.md. Keine Wiederholung des Pakets.

# Verdikt: <kurztitel>

- **Spec:** `spec_<JJJJMMTT>_<kurztitel>.md`
- **Handover:** `handover_<JJJJMMTT>_<kurztitel>.md`
- **Datum:** <JJJJ-MM-TT>
- **Modell:** <Modellname aus dem System-Prompt>
- **Gepruefte Dateien:** <Liste der tatsaechlich gelesenen Code-Dateien>

Dateiname: `verdict_<JJJJMMTT>_<kurztitel>_<modellkuerzel>.md`

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
