# Scout-Planungsdiskussion mit Slipstream

Vorbereitet, noch nicht ausgeführt. Aufgabe ist **scout_kw_doppelversand** aus
Hawes Originalprompt, nicht die alte eingefrorene scout_20261014-Aufgabe.
Nur die erste Diskussionsantwort: keine Spec, keine Umsetzung, kein Mailversand.

## Eingabe

original_user_prompt.txt enthält den Originalauftrag. prompt.json enthält genau
zwei Nachrichten: die aktuelle Review-Rolle samt Modellidentität/Information zum
Dateikontext und den Originalauftrag mit vollständigen, nummerierten Dateien:

- agents/llm_scout/llm_scout.py
- scripts/send_scout_email.py
- scripts/run_scout_pipeline.sh
- docs/projekt_management/_vorlage_spec.md

Snapshots und SHA-256 in INPUT_MANIFEST.json/FROZEN.json. Keine vorherige
Modellantwort, Lösungsschlüssel oder nachträglichen Korrekturen im Modellkontext.
Quellcode enthält Konfigurationsnamen, keine ausgelesenen Schlüsselbunddaten.
Die Dateien werden als Text übermittelt, nicht importiert/ausgeführt. Keine
Datei-/Shell-/MCP-Werkzeuge für das Modell. Der spätere Spec-Schreibauftrag wird
jetzt nicht gegeben. Keine Änderungen an Quelldateien oder Git-Zustand.

## Modell und Grenzen

Bewährtes Slipstream-v0.3.4-Bundle, vorhandener verifizierter Qwen3.6-35B-A3B-
UD-Q4_K_XL, GGUF extern, aktive PGRN intern. Kein Download oder Konvertierung.
Cache2GiB/Reserve8GiB, IO1, Batch32/UBatch32, MTP4, Temp0/Seed42.
Kontext32768, weil Originalauftrag, Rolle, vier vollständige Dateien und4096
Ausgabetokens hineinpassen müssen. Template wird vor der Anfrage tokenisiert;
bei fehlendem Platz Abbruch statt stiller Kürzung. Kein Kontextverschieben.
Thinkingoff/Budget0/Formatdeepseek; separate Reasoningdaten werden gespeichert,
wenn geliefert. Maximal4096generierteTokens; length ist unvollständig.

Laden bis420s, Anfrage bis1800s, kein automatischer Retry. Das frühere Modell
benötigte für9843Prompttokens rund12Minuten; dieser vollständige Kontext kann
erneut einen langen Lauf ergeben. Fortschrittsmeldung alle30s auch vor dem
allerersten Antworttoken. Speicher-/Swapoutwache wie bei bewährten Tests.

## Start im normalen macOS-Terminal

Das Labor lief bei der Vorbereitung noch. Bestehende Dienste werden niemals
automatisch gestoppt. Vorher das normale Labor über dessen Launcher beenden;
nicht parallel zu Qwen3.8 laden. Dieser konservative Starter verlangt alle
Laborports8080/8091/8092/8093/8787frei und keine andere erkannte Modellinstanz.
Danach:

```bash
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/scout_planning_comparison/run_review.py'
```

Eigene Engine auf127.0.0.1:8083, danach eigene Engine/Client/caffeinate beenden.
Keine Dienste wieder starten. Ctrl+C bereinigt ebenfalls nur eigene Prozesse.
Die bekannten ps-/localhost-Beschränkungen der Agentenumgebung wurden nicht
nochmals ausgelöst; eigentlicher Start im normalen Terminal erforderlich.

## Ergebnisse und Vergleich

runs/<UTC>/answer.txt und reasoning.txt unveränderte Originalstrings;
stream.jsonl, request.json, responses.json, report.json, engine.log,
memory.jsonl mit Zeiten, Tokenzahlen, Finish-Grund und Speicherverlauf.
Die technische Bestehensmeldung bedeutet keine Bestätigung fachlicher Qualität.

Nach dem Lauf die gespeicherte Diskussionsantwort gegen den Code prüfen und der
geposteten Qwen3.8-Antwort gegenüberstellen. Die Bewertung ist nicht blind:
Qwen3.8-Antwort und eigene Korrekturen sind dem auswertenden Assistenten bekannt,
dem getesteten Modell aber nicht übermittelt worden. Kriterien: belegte
Codeaussagen, konkrete Wirkung, unbegründete Scope-Erweiterung, nötige Rückfrage,
Befolgung der Diskussionsphase, abgeschlossene Antwort, Laufzeit.

Vergleichsgrenzen: Qwen3.8 erhielt den Kontext über die bisherige UI/ggf.Tools;
Slipstream bekommt vier vollständige Dateien inline. Die genauen UI-Nachrichten,
Tooltranskripte und Samplingwerte wurden nicht aufgezeichnet. Es ist daher ein
qualitativer Vergleich zweier Arbeitskonfigurationen, kein kontrollierter
isolierter Backendbenchmark und keine allgemeine Modellrangliste.
