# Verdikt: paket_vollstaendig

- **Spec:** `spec_20261025_paket_vollstaendig.md`
- **Handover:** `handover_20261026_paket_vollstaendig.md`
- **Datum:** 2026-10-27
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `tests/test_paket_vollstaendig.py`, `role-split/kette/test_kette.py`, `role-split/kette/prompts/review_api.md`, `role-split/kette/prompts/review2_api.md`

## Ergebnis

**PASS** – Die Implementierung deckt alle Spezifikationen ab. Die Unterscheidung zwischen „zur Kette gehörig" und „fremd" funktioniert korrekt über den Kurztitel-Check. Die Vorrang-Kürzung und die harte Obergrenze sind implementiert. Die Tests sind robust und testen die neuen Pfade.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1 | Paket nimmt alle geänderten/neuen Code-Dateien auf (A1) | erfüllt | `kette.py:638-675` (`_aenderungen`) |
| 2 | Dateien außerhalb des Handovers werden markiert (A2) | erfüllt | `kette.py:657-658` (`_kappen`) |
| 3 | Zweistufige Vorrang-Kürzung bei Paketgröße > 80.000 Zeichen (A3) | erfüllt | `kette.py:632-635` (`_vorrang`), `kette.py:745-756` (Kürzungsschleife) |
| 4 | Harte Obergrenze KETTE_PAKET_MAX, Exit 1 bei Überschreitung (A4) | erfüllt | `kette.py:520`, `kette.py:762-766` |
| 5 | Gegenprobe berücksichtigt role-split/kette/ (A5) | erfüllt | `kette.py:395-396` (Filter entfernt) |
| 6 | Bestehende Tests bleiben grün oder werden bewusst angepasst (A6) | erfüllt | `test_kette.py:255-280` (angepasst), `test_paket_vollstaendig.py:180-184` (Prüfung) |
| 7 | Paket ohne Code trotz Änderungen ist ein lauter Fehler (A7) | erfüllt | `kette.py:739-744`, `kette.py:759-761` |
| 8 | Abnahme – echter Lauf am K7-Stand (A8) | offen | Manuell durch Hawe (T10) |

## Handover gegen Code

- **Annahme Vorrang 1:** Der Code definiert Vorrang 1 als „in der Übergabe genannt ODER außerhalb tests/". Dies entspricht der Vereinbarung: „Vorrang 1, nie weglassen: alle Dateien aus der Übergabe und alle geänderten Dateien außerhalb von tests/".
- **Fremde Commits:** Der Code listet fremde Dateien nur auf, wenn sie nicht in der Übergabe genannt sind. Wenn eine fremde Datei in der Übergabe genannt ist, wird sie mit Inhalt aufgenommen (Vorrang 1). Dies ist korrekt implementiert (`kette.py:647-648`: `if d in offen or d in neu or (nur and d in nur): kette.append(d)`).
- **Exit 1 bei zu großem Paket:** Die Prüfung erfolgt nach der Kürzung (`kette.py:762`).

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `kette.py:640` | mittel | **Randfall Kurztitel-Regex:** Der Regex `(?<![a-z0-9_]){re.escape(kurztitel)}(?![a-z0-9_])` verhindert, dass „g" in „gross" trifft. Das ist korrekt. Ein potentielles Problem besteht, wenn der Kurztitel Sonderzeichen enthält, die nicht escaped werden könnten (hier ist `re.escape` sicher). Oder wenn der Kurztitel leer ist (Fall `None`, geprüft in Zeile 641). Dies ist robust. |
| 2 | nein | nein | nein | niedrig | `kette.py:745-756` | niedrig | **Vorrang-Kürzung Logik:** Die Schleife löscht Dateien aus `drin` und baut das Paket neu. Da `_vorrang` deterministisch ist und `drin` sortiert wird, ist das Ergebnis reproduzierbar. Die Reihenfolge (erst 3, dann 2) ist korrekt. |

## Nicht geprüft

- **Kann Hawe selbst pruefen:** T10 (Echter Lauf `review-auto mail_server_test`). Der Test benötigt einen funktionierenden Router und das 35B-Modell.
- **Braucht externe Quelle:** Keine. Alle logischen Anforderungen sind im Code und den Unit-Tests abgedeckt.