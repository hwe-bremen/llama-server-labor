# Begrenzter Geschwindigkeitstest: Experten-Cache2GiB gegen12GiB

Vorbereitet, noch nicht ausgeführt. Kein neuer Qualitäts-/Reviewer-Ausbau.

## Fester Umfang

Genau2frische Engine-Prozesse, Reihenfolge A2GiB, danach B12GiB. Jeweils3identische
kurze Anfragen. Identischer eingefrorener Prompt aus dem bereits erstellten
case04, keine Musterlösung. Der Code dient nur als festes Inferenzmaterial.
Maximal128generierteTokens pro Anfrage; finish_reason=length ist hier der
beabsichtigte Lastdeckel und keine vollständige Review-Antwort. Keine Bewertung
von Qualität oder Inhalt, keine Ausführung generierter Texte.

GGUF extern, aktive PGRN intern; dieselbe verifizierte Engine und Artefakte.
Einziger Unterschied der Engineargumente zwischen A/B: --pgrn-cache-gb2/12.
Kontext4096, Headroom8GiB, IO1, Batch/UBatch32, MTP4, Temp0/Seed42,
Thinkingoff/Budget0, kein mmap/repack/warmup, kein Kontextverschieben,
cache_prompt=false, identische neue Nachrichtenpaare ohne Historie.

Die installierte --help bezeichnet pgrn-cache-gb als harte Obergrenze; die reale
Zuteilung kann kleiner sein. Diese wird aus nativen Cache-Zeilen erfasst.
12GiB ist ein begrenzter sechsmal größerer Zielcache auf dem48GiBMac, kein
Versuch, alle Experten in den Speicher zu drücken. Aktuelle memory_pressure
meldete84%free, was nicht mit exakt allocierbarem RAM gleichgesetzt wird.
Engineadmission/8GiBReserve und vorhandene Swapout-Abbruchwache bleiben aktiv.

## Messung

Prozessladen, native Promptzeit/-rate, erster finaler Antworttext, native
Decoderate, Anfragezeit, Prompt-/Ausgabetokens, native Cachegröße/Highwater und
Hits/Misses je Anfrage. RSS und systemweite Swapouts laufend überwacht.
Geräteweite physische Lesezähler pro Anfrage und in Rohsamples; keine exklusive
Prozess-/Dateizuordnung behaupten. Fehlende Gerätewerte entwerten nicht die
nativen Geschwindigkeitssamples, bleiben ausdrücklich fehlend.

Erste Anfrage arena-kalt; zweite/dritte mit bereits gefüllter Arena. Keine
Prompt-KV-Wiederverwendung voraussetzen: tatsächliches cache_n muss0sein.
Physischer OS-Dateicache unkontrolliert, keine Cache-Purges/Speicherverknappung.
A läuft zuerst, B kann vom erwärmten OS-Cache profitieren. Nur ein Prozesspaar;
drei Requests sind keine drei unabhängigen Prozesswiederholungen.

Auswertbar nur bei zwei erfolgreich bereinigten Prozessen, je3Anfragen,
identischen CLI-Argumenten außer Cache, messbar größerer realer B-Arena,
cache_n0 und gleichen Tokenzahlen. Identität aller sechs Antworttexte separat
prüfen; bei Abweichungen ist der Inhalt/Expertenzugriff nicht mehr vollständig
gleich, sodass eine spätere Bewertung diesen Vorbehalt berücksichtigen muss.
Kein Signifikanzanspruch, keine Langkontext-Hochrechnung aus dem kurzen Test.

Native Miss-Deltas und tatsächliche Cachegröße helfen, eine Besserung durch
Expertenwiederverwendung von bloßem OS-Dateicaching zu unterscheiden. Auch ein
positives Ergebnis beweist weder Reviewerqualität noch gleich schnelle
Verarbeitung des13.772TokenScout-Prompts. Der Kontext ist hier bewusst kürzer.

## Start

Im normalen macOS-Terminal wie bei den bisherigen Inferenztests:

```bash
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/cache_speed_comparison/run_comparison.py'
```

Labor/andere Modellinstanzen müssen gestoppt sein. Auch ein Ollama-bge-m3-
Runner zählt im konservativen Guard als andere Instanz. Keine automatische
Entladung oder Dienststopps; bei Konflikt Abbruch. Eine gemeinsame Sperrdatei
verhindert konkurrierende eigene Experimente. Prozessprüfung erfolgt im normalen
Terminal; bekannte ps-/localhost-Sandboxbeschränkungen nicht erneut ausgelöst.

Je Prozess Laden bis420s, Client bis780s; pro Anfrage bis240s. Kein Retry,
kein weiterer Variantentest bei Fehler/Swapout-Abbruch. Fortschritt alle30s.
Es ist grob ein Lauf im Bereich10–15Minuten denkbar, keine gemessene Zusage;
die genannten Zeitlimits sind die harten Grenzen. Ctrl+C bereinigt nur eigene
Engine/Client/caffeinate. Labor wird danach nicht automatisch gestartet.

## Dateien und Auswertung

runs/<UTC>/A2GiB und B12GiB enthalten command/report.json, engine.log,
memory.jsonl, responses.json,3request-/stream-/answer-Dateien. Übergeordnet:
summary.json, ERGEBNIS.md mit Median/Spannweite, erste/wärmere Anfragen getrennt,
realer Cachegröße, CLI-Gleichheitsprüfung, Swap und B/A-Verhältnissen.

Offlineprüfung in test_harness.py verwendet nur künstliche Daten in temporären
Ordnern:3gleiche Requests, erwartetes length, Speicherung, Counter-Deltas und
A/B-Argumentkontrolle. Sie ist kein Geschwindigkeitsergebnis.

Nach dem tatsächlichen Lauf prüfen wir, ob12GiB wirklich zugelassen wurden,
Cache-Misses sinken und insbesondere Eingabeverarbeitung/TTFT besser werden.
Ein fehlender Vorteil bei diesem Paar ist kein universeller Gegenbeweis;
der begrenzte Versuch liefert die letzte Entscheidungsgrundlage für diesen
Reviewer-Ausbau. Keine weiteren Modelle, Konvertierungen oder Installation.
