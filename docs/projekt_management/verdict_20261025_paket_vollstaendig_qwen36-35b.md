# Verdikt: paket_vollstaendig

- **Spec:** `spec_20261025_paket_vollstaendig.md`
- **Handover:** `handover_20261025_paket_vollstaendig.md`
- **Datum:** 2026-10-26
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `role-split/kette/test_kette.py`, `tests/test_paket_vollstaendig.py`

## Ergebnis

**NACHBESSERN** – Die Implementierung der Vorrang-Kürzung (A3) und der harten Obergrenze (A4) ist fehlerhaft. Die Bedingung für die Auslösung der Kürzung prüft nur den Inhalt der Code-Dateien, ignoriert aber den Paket-Rahmen (Header, Anforderung, Spec). Dies führt dazu, dass bei großen Paketen die Kürzung zu spät oder gar nicht ausgelöst wird, oder die harte Obergrenze (A4) aufgrund der falschen Messgröße falsch greift. Zudem ist die Markierung „nicht in der Übergabe genannt" (A2) nur teilweise implementiert (nur bei `_kappen`, nicht bei der Vorrang-Logik selbst konsistent geprüft).

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Paket nimmt alle geänderten/neuen Code-Dateien auf | erfuellt | `kette.py:600-740` |
| A2 | Dateien außerhalb des Handovers werden markiert | teilweise | `kette.py:745-750` |
| A3 | Zweistufige Vorrang-Kürzung bei Paketgröße > 80.000 Zeichen | nicht | `kette.py:715-730` |
| A4 | Harte Obergrenze KETTE_PAKET_MAX, Exit 1 bei Überschreitung | nicht | `kette.py:860-862` |
| A5 | Gegenprobe berücksichtigt role-split/kette/ | erfuellt | `kette.py:394-398` |
| A6 | Bestehende Tests bleiben grün oder werden bewusst angepasst | erfuellt | `test_kette.py:253-275` |
| A7 | Paket ohne Code trotz Änderungen ist ein lauter Fehler | erfuellt | `kette.py:795-810` |
| A8 | Abnahme – echter Lauf am K7-Stand | nicht getestet | - |

## Handover gegen Code

- **A3 Vorrang-Kürzung:** Der Handover behauptet, die Kürzung basiere auf der Größe des Code-Abschnitts. Der Code misst `gesamt = sum(len(v[0]) for v in datei_inhalte.values())`. Das ist korrekt für den Code-Teil. **ABER**: Die Bedingung `if gesamt > PAKET_WARNUNG_ZEICHEN` wird vor dem Hinzufügen des Headers, der Anforderung und der Spec zum Paket geprüft. Wenn das Paket insgesamt (inkl. Header) > 150.000 Zeichen ist, aber der Code-Teil < 80.000, wird **nicht** gekürzt. Das widerspricht der Absicht, das Paket klein zu halten. Die Spec sagt: „Ist die Gesamtpaketgröße ... größer als PAKET_WARNUNG_ZEICHEN". Der Code misst nur den Code-Teil.
- **A4 Harte Obergrenze:** Der Code prüft `if groesse > KETTE_PAKET_MAX` am Ende von `paket()`. `groesse` ist `len(paket_text)`. Das ist korrekt. **ABER**: Da A3 falsch misst, kann es sein, dass nach der (nicht ausgelösten) Kürzung das Paket immer noch > 150.000 Zeichen ist, aber der Code dann abbricht. Das ist technisch „Exit 1", aber die Kürzung wurde nicht angewendet, wie gefordert. Die Spec verlangt: „nach der Vorrang-Kürzung". Wenn die Kürzung nicht ausgelöst wurde, ist der Zustand nicht der gewünschte.
- **A2 Markierung:** Der Code fügt die Markierung in `_kappen` ein. Das passiert für alle Dateien, die `nicht_genannt=True` bekommen. In `kette.py:710` wird `nicht_genannt` basierend auf `im_ho` gesetzt. Das ist korrekt. **ABER**: Wenn eine Datei durch Vorrang-Kürzung weggelassen wird, erscheint sie nicht im Code-Teil, sondern in der „Weggelassen"-Liste. Dort steht keine Markierung „nicht in der Übergabe genannt". Die Spec sagt: „Die Markierung gilt für alle Vorrang-Stufen, auch Vorrang 1." Sie sagt nicht explizit, dass sie in der „Weggelassen"-Liste stehen muss, aber die Logik der Markierung ist nur im Code-Teil aktiv. Das ist ein kleines Design-Problem, aber nicht kritisch, da weggelassene Dateien sowieso nicht bewertet werden.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `kette.py:715-730` | A3 nicht erfüllt | Die Vorrang-Kürzung wird basierend auf der Größe des **Code-Teils** ausgelöst, nicht der **Gesamtgröße** des Pakets. Die Spec verlangt: „Ist die Gesamtpaketgröße ... größer als PAKET_WARNUNG_ZEICHEN". Korrektur: Die Größe muss vor der Kürzung geschätzt werden (Code-Teil + Header + Spec + Anforderung) oder die Kürzung muss so angepasst werden, dass sie die Gesamtgröße berücksichtigt. Alternativ: Die Bedingung muss `len(paket_text) + geschaetzter_code > PAKET_WARNUNG_ZEICHEN` sein, wobei `paket_text` noch nicht geschrieben ist. Besser: Schätze die Gesamtgröße vor der Kürzung. |
| 2 | nein | ja | ja | hoch | `kette.py:860-862` | A4 nicht erfüllt | Die harte Obergrenze wird nach der (fehlerhaften) Kürzung geprüft. Wenn die Kürzung nicht ausgelöst wurde (weil Code-Teil klein, aber Gesamtgröße groß), wird trotzdem Exit 1 geworfen. Das ist ein „stiller" Fehler, weil die Kürzung nicht angewendet wurde, wie gefordert. Korrektur: Stelle sicher, dass die Kürzung korrekt ausgelöst wird (siehe Befund 1). |
| 3 | nein | nein | nein | niedrig | `kette.py:745-750` | A2 teilweise | Die Markierung „nicht in der Übergabe genannt" fehlt in der „Weggelassen"-Liste. Die Spec sagt nicht explizit, dass sie dort stehen muss, aber es ist inkonsistent. Korrektur: Füge die Markierung auch in der „Weggelassen"-Liste hinzu, wenn die Datei nicht im Handover war. |

## Nicht geprüft

- **Kann Hawe selbst pruefen:** `python3 role-split/kette/kette.py paket mail_server_test` und prüfen, ob die Paketgröße korrekt ist und ob die Kürzung ausgelöst wird, wenn das Paket groß ist.
- **Braucht externe Quelle:** Keine.

## Abweichende Meinung

- Keine. Die Implementierung der Vorrang-Kürzung ist grundlegend fehlerhaft, da sie die falsche Größe misst.