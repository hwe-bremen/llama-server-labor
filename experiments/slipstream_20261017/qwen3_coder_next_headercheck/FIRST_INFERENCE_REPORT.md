# Qwen3-Coder-Next: erster isolierter Inferenztest

## Ergebnis: BLOCKED

[BELEGT] Vorprüfung am 2026-10-18T11:25:40.467189+00:00. Kein eigener Server gestartet, keine Testanfrage gesendet und kein bestehendes Modell entladen. Die Blockade ist das aktuelle Speicherbudget, kein nachgewiesener Modellfehler.

## 1. Vorprüfung und Modellidentität

[BELEGT] SSD eingebunden: True; Port 8083 frei: True.
GGUF: 48,528,320,544 Bytes. PGRN: 46,909,751,296 Bytes. Beide regulär, Größen passend und Änderungs-/Statuszeiten vor dem erfolgreichen Prüfabschluss.

[DOKUMENTIERT] Erfolgreicher Lauf: `/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3_coder_next_headercheck/download_conversion_runs/20261018T091238425764Z/result.json`. Vollständige GGUF-SHA-256-Prüfung, nativer Dry-run, Konvertierung Exit 0 und vollständige CRC-Prüfung aller 24.576 Records dokumentiert. Keine unnötige erneute Vollhashprüfung durchgeführt.

GGUF-SHA-256: `9e6032d2f3b50a60f17ce8bf5a1d85c71af9b53b89c7978020ae7c660f29b090`.
PGRN-SHA-256: `7c2638876bf7ecca53fc84f55a5803bf14405f817c1198698e8b2802417ab10e`.
[BELEGT] Engine-SHA-256 `7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e` stimmt mit der geprüften v0.3.4-Binary überein. Vorbereitete CLI-Flags in der zugehörigen gespeicherten Hilfe vorhanden: True.

## 2. Startbefehl und Parameter

Nicht ausgeführt. Geplante Argumentliste:

```sh
/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/runtime/Slipstream.app/Contents/Resources/resources/llama-server --model '/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf' --pgrn /Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/pgrn/qwen3-coder-next/Qwen3-Coder-Next-Q4_K_M.pgrn --host 127.0.0.1 --port 8083 --ctx-size 4096 --pgrn-cache-gb 12 --pgrn-headroom-gb 8 --batch-size 25 --ubatch-size 25 --parallel 1 --spec-type none --reasoning off --temp 0 --seed 42 --gpu-layers 99 --jinja
```

[DOKUMENTIERT] Kontext 4096, Cache 12 GiB, Headroom 8 GiB, batch=ubatch=25, parallel=1, keine Spekulation, reasoning off, Temperatur 0, Seed 42, GGUF-Jinja. Stagingobergrenze aus der Codeprüfung: höchstens 250 angeforderte IDs bei zehn aktiven Experten je Token.
[HYPOTHESE] Effektive Werte müssen beim späteren tatsächlichen Start aus dem Log bestätigt werden. Noch kein Nachweis des Laufzeitpfads.

## 3. Lade- und Speicherbeobachtung

[BELEGT] memory_pressure -Q meldet 27 % freien Speicher. Bei 48 GiB entspricht das näherungsweise 12.96 GiB. Dies ist eine prozentbasierte Schätzung, keine präzise Zusage allozierbaren Speichers.
[BELEGT] vm_stat: wired 26.09 GiB; Compressor 8.27 GiB. Kumulative Swap-Zähler sind in den Rohdaten; sie belegen keine aktuelle Swaprate. Aktuelle Swapbelegung und allgemeine Prozess-RSS-Abfrage sind von der Ausführungsumgebung gesperrt.

[DOKUMENTIERT / RECHNERISCH] Residente Tensoren + 12 GiB Expertencache + Scratch vor Backendalignment + F16-Attention-KV bei 4096 Kontext ergeben 14.66 GiB. Rekurrente Zustände, Graph-/Prefillbuffer und Backendoverhead fehlen noch. Mit geplantem Headroom von 8 GiB ergibt sich bereits eine konservative Planungsschwelle von 22.66 GiB zusätzlich zum bestehenden Bedarf. Dies ist eine Planungsregel, keine gemessene Runtime-Admission.

[BELEGT] lsof zeigt einen bestehenden llama-server-Prozess PID 57185 mit geöffneter Qwen3.6-27B-MTP-GGUF sowie einen Ollama-Runner PID 50719 mit Modelldatei. Das beweist geöffnete Modellgewichte, nicht deren vollständig residenten RAM-Anteil. Kein Modelllade-Endpunkt aufgerufen.

Kein plausibles zusätzliches RAM-Budget; Teststart gemäß Auftrag unterlassen. Ladezeit, Peak und Tokens/s nicht gemessen.

## 4. Funktionstests

| Test | Vorbereitung | Ergebnis |
|---|---|---|
| A: 17 + 25 | 32 Ausgabetokens, erwartet 42 | Nicht ausgeführt |
| B: Kennwort im längeren Prompt | 64 Ausgabetokens; tatsächliche Eingabetokenzahl muss mindestens 200 betragen | Nicht ausgeführt; Tokenzahl nicht gemessen |
| C: Code-Review | 512 Ausgabetokens; Null fälschlich eingeschlossen, Division durch null bei leerer Auswahl | Nicht ausgeführt |

Requests und Erwartungswerte liegen im Rohdatenverzeichnis. Keine Aussagen über Reviewerqualität oder Metal-Ausführung möglich.

## 5. Fehler und offene Fragen

- [BELEGT] Speicherprüfung verhindert den Start; Port und Dateigrößen sind kein Blocker.
- [BELEGT] ps und sysctl sind hier eingeschränkt; keine Schutzmechanismen umgangen.
- [HYPOTHESE] Nach bewusstem Freigeben von RAM durch den Benutzer kann der isolierte Test möglich sein. Eine neue Vorprüfung bleibt erforderlich.
- [HYPOTHESE] PGRN-Laden, MXFP4-Shared-Experts auf Metal, effektive ubatch und Modellantworten sind noch ungeprüft.

Vorbereitete, noch nicht angewandte Grenzen: Laden maximal 20 Minuten, je Anfrage maximal 10 Minuten, gesamter Versuch maximal 60 Minuten; regelmäßige Beobachtung und Abbruch bei kritischem Druck. Ein späterer Test muss ausschließlich seine eigene PID stoppen.

## 6. Abschlusszustand und Empfehlung

[BELEGT] Kein eigener Prozess zu beenden. Beobachtete Labor-Listener vor/nachher identisch: True. Das ist ein Listenernachweis, keine umfassende Funktionsprüfung bestehender Dienste.

Nächster Schritt: Benutzer gibt bewusst RAM frei, etwa durch eigenes Stoppen bzw. Entladen des normalen LLM-Labors. Das wurde hier ausdrücklich nicht vorgenommen. Anschließend Vorprüfung und isolierten Test erneut ausführen; keine automatische Fortsetzung oder Neustartschleife eingerichtet.

Rohdatenverzeichnis: `/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3_coder_next_headercheck/first_inference_runs/20261018T112540343132Z`.
