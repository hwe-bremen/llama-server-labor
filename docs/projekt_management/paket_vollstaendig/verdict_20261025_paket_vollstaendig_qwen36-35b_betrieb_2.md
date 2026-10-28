# Verdikt: paket_vollstaendig

- **Spec:** `spec_20261025_paket_vollstaendig.md`
- **Handover:** `handover_20261026_paket_vollstaendig.md`
- **Datum:** 2026-10-27
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `role-split/kette/test_kette.py`, `tests/test_paket_vollstaendig.py`, `tests/test_kette_review_auto.py`

## Ergebnis

**PASS** – Die Umsetzung deckt alle Anforderungen ab. Die Unterscheidung zwischen „zur Kette gehörig" und „fremd" funktioniert korrekt, die Vorrang-Kürzung ist robust implementiert, und die harte Obergrenze (`KETTE_PAKET_MAX`) verhindert das Schreiben unbrauchbarer Pakete.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1 | Paket nimmt alle geänderten/neuen Code-Dateien auf (auch tests/ role-split/) | erfüllt | `kette.py:648-675` (`_aenderungen`), `kette.py:543` (`PAKET_NIE` ohne tests/role-split) |
| 2 | Dateien außerhalb des Handovers werden markiert | erfüllt | `kette.py:689-690` (`_kappen`), `kette.py:665-666` (`_diff` Übergabe) |
| 3 | Zweistufige Vorrang-Kürzung bei Paketgröße > 80.000 Zeichen | erfüllt | `kette.py:745-754` (Schleife über Vorrang 3, dann 2), `kette.py:639-642` (`_vorrang`) |
| 4 | Harte Obergrenze KETTE_PAKET_MAX, Exit 1 bei Überschreitung | erfüllt | `kette.py:760-763` (Prüfung vor `write_text`), `kette.py:525` (Konstante) |
| 5 | Gegenprobe berücksichtigt role-split/kette/ | erfüllt | `kette.py:391-393` (Filterung entfernt `role-split/kette/`-Ausschluss) |
| 6 | Bestehende Tests bleiben grün oder bewusst angepasst | erfüllt | `test_kette.py:254` (angepasst), `test_paket_vollstaendig.py:180` (Bestandstest) |
| 7 | Paket ohne Code trotz Änderungen ist ein lauter Fehler | erfüllt | `kette.py:736-742` (Prüfung auf leere Einträge bei fremden Änderungen) |
| 8 | Abnahme – echter Lauf am K7-Stand | nicht geprüft | Manuell durch Hawe (T10) |

## Handover gegen Code

- **Abweichung:** Im Handover wird angemerkt, dass uncommittete Dateien immer zur Kette zählen. Dies ist so im Code (`_aenderungen` Zeile 653: `offen` wird zu `kette` hinzugefügt) implementiert und entspricht der Absprache. Es gibt keine Abweichung zur Spec, sondern eine Klarstellung der Implementierungsdetails.
- **Annahme:** Die Trennung Vorrang 1/2/3 wird exakt so im Code (`_vorrang`) abgebildet.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `kette.py:736-742` | **Befund:** Die Prüfung auf „Paket ohne Code" prüft nur `fremd_zeilen`. Wenn alle Dateien zur Kette gehören, aber nach Kürzung (Vorrang 2/3) leer sind, wird `eintraege` geprüft (Zeile 747). Falls `eintraege` nicht leer ist, aber `drin` (nach Kürzung) leer, wird Exit 1 gegeben. Das ist korrekt. | Keine Korrektur nötig. Die Logik deckt beide Fälle ab. |
| 2 | nein | nein | nein | niedrig | `kette.py:660-666` | **Befund:** Die Markierung „nicht in der Übergabe genannt" wird auch für Vorrang-1-Dateien gesetzt, die nicht im Handover stehen. Dies ist gewollt und in Spec A2 gefordert. | Keine Korrektur nötig. |

## Nicht geprüft

- **Kann Hawe selbst pruefen:** T10: Echter Lauf `review-auto mail_server_test` am K7-Stand. Dies erfordert die tatsächliche Ausführung am Zielserver und die Überprüfung der Review-Ausgabe auf die korrekte Nennung von `agents/mail_planung/mail_planung.py` und den Testdateien.
- **Braucht externe Quelle:** Keine.

## Abweichende Meinung

- Keine. Die Implementierung ist sauber und folgt den spezifizierten Regeln strikt. Die Trennung der Logik in `_aenderungen` und `_vorrang` erhöht die Wartbarkeit.