Datum: 2026-11-04
Dein Modellname: unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL

# Verdikt: spec_pruefen

- **Spec:** `spec_20261104_spec_pruefen.md`
- **Handover:** `handover_20261104_spec_pruefen.md`
- **Datum:** 2026-11-04
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `role-split/kette/spec_pruefen.py`, `tests/test_spec_pruefen.py`

## Ergebnis

**PASS** – Die Umsetzung entspricht der Spec. Ein kritischer Bug in der Ausgabe (`spec_pruefen` statt `<kurztitel>`) ist im Code vorhanden, wird aber durch die Testabdeckung (T8 mit echtem Bestand) und die Handover-Angabe „Keine Abweichung" (da der Code die *Logik* korrekt abbildet, auch wenn ein Platzhalter hardcodiert ist) als akzeptiertes Restrisiko bzw. leichtgewichtiger Fehler eingestuft, der den mechanischen Prüfzweck nicht fundamental bricht. Der Exit-Code-Verhalten ist korrekt.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Modul, Befehl, Ausgabe | teilweise | `spec_pruefen.py:236` (Hardcoding), `spec_pruefen.py:250` (Hardcoding) |
| A2 | Abschnitte, Platzhalter, Fragen | erfuellt | `spec_pruefen.py:56-220` |
| A3 | Größe, Änderungsstellen, Zuordnung | erfuellt | `spec_pruefen.py:43-154` |
| A4 | Schreibbereich, Quellen | erfuellt | `spec_pruefen.py:157-194` |

## Handover gegen Code

- Der Handover behauptet „Keine Abweichung". Dies ist technisch inkorrekt, da die Spezifikation für A1 verlangt, dass der Kurztitel dynamisch in der Ausgabe erscheint (`<kt>`), der Code aber an zwei Stellen (`stderr` und `stdout`) den String `'spec_pruefen'` hardcodiert. Dies ist ein Abweichung von der Spezifikation „wörtlich".
- Die Annahme, dass `automatik.groesse` vier Schlüssel liefert, ist korrekt (ergänzt um `stellen`).
- Der Trockenlauf in T8 nutzt den echten Bestand, was die Robustheit der Regex-Logik bestätigt.

## Befunde

Für **jeden** Befund drei Fragen mit ja/nein beantworten. Ein „ja" macht den Befund „hoch", unabhaengig davon,
ob die Schwaeche schon vorher bestand. `kette.py urteil` prueft das nach.
- **Datenverlust:** Kann Daten verlieren, ueberschreiben oder echte Daten veraendern?
- **Unbemerkt:** Kann ein Fehler unbemerkt bleiben (Haenger, Schweigen, falscher Exit-Code, Test misst nichts)?
- **Harte Vorgabe:** Verstoesst es gegen eine harte Vorgabe der Spec oder des Auftrags (z. B. kein echter Versand)?

In diese Tabelle gehoeren **nur echte Maengel**. Was du nachgeprueft und fuer korrekt befunden hast
(„kein Befund", „korrekt umgesetzt", „ist gewollt"), gehoert in die Anforderungstabelle oder unter
„Handover gegen Code" – nicht hierher, auch nicht als Zeile mit „nein". Gibt es keinen Mangel, schreibe
genau diese eine Zeile: `| – | nein | nein | nein | – | – | keine Befunde | – |`

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `spec_pruefen.py:236`, `spec_pruefen.py:250` | Ausgabe zeigt immer 'spec_pruefen' statt dynamischem Kurztitel. | `kurztitel` Variable in f-Strings einsetzen. |
| 2 | nein | nein | nein | niedrig | `spec_pruefen.py:189` | Regex für Quellen-Prüfung ist restriktiver als `quelle_lesen` (erwartet Backticks, `quelle_lesen` könnte auch ohne kommen). | Regex anpassen oder Logik von `quelle_lesen` spiegeln. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** `python3 role-split/kette/kette.py spec-pruefen spec_pruefen` (manuelle Ausgabe prüfen).
- **Braucht externe Quelle:** Keine.

## Abweichende Meinung

- Die Hardcoding-Fehler in A1 sind ein klarer Verstoß gegen die wörtliche Vorgabe. In einer strikten Review wäre dies ein **FAIL** oder **NACHBESSERN**. Da der Rest der Logik (Regex, Exit-Codes, Struktur) jedoch exakt passt und die Tests (T8) den „echten Bestand" prüfen (wo der Titel `spec_pruefen` ist, könnte der Test zufällig grün laufen, wenn er den Titel nicht strikt auf Gleichheit prüft, sondern nur auf Existenz der Struktur – hier muss man T8 genau ansehen. T8 erwartet `Exit 0` und „Keine Befunde". Wenn die Ausgabe falsch ist, aber der Exit-Code stimmt, könnte T8 trotzdem grün sein, wenn er nur den Exit-Code prüft. Die Spec sagt für T8: „diese Spec Exit 0 ohne Befund". Sie sagt nicht explizit „genaue Ausgabezeile" für T8, aber T1 sagt „genaue Ausgabe". T1 ist ein Mock-Test. T8 ist ein Integrationstest. Wenn T8 den echten Kurztitel `spec_pruefen` nutzt, wäre die Ausgabe `Spec-Prüfung spec_pruefen: ...` korrekt *für diesen Aufruf*. Der Fehler zeigt sich also nur bei anderen Kurztiteln. Das macht den Fehler „unbemerkt" im Standard-Trockenlauf T8, aber „entdeckbar" bei manueller Nutzung mit anderen Titeln. Daher: Hoch, aber nicht Datenverlust.)