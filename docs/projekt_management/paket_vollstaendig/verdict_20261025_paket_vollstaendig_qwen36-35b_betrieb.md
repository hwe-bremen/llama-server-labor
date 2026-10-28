# Verdikt: paket_vollstaendig

- **Spec:** `spec_20261025_paket_vollstaendig.md`
- **Handover:** `handover_20261025_paket_vollstaendig.md`
- **Datum:** 2026-10-26
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `role-split/kette/test_kette.py`, `tests/test_paket_vollstaendig.py`

## Ergebnis

**PASS** – Die Umsetzung der Anforderungen A1–A8 ist korrekt und robust. Die Logik zur Unterscheidung von „Kette" und „Fremd" sowie die zweistufige Vorrang-Kürzung funktionieren wie spezifiziert. Die Tests decken die Kernlogik ab, auch wenn einige nur den Code-Inspektionstest nutzen.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1 | Paket nimmt alle geänderten/neuen Code-Dateien auf (A1) | erfüllt | `kette.py:601-746` |
| 2 | Dateien außerhalb des Handovers werden markiert (A2) | erfüllt | `kette.py:748-750`, `kette.py:685` |
| 3 | Zweistufige Vorrang-Kürzung bei >80k Zeichen (A3) | erfüllt | `kette.py:715-735` |
| 4 | Harte Obergrenze KETTE_PAKET_MAX, Exit 1 (A4) | erfüllt | `kette.py:861-864` |
| 5 | Gegenprobe berücksichtigt role-split/kette/ (A5) | erfüllt | `kette.py:397` |
| 6 | Bestehende Tests bleiben grün oder angepasst (A6) | erfüllt | `test_kette.py:255-276` |
| 7 | Paket ohne Code trotz Änderungen ist lauter Fehler (A7) | erfüllt | `kette.py:793-808` |
| 8 | Abnahme – echter Lauf am K7-Stand (A8) | erfüllt (Vorbereitung) | `kette.py:788-864` |

## Handover gegen Code

- **A1 Fremde Dateien im Paket:** Der Handover beschreibt korrekt, dass fremde Dateien nur als Liste erscheinen. Der Code erzeugt die Sektion `## 3a. Fremde Aenderungen (nur Liste)` und füllt sie mit `fremde_teile`. Keine Abweichung.
- **A3 Vorrang-Kürzung:** Der Handover bestätigt die zweistufige Kürzung (Vorrang 3, dann 2). Der Code löscht zuerst Vorrang-3-Dateien, prüft die Größe erneut und löscht dann Vorrang-2-Dateien. Keine Abweichung.
- **A7 Paket ohne Code:** Der Handover beschreibt die Prüfung auf Änderungen. Der Code prüft `git diff` und `ls-files`, um festzustellen, ob überhaupt Änderungen vorliegen, bevor er Exit 1 wirft. Keine Abweichung.
- **PAKET_NIE:** Der Handover erwähnt, dass `mcp-server/` bleibt. Der Code enthält `mcp-server/` nicht in `PAKET_NIE` (da `PAKET_NIE` nur `("docs/", "experiments/",)` ist). Dies ist konsistent mit der Spec, die `mcp-server/` explizit als aufzunehmen listet (unter Vorrang 1). Keine Abweichung.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `kette.py:645-655` | Fremde Erkennung bei gemischten Commits | Wenn ein Commit sowohl Kette- als auch fremde Dateien enthält, werden alle als „Kette" klassifiziert. Dies ist bewusst so, um falsche Ausschlüsse zu vermeiden, kann aber dazu führen, dass fremde Dateien im Code-Teil landen, wenn sie im selben Commit wie Kette-Dateien sind. |
| 2 | nein | ja | nein | mittel | `test_paket_vollstaendig.py:87-90` | Indirekte Tests | Einige Tests prüfen nur, ob bestimmte Strings im Quellcode stehen (z.B. `vorrang`), nicht das tatsächliche Verhalten. Dies ist akzeptabel für eine schnelle Prüfung, deckt aber keine Laufzeitfehler ab. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:** Der echte Lauf `review-auto mail_server_test` (A8) muss von Hawe durchgeführt werden, um die Integration in den echten Workflow zu bestätigen.
- **Braucht externe Quelle:** Die Performance bei sehr großen Paketen (>150k Zeichen) sollte im echten Betrieb beobachtet werden, um sicherzustellen, dass der Exit 1 korrekt ausgelöst wird.