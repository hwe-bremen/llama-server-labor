# Qwen3Next – isolierter Diagnosebuild: Prüfbericht

Stand: 18.10.2026. **BUILD BLOCKED**.

## 1. Ergebnis

**Es liegt keine Diagnosebinary vor.** Phase A hat die veröffentlichte Rekonstruktionsanleitung eindeutig identifiziert, aber deren Quellidentität mit der tatsächlich ausgelieferten Releaseengine nicht ausreichend geklärt. Gemäß Auftrag wurde vor Instrumentierung, CMake-Konfiguration und Build angehalten. Das ist kein fehlgeschlagener Kompilierversuch.

Der Unterschied zwischen dem offiziellen Quellpin und der Buildkennung ist jetzt enger eingegrenzt: Der vorgesehene Basispin ist vollständig aufgelöst, der vorhandene Patch stimmt mit dem Release überein, und die Generierung der Versionskennung ist aus dem gepinnten Buildcode bekannt. Eine überprüfbare Zuordnung des ausgelieferten `852e7daa1`-Standes zur Rekonstruktion fehlt weiterhin.

| Phase | Status |
|---|---|
| A – Herkunft und Buildgrundlage | untersucht; Freigabekriterium Quellidentität nicht erfüllt |
| B – isoliertes Verzeichnis | nur Bericht, Quellenbelege und Prüfprotokolle angelegt; kein Enginecheckout |
| C – Instrumentierung | nicht angewendet |
| D – Diagnosepatch | nicht erstellt; ohne bestätigte Buildquelle wäre er kein geprüfter Buildpatch |
| E – Build | nicht begonnen |
| F – späterer Test | Befehl und Request unten dokumentiert, nicht ausgeführt |

## 2. Quellenidentität

### Bestätigte Veröffentlichung

| Bestandteil | Identität |
|---|---|
| Slipstream-Tag | `v0.3.4` |
| Annotiertes Tagobjekt | `c67119f1773b13cc4f5c80858dd3fa0fe5f9754e` |
| Zielcommit des Tags | `0b30cac2a6a40439b74cce6a512f08166f6e3ab3` |
| `apply.sh`-Basispin | `79bba02a6741` |
| Aufgelöster llama.cpp-Commit | `79bba02a6741de194912d370015866414faa83ad` |
| Seams-Patch Git-Blob | `dd9cb1adec7b06907bfd99fd749d57b58800f02d` |
| Seams-Patch SHA-256 | `3f9ce71145da71f62f0f1fcd9b75a72a804ca553fbf57fd63dcb333ed228794d` |

Die Tagauflösung und der vollständige öffentliche Releasebaum sind in `logs/provenance_api.json` gespeichert. `source_manifest.json` enthält die Hashes der gespeicherten Textbelege. Der Git-Blob des bereits vorhandenen lokalen Patches wurde aus seinen Bytes neu berechnet und stimmt exakt mit dem Blob des Releasebaums überein.

`source/apply.sh`:4–10 beschreibt: llama.cpp klonen, auf den Pin auschecken, `engine/*` pfadtreu darüberkopieren, `patches/slipstream-seams.patch` anwenden. Der gesamte `engine/`-Overlay gehört damit zur Buildquelle; der Patch allein reicht nicht. Das Skript wurde nur gelesen, nicht ausgeführt. Es gibt im untersuchten Releasebaum keinen vollständigen vendorten llama.cpp-Checkout und keine CI-Buildprovenienz, die den ausgelieferten Enginehash einem vollständigen Buildbaum zuordnet.

### Tatsächliche Releasebinary

Pfad relativ zum Experiment: `runtime/Slipstream.app/Contents/Resources/resources/llama-server`.

- SHA-256: `7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e`.
- Gespeicherte native Versionsausgabe: `10116 (852e7daa1)`.
- Compilerkennung der Releasebinary: `AppleClang 21.0.0.21000101`, Ziel `Darwin arm64`.
- Statische Mach-O-Prüfung: arm64, Mindest-macOS 26.0, SDK 26.5.

Die Versionsausgabe stammt aus `../logs/engine-version.txt`; sie wurde nicht durch einen neuen Serveraufruf erzeugt. Hash, Architektur und Mach-O-Angaben wurden in diesem Auftrag lesend überprüft.

### Was bedeuten 10116 und 852e7daa1?

`source/upstream-build-info.cmake`:18–40 ermittelt `BUILD_COMMIT` mit `git rev-parse --short HEAD` und `BUILD_NUMBER` mit `git rev-list --count HEAD`. Die Nummer ist damit im veröffentlichten Mechanismus ein Git-Historienzähler, keine Slipstream-Releaseversion. Der Hash bezeichnet im normalen Mechanismus den Buildcheckout-HEAD. Uncommittete Änderungen werden durch diese Kennung nicht vollständig beschrieben.

**Nicht nachgewiesen:** dass genau dieser Mechanismus bei der ausgelieferten Binary ohne Überschreibung oder veraltete generierte Buildinformationen verwendet wurde. Ein privater Forkcommit, lokale Zusatzcommits oder alte Buildmetadaten sind mögliche Erklärungen, keine belegten Tatsachen.

Die GitHub-Abfragen für `852e7daa1` liefern sowohl unter `ggml-org/llama.cpp` als auch unter `Schero94/slipstream` HTTP 422 mit „No commit found“. Auch im vorhandenen benachbarten llama.cpp-Checkout ist das Objekt nicht vorhanden. Das beweist nicht, dass der Commit nirgendwo existiert; es bedeutet, dass seine Quellen in diesen geprüften Beständen nicht auflösbar sind.

`source/RELEASE_0.3.1.md` nennt für einen früheren qualifizierten Enginebuild zusätzlich `0c716f30be270d1fb1077a1a0795684e6faeecf8`. `source/RELEASE_0.3.4.md` erklärt die neue Version als Änderung der Bedienoberfläche ohne Engine-Verhaltensänderung. Diese Aussagen liefern keine belastbare Brücke zu `852e7daa1`. Der ältere Releaseplan dokumentiert einen LLM-BOOM-Mirror als Entwicklungsquelle, aber ebenfalls keine solche Zuordnung. Dieser Mirror wurde nicht als verifizierte oder verfügbare Buildquelle vorausgesetzt.

### Tatsächlich verwendete Quellen

Nur Textbelege aus dem exakten Slipstream-Releasecommit und dem exakten llama.cpp-Pin sowie vorhandene lokale Logs, Quellenabbilder und Binaryanalysen. Kein aktueller Default-Branch, kein Update, kein Wechsel eines vorhandenen Checkouts. Die acht neu gespeicherten Quelldokumente sind Belegdateien, kein vollständiger Enginequellbaum.

## 3. Build-Reproduzierbarkeit

| Ebene | Befund |
|---|---|
| Veröffentlichte Rekonstruktion | eindeutig definiert: Pin + vollständiges engine-Overlay + Seams-Patch |
| Quellidentität mit Releasebinary | unzureichend geklärt; maßgeblicher Blocker |
| Buildäquivalenz | dokumentierte Optionen bekannt; tatsächlicher Release-CMakeCache und vollständige Buildprovenienz fehlen |
| Binäridentität | kein neuer Build, deshalb nicht geprüft; identischer Hash wäre auch nicht zwingend erforderlich |

Die offizielle Anleitung in `source/Slipstream-README.md`, Abschnitt „Building from source“, sowie `source/apply.sh`:12–17 nennen:

```text
CMAKE_BUILD_TYPE=Release
BUILD_SHARED_LIBS=OFF
LLAMA_OPENSSL=OFF
LLAMA_CURL=OFF
GGML_METAL_EMBED_LIBRARY=ON
CMAKE_OSX_ARCHITECTURES=arm64
```

Das sind belegte veröffentlichte Optionen, kein aus der Binary rekonstruierter vollständiger CMakeCache. Ein künftiger isolierter Build müsste Metal-Aktivierung und die übrigen tatsächlich wirksamen Defaults im Cache kontrollieren. Vorliegende Mach-O-Abhängigkeiten sind ausschließlich Systembibliotheken/Frameworks, darunter Metal, MetalKit, Accelerate und CoreML; keine Homebrew- oder `@rpath`-Abhängigkeit wurde angezeigt. Dies unterstützt die statische Paketierung, beweist aber nicht jede Compileroption.

Der bereits vorliegende Callback-/Argsort-Binaryabgleich bestätigt wichtige Teilfunktionen. Er ersetzt keinen Nachweis der gesamten Graph-, Scheduler- und Backendquellen. Gerade dort könnte die noch unbekannte Fehlerursache liegen.

## 4. Instrumentierung

**Nicht implementiert.** Die geplante Stelle bleibt `src/llama-context.cpp`, `llama_context::pgrn_eval`, nach dem Pointer-/Pending-Check im `if (is_pgrn)`-Block, unmittelbar vor dem sechsfachen Geometrie-Guard. Lokaler Quellenanker: `../qwen3_coder_next_headercheck/source_evidence/slipstream-seams_v0.3.4.patch`:2100–2104.

Geplant ist genau eine Logzeile mit `[PGRN-DIAG]`, Tensorname, Layer, numerischem Typ, vier `ne`-Werten, vier `nb`-Werten, `n_expert_used`, `ask`, `is_pgrn` und `compact`. Formatierung: geeignete 64-Bit-Makros für `ne`, `%zu` für `nb`, korrekt gecastete skalare Felder. Keine Tensorinhalte, keine Synchronisation oder Tensoroperationen. Ein formatstabiles Escaping des Namens muss bei der Implementierung berücksichtigt werden.

Es gibt daher noch keinen Nachweis einer tatsächlich implementierten rein beobachtenden Instrumentierung. Dieser Nachweis gehört zur späteren Patchprüfung.

## 5. Patchprüfung

Kein Diagnosepatch erzeugt oder angewendet. Keine ursprüngliche Quellzeile verändert oder entfernt. Kein Guard abgeschwächt. Der vorhandene offizielle Seams-Patch wurde lediglich gegen seinen veröffentlichten Blob geprüft. Eine Patchdatei mit dem angeforderten Diagnosenamen wird erst auf der ausreichend geklärten isolierten Enginequelle erstellt.

## 6. Build

Kein CMake-Konfigurationslauf, keine Kompilation, kein Linkschritt; folglich kein Build-Exit-Code und keine Buildartefakte.

Lokale Vorprüfung (`logs/preflight.json`):

- Apple clang 21.0.0, Buildkennung `clang-2100.3.34.2`, Ziel arm64-apple-darwin27.0.0.
- CMake 4.1.1.
- Aktives macOS SDK 27.0 aus CommandLineTools.
- Rund 999 GiB verfügbar, geprüft vor Quellenablage; kein großes Repository kopiert.
- `xcrun --find metal` findet keinen Offline-Metalcompiler.

**Der fehlende Offline-Metalcompiler ist hier kein bestätigter Buildblocker.** Der gepinnte `source/upstream-metal-CMakeLists.txt` bettet mit `GGML_METAL_EMBED_LIBRARY=ON` den Metal-Quelltext über Assembly ein; nur der alternative Zweig ruft `xcrun metal`/`metallib` auf. Für den dokumentierten Weg werden die Frameworks sowie C/C++/ObjC/ASM-Werkzeuge benötigt. Ohne Konfiguration wurde deren vollständige Einsatzfähigkeit nicht geprüft. Rust/Tauri wäre für den App-Build relevant, nicht für das hier angestrebte einzelne Serverziel.

Compiler-Unterversion und SDK weichen von der Releaseumgebung ab. Das wäre zu dokumentieren, ist aber allein kein Beweis fehlender funktionaler Äquivalenz. Es wurde keine Installation oder Aktualisierung zur Angleichung vorgenommen.

## 7. Binaryprüfung

| Prüfung | Referenz | Diagnosebinary |
|---|---|---|
| Architektur | Mach-O arm64 bestätigt | nicht vorhanden |
| SHA-256 | vor/nach identisch mit Vorgabe | nicht vorhanden |
| PGRN/Qwen3Next | durch vorhandene statische Analyse belegt | nicht prüfbar |
| Metal | Frameworkabhängigkeiten bestätigt | nicht prüfbar |
| `[PGRN-DIAG]` | keine Änderung vorgenommen | nicht vorhanden |
| Funktionsvergleich | vorhandene Teilanalysen gelesen | mangels Build nicht möglich |

Die Abweichungen eines zukünftigen Builds können erst nach seiner Erstellung bewertet werden. Die derzeit bekannte Diskrepanz betrifft Buildmetadaten und fehlende Quellzuordnung, nicht einen bereits nachgewiesenen funktionalen Unterschied.

## 8. Laborisolation

Alle neuen Dateien dieses Auftrags liegen ausschließlich unter `qwen3next_diagnostic_build/`: Bericht, Quellenmanifest, Textbelege und Prüfprotokolle. Kein ausführbarer Startlauncher, kein neuer Enginequellbaum und keine neue Engineinstallation wurden angelegt.

Die Releasebinary wurde erneut gehasht und entspricht weiterhin exakt der Vorgabe. Die beobachteten Listener auf 8080, 8091, 8092, 8083 und 8787 wurden vor der Ergebnisablage und zum Abschluss verglichen; Ergebnis siehe `logs/final_verification.json`. Diese Beobachtung betrifft die sichtbaren Listener, nicht einen vollständigen Nachweis aller internen Dienstzustände. Es wurden keine Dienststeuerungsbefehle oder HTTP-Anfragen ausgeführt.

Vorhandene Git-Arbeitsverzeichnisse wurden nur gelesen. Modelle und PGRN-Dateien wurden weder geschrieben noch erneut konvertiert. Ihre bekannten Hashes wurden aus dem Konvertierungsprotokoll übernommen; ein erneutes vollständiges Hashen der etwa 95 GB Modell-/PGRN-Daten war für diesen Quellenblocker nicht erforderlich.

## 9. Vorbereiteter Diagnosetest

**Nur dokumentierter Entwurf. Nicht ausführungsbereit: Die genannte Diagnosebinary existiert nicht. Kein Serverstart und keine Anfrage erfolgt.**

GGUF und PGRN wurden aus `../qwen3_coder_next_headercheck/download_conversion_runs/20261018T091238425764Z/result.json` übernommen. Alle Optionen entsprechen dem tatsächlich gespeicherten fehlgeschlagenen Testaufruf; lediglich der zukünftige Binarypfad ist der vom Auftrag vorgesehene Zielpfad.

```sh
/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3next_diagnostic_build/bin/llama-server-pgrn-diagnostic --model '/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf' --pgrn /Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/pgrn/qwen3-coder-next/Qwen3-Coder-Next-Q4_K_M.pgrn --host 127.0.0.1 --port 8083 --ctx-size 4096 --pgrn-cache-gb 12 --pgrn-headroom-gb 8 --batch-size 25 --ubatch-size 25 --parallel 1 --spec-type none --reasoning off --temp 0 --seed 42 --gpu-layers 99 --jinja --verbosity 5 --log-colors off
```

Request wie im ursprünglichen Test, keine neuen Evaluationsfälle:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Antworte ausschließlich mit der Zahl: 17 + 25"
    }
  ],
  "max_tokens": 32,
  "temperature": 0,
  "seed": 42,
  "stream": false
}
```

Vor einer späteren Ausführung müssen Quellidentität, Build- und Patchprüfung erfüllt und der Diagnoselauf separat freigegeben sein. Port 8083 muss frei sein, ohne andere Prozesse zu stoppen. Der ursprüngliche Runner schloss geerbte `LLAMA_ARG_*`-Defaults aus; ein späterer Runner muss dies ebenfalls pro Kindprozess tun. Der bloße Shellbefehl oben enthält diese Umgebungsbereinigung nicht und darf deshalb nicht als vollständig äquivalenter ausführbarer Testharness verstanden werden. Warmup wird im Entwurf wie beim fehlgeschlagenen Test nicht deaktiviert.

## 10. Offene Risiken und konkreter nächster Schritt

**Abschluss: BUILD BLOCKED.** Nicht auf eine beliebige neuere Engine oder den benachbarten Checkout ausweichen.

Benötigt wird eine überprüfbare Herkunftsangabe des Herausgebers zur konkreten Engine mit SHA-256 `7d022ad...`: vollständiger Buildquellstand zu `852e7daa1`, zugehöriger Diff/Overlay gegenüber `79bba02a6741de194912d370015866414faa83ad`, einschließlich etwaiger uncommitteter Änderungen, sowie die relevanten Buildoptionen. Alternativ wäre eine überprüfbare Erklärung ausreichend, weshalb die abweichende Versionskennung nur Buildmetadaten betrifft und der veröffentlichte Rekonstruktionsbaum den ausgelieferten Enginequellen entspricht.

Mit diesen Belegen lässt sich das Phase-A-Kriterium erneut prüfen und anschließend der bereits spezifizierte isolierte Diagnosebuild durchführen. Es wurde keine Nachricht oder Issue an den Herausgeber gesendet.

### Öffentliche Primärquellen

- [Releasecommit und Quellenbaum](https://github.com/Schero94/slipstream/tree/0b30cac2a6a40439b74cce6a512f08166f6e3ab3)
- [Rekonstruktionsskript](https://github.com/Schero94/slipstream/blob/0b30cac2a6a40439b74cce6a512f08166f6e3ab3/apply.sh)
- [Buildanleitung](https://github.com/Schero94/slipstream/blob/0b30cac2a6a40439b74cce6a512f08166f6e3ab3/README.md)
- [Releasehinweise 0.3.4](https://github.com/Schero94/slipstream/blob/0b30cac2a6a40439b74cce6a512f08166f6e3ab3/docs/RELEASE_0.3.4.md)
- [Generierung der Buildkennung](https://github.com/ggml-org/llama.cpp/blob/79bba02a6741de194912d370015866414faa83ad/cmake/build-info.cmake)
- [Metal-Buildregeln](https://github.com/ggml-org/llama.cpp/blob/79bba02a6741de194912d370015866414faa83ad/ggml/src/ggml-metal/CMakeLists.txt)
