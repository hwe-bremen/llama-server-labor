# Qwen3-Coder-Next Q4_K_M: Laufzeit-Kompatibilitätsbefund

## Entscheidung: NO-GO für den getesteten Inferenzpfad

[BELEGT] Unveränderte Slipstream-v0.3.4-Engine lädt GGUF und PGRN, bestätigt die vorgesehenen Parameter und erreicht Bereitschaft. Die erste Anfrage scheitert beim Prefill mit einem PGRN-Geometriefehler. Damit ist die erfolgreiche Konvertierung kein Nachweis funktionsfähiger Inferenz.

Diese Entscheidung gilt für die tatsächlich getestete Binary, das konkrete Modell und die dokumentierten Parameter. Sie beweist nicht, dass jede alternative Konfiguration oder spätere Engineversion scheitern muss. Für solche Alternativen besteht kein Erfolgsnachweis. Kein weiterer Versuch gestartet.

## 1. Identität und Voraussetzungen

[BELEGT] Engine-SHA-256: `7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e`.
[DOKUMENTIERT] GGUF: unsloth/Qwen3-Coder-Next-GGUF, Qwen3-Coder-Next-Q4_K_M.gguf, Revision ce09c67b53bc8739eef83fe67b2f5d293c270632. Vollständige SHA- und PGRN-CRC-Prüfung im erfolgreichen Konvertierungsprotokoll. Geroutete Expertentypen Q4_K/Q6_K akzeptiert; keine nachgewiesene Quantisierungsblockade wie beim früheren GLM-Versuch.

[BELEGT] Aktueller Test: `first_inference_runs/20261018T120921572911Z/`. Start mit 4096 Kontext, batch=ubatch=25 und einer Sequenz; bestätigter PGRN-Cache 12286,59 MiB, Scratch 996,00 MiB, Headroom 8192,00 MiB. Modell laden / Bereitschaft nach rund 276,8 Sekunden. Nativer Live-Headroom nach Kontextallokation: 14951,88 MiB.

## 2. Tatsächlicher Fehler

[BELEGT] Test A fragt nach 17 + 25, höchstens 32 Ausgabetokens. Engine meldet 25 Prompttokens und effektiven Batch 25. Beim Prefill:

```text
process_ubatch: PGRN staging failed: top-k tensor geometry is incompatible with PGRN staging
llama_decode: failed to decode, ret = -3
srv decode: Compute error. off = 0, n_batch = 25, ret = -3
```

[BELEGT] Client erhält HTTP 500. Kein erfolgreiches Antwortobjekt und keine erfolgreiche Modellantwort. Tests B und C nicht gesendet. Die zwei früheren Abbrüche waren Fehler in der Testbeobachtung; dieser dritte tatsächliche Start erreicht die Anfrage und scheitert innerhalb der Engine.

## 3. Codebezug und Grenzen der Ursachenbestimmung

[BELEGT / CODEPRÜFUNG] `source_evidence/slipstream-seams_v0.3.4.patch`, Funktion `llama_context::pgrn_eval`, enthält genau diese Fehlermeldung. Sie wird gesetzt, wenn mindestens eine dieser Bedingungen nicht erfüllt ist:

- Tensor ist GGML_TYPE_I32.
- Erste Dimension entspricht model.hparams.n_expert_used.
- Zweite Dimension ist positiv.
- Dritte und vierte Dimension sind jeweils 1.
- Erster Byte-Stride entspricht sizeof(int32_t), also 4.

[BELEGT / CODEPRÜFUNG] Diese Prüfung kommt vor der separaten Kapazitätsprüfung, dem Auslesen der IDs und dem Aufruf zum Experten-Staging. Das beobachtete Problem ist daher keine belegte Überschreitung der 256 unterschiedlichen IDs. batch=ubatch=25 wurde bestätigt.

[HYPOTHESE] Ein vom qwen3next-/Backend-Graph gelieferter Callbacktensor entspricht nicht dem PGRN-Vertrag. Welche der Typ-, Dimensions- oder Stridebedingungen konkret verletzt ist, lässt sich aus dem vorhandenen Log nicht unterscheiden. Konkrete Tensorwerte werden bei diesem Fehler nicht protokolliert. Keine genauere Ursache oder einfache Batchlösung behauptet.

[BELEGT] MXFP4-Metalkernel werden vor dem Fehler kompiliert. Das beweist keine vollständige erfolgreiche MXFP4-Modellausführung. Tool-Calling und Reviewerqualität bleiben ungeprüft.

## 4. Speicher und Abschluss

[BELEGT] Gemessene freie Prozentanzeige während des protokollierten Laufs: 91 bis 92 Prozent. Kumulative Swapouts Anfang 14275454 / Ende 14275454. Diese Werte sind weder ein vollständiger Unified-Memory-Peak noch eine garantierte Allokationsreserve.

[BELEGT] Eigener Serverprozess PID 65833 kontrolliert beendet, Exit 0. Port 8083 anschließend frei, beobachtete übrige Labor-Listener vor/nachher unverändert. Keine bestehenden Dienste geändert. Keine Engine-, Konverter-, Modell- oder Konfigurationsänderung während dieser Diagnose.

## 5. Konsequenz

[BELEGT] Der frühere statische GO-Befund und die erfolgreiche Konvertierung bleiben als historische Ergebnisse nachvollziehbar; ihre Reichweite endet vor dem nun tatsächlich gescheiterten Laufzeitpfad. Für produktive Review-Evaluation mit dieser getesteten Installation gilt NO-GO.

[DOKUMENTIERT] Rohbelege: engine.log, result.json, request_A.json, memory.jsonl und FIRST_INFERENCE_REPORT.md im genannten Laufverzeichnis; Callbackcode im lokalen Quellabbild.

Nächster sinnvoller technischer Schritt wäre eine separate Untersuchung des Callbacktensor-Vertrags mit genauer Erfassung von Typ, ne[] und nb[]. Eine instrumentierte Engine oder ein Update wäre ein neuer, gesonderter Auftrag und wurde nicht vorgenommen. Keine erneute Konvertierung oder identische Testwiederholung empfohlen.
