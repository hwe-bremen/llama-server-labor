# Slipstream v0.3.4 – Qwen3Next-PGRN-Callbackdiagnose

Stand: 18.10.2026. Entscheidung: **INSTRUMENTIERUNG ERFORDERLICH**.

## 1. Zusammenfassung

**Die konkret verletzte Bedingung ist mit den verfügbaren Belegen nicht eindeutig bestimmbar.** Die vorhandene Binary bestätigt exakt den sechsfachen Geometrie-Guard des lokalen v0.3.4-Patches. Die gemeinsame Top-k-Funktion erzeugt eine I32-View mit der angeforderten Top-k-Breite; ein größerer Zeilenabstand ist ausdrücklich zulässig. Weder „View statt zusammenhängender Tensor“ noch „fehlende Compact Slots“ ist damit eine nachgewiesene Ursache.

Der erfolgreiche Vergleichslauf verwendet Qwen3.6-35B-A3B, GGUF-Architektur **qwen35moe**, 256 Experten / 8 aktive. Der fehlgeschlagene Lauf verwendet **qwen3next**, 512 / 10. Beide rufen die gemeinsame Funktion `build_moe_ffn` auf. Der Vergleichslauf benötigt keine aktivierten Compact Slots. Eine grundlegende Architekturinkompatibilität ist nicht belegt; ein konkreter kleiner Fix ebenfalls nicht.

**Laufzeitbeobachtung:** Test A erreicht nach Bereitschaft einen Prefill mit 25 Prompttokens, HTTP 500 und exakt der Geometriefehlermeldung. Das Log protokolliert weder den betroffenen Tensornamen noch `type`, `ne[]`, `nb[]`. Aus „25 Prompttokens“ folgt nicht, dass der fehlschlagende Callback zwingend `ne[1]=25` sieht: physische Ubatch-Zerlegung und letzte Schicht müssen getrennt betrachtet werden.

### Quellen, Identität und Untersuchungsgrenzen

Alle nachstehenden relativen Pfade beziehen sich auf:
`/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/`.

- **P**: `qwen3_coder_next_headercheck/source_evidence/slipstream-seams_v0.3.4.patch`. Zeilenangaben beziehen sich auf die Patchdatei, nicht auf eine rekonstruierte Zieldatei.
- **Q**: `qwen3_coder_next_headercheck/source_evidence/qwen3next_79bba02a6741.cpp`.
- **S**: `qwen3_coder_next_headercheck/source_evidence/stage_v0.3.4.cpp`.
- **L**: `qwen3_coder_next_headercheck/first_inference_runs/20261018T120921572911Z/engine.log`.
- **R**: gleiches Laufverzeichnis, `result.json` und `request_A.json`.
- **B**: `qwen3next_callback_diagnosis/binary_selected_disassembly.txt`.
- **C**: `qwen3next_callback_diagnosis/binary_context_scheduler_disassembly.txt`.
- **V**: `qwen_reference/runs/internal-20261017T161514971893Z/report.json` und `verified-summary.json`.

Der im Auftrag verkürzte Laufpfad wurde anhand der tatsächlich vorhandenen Dateien korrigiert: `first_inference_runs` liegt unter `qwen3_coder_next_headercheck`.

Die sechs Quellenhashes aus dem vorhandenen `source_evidence/manifest.json` wurden erneut geprüft: alle stimmen überein. Der aktuelle Engine-SHA-256 entspricht dem fehlgeschlagenen Lauf:
`7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e`.

`sources.json` dokumentiert den Quellpin `79bba02a6741`, aber für die ausgelieferte Binary Build `10116`, Commit `852e7daa1`. Das ist **kein Nachweis einer konkreten Codeabweichung**, verhindert aber eine ungeprüfte Gleichsetzung von Quellrekonstruktion und Releasebinary. Daher wurden zentrale Funktionen der vorhandenen Binary mit `nm`/`otool` statisch abgeglichen, ohne sie auszuführen.

Die vollständigen gepinnten Dateien `llama-graph.cpp`, `ggml.c`, `ggml-backend.cpp` und `qwen35moe.cpp` liegen im untersuchten Quellenbestand nicht vor; der Patch enthält davon nur Ausschnitte. Ein benachbarter llama.cpp-Checkout steht auf `84d7b2fca11d1be118ce776f6d72a486c4883b74` und enthält den angeforderten Commit nicht. Er wurde nicht als Beleg für den gepinnten Stand verwendet. Ergänzende Abrufe ausschließlich am angeforderten Pin scheiterten an DNS beziehungsweise deaktiviertem Webabruf. Keine Quelldatei wurde dadurch heruntergeladen; Fehlversuche sind unter `qwen3next_callback_diagnosis/source_evidence/manifest.json` dokumentiert. Ein lückenloser Source-Level-Nachweis aller Scheduler-/Backendtransformationen ist deshalb nicht möglich.

## 2. Callbackvertrag

**BESTÄTIGT – Code und Binary:** `llama_context::pgrn_eval`, P:2074–2159; B:98–133, Adressen `0x1003bcf24` bis `0x1003bcfa4`.

| Eigenschaft | Exakter Vertrag |
|---|---|
| Erkennung | Name enthält `ffn_moe_topk-` oder `pgrn_moe_slots-`; danach ausschließlich Dezimalziffern, Schicht muss in uint16 passen |
| Typ | `GGML_TYPE_I32`; Binary vergleicht Typcode `0x1a` |
| `ne[0]` | exakt `model.hparams.n_expert_used`, hier 10 |
| `ne[1]` | strikt positiv; Tokenzeilen |
| `ne[2]`, `ne[3]` | jeweils exakt 1 |
| `nb[0]` | exakt `sizeof(int32_t)` = 4 Bytes |
| nachfolgende Kapazitätsprüfung | `rows * row_ids <= pgrn_ids.size()`, mit Überlaufschutz |
| nachfolgende Zeilenprüfung | `nb[1] >= ne[0] * 4`; Gleichheit ist nicht erforderlich |
| `nb[2]`, `nb[3]` | kein eigenständiger Guard; bei singleton-Achsen nicht für das 2D-Auslesen verwendet |

**Speicherlayout:** contiguous IDs innerhalb jeder Tokenzeile; Padding zwischen Zeilen ist erlaubt. Der Callback fordert weder `ggml_is_contiguous()` noch eine gepackte Gesamtmatrix. Er liest mit `ggml_backend_tensor_get_2d` aus dem Backend, Quellstride `nb[1]`, Zielstride `4 * ne[0]` (P:2114–2122; B:`0x1003bd018`–`0x1003bd03c`). Das ist eine Kopie der IDs in den CPU-Puffer, keine vorherige Tensor-Normalisierung.

**Semantik und Reihenfolge:** Achse 0 bezeichnet die ausgewählten Expertenpositionen pro Token, Achse 1 die Tokenzeilen. Erwartet werden echte Experten-IDs, keine Float-Routerwerte. Der Callback verlangt keine numerische Sortierung der IDs und prüft keine Rangreihenfolge. Das Staging dedupliziert unter Beibehaltung der zuerst gesehenen Reihenfolge und prüft ID-Grenzen (S:58–78). Für die MoE-Berechnung muss die Zuordnung der Auswahlpositionen zu den Routinggewichten erhalten bleiben. Die exakte Tie-Break-Regel der argsort-Kernels ist aus den lokalen Ausschnitten nicht bestimmt und für den Geometrie-Guard irrelevant.

**Übergabe und Zeitpunkt:** `process_ubatch` registriert `pgrn_eval_callback` mit `this` als userdata am Backend-Scheduler (P:2017–2027). Der statische Wrapper leitet `ggml_tensor *tensor` und `bool ask` weiter. Bei `ask=true` wird anhand des Namens oder eines zusätzlichen Nutzer-Callbacks Interesse angemeldet und derselbe Pointer gespeichert. Bei `ask=false` muss der Pointer übereinstimmen; sonst entsteht eine andere Fehlermeldung. Erst anschließend erfolgt der Geometrie-Guard. Der Guard transformiert nichts und liest noch keine IDs.

Der False-Aufruf ist der Auswertungs-/Lesezeitpunkt des Vertrags, an dem Backenddaten verfügbar sein sollen. Dass die Daten des konkret fehlgeschlagenen Tensors vollständig und korrekt materialisiert waren, belegt das Fehlerlog nicht: der Abbruch geschieht vor dem Lesen. Auch das konkrete Synchronisationsverhalten des gepinnten Schedulers konnte ohne dessen vollständige Quelle nicht abschließend rekonstruiert werden.

**Architekturen:** Der Guard selbst unterscheidet keine Modellarchitektur. Nur der über den Namen ausgewählte Compact-Modus ändert den nachgelagerten Pfad: Original-IDs werden in Arenaslots übersetzt und in den Tensor zurückgeschrieben. Der normale Pfad ruft `pgrn_stage` auf (P:2133–2144).

## 3. Qwen3Next-Datenfluss

### Statisch belegte Kette

1. `load_arch_tensors` legt `ffn_gate_inp` mit `[n_embd,n_expert]` an; die Expertenmatrizen besitzen die Expertenachse als dritte Dimension (Q:94–96).
2. Nach Attention und Residualverbindung wird normalisiert und `build_layer_ffn` aufgerufen (Q:147–160). In der letzten Schicht kann vorher `ggml_get_rows` die Ausgabetoken auswählen (Q:142–145).
3. `build_layer_ffn` ruft den gemeinsamen `build_moe_ffn` mit `n_expert`, `n_expert_used`, SILU, Normalisierung der Gewichte und `SOFTMAX` auf; keine vorgegebenen IDs, kein Compact-Argument (Q:538–554). Der Headerpatch setzt `compact_slots=false` als Default (P:2510–2529). Die Binary bestätigt den Aufruf und das Nullsetzen des Compact-Arguments (B:`0x1004ff734`–`0x1004ff778`).
4. Die gemeinsame Binary erzeugt Routerlogits über `build_lora_mm(gate_inp,cur,...)`, benennt `ffn_moe_logits`, ruft den Softmax-Zweig auf und benennt `ffn_moe_probs` (B:`0x1003d64f4`–`0x1003d6648`). Logische Form: `[E,T,1,1]`, für diesen Modellpfad E=512 und T=Anzahl der an dieser Stelle verarbeiteten Tokens. Die genaue Backendmaterialisierung dieser Eingaben ist nicht im Fehlerlog sichtbar.
5. `ggml_argsort_top_k(selection_probs,k)` erzeugt die Auswahl; der gemeinsame Patch benennt dessen Quelle `ffn_moe_argsort` und das Ergebnis `ffn_moe_topk` (P:2406–2411). Die Binary bestätigt dieselbe Kette (B:`0x1003d68cc`–`0x1003d696c`).
6. Die Argsort-Funktion der tatsächlichen Binary erstellt zunächst einen I32-Tensor mit den Dimensionen der Auswahlwahrscheinlichkeiten und anschließend eine View: erste Dimension wird durch k ersetzt, weitere Dimensionen und höhere Strides werden übernommen (B:1706–1778, besonders `0x1005ddec4`–`0x1005ddf50`). Es handelt sich also nicht automatisch um eine kompakte `[k,T]`-Allokation.
7. Der normale Pfad verwendet `selected_experts` auch als `expert_slots`. Die spätere `reshape_3d`-Operation im Patch betrifft die Aktivierungen `cur`, nicht den benannten Top-k-Tensor (P:2415–2426). Compact würde stattdessen `ggml_dup(selected_experts)` als `pgrn_moe_slots` verwenden.
8. Der Scheduler übergibt einen anhand seines Namens erkannten Tensorpointer an den oben beschriebenen Callback. Welcher konkrete Name und welche Geometrie beim fehlgeschlagenen Aufruf vorlagen, bleibt offen.

### Logische Form versus Laufzeitlayout

Für reguläres Routing mit k=10 und einer flachen Tokenachse ist `[10,T,1,1]`, I32, `nb[0]=4` zu erwarten. Bei einer dicht angelegten Argsort-Quelle `[512,T,1,1]` ergibt sich für deren Top-k-View `nb[1]=2048`, nicht 40 Bytes; höhere Strides wären bei diesem Layout `2048*T`. Diese Werte sind eine **bedingte statische Layoutableitung**, keine gemessenen Werte des fehlgeschlagenen Callbacks. Gerade ein Zeilenstride von 2048 wäre zulässig.

Die Binary enthält im Graphkontext-Konstruktor eine bedingte Auswahl der verwendeten Expertenzahl (C:`0x1003d4dc0`–`0x1003d4de0`). Der Fehlerlog zeigt außerdem einen Warmup vor Bereitschaft (L:1240), der Vergleichslauf verwendet `--no-warmup` (V, `command`). Ob Warmupzustand oder Graphwiederverwendung den konkreten fehlerhaften Tensor beeinflusst, ist **OFFEN**. Es wird weder `ne[0]=512` behauptet noch daraus ein bewiesener Warmupfehler abgeleitet.

Die vollständigen Hilfsfunktionen und Schedulertransformationen sind nicht als gepinnte Quellen verfügbar. Deshalb ist eine statische Sollform nicht gleichbedeutend mit dem Nachweis der tatsächlichen Fehlergeometrie.

## 4. Vergleich mit Qwen3.6

Metadatenbeleg: `qwen_reference/metadata/results.json`:14–18; Qwen3Next: L:48–49 und 139–140.

| Eigenschaft | Qwen3.6-35B-A3B | Qwen3-Coder-Next |
|---|---|---|
| GGUF-Architektur | qwen35moe | qwen3next |
| Experten / aktive Experten | 256 / 8 | 512 / 10 |
| Routingfunktion | gemeinsames `build_moe_ffn` | gemeinsames `build_moe_ffn` |
| Auswahloperation | gemeinsamer Argsort-Top-k-Pfad; vollständige Modellspezifika nicht lokal verfügbar | gemeinsamer Argsort-Top-k-Pfad |
| Typ, reguläre Sollform | I32, `[8,T,1,1]` | I32, `[10,T,1,1]` |
| Achsen | Auswahlposition, Token | Auswahlposition, Token |
| reguläre View-Strides, bedingt | `nb[0]=4`, `nb[1]=1024` bei dichter Argsort-Quelle | `nb[0]=4`, `nb[1]=2048` bei dichter Argsort-Quelle |
| Callback | namengebundener Scheduler-Callback | derselbe Mechanismus |
| Compact Slots | Modellpatch vorhanden, nur aktiviert UND T=1 UND ausreichende Arena | keine entsprechende Modellanbindung im vorhandenen Patch |
| Vergleichslauf-Compact | kein `--pgrn-compact-slots`; Default false | ebenfalls kein Compact-Flag; Graphdefault false |
| Warmup | `--no-warmup` | Warmup im Log vorhanden |
| Batch/Ubatch | 32 / 32 | 25 / 25 |
| Speculation | `draft-mtp` angefordert | `none` |
| PGRN | erfolgreiche Ausgabe, Cache-Misses dokumentiert | Geometrie-Guard schlägt fehl |

Compact-Nachweis P:3517–3545; Default P:438 und 3119. V belegt zwei abgeschlossene Anfragen und `verified-summary.json` 64 bzw. 128 Ausgabetokens sowie Cache-Misses. Das ist ein positiver Inferenzbeleg, keine Qualitätsbewertung. Die unterschiedlichen Laufparameter machen den Vergleich nicht zu einem kontrollierten Test nur der Modellarchitektur.

**BESTÄTIGT:** Das Fehlen der Compact-Anbindung ist ein Implementierungsunterschied. **Nicht bestätigt:** dass dieser Unterschied den aktuellen Fehler verursacht. Der gemeinsame normale Stagingpfad ist gerade auch im erfolgreichen Referenzlauf vorgesehen.

## 5. Fehlerursache – jede Bedingung einzeln

Die Einstufung in der letzten Spalte betrifft den konkreten Laufzeitwiderspruch, nicht die Existenz des Guards.

| Guard | Statisch ableitbarer Graphbefund | Bewertung des tatsächlichen Fehlers |
|---|---|---|
| Typ I32 | Argsort-Binary legt I32 an und übernimmt den Typ in die View | **OFFEN**; keine belegte Typverletzung am Callback |
| `ne[0]==10` | Argsort-View verwendet den übergebenen k-Wert; normal wäre 10 | **OFFEN**; tatsächlicher k-Wert/Callbacktensor nicht protokolliert |
| `ne[1]>0` | positive Tokenzahl am Server; nicht identisch mit einem Beleg aller Callbackachsen | **OFFEN**; keine belegte Null-/Negativdimension |
| `ne[2]==1` | bei flacher Routereingabe bleibt diese Achse 1 | **OFFEN**; keine Laufzeitmessung |
| `ne[3]==1` | ebenso | **OFFEN**; keine Laufzeitmessung |
| `nb[0]==4` | I32-View des regulären Argsort-Pfads erwartet 4 | **OFFEN**; kein gemessener Stride |

**BESTÄTIGT:** Mindestens eine der sechs Bedingungen war bei einem erkannten Callbacktensor verletzt; der Pointervergleich davor wurde passiert. Welche Bedingung, welche Schicht und welcher Name betroffen waren, sagt die gemeinsame Fehlermeldung nicht.

**PLAUSIBEL als Untersuchungsrichtung, nicht als nachgewiesene Ursache:** Abweichung zwischen regulärem Graphresultat und tatsächlich erfasstem Scheduler-/View-Tensor oder abweichender Graphzustand. Keine einzelne dieser Möglichkeiten wird bevorzugt, solange die Metadaten fehlen.

**Abgrenzungen:** Ein größerer `nb[1]` löst diesen Guard nicht aus. Die Kapazitätsprüfung und die Prüfung zu kurzer Zeilen folgen danach. `PGR_STAGE_MAX=256` wird nochmals später im Staging geprüft (S:58–78). Bei tatsächlich 25 Zeilen und 10 IDs wären höchstens 250 verschiedene IDs möglich; dies ist eine bedingte Obergrenze, kein gemessener Tensorbefund. Die Gesamtzahl 512 Experten ist nicht dieselbe Größe wie die Zahl der in einem Aufruf gestagten Experten.

## 6. Korrekturoptionen – ausschließlich konzeptionell

| Nach künftiger Messung belegter Befund | Mögliche Korrekturstelle | Voraussetzungen und Risiken |
|---|---|---|
| falscher Callbackknoten oder falsche Namenszuordnung | Graphmarkierung/Schedulerintegration | den tatsächlichen Top-k-Knoten erfassen; Backendreihenfolge und Materialisierung bewahren |
| ausschließlich äquivalente Achsenanordnung | enger Graphadapter vor Callback | `reshape` nur bei passender Speicherordnung; bei Permutation gegebenenfalls `cont`/Kopie notwendig |
| abweichender k-Wert durch Graphzustand | Graphkontext/Wiederverwendung | reguläre Modellauswahl wiederherstellen; nicht einfach die Guardbedingung lockern |
| Layout entspricht View mit zulässigem Zeilenpadding | keine Korrektur nur wegen Padding | bereits unterstützt; zusätzliche Kopie würde die belegte Ursache nicht adressieren |
| Nutzung von Compact Slots erwünscht | architekturabhängige Erweiterung in qwen3next | Expertenmatrizen und Slot-IDs gemeinsam umstellen; kein begründeter Erstfix für diesen Prefillfehler |

Ein bloßes Abschneiden, Umordnen oder Casten von IDs ohne semantischen Nachweis ist ungeeignet. IDs, Auswahlgewichte und Expertenmatrizen müssen deckungsgleich bleiben. Eine allgemeine Änderung an `build_moe_ffn` oder dem Guard beeinflusst potenziell alle PGRN-MoE-Modelle; ein enger Adapter reduziert den Umfang, benötigt aber trotzdem Vergleichstests.

**Nach dem Guard bleibt offen:** erfolgreiche Expertenübertragung, vollständige Ausführung aller Schichten, numerische Korrektheit, Wiederholungs-/Decodepfad und Reviewerqualität. Die vorhandene Konvertierung und Bereitschaft belegen diese Punkte nicht. Weitere Probleme sind möglich, aber durch den aktuellen Abbruch nicht nachgewiesen.

## 7. Minimaler Instrumentierungsplan

**Nur Plan; keine Quelldatei geändert, kein Patch und kein Build erstellt.**

Ort: `src/llama-context.cpp`, `llama_context::pgrn_eval`, im `if (is_pgrn)`-Block nach dem bestehenden Pointer-/Pending-Check und unmittelbar vor dem Geometrie-Guard. Eindeutiger lokaler Anker: P:2100–2104, Binaryadresse `0x1003bcf24`.

Eine einzelne strukturierte Diagnosezeile pro betreffendem False-Callback soll ausschließlich enthalten:

- Tensorname;
- `tensor->type` als numerischer Enumwert;
- `tensor->ne[0..3]` als vier 64-Bit-Werte;
- `tensor->nb[0..3]` als vier `size_t`-Werte;
- `model.hparams.n_expert_used`;
- bereits ermittelte Schicht `layer`;
- Callbackargument `ask`, abgeleitete Flags `is_pgrn`, `compact`.

Formatierung mit passenden portablen Integerformaten (`PRId64`/`%zu` oder vorhandenen Projektformathelfern). Keine Tensorwerte, Routerwahrscheinlichkeiten oder Modelltexte auslesen. Kein `cont`, `cast`, Synchronisationsaufruf oder sonstiger zusätzlicher Eingriff. Der ursprüngliche Guard bleibt unverändert; nach dem Fehler weiterhin abbrechen.

Für genau diese Quellcodeinstrumentierung ist ein **separater Engine-Build** erforderlich. Vorher muss die zur Releasebinary passende vollständige Source-/Buildzuordnung geklärt werden; der bekannte Pin darf nicht stillschweigend als identisch ausgegeben werden. Ein diagnostischer Build bekommt einen separaten Pfad und Hash und ersetzt die vorhandene Binary nicht. Eine spätere Ausführung ist ein neuer Auftrag, nicht Teil dieser Diagnose.

Auswertung: Sechs Prädikate auf den protokollierten Werten prüfen. Beispielsweise würde `ne[0]!=10` zunächst nur die verletzte Breitenbedingung beweisen, nicht deren Entstehung. Danach gezielt die dafür relevante Graph-/Schedulerstelle untersuchen. Diese Minimalmessung unterscheidet die Fehlerklassen, garantiert aber noch keinen vollständigen kausalen Nachweis.

## 8. Aufwand und Risiken

Die Loggingänderung wäre klein (eine Ausgabestelle), der reproduzierbare separate Build ist der wesentliche vorbereitende Aufwand. Eine seriöse Zeitangabe ist ohne passende vollständige Quellen und Buildkonfiguration nicht möglich.

Eine lokale Adapterkorrektur erscheint grundsätzlich denkbar, ist aber erst nach Messung begründbar. Eine Erweiterung der Compact-Anbindung wäre ein größerer, separater Eingriff. Für die Kategorie „grundlegende Architekturinkompatibilität“ fehlen Belege.

Bei späterer Prüfung wären der ursprüngliche Fehlerprompt und ein positiver qwen35moe-Vergleich geeignet, den direkten Eingriff zu bewerten; numerische Parität und Decode bleiben zusätzliche erforderliche Gates vor produktiver Nutzung. In diesem Auftrag wurden keine Tests gestartet.

## 9. Empfehlung und Abschlussentscheidung

**INSTRUMENTIERUNG ERFORDERLICH.**

Nächster möglichst kleiner Schritt: zur vorhandenen Releasebinary passende Buildquellen sichern und ausschließlich die beschriebene Metadatenzeile in einem getrennten Diagnosebuild ergänzen. Erst auf Grundlage des damit erfassten konkreten Widerspruchs eine Korrektur entwerfen. Keine erneute Konvertierung und keine identische Wiederholung mit unveränderter Engine empfohlen.

Der bisherige NO-GO-Befund für den getesteten Inferenzpfad bleibt bestehen. Weder eine sichere kleine Reparatur noch eine grundlegende Unvereinbarkeit ist aus den verfügbaren Belegen ableitbar.

### Ausgeführte Arbeiten

Vorhandene Quellen und ausgewählte Logs gelesen; Quellen- und Binaryhashes geprüft; vorhandene Binary statisch disassembliert; ergänzende gepinnte Sourceabrufe erfolglos versucht. Neu geschrieben wurden ausschließlich dieser Diagnosebericht, zwei Disassembly-Auszüge und das Abrufprotokoll im neuen Diagnoseverzeichnis. Keine bestehenden Quellen, Testartefakte, GGUF/PGRN, Konfigurationen oder Dienste verändert; keine Inferenz, kein Build, kein Patch, kein Modell-Download.
