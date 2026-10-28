# Verdikt: kette_review_auto – Betrieb

- **Spec:** `spec_20261025_kette_review_auto.md`
- **Handover:** `handover_20261025_kette_review_auto.md`
- **Datum:** 2026-10-25
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `role-split/kette/kette.py` (Zeilen 85–115, 728–774, 1074–1386), `tests/test_kette_review_auto.py` (Zeilen 1–370), `docs/projekt_management/review_paket_20261025_kette_review_auto.md`

## Ergebnis

**NACHBESSERN** – Zwei Befunde der Schwere „hoch": (1) Timeout-Fehlerpfad ist unvollständig, weil `subprocess.TimeoutExpired` bei `urllib.request.urlopen` nie geworfen wird; der Fall „Zeitüberschreitung" bleibt unbemerkt und läuft durch als anderer Fehler. (2) Bei einem fehlgeschlagenen Lauf 2 wird das Lauf-1-Verdikt zwar gespeichert (wie gefordert), aber der Auswertbarkeits-Check wird übersprungen und `zusammenfuehren` nicht aufgerufen – das Ergebnis „UNVOLLSTÄNDIG" wird nie erreicht, und der Nutzer sieht nur die Exit-1-Meldung ohne Hinweis auf das erhaltene Verdikt.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `kette.py:1140` | `except subprocess.TimeoutExpired` wird bei `urllib.request.urlopen` niemals ausgelöst. `urllib` wirft `socket.timeout` (oder `urllib.error.URLError`), nicht `subprocess.TimeoutExpired`. Die Anforderung A8 verlangt explizit „Zeitüberschreitung → Exit 1 mit Meldung". Der Fall läuft stattdessen durch den allgemeinen `except Exception` (der aber im Code nie erreicht wird, weil `_api_ruf` alle Fehler abfängt) → die Timeout-Meldung erscheint nicht, und der Fall wird als unbekannter Fehler behandelt. Korrektur: `except socket.timeout` oder `except (socket.timeout, urllib.error.URLError)` fangen den Timeout ab und geben die korrekte Meldung. |
| 2 | nein | ja | nein | hoch | `kette.py:1267–1268` | Wenn Lauf 2 scheitert (z.B. Router nicht erreichbar), wird `return 1` sofort ausgeführt. Lauf-1-Verdikt existiert bereits (Zeile 1259), `zusammenfuehren` wird nicht aufgerufen, der Auswertbarkeits-Check (A6) wird nicht durchgeführt. Das Ergebnis ist nie „UNVOLLSTÄNDIG", obwohl nur ein Lauf gültig ist. Der Nutzer sieht „Lauf 2 gescheitert – Exit 1" im Terminal, aber keine Datei, die den Status dokumentiert. Die Anforderung sagt: „ein bereits gespeichertes gültiges Verdikt bleibt, das fehlerhafte wird nicht gespeichert, kein Gesamtbefund" – das Verdikt bleibt, aber der Nutzer hat keine Möglichkeit zu erkennen, dass es sich um einen unvollständigen Lauf handelt. Korrektur: Nach Lauf-2-Fehler prüfen, ob Lauf 1 gültig ist; wenn ja, Gesamtbefund als „UNVOLLSTÄNDIG" schreiben und Exit 1 zurückgeben. |
| 3 | nein | nein | nein | niedrig | `kette.py:1255` | `elapsed1 = int((dt.datetime.now() - dt.datetime.now()).total_seconds())` rechnet immer 0. Der Name `elapsed1` suggeriert eine Laufzeitberechnung, der Wert ist aber konstant 0. Kein Einfluss auf Logik. Korrektur: Startzeit vor `_api_ruf` speichern und nachher differenzieren. |
| 4 | nein | nein | nein | niedrig | `kette.py:1298–1303` | Der Code-Block `if len(gueltige_pfade) < 2:` enthält nur einen `pass` und keine Logik. Bei nur einem gültigen Lauf wird `zusammenfuehren` trotzdem mit einem Pfad aufgerufen, was `return 2` ergibt. Der Exit-Code 2 wird danach auf 1 überschrieben (Zeile 1318), wenn `unvollstaendig` True ist. Wenn beide Läufe gültig sind, ist alles korrekt. Korrektur: Entweder den Block entfernen oder eine sinnvolle Behandlung für den Ein-Fall einbauen. |
| 5 | nein | ja | nein | mittel | `kette.py:1107–1109` | Der Herzschlag-Thread ist ein `daemon=True`-Thread. `thread.join(timeout=2)` wartet maximal 2 Sekunden. Wenn der Thread danach noch läuft, wird er nicht mehr beendet – er läuft im Hintergrund weiter. Bei wiederholten `review_auto`-Aufrufen (z.B. in einem Script-Loop) stapeln sich Threads auf. Korrektur: `thread.join()` ohne Timeout oder `thread.daemon = True` mit explizitem `stop.set()` vor dem Verlassen. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:** T14 (echter Lauf am K7-Stand) – erfordert echten Router und Modell 35B-A3B.
- **Braucht externe Quelle:** Verhalten von `urllib.request.urlopen` bei Timeout vs. `socket.timeout` (Python-Doku).

## Abweichende Meinung

Keine.
