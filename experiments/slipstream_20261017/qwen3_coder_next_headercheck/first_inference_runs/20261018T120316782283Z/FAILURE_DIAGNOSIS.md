# Diagnose: zweiter Start, Cache-Rundung im Prüfskript

[BELEGT] Der echte Lauf lud das Modell und meldete Bereitschaft nach rund 276,9 Sekunden. Keine Testanfrage gesendet. Eigener Prozess anschließend kontrolliert beendet, Exit 0, Port 8083 frei.

[BELEGT] Tatsächliche Parameter im Debuglog: Architektur qwen3next; n_ctx=4096, n_batch=25, n_ubatch=25, n_seq_max=1. PGRN admitted cache=12286.59 MiB, scratch=996.00 MiB, headroom=8192.00 MiB. Live-Headroom nach Kontextallokation=14942.59 MiB. Damit ist PGRN-Admission nachgewiesen; Tokenausgabe weiterhin ungeprüft.

[BELEGT] Erneuter Abbruch durch zu enge Cache-Prüfung des Testskripts: erwartet 12288 MiB mit 1 MiB Toleranz. Der native Konverter ist nicht betroffen. Die Runtime rundet den angeforderten Höchstwert auf vollständige Slots ab: floor(12884901888 / 2039808) * 2039808 = 12883427328 Bytes = 12286.59375 MiB. Unterschied zum Höchstwert: 1474560 Bytes = 1.40625 MiB. Korrektes Verhalten der Engine; Fehler im Testskript.

[BELEGT / CODEPRÜFUNG] v0.3.4 engine/src/peregrine_runtime.cpp berechnet capacity64=expert_cache_bytes/slot_bytes und runtime->cache_bytes=capacity*slot_bytes. Quellausschnitt mit Herkunft und Git-Blob unter source_evidence/runtime_cache_rounding_v034.txt gespeichert.

[BELEGT] Korrektur ausschließlich im Testskript: Sollwert aus vollständigem Tensorinventar und maximalem Record berechnet; zweistellig gerundetes Log mit 0,006 MiB Toleranz verglichen. Headroom-Prüfung bleibt strikt. Keine Engine-/Modelländerung.

[BELEGT] Das vollständige echte Engine-Log dieses Laufs wird nun offline akzeptiert. Fünf manipulierte Varianten werden abgewiesen: falsche Cachewerte, falscher Headroom, ubatch=512 und zwei Sequenzen. Kein weiterer Serverstart zur Prüfung ausgeführt.

[HYPOTHESE] Erst ein weiterer autorisierter Terminaldurchlauf kann Tokenausgabe, Prefill und Review-Smoke-Test prüfen. Vorhandene Dateien und Logs bleiben unverändert. Derselbe run_first_inference.py-Befehl verwendet die korrigierte Prüfung.
