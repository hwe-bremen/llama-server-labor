# GLM / Slipstream: Kompatibilitätsprüfung vom 17.10.2026

**Abschließende kritische Neubewertung:** siehe
[ENTSCHEIDUNG_GLM_SLIPSTREAM.md](ENTSCHEIDUNG_GLM_SLIPSTREAM.md), Entscheidung C.
Die frühere Formulierung eines universellen frühen Split-Verbots unten ist
präzisiert: Der Guard betrifft bereits gefüllte Listen; bei anfangs leerer Liste
ist zusätzlich die Inkonsistenz zwischen Mehrteiler-Hash des Konverters und
Einzeldatei-Hash der Engine maßgeblich. Kein unterstützter Ausweg dadurch belegt.

## Ergebnis und Empfehlung

**Derzeit ist kein offiziell unterstützter, vollständig belegter GLM-/PGRN-Pfad
für diese Installation nachgewiesen. Keine weitere große Modellausgabe laden.**
Die bestehenden Dateien sind integer, aber typseitig inkompatibel. Zusätzlich
verweigert der PGRN-Ladepfad Split-GGUF. Beide Grenzen bleiben in v0.3.5 bestehen.

Empfehlung: den GLM-Inferenzversuch vorerst zurückstellen. Die ergänzende
HTTP-206-Metadatenprüfung ist abgeschlossen: Beide Teile beider Alternativen
wurden vollständig geprüft, und beide Ausgaben sind typseitig inkompatibel.
Eine spätere Engine-Installation, Zusammenführung von Gewichten, Konvertierung
oder ein großer Download benötigt weiterhin eine konkrete neue Freigabe nach
positivem Kompatibilitätsbefund.

## 1. Genau untersuchte Installation

| Komponente | Identifikation |
|---|---|
| Bundle | Slipstream 0.3.4, CFBundleVersion/ShortVersionString jeweils 0.3.4 |
| Engine | Build 10116, Commit-Anzeige `852e7daa1`, AppleClang 21, Darwin arm64 |
| Engine SHA-256 | `7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e` |
| Konverter SHA-256 | `af8e47e59d4dcd9eed556da061220af7bd10c3de8137eea2ddd866ab53ad8476` |
| Konverter Mach-O UUID | `0C104F69-CA14-32AD-863E-2848EDC1E7D5` |

Die Konverter-Hilfe besitzt keine separat dokumentierte Versionsausgabe. Seine
Identität wird daher nicht aus der Engine-Version abgeleitet, sondern durch das
offizielle, SHA-verifizierte Bundle und den exakten Binary-Hash festgehalten.
Der im Produktrepo veröffentlichte Source-Rekonstruktions-Pin `79bba02a6741`
ist NICHT die Commit-Anzeige des tatsächlich gebündelten Binaries. Der vollständige
historische Build-Quellbaum von `852e7daa1` war über die geprüften öffentlichen
Repo-Refs nicht zuzuordnen. Deshalb wurde die kritische Typprüfung zusätzlich
direkt am installierten Maschinencode kontrolliert.

## 2. Tatsächliche Typzulassung des Konverters

Öffentlicher v0.3.4-Code:

[engine/tools/pgrn-convert/pgrn-convert.cpp](https://github.com/Schero94/slipstream/blob/v0.3.4/engine/tools/pgrn-convert/pgrn-convert.cpp),
Zeilen 588–594, Git-Blob `46def2f2414a5ab0a9b1bb1843f73e00305bcd62`:

```cpp
if (!(type == 0 || type == 1 || type == 12 || type == 13 || type == 14)) {
    return fail("unsupported expert GGML type %u in %s", type, name);
}
```

**Direkter Binary-Beleg:** `otool -tvV` am installierten Konverter zeigt die
Grenze `type <= 14`, die Bitmaske `0x7003` und den Fehlerzweig zur genannten
Meldung. `0x7003` setzt genau die Bits 0, 1, 12, 13 und 14. Der Ausschnitt steht
in `logs/converter-actual-disassembly.txt` (Adressen 0x100002958–0x100002970;
Fehlerzweig 0x100002fcc). Das bestätigt die relevante Source-Bedingung unabhängig
vom nicht vollständig zugeordneten Build-Quellbaum. Es wurde kein Binary geändert.

| GGML-ID | Typ | Im Expertenkonverter zugelassen | In den 138 gestapelten Expertentensoren |
|---:|---|---|---:|
| 0 | F32 | ja | 0 |
| 1 | F16 | ja | 0 |
| 12 | Q4_K | ja | 92 |
| 13 | Q5_K | ja | 0 |
| 14 | Q6_K | ja | 0 |
| 6 | Q5_0 | **nein** | **24** |
| 8 | Q8_0 | **nein** | **22** |

Alle anderen IDs, einschließlich Q4_0 (2), Q5_1 (7) und BF16 (30), liegen ebenfalls
außerhalb dieser Experten-Zulassungsliste. Die Typzuordnung ist zusätzlich gegen
das lokale `/opt/homebrew/include/ggml.h` geprüft.

Die Einschränkung betrifft nur die vom Konverter erkannten gestapelten Tensoren
`blk.<n>.ffn_gate_exps.weight`, `ffn_up_exps.weight`, `ffn_down_exps.weight`.
Sie ist kein allgemeines Verbot dieser Typen in llama.cpp. Shared Experts
(`*_shexp.weight`), Attention, Embedding und andere residente Gewichte werden
dadurch nicht automatisch inkompatibel.

## 3. Vollständige lokale Metadatenprüfung beider Teile

Quelle: die bereits heruntergeladenen Dateien aus Revision
`b0f8153e9e7cf57cd3b0aad146667abf9de56f0e`, weiterhin unverändert extern.
Mit `inspect_gguf_metadata.py` wurden nur Header, Metadaten und Tensorverzeichnisse
gelesen. Kein Tensorpayload, keine Modellgewichte im Inferenzspeicher.

| Teil | Tensoren insgesamt | Gestapelte Expertentensoren | Ende des Tensorverzeichnisses |
|---|---:|---:|---:|
| 1/2 | 568 | 96 | Byte 9.344.743 |
| 2/2 | 235 | 42 | Byte 14.852 |
| Gesamt | **803** | **138** | — |

Beide Dateien deklarieren `split.count=2`, Indizes 0/1 und gemeinsam 803 Tensoren;
keine doppelten Tensornamen. Metadaten des ersten Teils: Architektur `glm4moe`,
47 Blöcke einschließlich eines NextN-Predict-Layers, 128 geroutete Experten,
8 ausgewählte Experten je Token.

| Tensorgruppe | Typen / Anzahl | Ergebnis |
|---|---|---|
| `ffn_gate_exps.weight` | 46 × Q4_K | Typprüfung bestanden |
| `ffn_up_exps.weight` | 46 × Q4_K | Typprüfung bestanden |
| `ffn_down_exps.weight` | 22 × Q8_0; 24 × Q5_0 | **Alle 46 scheitern** |
| Shared Experts, resident | 46 × Q8_0; 92 × Q5_K | Nicht Gegenstand der Experten-Typprüfung |
| Sonstige residente Gewichte | 331 × F32; 171 × Q4_K; 24 × Q6_K; 1 × Q8_0 | Nicht Gegenstand der Experten-Typprüfung |

Die Zahlen zählen jeweils gestapelte Tensoren mit 128 Experten, nicht 138 einzelne
Experten. Alle 138 Namen, Formen, Typen und Teil-Dateizuordnungen sowie die
betroffenen Layer je Typ sind vollständig in
`logs/glm-complete-tensor-inventory.json` aufgeführt.

## 4. Warum ein anderer K-Quant-Dateiname das Problem nicht löst

Die Down-Expertentensoren haben die Form `[1408, 4096, 128]`.
K-Quantisierungen verwenden Blöcke von 256 Werten entlang der ersten Dimension.
`1408 % 256 = 128`, also passt die Zeilenbreite nicht.

Der offizielle llama.cpp-Quantisierer behandelt solche Formen über
`tensor_type_fallback`: Q4_K → Q5_0, Q5_K → Q5_1, Q6_K → Q8_0.
Das erklärt die tatsächlich gemessene Mischung bei Q4_K_M.
Quellen: [llama-quant.cpp, Zeilen 362–405](https://github.com/ggml-org/llama.cpp/blob/79bba02a6741/src/llama-quant.cpp)
und [ggml-common.h, QK_K=256](https://github.com/ggml-org/llama.cpp/blob/79bba02a6741/ggml/src/ggml-common.h).

Diese Erklärung aus dem Upstream-Code ist von der unabhängigen Messung der
heruntergeladenen Typen zu unterscheiden. Sie beweist nicht den exakten
Erzeugungsablauf eines beliebigen anderen Uploads. Deshalb bleibt jede alternative
Datei bis zur Prüfung ihrer tatsächlichen Metadaten unbestätigt.

## 5. Zweite Grenze: Split-GGUF im PGRN-Inferenzpfad

Der Konverter kann die beiden Teile lesen. Der veröffentlichte Engine-Pfad
verweigert sie dagegen beim PGRN-Modellladen ausdrücklich:

```cpp
if (external_experts) {
    if (splits.size() > 1)
        throw std::runtime_error("PGRN v1 does not support split GGUF sources");
}
```

Quelle: [slipstream-seams.patch](https://github.com/Schero94/slipstream/blob/v0.3.4/patches/slipstream-seams.patch),
Bereich `llama_model_load`, Zeilen um 3296–3318. Auch der installierte Server-
Maschinencode enthält den zugehörigen Prüf- und Fehlerpfad: Vergleich der
Split-Vektorgröße mit 2 bei 0x1003a0674, Sprung bei >=2 zum Throw-Block
0x1003a13f0, dort Erzeugung und Werfen der passenden runtime_error. Beleg:
`logs/engine-split-guard-disassembly.txt`. Ein praktischer Modellstart zur
Auslösung dieses Fehlers wurde gemäß Grenze NICHT ausgeführt.

Außerdem bindet der Ladepfad die PGRN-Identität an die SHA-256 der GGUF-Quelle.
Ein nachträgliches Zusammenfügen bereits konvertierter Teile wäre daher kein
belegter Ausweg. Eine künftig genehmigte Zusammenführung müsste vor einer neuen
Konvertierung erfolgen und würde die unzulässigen Expertentypen trotzdem nicht
beheben. Hier wurde weder zusammengeführt noch konvertiert.

## 6. Neuere offizielle Slipstream-Version

Die geprüfte Release-Liste endet bei v0.3.5 (17.08.2026); dieser Release hat keine
Binär-Assets. Der aktuelle Main-Commit ist
`1518931afd732622d338c22793f946b860a381fd`. Die Veröffentlichung ergänzt einen
Dense-Modellpfad, keinen belegten Fix für GLM-Expertenstreaming.

Codevergleich v0.3.4/v0.3.5:

- Konverter-Datei: derselbe Git-Blob `46def2f2414a5ab0a9b1bb1843f73e00305bcd62`.
- Engine-Seams-Patch: derselbe Git-Blob `dd9cb1adec7b06907bfd99fd749d57b58800f02d`.
- PGRN-Leser: derselbe Git-Blob `f972dd1d59ed2f918eff81c914b237a37fb9eba3`.
- Der Release-Diff enthält keine Änderungen dieser Engine-Dateien.

Damit behebt v0.3.5 weder die Experten-Allowlist noch den Split-Ladepfad. Es wurde
keine offiziell qualifizierte neuere Engine für diese vorhandenen GGUFs gefunden.
oMLX ist ein anderer Modell-/Streamingpfad; die vorhandenen GGUFs sind damit nicht
automatisch weiterverwendbar. Eine Kompatibilität wird dafür hier nicht behauptet.

Quellen: [Release v0.3.5](https://github.com/Schero94/slipstream/releases/tag/v0.3.5),
[offizieller Versionsvergleich](https://github.com/Schero94/slipstream/compare/v0.3.4...v0.3.5).

## 7. Alternative veröffentlichte GGUFs: vollständige Metadatenprüfung

Die Terminal-Prüfung ist abgeschlossen. Für beide Kandidaten gilt
`all_parts_examined=true`, keine doppelten Tensornamen, vollständige Split-Indizes
0/1 und übereinstimmende deklarierte Gesamtzahlen.

| Ausgabe | Vollständiger Download, hier NICHT erfolgt | Tatsächlich gemessene Expertentypen | Status |
|---|---:|---|---|
| ggml-org Q4_K_M, Revision `23a7a815a57a697e59f36fd8a897c632730a1fe9` | 63.633.580.576 Bytes / 63,63 GB, zwei Teile | Gate/Up je 45 × Q4_K; Down 45 × Q4_0 (ID 2); insgesamt 780 Tensoren, davon 135 gestapelte Expertentensoren | **Inkompatibel:** alle 45 Down-Expertentensoren unzulässig |
| bartowski Q4_K_S, Revision `9c432824104581c615dcf71b955c7d2527f88cf9` | 68.310.026.944 Bytes / 68,31 GB, zwei Teile | Gate/Up je 46 × Q4_K; Down 22 × Q5_1 (ID 7) und 24 × Q5_0 (ID 6); insgesamt 803 Tensoren, davon 138 gestapelte Expertentensoren | **Inkompatibel:** alle 46 Down-Expertentensoren unzulässig |

Die ggml-org-Ausgabe enthält 46 Blöcke, die Bartowski-Ausgabe 47 einschließlich
NextN-Layer. Diese Unterschiede wurden nicht als Format- oder Laufzeitkompatibilität
interpretiert. Residente Shared-Expert- und sonstige Tensoren sind in den
vollständigen Ergebnissen separat aufgeführt; sie fallen nicht unter diese
Experten-Allowlist. Zusätzlich sind beide Ausgaben gesplittet und treffen auf
den bereits belegten PGRN-Split-Guard.

Lokale Messbelege: `logs/remote-metadata/results.json` enthält sämtliche
Tensorverzeichnisse beider Teile beider Kandidaten und die Gruppenstatistiken.
`logs/remote-metadata/budget.json` dokumentiert **78 verifizierte HTTP-206-Abrufe,
19.270.312 gelesene und ebenso viele reservierte Payload-Bytes** (19,27 MB).
Damit bleibt die Prüfung einschließlich der vorgesehenen Text-/Overheadreserve
unter dem autorisierten 100-MB-Limit. Keine vollständigen Modellgewichte wurden
nachgeladen. Der kleine erste ggml-org-Teil ist eine 9.308.768-Byte-Metadatendatei
mit null Tensoren und wurde vollständig gelesen.

Das Werkzeug akzeptiert nur HTTP 206 mit exakt passendem Content-Range,
Content-Length und Identity-Encoding. HTTP 200 wird ohne Bodyread abgewiesen.
Die gespeicherten Headerpräfixe reichen höchstens 256 KiB über das jeweilige
Tensorverzeichnis hinaus; der Parser liest keinen Tensorpayload. Deshalb sind
begrenzter Byte-Vorabruf und tatsächliche Metadatenanalyse zu unterscheiden.
Kein Modell wurde geladen, konvertiert oder praktisch inferiert.

Quellen zur Einordnung: [ggml-org Erzeugungsprotokoll](https://huggingface.co/ggml-org/GLM-4.5-Air-GGUF/blob/main/convert.log)
und [Bartowski-Dateiverzeichnis](https://huggingface.co/bartowski/zai-org_GLM-4.5-Air-GGUF/tree/main/zai-org_GLM-4.5-Air-Q4_K_S).
Entscheidend sind jetzt die direkt gemessenen Metadaten der gepinnten Revisionen,
nicht die Dateinamen oder allein das Erzeugungsprotokoll.

## 8. Höchstens drei Handlungsoptionen

| Option | Verifizierter Kompatibilitätsstatus | Aufwand / Download | Offene Punkte |
|---|---|---|---|
| Vorhandene Dateien + neuere offizielle Engine | **Kein geeigneter neuer Stand belegt**; v0.3.5 behebt beide Grenzen nicht | 0 zusätzliche Modell-GB; eine tatsächlich passende Runtime ist nicht identifiziert | Offizielle Unterstützung für Q5_0/Q8_0 im PGRN-Pfad und Split bzw. eine zuvor genehmigte Zusammenführung fehlen |
| Andere GLM-GGUF-Ausgabe | **Beide geprüften Alternativen inkompatibel**; ggml-org Q4_0, Bartowski Q5_1/Q5_0 in Down-Experten | Headerprüfung abgeschlossen: 19,27 MB; 63,63/68,31-GB-Downloads nicht empfohlen | Andere offiziell unterstützte Ausgabe erforderlich; zusätzlich ungesplitteter PGRN-Pfad und spätere Laufzeit-/Speicherprüfung |
| Versuch vorerst zurückstellen | **Empfohlen** | 0 große Downloads; Dateien unverändert behalten | Fortsetzen erst nach nachgewiesener offizieller Lösung oder nach separater Entscheidung für ein Entwicklungsprojekt |

48 GB Unified Memory sind nicht die Ursache dieses Abbruchs: er passiert bereits
bei der Typprüfung vor Cache-/Kontextplanung. Mehr Cache oder weniger Kontext
beheben weder diese Typen noch den Split-Guard. Ein normaler Vollresidenzpfad für
63–73-GB-Gewichte ist auf diesem 48-GB-Mac keine gleichwertige belegte Alternative
zum vorgesehenen Expertenstreaming. Keine ungeprüfte Laufzeit- oder PGRN-Größe
wird aus kompatiblen Metadaten abgeleitet.

## Änderungen und Grenzen

Aktualisiert wurden nur Befunde und Diagnosewerkzeuge im Experimentverzeichnis.
Kein Konverterpatch, keine Engine-Aktualisierung, kein Modellstart, keine
Konvertierung, Requantisierung, Dateilöschung oder Änderung bestehender Gewichte.
Es wurden keine Labordienste gestartet, beendet oder umkonfiguriert. Bei der
abschließenden Nachkontrolle waren auf 8080/8091/8092/8787 allerdings keine Listener
mehr sichtbar, anders als zu Beginn dieser Untersuchung. Die Ursache dieser
zwischenzeitlichen Statusänderung wurde nicht untersucht; ein unverändert
laufendes Labor wird deshalb nicht behauptet. Es erfolgte kein Neustart.
Beleg: `logs/compatibility-investigation-final-listeners.json`.
Vollständige strukturierte Belege:
`logs/glm-compatibility-source-evidence.json` und
`logs/glm-complete-tensor-inventory.json`.
