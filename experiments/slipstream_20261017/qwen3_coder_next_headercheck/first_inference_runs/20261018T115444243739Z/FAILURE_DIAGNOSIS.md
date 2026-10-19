# Diagnose des ersten tatsächlichen Inferenzstarts

[BELEGT] Engine-Log: `model loaded`, danach `listening on http://127.0.0.1:8083` nach rund 288,6 Sekunden. Das Skript erhielt Bereitschaft nach rund 288,9 Sekunden.

[BELEGT] Abbruchursache im result.json: `RuntimeError: Effektive Parameter fehlen/weichen ab: {}`. Keine der erwarteten Kernparameterzeilen war im Engine-Log enthalten. Startlog nennt verbosity=3. Keine Testanfragen gesendet.

[BELEGT] Eigener Testprozess sauber beendet, Exit 0; Port 8083 danach frei. Gesamtlauf als FAIL markiert, weil die geforderten Parameter nicht nachgewiesen wurden. Das ist kein Nachweis einer Modellinkompatibilität.

[BELEGT] Die zugehörige Enginehilfe unterstützt --verbosity 5 (Debug) und --log-colors off. Das Testskript setzt diese Optionen nun explizit; die Prüfung effektiver Kontext-, Batch-, Parallelitäts- und Cachewerte bleibt strikt. Keine Engine-/Konverteränderung, keine erneute Konvertierung und kein neuer Start durchgeführt.

[BELEGT] Vorhandenes Log reproduziert den Prüfabbruch. Ein synthetisches vollständiges Parameterlog wird akzeptiert; abweichende ubatch-/Headroomwerte werden weiterhin zurückgewiesen.

[HYPOTHESE] Mit Debuglogging werden die fehlenden Kerndiagnosen sichtbar. Das muss ein späterer echter Start bestätigen. PGRN-Admission und tatsächliche Tokenausgabe sind weiterhin nicht nachgewiesen.

[BELEGT] Speicherproben: freie Prozentanzeige Minimum 89 % / Maximum 92 %; kumulative Swapouts Anfang 14275454 / Ende 14275454. Keine Aussage über gesamten Unified-Memory-Peak aus RSS allein.

Fortsetzung im normalen Terminal mit demselben run_first_inference.py-Befehl. Der Ablauf startet genau einen eigenen Testserver, prüft dessen Parameter und beendet ihn nach Tests oder Fehler. Das normale LLM-Labor währenddessen gestoppt lassen.
