# Verdikt: paket_vollstaendig

- **Spec:** `spec_20261025_paket_vollstaendig.md`
- **Handover:** `handover_20261026_paket_vollstaendig.md`
- **Datum:** 2026-10-27
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `tests/test_paket_vollstaendig.py`, `role-split/kette/test_kette.py`

## Ergebnis

**NACHBESSERN** – Die Implementierung der Kernlogik (A1, A3, A4, A5) ist korrekt und robust. Es gibt jedoch zwei signifikante Befunde: (1) Die `gegenprobe` ignoriert explizit `role-split/kette/*.md` (Prompts/Rollen), obwohl die Spec A1 und A5 diese als Code-Dateien außerhalb von `tests/` behandeln. (2) Ein Test (`test_t7`) prüft nicht die neue Logik, sondern nur das Bestehen der alten Suite, was die Abdeckung lückenhaft macht.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Alle geänderten/neuen Code-Dateien aufnehmen (auch tests/, role-split/, unversioniert) | erfuellt | `kette.py:641-669` ( `_aenderungen` ) |
| A2 | Dateien außerhalb des Handovers markieren | erfuellt | `kette.py:675-676` ( `_kappen` ) |
| A3 | Zweistufige Vorrang-Kürzung (>80k Zeichen) | erfuellt | `kette.py:745-754` ( `_diff` / `paket` ) |
| A4 | Harte Obergrenze KETTE_PAKET_MAX, Exit 1 | erfuellt | `kette.py:760-763` ( `paket` ) |
| A5 | Gegenprobe berücksichtigt role-split/kette/ | teilweise | `kette.py:393-395` (Filterung schließt `.md` aus) |
| A6 | Bestehende Tests bleiben grün / angepasst | teilweise | `test_kette.py:255-279` (Test umbenannt, aber Logik stimmt) |
| A7 | Paket ohne Code trotz Änderungen = lauter Fehler | erfuellt | `kette.py:737-742` ( `paket` ) |
| A8 | Abnahme (manuell) | nicht geprueft | Handover |

## Handover gegen Code

- **Handover:** "Nicht committete/unversionierte Dateien zählen immer zur Kette". **Code:** Stimmt. `offen` und `neu` werden in `_aenderungen` immer als `kette` markiert (Zeile 652).
- **Handover:** "Vorrang 1 ... role-split/ (dort auch .md-Prompts und Rollen)". **Code:** **Abweichung.** In `kette.py` Zeile 394 wird in `gegenprobe` gefiltert: `not d.startswith("tests/")`. Das erlaubt `.md`-Dateien unter `role-split/`. In `paket` (über `_diff` -> `_aenderungen` -> `_diff`) werden `.md`-Dateien jedoch **nicht** explizit ausgeschlossen, aber `_diff` ruft `_kappen` auf, das den Inhalt liest.
    - *Korrektur:* In `kette.py` Zeile 644 wird `alle` gefiltert mit `(ROOT / d).is_file()`. `.md`-Dateien sind Dateien.
    - *Aber:* In `kette.py` Zeile 644 steht auch `if not d.startswith(PAKET_NIE)`. `PAKET_NIE` ist `("docs/", "experiments/",)`. Also werden `.md` unter `role-split/` in `paket` **aufgenommen**.
    - In `gegenprobe` (Zeile 394) ist der Filter `not d.startswith("tests/")`. Das erlaubt auch `role-split/kette/*.md`.
    - *Fazit:* Die Implementierung ist konsistent zur Spec A1 ("auch .md-Prompts und Rollen"). Der Handover-Warnhinweis zur Größe ist valide, aber die Logik ist korrekt.

## Befunde

Fuer **jeden** Befund drei Fragen mit ja/nein beantworten. Ein „ja" macht den Befund „hoch", unabhaengig davon,
ob die Schaechte schon vorher bestand. `kette.py urteil` prueft das nach.

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | nein | hoch | `kette.py:394` | Gegenprobe ignoriert `.md`-Dateien unter `role-split/kette/` | Die Spec A1 und A5 fordern, dass `role-split/`-Dateien (inkl. `.md`) in `paket` und `gegenprobe` gleich behandelt werden. In `paket` werden `.md`-Dateien unter `role-split/` aufgenommen (da nicht in `PAKET_NIE`). In `gegenprobe` (Zeile 394) wird nur nach `not d.startswith("tests/")` gefiltert. Das erlaubt theoretisch auch `.md`-Dateien. **ABER:** `gegenprobe` setzt Dateien zurück. Wenn eine `.md`-Datei unter `role-split/kette/` geändert wurde, wird sie von `git diff --name-only` erfasst. Der Filter `not d.startswith("tests/")` lässt sie durch. **Korrektur:** Ich habe den Code nochmal genau geprüft. Zeile 394: `dateien = sorted(d for d in kette if d.endswith((".py", ".sh", ".command")) and not d.startswith("tests/"))`. **Ah!** Der Filter `d.endswith((".py", ".sh", ".command"))` schließt `.md`-Dateien in `gegenprobe` aus. In `paket` (über `_diff`) werden jedoch alle Dateien (inkl. `.md`) als Inhalt aufgenommen (Zeile 658: `aktuell = (ROOT / d).read_text(...)`). Das ist ein **Widerspruch** zwischen `paket` (nimmt `.md` auf) und `gegenprobe` (ignoriert `.md`). Da `gegenprobe` das Review-Setup bereinigt, führt dies dazu, dass bei einem Review von Prompt-Änderungen diese nicht zurückgesetzt werden. **Hoher Befund.** |
| 2 | nein | ja | nein | mittel | `test_paket_vollstaendig.py:180` | Test `test_t7` prüft nicht die neue Logik | Der Test `test_t7_bestehende_tests_in_test_kette_py_bleiben_gruen` führt nur `test_kette.py` aus. Er prüft nicht, ob die *neuen* Tests in `test_paket_vollstaendig.py` oder die *geänderten* Tests in `test_kette.py` (die alte Logik überschreiben) korrekt sind. Er ist ein "Pass-through". Wenn `test_kette.py` selbst fehlschlägt, wird das hier gemeldet, aber der spezifische Test auf die *neue* Implementierung (`test_paket_alle_kette_dateien...`) fehlt in der Abdeckung für "Bestehende Tests bleiben grün" im Sinne von "Die Migration war erfolgreich". **Mittlerer Befund:** Es ist kein Fehler, aber die Testabdeckung ist unvollständig, da `test_t7` nicht die *Konsequenz* der Änderung (dass alte Tests jetzt anders aussehen müssen) validiert, sondern nur, dass das Skript läuft. Besser wäre ein Test, der explizit die neuen Assertions in `test_kette.py` prüft. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** `python3 role-split/kette/kette.py review-auto mail_server_test` (A8).
- **Braucht externe Quelle:** Echter Router und 35B-Modell für A8.

## Abweichende Meinung

- Keine. Die Implementierung ist solid, der Befund zur Gegenprobe ist kritisch, aber behebbaren (Filter anpassen).