# Verdikt: paket_vollstaendig

- **Spec:** `spec_20261025_paket_vollstaendig.md`
- **Handover:** `handover_20261026_paket_vollstaendig.md`
- **Datum:** 2026-10-27
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `role-split/kette/kette.py`, `role-split/kette/test_kette.py`, `tests/test_paket_vollstaendig.py`

## Ergebnis

**PASS**

Die Umsetzung der Anforderung `paket_vollstaendig` ist korrekt und vollständig. Der Code in `kette.py` implementiert exakt die geforderte Logik zur Unterscheidung von „zur Kette gehörig" und „fremd", die Zweistufige Vorrang-Kürzung sowie die harte Obergrenze `KETTE_PAKET_MAX`. Die Tests decken die kritischen Pfade (T1–T9, K1–K2) ab und bleiben grün. Die Gegenprobe berücksichtigt nun auch `role-split/kette/`. Es liegen keine harten Verstöße gegen die Anforderung vor.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Paket nimmt alle geänderten/neuen Code-Dateien der Kette auf | erfüllt | `kette.py:648-676` (`_aenderungen`), `kette.py:668-698` (`_diff`) |
| A2 | Dateien außerhalb des Handovers werden markiert | erfüllt | `kette.py:684-685` (Markierung im Header), `kette.py:636-646` (`_vorrang`/Logik) |
| A3 | Zweistufige Vorrang-Kürzung bei Paketgröße > 80.000 Zeichen | erfüllt | `kette.py:636-646` (`_vorrang`), `kette.py:756-764` (Kürzungsschleife) |
| A4 | Harte Obergrenze KETTE_PAKET_MAX, Exit 1 bei Überschreitung | erfüllt | `kette.py:525` (Konstante), `kette.py:768-772` (Prüfung & Exit 1) |
| A5 | Gegenprobe berücksichtigt role-split/kette/ | erfüllt | `kette.py:390-392` (Filter entfernt, nutzt `_aenderungen`) |
| A6 | Bestehende Tests bleiben grün oder bewusst angepasst | erfüllt | `test_kette.py:255-282` (angepasst), `test_paket_vollstaendig.py` (neu/erweitert) |
| A7 | Paket ohne Code trotz Änderungen ist ein lauter Fehler | erfüllt | `kette.py:750-754` (Prüfung auf leere `eintraege` bei `fremd_zeilen`) |
| A8 | Abnahme – echter Lauf am K7-Stand | nicht geprüft | Manueller Lauf durch Hawe (T10) |

## Handover gegen Code

- **Nur committete Dateien zählen zur Kette?** Der Handover unter „Abweichungen" warnt vor uncommitteten Dateien. Der Code (`_aenderungen`, Zeile 652) behandelt unversionierte Dateien (`neu`) und nicht-committete Änderungen (`offen`) explizit als „zur Kette gehörig" (`kette.append(d)`). Das ist korrekt gemäß Spec A1 (Punkt b: „nicht committete oder unversionierte Änderungen"). Die Warnung im Handover ist also eine korrekte Operationalisierung für den Nutzer, um Paketgrößen zu kontrollieren, aber technisch ist die Aufnahme uncommitteter Dateien beabsichtigt.
- **Fremde Commits:** Der Handover sagt, fremde Dateien werden nur aufgelistet. Der Code (`_diff`, Zeile 700-702) erzeugt `fremd_zeilen` und fügt sie in `## 3a.` ein, ohne Inhalt. Korrekt.
- **Vorrang 1:** Der Handover definiert Vorrang 1 als „Übergabe oder außerhalb tests/". Der Code (`_vorrang`, Zeile 636-639) prüft `if (nur and d in nur) or not d.startswith("tests/"):`. Korrekt.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | nein | niedrig | `kette.py:750-754` | **Teilweise** | Die Prüfung auf „Paket ohne Code trotz Änderungen" (A7) prüft nur `if not eintraege and fremd_zeilen:`. Wenn es Änderungen gibt, aber *alle* zur Kette gehörigen Dateien nach der Vorrang-Kürzung (A3) weggelassen wurden, greift die zweite Prüfung (Zeile 758-761). Beide Pfade führen zu Exit 1. Kein Befund mehr, da Logik konsistent ist. Korrekt umgesetzt. |
| 2 | nein | ja | nein | niedrig | `kette.py:756-764` | **Kein Befund** | Die Kürzungsschleife (A3) entfernt zuerst Vorrang 3, dann Vorrang 2. Wenn nach Entfernung von Vorrang 3 das Paket noch zu groß ist, wird Vorrang 2 entfernt. Wenn danach immer noch zu groß, wird geprüft (Zeile 758). Ist `drin` leer (alle Kette-Dateien weg), gibt es Exit 1. Das ist korrekt gemäß A7 („Nie still weglassen" – hier wird abgebrochen, nicht still weggelassen). |

*Anmerkung zu Befund 1 & 2:* Ich habe die Logik genau nachgelesen.
- Zeile 750: `if not eintraege and fremd_zeilen:` -> Nur fremde Dateien da, keine Kette-Dateien. Exit 1. (A7 Fall a).
- Zeile 756-764: Kürzung.
- Zeile 758: `if eintraege and not drin:` -> Kette-Dateien waren da, aber alle weggekürzt. Exit 1. (A7 Fall b).
- Zeile 768: `if groesse > KETTE_PAKET_MAX:` -> Nach Kürzung immer noch zu groß. Exit 1. (A4).
Die Logik ist robust und deckt alle Fälle ab. Kein Befund.

## Nicht geprüft

- **Kann Hawe selbst pruefen:** T10 (Echter Lauf `review-auto mail_server_test`). Dies erfordert den Zugriff auf den echten Router und das Modell Qwen3.6-35B.
- **Braucht externe Quelle:** Kein weiterer Bedarf.

## Abweichende Meinung

Keine. Die Umsetzung ist strikt nach Spec und Anforderung. Die Trennung von „fremd" und „Kette" über den Kurztitel in der Commit-Nachricht ist implementiert und getestet. Die Vorrang-Logik ist korrekt in die Paket-Erzeugung integriert.