# Qwen3-Coder-Next: Header- und PGRN-Prüfung

Stand: 2026-10-18T08:56:42.833157+00:00

## Entscheidung: GO

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
| shared_expert_resident | MXFP4 | 96 | resident / getrennt zu beurteilen |
| shared_expert_resident | Q6_K | 48 | resident / getrennt zu beurteilen |
| gate | Q4_K | 48 | ja |
| up | Q4_K | 48 | ja |

## Konverter und Engine

- Keine statisch erkennbaren Blocker in den vollständig geparsten Daten.

Die Konverterlogik wurde anhand des unveränderten v0.3.4-Codes abgebildet, nicht durch Start des Konverters geprüft. Shared Experts werden resident geladen. Eine unsplit Einzeldatei ergibt denselben Quellenhashpfad bei Konverter und Loader.

## Speicherberechnung

Aus vollständigen Tensorformen/Typen berechnet, keine Laufzeitmessung:

```json
{
  "pgrn": {
    "pgrn_file_bytes": 46909751296,
    "expert_payload_bytes": 46808432640,
    "padding_bytes": 100663296,
    "directory_bytes": 638976,
    "header_reserved_bytes": 16384,
    "header_used_bytes": 10096,
    "header_fits": true,
    "records": [
      {
        "layer": 0,
        "record_bytes": 2039808
      },
      {
        "layer": 1,
        "record_bytes": 2039808
      },
      {
        "layer": 2,
        "record_bytes": 2039808
      },
      {
        "layer": 3,
        "record_bytes": 2039808
      },
      {
        "layer": 4,
        "record_bytes": 2039808
      },
      {
        "layer": 5,
        "record_bytes": 2039808
      },
      {
        "layer": 6,
        "record_bytes": 1769472
      },
      {
        "layer": 7,
        "record_bytes": 1769472
      },
      {
        "layer": 8,
        "record_bytes": 2039808
      },
      {
        "layer": 9,
        "record_bytes": 1769472
      },
      {
        "layer": 10,
        "record_bytes": 1769472
      },
      {
        "layer": 11,
        "record_bytes": 2039808
      },
      {
        "layer": 12,
        "record_bytes": 1769472
      },
      {
        "layer": 13,
        "record_bytes": 1769472
      },
      {
        "layer": 14,
        "record_bytes": 2039808
      },
      {
        "layer": 15,
        "record_bytes": 1769472
      },
      {
        "layer": 16,
        "record_bytes": 1769472
      },
      {
        "layer": 17,
        "record_bytes": 2039808
      },
      {
        "layer": 18,
        "record_bytes": 1769472
      },
      {
        "layer": 19,
        "record_bytes": 1769472
      },
      {
        "layer": 20,
        "record_bytes": 2039808
      },
      {
        "layer": 21,
        "record_bytes": 1769472
      },
      {
        "layer": 22,
        "record_bytes": 1769472
      },
      {
        "layer": 23,
        "record_bytes": 2039808
      },
      {
        "layer": 24,
        "record_bytes": 1769472
      },
      {
        "layer": 25,
        "record_bytes": 1769472
      },
      {
        "layer": 26,
        "record_bytes": 2039808
      },
      {
        "layer": 27,
        "record_bytes": 1769472
      },
      {
        "layer": 28,
        "record_bytes": 1769472
      },
      {
        "layer": 29,
        "record_bytes": 2039808
      },
      {
        "layer": 30,
        "record_bytes": 1769472
      },
      {
        "layer": 31,
        "record_bytes": 1769472
      },
      {
        "layer": 32,
        "record_bytes": 2039808
      },
      {
        "layer": 33,
        "record_bytes": 1769472
      },
      {
        "layer": 34,
        "record_bytes": 1769472
      },
      {
        "layer": 35,
        "record_bytes": 2039808
      },
      {
        "layer": 36,
        "record_bytes": 1769472
      },
      {
        "layer": 37,
        "record_bytes": 1769472
      },
      {
        "layer": 38,
        "record_bytes": 2039808
      },
      {
        "layer": 39,
        "record_bytes": 1769472
      },
      {
        "layer": 40,
        "record_bytes": 1769472
      },
      {
        "layer": 41,
        "record_bytes": 2039808
      },
      {
        "layer": 42,
        "record_bytes": 2039808
      },
      {
        "layer": 43,
        "record_bytes": 2039808
      },
      {
        "layer": 44,
        "record_bytes": 2039808
      },
      {
        "layer": 45,
        "record_bytes": 2039808
      },
      {
        "layer": 46,
        "record_bytes": 2039808
      },
      {
        "layer": 47,
        "record_bytes": 2039808
      }
    ]
  },
  "memory": {
    "resident_tensor_payload_bytes": 1713898496,
    "routed_tensor_payload_bytes": 46808432640,
    "all_tensor_payload_bytes": 48522331136,
    "expert_cache_bytes": 12884901888,
    "scratch_payload_bytes_before_backend_alignment": 1044381696,
    "gguf_plus_pgrn_bytes": 95438071840,
    "runtime_overhead_measured": false,
    "kv_f16_single_sequence_assuming_engine_layout": {
      "16384": 402653184,
      "32768": 805306368
    },
    "full_attention_layers_from_metadata": 12
  }
}
```

PGRN: feste 16 KiB Header + auf 16 KiB ausgerichtete Expertenrecords + 26 Bytes je Record. GGUF und PGRN werden weiterhin beide benötigt. Backendalignment, Graph-/Prefillbuffer, rekurrente Zustände, Betriebssystem und andere laufende Modelle kommen hinzu. Residente Gewichte + 12 GiB Cache + Scratch + KV sind eine Untergrenze, kein garantierter Peak. KV wird nur aus vorhandenen Attention-Metadaten abgeleitet; ohne ausreichende Schlüssel bleibt es offen.

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

## Offline-Nachprüfung

Typ 39 ist MXFP4: 17 Bytes je 32 Werte. In dieser Datei betrifft er 96 residente Shared-Expert-Tensoren, keine gerouteten Experten. Die Konverter-Whitelist bleibt unverändert. Der gepinnte Metalcode und die eingebetteten Kernels des vorhandenen Binaries enthalten MXFP4-Unterstützung. Die frühere Einstufung UNGEKLÄRT entstand durch die unvollständige Typentabelle des Prüfskripts. Sämtliche Bytebereiche wurden nun mitberechnet und erneut geprüft. Zusätzlich übertragene GGUF-Bytes: 0. Ursprüngliche Ergebnisdateien bleiben erhalten.

Offlinevalidierung der ergänzten Typzuordnung: **15 Tests bestanden**. Insbesondere bleibt MXFP4 für geroutete Experten abgewiesen; die Änderung betrifft die Größenberechnung residenter Tensoren.
