# Samplingdiagnose und GLM-4.5-Air: Prüfung vom 18.10.2026

## Entscheidung

**Phase A: vorbereitet, Startversuch durch die Ausführungsumgebung blockiert. Keine neue Inferenz und keine Aussage zum Temperaturvergleich möglich.**

**Phase B: NO-GO für GLM-4.5-Air Q4_K_M mit der vorhandenen Slipstream/PGRN-Installation.** Die lokalen Gewichte enthalten nicht zugelassene Expertentypen. Zusätzlich ist der dokumentierte Split-/Quellenhash-Pfad inkonsistent. Mehr RAM, ein größerer Cache und andere SSD-Pfade beheben diese Formatprobleme nicht.

Die frühere positive Machbarkeitsannahme im Auftrag ist damit überholt. Bereits vorhandene Projektberichte vom 17.10. enthalten diese Einschränkungen. Die wesentlichen Dateigrößen, Tensorinventare, Templates und Binary-Identitäten wurden heute erneut lokal geprüft.

Kennzeichnungen: **[BELEGT]** aktuelle lokale Prüfung oder konkret benannte gespeicherte Messung; **[DOKUMENTIERT]** veröffentlichte Beschreibung bzw. gespeicherter Quelltext; **[HYPOTHESE]** ungeprüfte Erwartung. Historische Belege werden ausdrücklich als solche bezeichnet.

## Teil A – Samplingdiagnose

### Vorhandene Testumgebung

**[BELEGT]** Der bisherige 12-GiB-Test ist rekonstruierbar:

- Starter und Runner: `../real_review_model_tags_12gib/run_review.py` und `isolated_runner.py`.
- Referenzlauf: `../real_review_model_tags_12gib/runs/20261017T211054421177Z/`.
- Tatsächliches Modell: Qwen3.6-35B-A3B, Ausgabe **UD-Q4_K_XL**, Architektur `qwen35moe`; kein GLM-Modell.
- GGUF: `/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen35b-reference/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`, 22.853.663.008 Bytes.
- PGRN: `../pgrn/Qwen3.6-35B-A3B-UD-Q4_K_XL.pgrn`, 20.128.754.176 Bytes, interne SSD.
- Engine: `../runtime/Slipstream.app/Contents/Resources/resources/llama-server`.
- Bundle 0.3.4; gespeicherte Buildausgabe b10116 / `852e7daa1`.
- Aktuell erneut berechnete Engine-SHA-256: `7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e`, identisch zum früheren Lauf.

Die großen Qwen-Dateien wurden heute per Pfad und Größe kontrolliert, nicht vollständig neu gehasht. Der vorhandene Runner prüft zusätzlich die früheren Download-/Konvertierungsnachweise. Für einen tatsächlichen Lauf ist seine Vorprüfung weiterhin erforderlich.

### Tatsächlicher Startversuch und Grenze

**[BELEGT]** Bereits ein Socket-Bind an `127.0.0.1:8083` scheitert mit `PermissionError: [Errno 1] Operation not permitted`. Derselbe Fehler beendet den vorbereiteten Starter, bevor er eine Engine startet. Belege: `preflight.json`, `attempt.log`.

Auch `/bin/ps` ist gesperrt; `sysctl` und `diskutil info` sind nur eingeschränkt bzw. nicht nutzbar. Damit fehlen zusätzlich Teile der bisherigen Prozess-/Systemvorprüfung. Dies ist kein gemessener Slipstream- oder Modellfehler. Es wurde keine Schutzprüfung entfernt und kein alternativer Ausführungsweg verwendet.

Auf 8080/8091/8092/8093/8787/8083 waren laut `lsof` keine Listener sichtbar; keine `llama-server`-Instanz wurde gefunden. Wegen des gesperrten vollständigen Prozesschecks wird daraus keine umfassende Aussage über alle denkbaren Modellprozesse abgeleitet. Keine vorhandenen Dienste wurden beendet, entladen, gestartet oder umkonfiguriert.

### Vorbereiteter Test

`run_sampling.py` verwendet den vorhandenen isolierten Runner unverändert und beendet ausschließlich seine eigenen Unterprozesse. Er verlangt ein bereits gestopptes Labor und verweigert den Lauf bei anderen erkannten Modellinstanzen. Ein laufendes Labor wird nicht automatisch angehalten. Beide Requests laufen nacheinander in derselben eigenen Engine. Promptcache ist deaktiviert.

| Einstellung | A | B |
|---|---|---|
| Modell / Engine / Template | vorhandener Qwen-Stand | identisch |
| Expertencache / Reserve | 12 / 8 GiB | identisch |
| Kontext / Parallelität | 16.384 / 1 | identisch |
| Batch / Ubatch / IO-Threads | 32 / 32 / 1 | identisch |
| MTP | draft-mtp, maximal 4 | identisch |
| Thinking | reasoning off, Budget 0, enable_thinking=false | identisch |
| Temperatur | 0 | 0,6 |
| Seed / maximale Ausgabe | 42 / 512 Tokens | identisch |
| Sonstige Sampler | vorhandene Engine-Defaults, kein neues Override | identisch |

Die gespeicherten bisherigen Defaults waren top_k 20, top_p ca. 0,95, min_p ca. 0,05, repeat_penalty 1 und DRY 0. Bei einer späteren Ausführung speichert der vorhandene Runner erneut `/props`; die tatsächlichen Werte sind dann erneut zu kontrollieren. Die CLI-Defaulttemperatur bleibt 0; die beiden API-Requests überschreiben sie explizit.

**[BELEGT]** Die vorbereiteten JSON-Requests unterscheiden sich ausschließlich im Feld `temperature`. Der identische Prompt ist vollständig in `A-request-prepared.json` und `B-request-prepared.json` enthalten. Nachrichten-SHA-256: `1f721f3c97ed3f143be73e5d150bfef3f8660ef85596cd068d135503229b7e10`.

Codeprobe:

```python
def clamp(value: int, lower: int, upper: int) -> int:
    if lower > upper:
        raise ValueError("lower must not exceed upper")
    return min(max(value, lower), upper)
```

Spezifikation: Nur Python-int-Eingaben; Begrenzung auf das inklusive Intervall, `ValueError` bei umgekehrten Grenzen; keine zusätzliche Typprüfung verlangt. Die Systemnachricht erlaubt ausdrücklich „Keine Beanstandung“ und verbietet zusätzliche erfundene Anforderungen.

**[BELEGT]** 2.541 Kombinationen wurden gegen eine unabhängig formulierte Fallunterscheidung geprüft. Zusätzlich gilt allgemein: Bei gültigem Intervall hebt `max` den Wert mindestens auf die Untergrenze; `min` begrenzt das Ergebnis auf die Obergrenze. Der vorangestellte Guard behandelt ungültige Intervalle. Das korrekte Reviewurteil ist „Keine Beanstandung“. Beleg: `prepared-verification.json`.

### Originalantworten und Messwerte

| Messgröße | A: Temperatur 0 | B: Temperatur 0,6 |
|---|---|---|
| Originalantwort | nicht erzeugt | nicht erzeugt |
| finish_reason | nicht vorhanden | nicht vorhanden |
| Eingabe-/Ausgabetokens | nicht gemessen | nicht gemessen |
| Inferenzlaufzeit | nicht gemessen | nicht gemessen |
| Wiederholungen / korrekter Abschluss | nicht prüfbar | nicht prüfbar |
| Falsche Beanstandungen | nicht prüfbar | nicht prüfbar |

Es werden keine Antworten aus älteren Vollreviews als Ergebnisse dieses neuen Tests ausgegeben.

### Interpretation und Fortsetzung

**[HYPOTHESE]** Greedy-Decodierung könnte die frühere semantische Wiederholungsschleife stabilisiert haben. Der heutige Startversuch liefert dazu keine neue Evidenz. Die bisherigen negativen Reviewbefunde bleiben unverändert; ein vollständiger neuer Review-Eval ist durch diese Vorbereitung nicht gerechtfertigt.

Auch ein späterer Erfolg beider kurzen Antworten würde die Hypothese nicht widerlegen: Der kleine Prompt könnte die frühere Schleife überhaupt nicht auslösen. Ein Erfolg nur bei 0,6 wäre ein lokaler Hinweis, kein Zuverlässigkeitsnachweis. Ein erfolgreicher API-Transport oder `[DONE]` genügt nicht; fachliches Urteil, Wiederholungen und Abschluss sind separat auszuwerten.

Zur Fortsetzung braucht es eine normale lokale Sitzung mit erlaubtem localhost-Bind und vollständiger Prozessprüfung. Dann aus dem Repository ausführen:

```sh
python3 -B experiments/slipstream_20261017/sampling_glm_20261018/run_sampling.py
```

Der Starter wurde syntaktisch geprüft; Codeprobe und Requestvergleich wurden ausgeführt. Der Inferenzpfad bleibt ungetestet. Er speichert vollständige SSE-Streams, Originaltexte, HTTP-Metadaten, usage, finish_reason, Laufzeiten und gegebenenfalls native timings unter `runs/<Zeitstempel>/`. Der bestehende Runner ergänzt Enginekommando, `/props`, Speicherüberwachung und kontrolliertes Cleanup. Nach einem tatsächlichen Lauf müssen beide Originalantworten inhaltlich geprüft und dieser Bericht ergänzt werden.

## Teil B – GLM-4.5-Air vorbereiten

### Modell und vorhandene Dateien

**[DOKUMENTIERT, heute online gelesen]** Die Hersteller-Modelcard beschreibt GLM-4.5-Air als MoE mit 106B Gesamt- und 12B aktiven Parametern sowie Thinking-/Non-Thinking-Modus. Die Anbieter-Dateiansicht führt weiterhin zwei Q4_K_M-Teile mit zusammen rund 73 GB.

**[BELEGT, heute lokal gelesen]** Beide Dateien sind bereits vorhanden; kein erneuter Download erforderlich:

| Datei unter `/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/glm-4.5-air-q4_k_m/` | Bytes | Tensoren |
|---|---:|---:|
| GLM-4.5-Air-Q4_K_M-00001-of-00002.gguf | 50.000.746.752 | 568 |
| GLM-4.5-Air-Q4_K_M-00002-of-00002.gguf | 22.975.001.632 | 235 |
| Summe | **72.975.748.384** | **803** |

Das sind 72,98 GB bzw. rund 67,96 GiB. Beide deklarieren Splitanzahl 2 mit Indizes 0/1 und gemeinsam 803 Tensoren, ohne doppelte Tensornamen. Architektur `glm4moe`, 47 Blöcke einschließlich eines NextN-Predict-Layers, 128 geroutete Experten und 8 ausgewählte Experten je Token.

Revision laut vorhandenem, früher SHA-verifiziertem Downloadnachweis: `b0f8153e9e7cf57cd3b0aad146667abf9de56f0e`. Heute wurden Header und Tensorverzeichnisse erneut gelesen, keine vollständige 73-GB-Prüfsummenberechnung. Pfad-/Größen-/Metadatenprüfung ist von einer erneuten vollständigen Integritätsprüfung zu unterscheiden.

### Konverter und Engine

**[BELEGT]** Aktuelle Binary-Hashes entsprechen den bereits analysierten Binaries:

- Engine: `7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e`.
- pgrn-convert: `af8e47e59d4dcd9eed556da061220af7bd10c3de8137eea2ddd866ab53ad8476`.

Die Engine enthält `glm4moe` und GLM4-MoE-Modell-/Graphsymbole. Das belegt implementierte Architekturpfade, keinen erfolgreichen GLM/PGRN-Betrieb.

**[DOKUMENTIERT / historischer Binary-Beleg]** Der Konverter erlaubt für gestapelte geroutete Experten nur F32, F16, Q4_K, Q5_K und Q6_K. Die gespeicherte Disassembly bestätigt die Bitmaske `0x7003`. Die aktuellen Hashes ordnen diesen Beleg weiterhin den vorhandenen Binaries zu.

| Tensorgruppe, heute erneut inventarisiert | Typen | Ergebnis |
|---|---|---|
| Gate / Up | jeweils 46 × Q4_K | zugelassen |
| Down | 22 × Q8_0 und 24 × Q5_0 | **alle 46 nicht zugelassen** |
| Shared Experts | Q8_0 / Q5_K | resident; nicht mit der gestapelten Expertenprüfung verwechseln |

Die Down-Form `[1408, 4096, 128]` passt nicht zur 256er-Blockbreite der K-Quants: `1408 % 256 = 128`. Der gespeicherte Upstream-Quellbeleg erklärt die Fallbacktypen. Ein Q4_K_M-Dateiname garantiert also keine durchgängigen Q4_K-Expertentensoren.

Der frühere Konverter-Dry-run scheiterte entsprechend bereits an `unsupported expert GGML type 8 in blk.1.ffn_down_exps.weight`. Heute wurde keine Konvertierung und kein weiterer Dry-run gestartet.

**[DOKUMENTIERT / historischer Binary-Beleg]** Der Splitbefund ist genau zu formulieren: Bei bereits gefüllter Teileliste greift ein expliziter Mehrteiler-Guard. Beim Einstieg über eine einzelne Datei ist diese Liste zunächst leer; unabhängig davon erwartet die Engine einen Hash der ersten GGUF-Datei, während der native Split-Konverter alle Teile gemeinsam hasht. Damit ist kein konsistenter offiziell unterstützter Pfad für die vorliegenden Split-Sidecars belegt. Zusammenführen vor der Konvertierung könnte die Identitätsfrage adressieren, beseitigt aber keine inkompatiblen Tensoren.

**Versionsgrenze:** Der letzte lokal belegte Vergleich vom 17.10. nennt v0.3.5 ohne Änderungen an den entscheidenden Konverter-/PGRN-Dateien. GitHub und Raw-GitHub waren über die heutige Webrecherche nicht erreichbar. Deshalb wird v0.3.5 hier nicht als heute verifizierter neuester Release ausgegeben. Ein eventueller neuer Fix bleibt offen; die Unverträglichkeit der vorhandenen, per Hash identischen Binaries ist davon unabhängig.

### Chat-Template, Thinking und Tool-Calling

**[BELEGT]** Das konkrete GLM-Template wurde heute direkt aus dem ersten GGUF extrahiert: `glm-template.jinja`, SHA-256 `15a206ef798293a877c992af1ea4c5aac10dbbda1074ee8acda12f894ca55fb4`. BOS-ID 151331, EOS-ID 151329.

Das Template enthält GLM-Rollenmarker, `enable_thinking`, `/nothink`, einen leeren Thinkblock für deaktiviertes Thinking sowie Tooldefinitionen, `<tool_call>` und `<|observation|>` für Werkzeugergebnisse. Das ist statisch belegte Serialisierung. Der Qwen-Templatezweig darf nicht auf GLM übertragen werden.

**Offen:** Renderkompatibilität mit der gebündelten Jinja-Implementierung, tatsächliche Thinking-Steuerung, Erkennung strukturierter tool_calls, korrekte Argumente, Call-IDs und Fortsetzung nach Toolergebnis. Weder Modellfähigkeiten laut Hersteller noch Tool-Markup im Template beweisen einen vollständigen Werkzeugzyklus in dieser Engine. MCP wird vom Client/Proxy ausgeführt; das Modell spricht nicht selbst MCP. Ein funktionierender MCP-Server ersetzt keinen Tool-Calling-Nachweis.

### RAM und SSD

**[DOKUMENTIERT]** Zielhardware: M4 Pro mit 48 GB Unified Memory. Die Hardware-RAM-Abfrage per sysctl war heute gesperrt. Die 12B aktiven Parameter sind keine Zusage eines entsprechenden Gesamt-RAM-Bedarfs.

**[BELEGT]** Das Volume ist eingehängt und APFS-formatiert. Die IORegistry ordnet `disk6s2` einer extern über USB verbundenen **Samsung PSSD T7**, Solid State, rund 1 TB physischer Kapazität zu. Anschlussgeschwindigkeit und nachhaltige bzw. zufällige Leserate wurden nicht gemessen. Kein Schreibbenchmark wurde ausgeführt.

| Ablage | Freier Platz laut aktuellem `df -k` | Bewertung |
|---|---:|---|
| Interne Datenpartition | rund 1.122 GB / 1.045 GiB | ausreichend für geplante zusätzliche Dateien |
| Extern M4 Speicher | rund 881 GB / 820 GiB | ausreichend, vorhandene GLM-GGUFs sind bereits berücksichtigt |

APFS teilt Speicher dynamisch; diese Werte sind Momentaufnahmen, keine Reservierung.

Aus den heute gelesenen Formen und GGML-Blockgrößen ergibt sich rechnerisch ein Rohpayload von **67.637.346.304 Bytes / 62,99 GiB** für die gestapelten Experten. Dies ist **keine erzeugte oder kompatible PGRN-Datei**: Layout, Verzeichnis, Padding und ein künftig korrigierter Pfad bleiben ungemessen. Eine frühere grobe PGRN-Schätzung wird dadurch nicht als getesteter Speicherbedarf bestätigt.

| Variante, erst nach Kompatibilitätslösung | Technischer Stand | Erwartbare Leistung |
|---|---|---|
| GGUF extern, PGRN intern, Engine/Logs intern | Pfade grundsätzlich frei wählbar; Qwen läuft bereits mit dieser Aufteilung | [HYPOTHESE] günstigere Cold-Expert-Zugriffe über die interne SSD; GLM nicht gemessen |
| GGUF und PGRN extern | vorhandene CLI akzeptiert einen PGRN-Dateipfad; Mount und Identität müssen stabil bleiben; heutiger GLM-Pfad trotzdem blockiert | [HYPOTHESE] USB-Latenz und geteiltes Laufwerk können Cache-Misses verteuern; keine belastbare Tokenrate |

Bei hypothetischem Merge unter Erhalt beider Quellen kämen etwa 73 GB für eine Einzel-GGUF und mindestens die Größenordnung des Expertenpayloads für PGRN hinzu, zusammen etwa 141 GB vor temporärem Overhead. Eine vorsichtige reine Platzplanung könnte 170 GB zusätzlich frei halten. Das ist keine Freigabe und keine garantierte tatsächliche Ausgabegröße. Die genannten freien Plätze reichen dafür derzeit aus.

Für RAM sind residente Gewichte, Expertencache, KV-Cache, Arbeitsbuffer, Metal-Overhead, Betriebssystem und andere Anwendungen gemeinsam zu messen. 12 GiB Cache, 8 GiB Reserve und 8192 Kontext bleiben GLM-Planwerte. Die 48-GB-Eignung und Swapfreiheit lassen sich vor einer funktionierenden Konvertierung und Laufzeitmessung nicht zusichern.

### Bedingter Implementierungs- und Testplan

**Voraussetzung vor Test 1:** Ein konkret identifizierter, belegter Pfad muss sowohl Q5_0/Q8_0-Experten als auch die Quellenidentität/Teilung korrekt unterstützen. Alternative Gewichte sind anhand aller Tensorverzeichnisse zu prüfen, bevor ein großer Download erwogen wird. Ein neues Bundle bzw. ein Merge wären gesonderte Änderungen. Keine solchen Änderungen sind hier erfolgt oder freigegeben.

| Stufe | Durchführung nach späterer Freigabe | Erfolgskriterium / Abbruch |
|---|---|---|
| 1. Konvertierung | Gepinnte kompatible Dateien und Konverter prüfen; erst Metadaten/Dry-run, dann vollständige PGRN-Erzeugung | Alle Experten akzeptiert, Quelle eindeutig gebunden, Ausgabe vollständig/validiert; bei Typ-/Hashfehler stoppen |
| 2. Modellstart | Eigene Engine ausschließlich 127.0.0.1:8083; Labor vorher nur lesen; keine automatischen Entladungen | /health, /v1/models, /props stimmen; tatsächlicher PGRN-Zugriff, RAM-/Swapüberwachung, kontrollierter Stop |
| 3. Einfache Inferenz | Kurze überprüfbare Aufgaben, z.B. 17+25 und „Berlin“ zur Hauptstadt Deutschlands | Richtige Antworten, begrenzte Ausgabe, stop und DONE; kein bloßer HTTP-Erfolg |
| 4. Template / Thinking | GGUF-Template gegen /props und /apply-template prüfen; Thinking bewusst an/aus testen | Nachweis der tatsächlichen Renderzweige; Content/Reasoning und Tokenverbrauch getrennt dokumentiert |
| 5. Tool-Calling | Lokales deterministisches Werkzeug add(a,b), Aufgabe 17+25; Toolcall aufzeichnen, real ausführen, Toolergebnis mit Call-ID zurückgeben | Strukturierter richtiger Aufruf und finale Antwort 42; keine nur behauptete Ausführung; auch Streamingfragmente prüfen |
| 6. MCP / Rollen | Eigener temporärer Client/Proxy mit Kopien der Rollen; ausschließlich Testdateien lesen | Tatsächlich protokollierter MCP-Aufruf, richtiges Ergebnis und Abschluss; keine Bearbeitung bestehender Rollen oder Routerkonfiguration |
| 7. Review-Eval | Bestehende eingefrorene Aufgaben und Rubrik unverändert wiederverwenden | Korrekte und fehlende Befunde, False Positives, saubere Fälle ohne Befund und Abschluss getrennt bewerten |

**Vorläufige Startparameter, keine lauffähige Freigabe:** `--model <kompatible-eindeutige-Quelle> --pgrn <dazu-identische-PGRN> --host 127.0.0.1 --port 8083 --alias glm-air-experiment --jinja --ctx-size 8192 --parallel 1 --pgrn-cache-gb 12 --pgrn-headroom-gb 8 --pgrn-io-threads 1 --pgrn-hot-percent 0 --batch-size 32 --ubatch-size 32 --gpu-layers 99 --no-mmap --no-repack --no-warmup --cache-type-k f16 --cache-type-v f16 --no-context-shift --spec-type none --seed 42`.

Diese Flags stammen aus der vorhandenen Engine-Hilfe bzw. dem bewährten Qwen-Aufbau. Ihre gesamte GLM-Kombination ist unqualifiziert. Für die erste kurze Non-Thinking-Prüfung wären `--reasoning off --reasoning-budget 0` und `chat_template_kwargs.enable_thinking=false` gemeinsam zu testen; für den späteren Review muss Thinking ausdrücklich festgelegt und getrennt verglichen werden. Qwen-MTP wird nicht ungeprüft auf GLM übertragen. Sampling einschließlich top_k/top_p/min_p ist pro Lauf explizit festzuhalten; der heutige Temperaturdiagnosewert 0,6 ist kein belegter GLM-Optimalwert.

Pro Lauf sind Modellrevision/Quantisierung und Hashes, Engine/Build, Template, Kontext, Sampling, Thinking, Cachegröße, Dateipfade, Tokenzahlen, Lade-/Prefill-/Generierungs-/Gesamtzeit, Speicher/Swap, tatsächliche Tools, fachliche Treffer/Fehler sowie Transport- und semantischer Abschluss zu speichern. Vergleichsmodelle, Eingaben, Bewertungsschlüssel und saubere Kontrollfälle bleiben erhalten. Nach jeder Stufe bei Fehlern anhalten; den Review-Eval nicht vorziehen.

## Quellen und Abgrenzung

- Heute erneut gelesen: `preflight.json`, `glm-inventory.json`, `glm-template.jinja`, `glm-template-metadata.json`, `engine-glm-symbols.txt`, vorbereitete Requests und Verifikation.
- Historisch, lokal gelesen: `../ENTSCHEIDUNG_GLM_SLIPSTREAM.md`, `../GLM_KOMPATIBILITAET.md`, `../review_diagnostics_20261018/URSACHENANALYSE.md`, `../logs/glm-decision-source-review.json`, `../logs/glm-compatibility-source-evidence.json`, `../sources.json`.
- [Hersteller-Modelcard GLM-4.5-Air](https://huggingface.co/zai-org/GLM-4.5-Air), heute erreichbar.
- [Unsloth Q4_K_M-Dateien](https://huggingface.co/unsloth/GLM-4.5-Air-GGUF/tree/main/Q4_K_M), heute erreichbar.
- [Konverter v0.3.4](https://github.com/Schero94/slipstream/blob/v0.3.4/engine/tools/pgrn-convert/pgrn-convert.cpp) und [Engine-Patch](https://github.com/Schero94/slipstream/blob/v0.3.4/patches/slipstream-seams.patch): gespeicherte Quellbelege; heutiger Onlineabruf nicht erfolgreich.

Nur neue Diagnoseartefakte in diesem Unterverzeichnis angelegt. Keine Installation, kein Modell-Download, keine Konvertierung, kein Merge, kein Modellstart und keine Veränderung von Gewichten oder SSD. Die abschließende Prüfung bestätigt 139 unveränderte geschützte Dateien einschließlich vorhandener Rollen, Konfiguration und Testartefakte; außerdem unveränderte getrackte Änderungen, Index und HEAD. Auf allen sechs geprüften Labor-/Testports bleiben keine Listener sichtbar. Beleg: `final-validation.json`.
