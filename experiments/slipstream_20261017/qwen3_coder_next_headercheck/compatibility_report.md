# Qwen3-Coder-Next: Header- und PGRN-Prüfung

Stand: 2026-10-18T08:56:42.833157+00:00

## Entscheidung: UNGEKLÄRT

Ein GO betrifft ausschließlich statisch geprüfte Voraussetzungen für eine spätere Downloadentscheidung. Kein Download-, Konvertierungs- oder Inferenzstart ist freigegeben.

## Modellidentität

- Repository: unsloth/Qwen3-Coder-Next-GGUF
- Datei: Qwen3-Coder-Next-Q4_K_M.gguf
- Feste Revision: ce09c67b53bc8739eef83fe67b2f5d293c270632
- Veröffentlichte Größe: 48,528,320,544 Bytes
- Veröffentlichte SHA-256/LFS-OID: 9e6032d2f3b50a60f17ce8bf5a1d85c71af9b53b89c7978020ae7c660f29b090
- Vollständiger Modellhash wurde nicht lokal verifiziert.

## HTTP und Transferbudget

- GGUF-Bodybytes dieser Ausführung: 5,989,408
- GGUF-Bodybytes kumuliert: 5,989,408
- Konservativ reserviert, einschließlich Fehlversuchen: 5,989,432/33,554,432
- Erfolgreiche 206-Requests: 45
- Keine automatischen Retries. HTTP 200 wird vor Body-Lektüre abgewiesen.
- HTTPS-Redirect-Bodys werden nicht gelesen. HTTP-Header/TLS-Overhead sind keine GGUF-Bodybytes.

## Tatsächliche GGUF-Metadaten [BELEGT]

- Version: 3; Metadateneinträge: 53; Tensoren: 843
- Architektur: qwen3next
- Headerende: 5989408; Tensorpayloadbeginn: 5989408
- Alignment: 32
- Split-Metadaten: {}
- Chat-Template in tensor_inventory.json gespeichert, sofern im GGUF vorhanden.

## Vollständige Tensorstatistik [BELEGT]

| Gruppe | GGML-Typ | Tensorzahl | Konverterfreigabe für geroutete Experten |
|---|---|---:|---|
| other_resident | F32 | 313 | resident / getrennt zu beurteilen |
| other_resident | Q4_K | 113 | resident / getrennt zu beurteilen |
| other_resident | Q5_K | 72 | resident / getrennt zu beurteilen |
| other_resident | Q6_K | 9 | resident / getrennt zu beurteilen |
| down | Q4_K | 24 | ja |
| down | Q6_K | 24 | ja |
| shared_expert_resident | F32 | 48 | resident / getrennt zu beurteilen |
| shared_expert_resident | Q6_K | 48 | resident / getrennt zu beurteilen |
| shared_expert_resident | UNKNOWN_39 | 96 | resident / getrennt zu beurteilen |
| gate | Q4_K | 48 | ja |
| up | Q4_K | 48 | ja |

## Konverter und Engine

- Keine statisch erkennbaren Blocker in den vollständig geparsten Daten.
- Offen: Unbekannte GGML-Blockgröße: blk.0.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.0.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.1.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.1.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.2.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.2.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.3.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.3.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.4.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.4.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.5.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.5.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.6.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.6.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.7.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.7.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.8.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.8.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.9.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.9.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.10.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.10.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.11.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.11.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.12.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.12.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.13.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.13.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.14.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.14.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.15.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.15.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.16.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.16.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.17.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.17.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.18.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.18.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.19.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.19.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.20.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.20.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.21.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.21.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.22.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.22.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.23.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.23.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.24.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.24.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.25.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.25.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.26.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.26.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.27.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.27.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.28.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.28.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.29.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.29.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.30.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.30.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.31.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.31.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.32.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.32.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.33.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.33.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.34.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.34.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.35.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.35.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.36.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.36.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.37.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.37.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.38.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.38.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.39.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.39.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.40.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.40.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.41.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.41.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.42.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.42.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.43.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.43.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.44.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.44.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.45.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.45.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.46.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.46.ffn_up_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.47.ffn_gate_shexp.weight, Typ 39
- Offen: Unbekannte GGML-Blockgröße: blk.47.ffn_up_shexp.weight, Typ 39

Die Konverterlogik wurde anhand des unveränderten v0.3.4-Codes abgebildet, nicht durch Start des Konverters geprüft. Shared Experts werden resident geladen. Eine unsplit Einzeldatei ergibt denselben Quellenhashpfad bei Konverter und Loader.

## Speicherberechnung

Keine belastbare vollständige Speicherfreigabe wegen der oben genannten Blocker/offenen Daten.

## Prefill-Risiko und mögliche spätere Auflage

[BELEGT: v0.3.4-Codeprüfung] PGR_STAGE_MAX=256 begrenzt die
unterschiedlichen Experten in einem pgr_stage_selected-Aufruf, nicht die
Gesamtexpertenzahl. Der Callback übergibt rows × top_k zusammen an pgrn_stage.
Die Deduplizierung mit der 256er-Prüfung erfolgt VOR der späteren IO-Fensterung.
Diese Fensterung verhindert den Überlauf daher nicht. Für 512 Modell-Experten
und top_k=10 sind mehr als 256 unterschiedliche IDs ab 26 Tokenzeilen möglich.
Konkretes Gegenbeispiel: 26 Zeilen mit den disjunkten IDs 0 bis 259.
Es ist kein Beweis, dass natürliches Routing dieses Muster tatsächlich erzeugt.
Der untersuchte Callback teilt den Nicht-Compact-Aufruf nicht vorher auf.
Der Patch ergänzt Compact Slots explizit im qwen35moe-Graph für Ein-Token-
Ausführung. Der untersuchte qwen3next-Graph übergibt diese optionale Auswahl
nicht und nutzt den Standardpfad; Compact Slots dürfen für diesen Kandidaten
nicht als vorhandene Lösung behauptet werden. Der Code erlaubt 512
Experten grundsätzlich (Grenze UINT16_MAX). Kontextlänge und Ubatch sind
verschiedene Größen: Auch 16K/32K-Kontext erzwingt keinen 16K/32K-Stagingaufruf.
Eine spätere explizite Ubatch-Grenze von höchstens floor(256/top_k), bei top_k=10
also 25, begrenzt die Anzahl angeforderter IDs unabhängig vom Routing. Dies ist
eine aus dem Code abgeleitete konservative Auflage für einen späteren Lauf,
keine in dieser Untersuchung vorgenommene Konfigurationsänderung.

## Grenzen und Quellen

- Keine Engine oder Konvertierung gestartet. Keine Ports, Server oder Modelle verändert.
- Reviewqualität und korrektes Tool-Calling sind weiterhin ungeprüft.
- Binaryidentitäten: {"llama-server": {"sha256": "7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e", "matches_inspected_v034": true}, "pgrn-convert": {"sha256": "af8e47e59d4dcd9eed556da061220af7bd10c3de8137eea2ddd866ab53ad8476", "matches_inspected_v034": true}}
- Vorhandener Parser: ../inspect_gguf_metadata.py (HeaderReader, EXPERT, summarize).
- Quellenabbilder unter source_evidence/; Herkunft und Hashes in source_evidence/manifest.json.
- [Gepinnter GGUF-LFS-Zeiger](https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF/raw/ce09c67b53bc8739eef83fe67b2f5d293c270632/Qwen3-Coder-Next-Q4_K_M.gguf)
- [Konverter v0.3.4](https://github.com/Schero94/slipstream/blob/v0.3.4/engine/tools/pgrn-convert/pgrn-convert.cpp)
- [Staging v0.3.4](https://github.com/Schero94/slipstream/blob/v0.3.4/engine/src/peregrine_stage.cpp)
- [Loader und Callback](https://github.com/Schero94/slipstream/blob/v0.3.4/patches/slipstream-seams.patch)

## Ausführung im normalen macOS-Terminal

```sh
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3_coder_next_headercheck/check_qwen3_coder_next.py'
```

Der absolute Pfad funktioniert unabhängig vom aktuellen Arbeitsverzeichnis. Das Budget bleibt über Wiederholungen erhalten. Bei fehlendem Netzwerk keine automatischen Wiederholungen.

## Lokale Offlinevalidierung

14 synthetische Tests bestanden: Headergrenzen, vollständige Tensorprüfung, fehlerhafte Typen/Formen/Offsets, HTTP-200-Abweisung ohne Bodyread, HTTPS-Weiterleitung, Teilantworten und kumuliertes Budget. Dies ist kein Remote- oder Inferenznachweis.
