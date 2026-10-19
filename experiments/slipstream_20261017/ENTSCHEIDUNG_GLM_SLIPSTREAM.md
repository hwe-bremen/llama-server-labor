# Entscheidungsvorlage: GLM-4.5-Air mit Slipstream

Stand: 17.10.2026. Zielsystem: MacBook Pro M4 Pro, 48 GB Unified Memory.

**Entscheidung C: Kein durchgängig offiziell unterstützter, öffentlich
reproduzierbarer Weg konnte belegt werden. Das GLM-/PGRN-Experiment wird
vorerst als technisch blockiert abgeschlossen.**

Das ist keine Behauptung theoretischer Unmöglichkeit. Es fehlt die belegte Kette
aus konkreter veröffentlichter Datei, passendem Konverter, passender Engine und
erfolgreichem PGRN-Modellbetrieb. Eine konkrete angekündigte Korrektur wurde
ebenfalls nicht gefunden; Entscheidung B wäre daher nicht belegt.

## Was das Projekt selbst für GLM nennt und tatsächlich dokumentiert

| Beleg | Inhalt | Aussagekraft |
|---|---|---|
| Offizielle README, Compatible models | GLM-4.5-Air, 106B/12B; zugleich Einschränkung auf geeignete Expertentypen | Kompatibilitätsbehauptung mit Voraussetzungen, kein GLM-E2E-Test |
| App-Katalog v0.3.4, `app/dist/app.js`, Zeilen 205–209 | Repo `unsloth/GLM-4.5-Air-GGUF`, Datei `GLM-4.5-Air-UD-Q4_K_XL.gguf`, `gb:63`, kein Draft/MTP | Konkreter Katalogeintrag; keine gepinnte Modellrevision, Prüfsumme oder GLM-spezifische Engine-Zuordnung |
| URL-Erzeugung desselben Codes, Zeilen 1065–1068 | `/resolve/main/${m.file}` | Erwartet die genannte Einzeldatei im Repository-Stamm; keine automatische Übersetzung dieses GLM-Eintrags in einen anderen Unterordner/Shardnamen |
| Modellanbieter, gepinnte Revision `b0f8153e9e7cf57cd3b0aad146667abf9de56f0e` | Tatsächlich Ordner `UD-Q4_K_XL/` mit `GLM-4.5-Air-UD-Q4_K_XL-00001-of-00002.gguf` und `…00002-of-00002.gguf`, zusammen laut Dateiansicht rund 67,7 GB | Der geprüfte Anbieterstand entspricht nicht dem Einzeldateipfad im App-Katalog; keine Gewichte abgerufen und keine Expertentypen dieser Ausgabe neu geprüft |
| Projektprotokoll `bench/RESULTS.md`, GLM-Eintrag vom 21.07.2026 | Q4_K_M, exakt 72.975.748.384 Bytes, auf M3 Pro/36 GB mit `--cpu-moe --gpu-layers 99` versucht; Kernel Panic dokumentiert | Ausdrücklich fehlgeschlagener Versuch mit gewöhnlichem mmap/CPU-MoE, kein erfolgreicher PGRN-Lauf; Bytezahl entspricht unserer Ausgabe, vollständige Artefaktidentität dadurch allein nicht bewiesen |

Damit ist die präzise Antwort auf „Was verwendet das Projekt?“ zweigeteilt:
Der **Katalog empfiehlt UD-Q4_K_XL als Einzeldatei**; der **auffindbare konkrete
GLM-Versuch betrifft Q4_K_M und ist fehlgeschlagen**. Eine erfolgreich verwendete,
reproduzierbar identifizierte GLM-PGRN-Dateikombination wurde nicht gefunden.
GLM ist bereits als kompatibel gelistet, nicht ausdrücklich nur als zukünftiges
Modell angekündigt. Der erfolgreiche Betrieb ist dadurch trotzdem nicht belegt.

Installiert ist das offizielle Bundle v0.3.4 mit Engine Build 10116,
Commit-Anzeige `852e7daa1`. Für den Konverter ist keine eigene Build-Version
dokumentiert; sein SHA-256 steht im Kompatibilitätsbericht. Der öffentliche
Rekonstruktions-Pin `79bba02a6741` ist nicht der angezeigte Binary-Commit.
Deshalb werden Sourceanalyse und Binarybelege getrennt ausgewiesen.

## Codebefunde: Typgrenze und genaue Reichweite des Split-Problems

Der Konverter erlaubt für gestapelte geroutete Experten ausschließlich F32 (0),
F16 (1), Q4_K (12), Q5_K (13), Q6_K (14). Die Bedingung steht in
`engine/tools/pgrn-convert/pgrn-convert.cpp`, Zeilen 588–594, und ist im tatsächlich
installierten Konverter als Bitmaske `0x7003` belegt. Residente Shared Experts,
Attention und andere Gewichte sind nicht mit dieser Experten-Allowlist
gleichzusetzen. Alle drei bisher vollständig inventarisierten Ausgaben scheitern
an ihren Down-Expertentypen; ein Zusammenführen ändert diese Typen nicht.

**Korrektur der früheren pauschalen Split-Aussage:** Der ausdrückliche
`splits.size() > 1`-Guard sitzt im gemeinsamen `llama_model_load`, vor dem
Konstruktor des GGUF-Loaders, und wird bei gesetztem `params.pgrn_path` aktiv.
Er ist somit weder UI- noch Router-spezifisch. Seine unmittelbare Wirkung hängt
aber vom Einstieg ab:

- `llama_model_load_from_splits`: Die Teileliste ist schon gefüllt. Mehrere Teile
  werden durch den expliziten Guard abgewiesen.
- `llama_model_load_from_file`: Der veröffentlichte Basiscode übergibt zunächst
  eine leere Liste. Weitere Teile werden erst im nachfolgenden
  `llama_model_loader` erkannt. Der frühe Guard allein beweist für diesen Einstieg
  also kein ausnahmsloses Split-Verbot.
- Unabhängig davon prüft derselbe PGRN-Einstieg vorher
  `pgr_sha256_file(fname)` gegen `pgrn_model_sha256`. Der native Konverter bildet
  für Split-Quellen dagegen einen SHA-256-Strom über **alle Teile in Reihenfolge**
  (Zeilen 683–708). Ein regulär so erzeugtes Split-Sidecar hat deshalb nicht die
  erwartete Identität der ersten Datei. Der Einzeldatei-Einstieg liefert keinen
  konsistent unterstützten Ausweg.

Der installierte Server bestätigt zusätzlich zum Split-Fehlerzweig den
Datei-Hash-Aufruf, den PGRN-Hash-Abruf und `strcmp` **vor** dem Loader-Aufruf
(Disassembly-Adressen 0x1003a06b8–0x1003a0730). Die Zuordnung der Eintrittslisten
stammt aus dem veröffentlichten Basiscode plus Patch; kein Modellstart wurde
ausgeführt, um einen konkreten Fehler über diesen Einstieg auszulösen.

Die README-Angabe, dass Mehrteiler in einem Durchlauf konvertiert werden,
ist damit kein Nachweis eines durchgängigen Split-PGRN-Inferenzbetriebs.
Diese Aussage betrifft den GGUF/llama.cpp-PGRN-Pfad. Ein allgemeines Verbot
aller PGRN-Implementierungen, insbesondere des separaten MLX-Pfads, folgt daraus
nicht. Auch für MLX wurde aber kein vollständiges offizielles GLM-Rezept mit
Dateien, Versionen und Erfolgsbeleg gefunden; der GLM-Katalogeintrag besitzt
anders als der Qwen-Eintrag keinen MLX-Twin.

## Ist Zusammenführen offiziell vorgesehen?

**Im Upstream llama.cpp: ja.** Das dokumentierte Werkzeug `llama-gguf-split`
unterstützt `--merge` mit erster Teildatei und neuer Zieldatei. Sein Code übernimmt
Tensor-Metadaten und kopiert Tensorbytes; er requantisiert nicht.

**Als vollständige Slipstream-GLM-Anleitung: nicht belegt.** Weder das geprüfte
Bundle-Ressourcenverzeichnis noch dessen Runtime-Manifest enthält dieses Werkzeug
als ausgelieferte Komponente. Der geprüfte Slipstream-App-Pfad konvertiert direkt
und startet direkt mit `--model`/`--pgrn`; kein GLM-Merge-Schritt ist erkennbar.

Eine gültige Einzeldatei würde das Split-/Identitätsproblem grundsätzlich
adressieren, sofern das PGRN anschließend aus genau dieser Einzeldatei neu erzeugt
wird. Die inkompatiblen Q5_0/Q8_0-Expertentypen unserer Dateien blieben erhalten.
Deshalb ist Merge hier keine Lösung und wird nicht ausgeführt. Bei Erhalt der
Quellen würde allein die neue GGUF nochmals ungefähr 72,98 GB Speicher benötigen
(Schätzung nahe der Summe, Metadaten werden neu geschrieben), zusätzlich zu einer
weiterhin nicht erzeugten PGRN. Für diesen blockierten Weg gibt es keinen
belastbaren vollständigen Speicherplan und keine gemessene PGRN-Größe.

## Releases, angekündigte Korrekturen und tatsächliche Tests

Neuester geprüfter Release ist v0.3.5 vom 17.08.2026; Main-Commit
`1518931afd732622d338c22793f946b860a381fd`. Der Release erweitert den Dense-Metal-
Pfad für Dolphin3. Der Versionsvergleich ändert weder Konverter noch PGRN-
Engine-Patch oder PGRN-Leser. Er behebt die GLM-Hindernisse nicht.
Die öffentlich abgefragten Issues und Pull Requests (`state=all`, jeweils
`per_page=100`) waren leer. In diesen Quellen und den geprüften Release-Hinweisen
steht keine konkrete GLM-Korrektur in Arbeit. Das ist der Befund dieser öffentlichen
Quellen, keine Aussage über unveröffentlichte Entwicklerpläne.

| Evidenzklasse | Belastbarer Stand |
|---|---|
| Projektangaben | GLM wird als kompatibel katalogisiert; Mehrteiler-Konvertierung wird beschrieben; GLM-PGRN-E2E-Nachweis nicht gefunden |
| Code/Binary | Experten-Allowlist; früher Split-Guard; inkonsistente Quellenidentität für native Split-Sidecars; v0.3.5 ohne relevanten Fix |
| Ausgeführte Tests auf diesem Mac | Modellloser Engine-/Proxy-/HTTP-Test bestanden; SHA-geprüfter Download; Konverter-Dry-run mit Typfehler; vollständige lokale und begrenzte Remote-Tensorinventare |
| Nicht ausgeführt | GLM-Inferenz, vollständige Konvertierung, PGRN-Messung, Merge, Speicher-/Leistungsqualifikation |

## Wo die ursprüngliche Empfehlung falsch oder unvollständig war

1. Die allgemeine Modellliste und Unterstützung der Architektur `glm4moe` wurden
   zu stark als Freigabe der konkreten Q4_K_M-Dateien interpretiert. Deren
   Expertentypen hätten **vor dem 72,98-GB-Download** geprüft werden müssen.
2. Die empfohlene Q4_K_M-Ausgabe entsprach nicht einmal dem konkreten
   UD-Q4_K_XL-Eintrag des Projekts. Auch dieser Eintrag besitzt keinen belegten
   durchgängigen Erfolgsnachweis und passt nicht zur geprüften Dateiaufteilung.
3. Fähigkeit zur Split-Konvertierung wurde unzureichend von Split-Inferenz
   getrennt. Die spätere Behauptung eines universellen frühen Split-Guards war
   ebenfalls zu grob; entscheidend sind Eintrittsliste **und** Quellenidentität.
4. Mehr RAM, aktive Parameter und die sinnvolle Aufteilung GGUF extern/PGRN
   intern beantworten keine Formatkompatibilität. 48 GB machen den Weg weder
   automatisch möglich noch verursachen sie den beobachteten Typfehler.
5. Die Werte 12 GiB Expertencache, 8 GiB Reserve und 8192 Kontext in der alten
   Konfiguration sind ungeprüfte Planwerte. 60–70 GB PGRN waren eine Schätzung.
   Sie sind keine Empfehlung für einen qualifizierten GLM-Betrieb. Der erfolgreiche
   modelllose API-Test liefert dafür ebenfalls keinen Nachweis.

Die ursprüngliche positive Machbarkeitsempfehlung wird daher ausdrücklich
zurückgenommen. Weitere zufällige Quantisierungen werden nicht gesucht.
Alle vorhandenen Gewichte bleiben erhalten. Wiederaufnahme erst bei einem
konkreten offiziellen, reproduzierbaren GLM-PGRN-Rezept oder einem nachweisbaren
Fix für Konverter **und** Inferenzpfad; anschließend wäre dessen Ausführung
gesondert freizugeben. Jetzt ist keine weitere Aktion erforderlich.

## Quellen und lokale Belege

- [Slipstream README](https://github.com/Schero94/slipstream), Compatible models / Converting a model by hand.
- [App-Katalog v0.3.4](https://github.com/Schero94/slipstream/blob/v0.3.4/app/dist/app.js), Zeilen 205–209 und 1065–1068.
- [Projekt-Messprotokoll](https://github.com/Schero94/slipstream/blob/v0.3.4/bench/RESULTS.md), GLM-Fehlschlag vom 21.07.2026, Zeilen 2285–2304.
- [Vom Projekt benannte Ausgabe beim Anbieter](https://huggingface.co/unsloth/GLM-4.5-Air-GGUF/tree/b0f8153e9e7cf57cd3b0aad146667abf9de56f0e/UD-Q4_K_XL).
- [Konverter](https://github.com/Schero94/slipstream/blob/v0.3.4/engine/tools/pgrn-convert/pgrn-convert.cpp), Typen/Quellenhash.
- [Engine-Patch](https://github.com/Schero94/slipstream/blob/v0.3.4/patches/slipstream-seams.patch), `src/llama.cpp`, Hunk bei Basiszeile 279.
- [Basis: Lade-Einstiege](https://github.com/ggml-org/llama.cpp/blob/79bba02a6741/src/llama.cpp), Zeilen 426–449; [Split-Erkennung](https://github.com/ggml-org/llama.cpp/blob/79bba02a6741/src/llama-model-loader.cpp), Zeilen 592–614.
- [Upstream Merge-Dokumentation](https://github.com/ggml-org/llama.cpp/blob/79bba02a6741/tools/gguf-split/README.md) und [Merge-Code](https://github.com/ggml-org/llama.cpp/blob/79bba02a6741/tools/gguf-split/gguf-split.cpp), Zeilen 485–555.
- [Release v0.3.5](https://github.com/Schero94/slipstream/releases/tag/v0.3.5), [Versionsvergleich](https://github.com/Schero94/slipstream/compare/v0.3.4...v0.3.5), [Issues](https://github.com/Schero94/slipstream/issues), [PRs](https://github.com/Schero94/slipstream/pulls).
- Lokal: `GLM_KOMPATIBILITAET.md`, `TESTPROTOKOLL.txt`, `logs/glm-decision-source-review.json`, `logs/glm-complete-tensor-inventory.json`, `logs/remote-metadata/results.json`, `logs/engine-split-guard-disassembly.txt`, `logs/converter-actual-disassembly.txt`.

Nur Dokumentation und Quellenbelege im Experimentverzeichnis aktualisiert.
Keine Änderungen an Code oder Konfiguration; keine Gewichte abgerufen oder
verändert; keine Installation, Konvertierung oder Modellstarts.
