# Kleine Qwen-Code-Review-Evaluation

Sechs vorab formulierte, lokal überprüfte Python-Fälle. Vier Fehlerfälle über
Dateigrenzen, Cleanup, Nebenläufigkeit und Architektur; zwei korrekte Gegenbeispiele.
Diese Zuordnung und die Lösungen stehen NICHT im Modellprompt. Der Reviewer erhält
nur einen unveränderten einheitlichen Auftrag, vollständige Quelldateien mit
Zeilennummern und Rahmenbedingungen. Keine Tools, kein Repositoryzugriff, kein
Gedächtnis, keine Chat-Historie, kein Nachfragen/Retry mit Lösungshinweisen.

Die vier privaten Reproduktionstests bestätigen die jeweils beschriebene
Vertragsverletzung. Ihre Assertions prüfen den reproduzierten Fehlerzustand;
grüne Tests bedeuten hier nicht fehlerfreien Fallcode. Zwei weitere Tests
bestätigen Cancellation-/Exception-Cleanup sowie Mandantentrennung, Invalidierung
und Kapazität der Gegenbeispiele.

## Unveränderliche Aufgaben und getrennte Lösungen

- `model_cases/case01` bis `case06`: Code und vollständiger Vertrag je Fall.
- `prompts/`: exakt erlaubte fertige Modellnachrichten, keine privaten Dateien.
- `instruction.txt`: der vom Nutzer vorgegebene Reviewer-Auftrag wortgleich.
- `settings.json`: vorab festgelegte Bedingungen.
- `private/answer_key.json`: Musterlösungen, Trigger und relevante Positionen.
- `private/verify_cases.py`, `verification.txt`: unabhängige Ausführung der
  selbst erstellten Reproduktionen/Gegenbeispiele vor den Modellantworten.
- `private/RUBRIK.md`: unveränderliche qualitative Bewertungsregeln.
- `FROZEN.json`: SHA-256 aller oben relevanten Aufgaben/Prompts/Privatdateien.

Private Dateien liegen zwar im Experimentverzeichnis, aber der Modellserver
bekommt ausschließlich die explizit gebauten Nachrichten. Er hat in diesem Lauf
keine Dateisystem-/MCP-Werkzeuge. Die Dateiübertragungsliste ist keine automatische
Rekursionssuche über das Evaluationsverzeichnis.

## Speicher, Kontext und Laufzeit

Dieselbe verifizierte Engine und Qwen-GGUF extern/PGRN intern. Cache2GiB,
Reserve8GiB, Batch/UBatch32/32, I/O1, MTP4, Temp0/Seed42, ein Slot, kein Repack,
keine Compact-/Prefetch-Erweiterung. **Kontext4096 statt512**, weil vollständiger
Code plus Review sonst nicht hineinpasst; keine ungeprüfte Übernahme der großen
Kontexte des Produktivlabors. Ausgabe je Fall höchstens1024Tokens, Thinking aus.
Kein Kontextverschieben; tatsächliches Chattemplate wird vor jeder Anfrage
gerendert und tokenisiert, mit128Tokens Marge vor dem Ausgabelimit.

Eine frische Unterhaltung heißt für jeden Fall neue System-/User-Nachrichten,
kein voriger Fall im Request, `cache_prompt=false`. Der physische Expertencache
bleibt zwischen Fällen warm; die feste Reihenfolgecase01…06 und deren Einfluss
auf Laufzeiten werden dokumentiert. Das ist kein Kaltcachevergleich.

SSE-Rohantworten, Klartext, genaue Requests, Prompttokenzahl, Finish-Grund,
Usage/nativeTimings, TTFT, Gesamtzeit und Engine-/Speicherlogs werden gespeichert.
`finish_reason=length` oder fehlender Abschluss/Antwort wird als unvollständig
markiert. Grenzen:600s je Fall und3660s für den Client insgesamt. Es gibt keine
automatische inhaltliche Benotung anhand von Schlüsselwörtern.

Nach Vorliegen der Antworten wird jeder Fall anhand der eingefrorenen privaten
Rubrik fachlich bewertet: gefunden/teilweise/übersehen, Ursache, falsche Befunde,
Gegenbeispiel-Fehlalarme, gekennzeichnete Vermutungen und praktische Laufzeit.
Abgeschnittene Antworten nicht pauschal als fachliches Versagen auslegen.
Keine Gesamtnote und keine allgemeine Qualitäts- oder Haiku-Aussage.
Aufgabenerstellung und Bewertung stammen vom gleichen Assistenten; die
Unabhängigkeit ist begrenzt, sechs kleine Fälle sind keine repräsentative Stichprobe.

## Freigegebene Ausführung

Wie bei den vorigen Inferenztests wegen der localhost-Beschränkung im normalen
macOS-Terminal ausführen. Keine zusätzliche Freigabe erforderlich:

```bash
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/reviewer_eval_6cases/run_eval.py'
```

Wenn das Labor oder andere erkannte Modellinstanzen laufen: Abbruch, kein
automatisches Stoppen oder Entladen. Nur eigene Engine/Client/caffeinate-Prozesse
werden nach dem Test beendet. Labor nicht automatisch neu starten. Ctrl+C führt
zum Cleanup. Keine Downloads, keine Konvertierung. Modellantworten werden niemals
als Befehle ausgeführt.

Ergebnisse in `runs/<UTC-Zeit>/`: `responses.json`, sechs `*-request.json`,
`*-stream.jsonl`, `*-answer.md`, technische `DURCHFUEHRUNG.md`, `engine.log`,
`memory.jsonl`, `report.json`. Letzterer enthält Geräte-/Arbeitsspeicher- und
Cleanup-Befunde; die technische Meldung INFERENZTEST BESTANDEN ist keine
inhaltliche Reviewer-Qualifikation.
