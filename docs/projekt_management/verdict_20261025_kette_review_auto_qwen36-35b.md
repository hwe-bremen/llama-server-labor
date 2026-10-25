# Verdikt: kette_review_auto

- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Datum:** 2026-10-25
- **Rücksetzpunkt:** a74e250
- **Geprüft gegen:** review_paket_20261025_kette_review_auto.md

## Ergebnis

**NACHBESSERN**

## Befunde

| # | Schwere | Datenverlust | Unbemerkt | Harte Vorgabe | Beschreibung |
|---|---------|:---:|:---:|:---:|---|
| 1 | hoch | nein | ja | nein | A4: Daueranzeige immer 0 s (Zeile 1255: `dt.datetime.now() - dt.datetime.now()`). Die Spec verlangt „Nach dem Lauf Dauer". |
| 2 | hoch | nein | ja | nein | A5: `_freier_verdiktpfad` prüft nur `exists()`, schreibt aber mit `write_text` (kein exklusiver Modus `x`). Race Condition – keine harte Vorgabe, aber die Spec sagt „exklusiv angelegt". |
| 3 | hoch | nein | ja | ja | A8: `subprocess.TimeoutExpired` wird von `urllib.request.urlopen` nie geworfen (Zeile 1140). Der Timeout-Fall „Zeitüberschreitung nach n s" wird nie angezeigt. Stattdessen kommt `socket.timeout`/`URLError` → „Router nicht erreichbar". |
| 4 | hoch | nein | ja | ja | A7/A6: `zusammenfuehren` (Zeile 730) bricht mit Exit 2 ab, wenn < 2 Verdikte übergeben werden. Bei nur einem gültigen Lauf wird `pass` gemacht (Zeile 1303), dann `zusammenfuehren([ein_pfad])` → Exit 2, kein Gesamtbefund. Die Spec sagt „trotzdem zusammenführen". |
| 5 | hoch | nein | ja | ja | A6: Warnhinweis bei UNVOLLSTÄNDIG wird nur eingefügt, wenn `gesamt_pfad.exists()` (Zeile 1310). Wenn `zusammenfuehren` fehlschlägt (z.B. Fall 4), existiert der Pfad nicht → Warnhinweis bleibt aus. |
| 6 | mittel | nein | ja | nein | A1: Prompt verlangt „Verdikt als reine Textantwort", aber der Code speichert die Antwort blind als Datei – er prüft nicht, ob die Antwort tatsächlich ein Verdikt-Format hat, bevor sie gespeichert wird. |
| 7 | mittel | nein | ja | nein | A6: `text.replace("**PASS**", "**UNVOLLSTÄNDIG**")` (Zeile 1312) ersetzt nur PASS. Wenn das Ergebnis NACHBESSERN oder FAIL ist, bleibt es so – das ist korrekt, aber die Anforderung sagt „nie PASS". Bei NACHBESSERN/FAIL ist UNVOLLSTÄNDIG nicht angezeigt, was irreführend sein kann. |

## Anforderungen einzeln

**A1: Neue Prompts ohne Datei-Zugriff** – teilweise erfüllt. Befund 6: Der Prompt enthält keine verbotenen Wendungen, aber der Code erzwingt nicht, dass die Antwort ein gültiges Verdikt ist.

**A2: Prüfen zuerst** – erfüllt. Exit 1 bei roten Unit-Tests, Exit 2 bei Werkzeugfehler.

**A3: Review-Paket bauen** – erfüllt. Exit 2 bei `paket`-Fehler.

**A4: Zwei Review-Läufe** – teilweise erfüllt. Befund 1: Daueranzeige immer 0 s.

**A5: Verdikte speichern, nie überschreiben** – teilweise erfüllt. Befund 2: Kein exklusiver Schreibvorgang.

**A6: Auswertbare Befund-Tabelle** – teilweise erfüllt. Befund 4, 5, 7: Gesamtbefund-Logik bei nur einem gültigen Lauf und Warnhinweis.

**A7: Zusammenführen** – nicht erfüllt. Befund 4: `zusammenfuehren` bricht bei < 2 Verdikten ab.

**A8: Fehlerfälle** – teilweise erfüllt. Befund 3: Timeout-Meldung toter Code.

**A9: Echter Lauf** – nicht geprüft (manuell, kein Code).

## Nicht geprüft

- T14 (echter Lauf am K7-Stand): erfordert echten Router, kein Code.
- Die Testabdeckung für T7 (bitgleiche alte Datei), T8 (Ergebnis UNVOLLSTÄNDIG im Output), T12 (HTTP-Fehler-Fall) ist unvollständig, aber das sind Testlücken, keine Codebefunde.
