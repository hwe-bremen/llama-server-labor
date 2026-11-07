Verdikt: Newsletter-Filter und Termin-Validierung

- **Spec:** `spec_20261107_mail_filter.md`
- **Handover:** `handover_20261107_mail_filter.md`
- **Datum:** 2026-11-07
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `agents/mail_planung/mail_planung.py`, `tests/test_mail_filter.py`

## Ergebnis

**PASS** – Die Umsetzung erfüllt alle spezifizierten Anforderungen (A1–A3). Die Newsletter-Erkennung und das Überspringen funktionieren korrekt, der Absender wird RFC-konform dekodiert und nackte Datumsangaben werden mechanisch aus der Terminliste gefiltert. Keine Datenverluste oder Verstöße gegen harte Vorgaben.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1 | Newsletter-Erkennung (List-Unsubscribe/Precedence) | erfuellt | `mail_planung.py:228-235` |
| 2 | Ausnahme für Projekt-Absender (mail_projects.json) | erfuellt | `mail_planung.py:238-258` |
| 3 | Absender lesbar dekodieren (RFC 2047) | erfuellt | `mail_planung.py:261-269` |
| 4 | Newsletter überspringen (kein Laden, kein Zählen) | erfuellt | `mail_planung.py:340-346` |
| 5 | Termin-Filter (nur mit Beschreibung) | erfuellt | `mail_planung.py:548-550` |
| 6 | Prompt-Änderung (kein nacktes Datum) | erfuellt | `mail_planung.py:688-691` |
| 7 | Tests T1-T8 grün und Spezifisch | erfuellt | `tests/test_mail_filter.py` |

## Handover gegen Code

- Keine Abweichung gefunden. Der Handover behauptet korrekt, dass keine Abweichungen vorliegen und alle Tests grün sind. Die im Handover genannten „bekannten Schwächen" (z.B. fehlende Persistenz von übersprungenen Newslettern) sind laut Spec beabsichtigt und werden im Code auch nicht korrigiert (was richtig ist).

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `mail_planung.py:245-256` | `projekt_absender` lädt die Konfigurationsdatei bei *jeder* geprüften Mail neu. Dies ist ineffizient, aber funktional korrekt und verstößt nicht gegen die Spec. | Caching der Konfiguration in einer globalen Variable oder beim Start des Skripts, um I/O zu reduzieren. |
| 2 | nein | nein | nein | niedrig | `mail_planung.py:688-691` | Der Prompt ist textlich korrekt, aber die Garantie, dass das LLM dem folgt, liegt beim Modell, nicht am Code. | Keine Code-Änderung möglich. Beobachtung im echten Lauf (T7/T8). |
| – | nein | nein | nein | – | – | keine Befunde | – |

## Nicht geprüft

- **Kann Hawe selbst pruefen:** Echter Lauf mit einer Mischung aus echten Newslettern (mit `List-Unsubscribe`) und echten Projekt-Mails, um die visuelle Ausgabe im Terminal und die DB-Einträge zu bestätigen.
- **Braucht externe Quelle:** Die korrekte Dekodierung von komplexen RFC-2047-Kopfzeilen in der Praxis (z.B. verschachtelte Kodierungen) ist durch die Unit-Tests abgedeckt, aber der echte Postfach-Inhalt ist die finale Instanz.