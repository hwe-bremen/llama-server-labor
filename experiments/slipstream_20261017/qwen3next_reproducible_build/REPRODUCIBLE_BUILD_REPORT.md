# Slipstream v0.3.4 – reproduzierbarer Referenz- und Diagnosebuild

Stand: 18.10.2026. **BUILD BLOCKED**.

## 1. Zusammenfassung

Binary A wurde nicht erstellt. Binary B wurde nicht erstellt. Die Arbeit erreicht Phase A und den Beschaffungsversuch in Phase B. Beide exakt gepinnten Git-Fetches scheitern mit Exit 128: `Could not resolve host: github.com`. Ohne vollständige Quellen einschließlich Gitobjekten und engine-Overlay wurde kein Build begonnen.

Die geänderte Vorgabe ist berücksichtigt: Die ungeklärte Herkunft der ausgelieferten `10116 (852e7daa1)`-Binary ist **kein Abbruchgrund dieses Auftrags**. Der aktuelle Blocker ist die Quellenbeschaffung im eingeschränkten lokalen Ausführungsprozess, nicht die frühere Herkunftsfrage. Einzelne öffentliche Textbelege konnten zuvor über den GitHub-Zugang gelesen werden; sie ersetzen keinen vollständigen, integritätsgeprüften Gitquellbestand. Es wurde keine andere Revision eingesetzt und keine Netzwerk- oder Berechtigungseinstellung verändert.

## 2. Quellenidentität

Verbindliche Sollbasis:

| Bestandteil | Identität |
|---|---|
| Slipstream | `https://github.com/Schero94/slipstream.git` |
| Releasecommit | `0b30cac2a6a40439b74cce6a512f08166f6e3ab3` |
| Release | v0.3.4; zuvor aufgelöstes Tagobjekt `c67119f1773b13cc4f5c80858dd3fa0fe5f9754e` |
| llama.cpp | `https://github.com/ggml-org/llama.cpp.git` |
| Basiscommit | `79bba02a6741de194912d370015866414faa83ad` |
| Seams-SHA-256 | `3f9ce71145da71f62f0f1fcd9b75a72a804ca553fbf57fd63dcb333ed228794d` |
| Overlay | vollständiger `engine/`-Baum des genannten Slipstream-Commits |

Diese Identitäten sind durch den Auftrag und die vorige Quellenprüfung festgelegt. Sie sind noch keine Aussage, dass vollständige Quellen in diesem neuen Verzeichnis vorhanden wären. `manifests/source_manifest.json` trennt die erwarteten Werte vom erreichten Zustand. Die vorherigen Belege liegen unverändert unter `../qwen3next_diagnostic_build/`.

## 3. Rekonstruktion

Vor Beginn wurden freier Speicherplatz (rund 999 GiB) und Git/CMake/Clang/Make geprüft. `apply.sh` wurde vollständig aus dem zuvor gespeicherten, releasegepinnten Beleg gelesen, nicht ausgeführt.

Neu angelegt wurden ausschließlich dieses isolierte Verzeichnis, seine Protokoll-/Manifestunterverzeichnisse und zwei leere Gitrepositories `upstream/` und `slipstream/`. In beiden wurde ein Fetch ausschließlich des festgelegten vollständigen Commits versucht. Die Originalausgaben stehen in `logs/upstream_fetch.json` und `logs/slipstream_fetch.json`. Kein Checkout fand statt, weil kein Fetch erfolgreich war.

Noch ausstehend: Gitobjektprüfung, Commit-/Tagprüfung im beschafften Bestand, Hashprüfung des beschafften Patches, vollständige Inventarisierung und Hashprüfung des engine-Overlays, Aufbau der Referenzquelle, kontrollierte Patchanwendung. Der vorhandene benachbarte llama.cpp-Checkout wurde nicht als Ersatz benutzt.

### Konkrete Fortsetzung der Quellenbeschaffung

Die folgenden Befehle sind für das normale Terminal des Nutzers vorgesehen. Sie laden nur die festgelegten Quellen in die beiden bereits angelegten isolierten Repositories. Sie starten keinen Build, keinen Server und keine Inferenz. Sie ändern keine bestehenden Laborbranches.

```sh
git -C /Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3next_reproducible_build/upstream fetch --depth=1 https://github.com/ggml-org/llama.cpp.git 79bba02a6741de194912d370015866414faa83ad

git -C /Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3next_reproducible_build/slipstream fetch --depth=1 https://github.com/Schero94/slipstream.git 0b30cac2a6a40439b74cce6a512f08166f6e3ab3
```

Erst nach erfolgreicher Beschaffung: jeweiliges `FETCH_HEAD` gegen den erwarteten vollständigen Commit prüfen, Gitobjektintegrität prüfen, detached auschecken, Overlaymanifest erstellen und Patch prüfen. Der Build beginnt anschließend mit der unveränderten Referenzquelle. Solange die Fetches fehlen, sind keine kompilierbaren vollständigen Quellen vorbereitet.

## 4. Referenzbuild

Nicht konfiguriert oder kompiliert; kein Build-Exit-Code und kein Binaryhash. Geplante offizielle Optionen:

```text
CMAKE_BUILD_TYPE=Release
BUILD_SHARED_LIBS=OFF
LLAMA_OPENSSL=OFF
LLAMA_CURL=OFF
GGML_METAL_EMBED_LIBRARY=ON
CMAKE_OSX_ARCHITECTURES=arm64
```

Verfügbare Werkzeuge sind in `logs/toolchain.json` dokumentiert: Apple clang 21.0.0, CMake 4.1.1 und macOS SDK 27.0. Die vollständige Buildtauglichkeit einschließlich tatsächlicher CMake-Defaults ist erst bei vorhandenen Quellen feststellbar. Insbesondere werden Metal, PGRN, Qwen3Next und die Abhängigkeiten noch nicht als geprüft ausgegeben.

Der vorher festgestellte fehlende separate Offline-Metalcompiler ist kein nachgewiesener Blocker des dokumentierten Embedded-Metal-Wegs: Der gepinnte CMake-Code bettet dort Metal-Quelltext ein. Keine Installation oder Paketänderung vorgenommen.

## 5. Diagnoseinstrumentierung

Nicht angewendet, weil die unveränderte Referenz noch nicht gebaut werden konnte. Nach erfolgreichem Referenzbuild ist eine unabhängige Quellkopie zunächst vollständig gegen die Referenzquelle zu vergleichen. Danach darf ausschließlich die eine `[PGRN-DIAG]`-Logausgabe in `llama_context::pgrn_eval` vor dem Geometrie-Guard ergänzt werden.

Erforderliche Felder: Name, Layer, Typ, `ne[0..3]`, `nb[0..3]`, `n_expert_used`, `ask`, `is_pgrn`, `compact`. Keine Tensorinhalte und keine zusätzlichen GGML-, Transfer- oder Synchronisationsoperationen. Der Guard bleibt unverändert.

Es existiert kein Diagnosepatch. Hinzugefügte/geänderte Enginequellzeilen: 0. Eine Prüfung auf rein beobachtende Wirkung ist erst an der späteren tatsächlichen Änderung möglich; diese Eigenschaft wird derzeit nicht als erreicht behauptet.

## 6. Diagnosebuild

Nicht begonnen. Kein Compilerlauf, keine Diagnosebinary, kein SHA-256. Nach erfolgreichem Referenzbuild müssen Compiler und sämtliche relevanten Konfigurationsoptionen identisch verwendet werden. Pfadbedingte Buildunterschiede sind gesondert zu dokumentieren.

## 7. Vergleich

Kein Referenz-/Diagnosevergleich möglich, weil beide Quellen-/Binarypaare noch fehlen. Vorgesehene Nachweise: vollständiger Quellenvergleich vor Instrumentierung, danach ausschließlich die definierte Änderung in `src/llama-context.cpp`, Guardvergleich, CMakeCache-Vergleich sowie statische Prüfung beider Mach-O-Dateien. Keine Gleichheit aus den nur geplanten Optionen ableiten.

## 8. Abweichung zur ausgelieferten Releasebinary

Die vorhandene Releasebinary mit SHA-256 `7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e` bleibt die unveränderte historische Referenz. Künftige A/B-Binaries rekonstruieren ausdrücklich die veröffentlichte Implementierung. Quell- oder Funktionsidentität mit dem ausgelieferten `852e7daa1`-Stand wird nicht behauptet und ist keine Voraussetzung mehr für diesen Buildauftrag.

Die lokale Compiler-Unterversion und das SDK können gegenüber der Paketierungsumgebung abweichen. Das beeinträchtigt mögliche Binäridentität und muss später bei der Interpretation berücksichtigt werden. Es gibt derzeit noch keine neuen Binaries, an denen weitere Unterschiede messbar wären.

## 9. Laborisolation

Releasehash vor/nach identisch mit Vorgabe. Beobachtete Listener auf 8080, 8091, 8092, 8083 und 8787 vor/nach identisch; Belege: `logs/listeners_before.txt`, `logs/listeners_after.txt`, `logs/verification.json`. Dies ist eine Listenerbeobachtung, keine vollständige Prüfung interner Dienstzustände.

Keine Dienste gestoppt oder gestartet; keine Ports belegt; keine HTTP-/Inferenzanfragen. Keine Modelle, PGRN, bestehenden Quellen oder Buildverzeichnisse verändert. Keine globalen Umgebungsvariablen gesetzt, keine Systempakete installiert, keine Homebrew-Aktion. Keine schreibbaren Symlinks auf bestehende Laborbestände angelegt.

## 10. Vorbereitung der Laufzeittests

Nur Testplan, keine Ausführung und kein ausführbarer Launcher:

1. Voraussetzung: Beide Binaries erfolgreich bauen und statisch prüfen; neuer gesonderter Auftrag für Laufzeittests.
2. Modell- und PGRN-Pfade aus `../qwen3_coder_next_headercheck/download_conversion_runs/20261018T091238425764Z/result.json` übernehmen. Vor dem Test Verfügbarkeit/Identität prüfen, nichts neu konvertieren.
3. Geerbte `LLAMA_ARG_*` ausschließlich aus der Umgebung des jeweiligen Kindprozesses entfernen. Die globale Umgebung bleibt unverändert.
4. Nur einen eigenen Testprozess gleichzeitig; Port 8083 muss frei sein. Keine bestehenden Dienste stoppen.
5. Lauf A mit `reference/bin/llama-server-reference`: Host 127.0.0.1, Port 8083, Kontext 4096, Batch/Ubatch 25, parallel 1, PGRN-Cache 12 GiB, Headroom 8 GiB, Temperatur 0, Seed 42. Sonstige Optionen wie ursprünglicher Lauf (`spec-type none`, `reasoning off`, `gpu-layers 99`, Jinja); keine unbegründete Warmupänderung.
6. Genau der ursprüngliche Request: „Antworte ausschließlich mit der Zahl: 17 + 25“, `max_tokens=32`, `stream=false`, Temperatur 0, Seed 42.
7. Nur falls A denselben PGRN-Geometriefehler reproduziert, eigener Lauf B mit `diagnostic/bin/llama-server-pgrn-diagnostic` und identischen Parametern. A vorher kontrolliert als eigenen Testprozess beenden.
8. Bei anderem Verhalten von A anhalten und Abweichung dokumentieren; B nicht als Erklärung des historischen Releasefehlers interpretieren.
9. Bei B tatsächliche Logwerte des fehlschlagenden Tensors erfassen und jedes Guardprädikat einzeln auswerten. Keine Formatbeispielzahlen als Messwerte verwenden.

Die aus dem vorhandenen erfolgreichen Konvertierungsprotokoll bekannten Pfade:

- GGUF: `/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf`
- PGRN: `/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/pgrn/qwen3-coder-next/Qwen3-Coder-Next-Q4_K_M.pgrn`

## 11. Offene Risiken und Abschluss

**BUILD BLOCKED** wegen fehlgeschlagener Beschaffung der vollständigen festgelegten Quellen. Kein Kompilierversuch wurde unternommen; deshalb nicht „BUILD FAILED“.

Nächster konkreter Schritt: die beiden oben dokumentierten Fetch-Befehle im normalen Terminal ausführen oder einen funktionsfähigen genehmigten Git-Netzwerkzugang für diesen Ausführungsprozess bereitstellen. Danach kann die Rekonstruktion mit Objekt-/Quellenprüfung und Referenzbuild fortgesetzt werden. Die frühere Herkunftsfrage wird dabei nicht erneut als Stopkriterium verwendet.

Die Voraussetzungen für kontrollierte Laufzeittests sind noch nicht erfüllt.
