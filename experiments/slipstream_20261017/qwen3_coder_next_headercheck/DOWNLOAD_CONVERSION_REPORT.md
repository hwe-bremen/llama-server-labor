# Qwen3-Coder-Next: Download und PGRN-Konvertierung

## Bewertung: READY WITH CONDITIONS

- Stand: 2026-10-18T09:12:38.425598+00:00
- Revision: ce09c67b53bc8739eef83fe67b2f5d293c270632
- Exakte Quelle: https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF/resolve/ce09c67b53bc8739eef83fe67b2f5d293c270632/Qwen3-Coder-Next-Q4_K_M.gguf
- Erwartete GGUF-Größe: 48,528,320,544 Bytes
- Erwartete GGUF-SHA-256: 9e6032d2f3b50a60f17ce8bf5a1d85c71af9b53b89c7978020ae7c660f29b090
- Erwartete PGRN-Größe: 46,909,751,296 Bytes

**Kein Inferenzserver gestartet. Bestehendes Labor nicht verändert.**

## Ausführungsnachweise [BELEGT]

```json
{
  "checked_at": "2026-10-18T09:12:38.425598+00:00",
  "status": "READY WITH CONDITIONS",
  "model_started": false,
  "full_model_download_started": true,
  "conversion_started": true,
  "preflight": {
    "external_mounted": true,
    "external_free_bytes": 883828822016,
    "internal_free_bytes": 1121691774976,
    "existing_gguf_bytes": 0,
    "existing_pgrn_or_partial_bytes": 0,
    "binaries": {
      "llama-server": {
        "sha256": "7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e",
        "matches_inspected_v034": true
      },
      "pgrn-convert": {
        "sha256": "af8e47e59d4dcd9eed556da061220af7bd10c3de8137eea2ddd866ab53ad8476",
        "matches_inspected_v034": true
      }
    },
    "native_converter_help": "usage: /Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/runtime/Slipstream.app/Contents/Resources/resources/pgrn-convert --input model.gguf --output model.pgrn [--expect-sha256 HEX]\n          [--min-free-gb N=16] [--io-threads N] [--progress jsonl]\n          [--dry-run] [--no-verify] [--resume] [--no-journal]\n\n  --resume      continue an interrupted conversion from its .partial +\n                .partial.journal, re-checking the CRC of everything\n                already written before appending\n  --no-journal  do not keep a resume journal; a cancelled run then\n                deletes its .partial as before\n\nexit codes: 0 done, 1 error, 2 cancelled (resumable)\n",
    "external_target_files": [],
    "internal_target_files": []
  },
  "gguf": {
    "file": "/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf",
    "size_bytes": 48528320544,
    "sha256": "9e6032d2f3b50a60f17ce8bf5a1d85c71af9b53b89c7978020ae7c660f29b090",
    "sha256_verified": true,
    "allocated_bytes": 48536788992
  },
  "local_header_verified": true,
  "dry_run": {
    "argv": [
      "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/runtime/Slipstream.app/Contents/Resources/resources/pgrn-convert",
      "--input",
      "/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf",
      "--dry-run"
    ],
    "exit_code": 0,
    "result": {
      "source": "/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf",
      "source_size": 48528320544,
      "source_shards": 1,
      "layers_with_experts": 48,
      "experts_per_layer": 512,
      "expert_count": 24576,
      "estimated_output_bytes": 46909751296
    }
  },
  "conversion": {
    "argv": [
      "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/runtime/Slipstream.app/Contents/Resources/resources/pgrn-convert",
      "--input",
      "/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf",
      "--output",
      "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/pgrn/qwen3-coder-next/Qwen3-Coder-Next-Q4_K_M.pgrn",
      "--expect-sha256",
      "9e6032d2f3b50a60f17ce8bf5a1d85c71af9b53b89c7978020ae7c660f29b090",
      "--min-free-gb",
      "20",
      "--io-threads",
      "1",
      "--progress",
      "jsonl"
    ],
    "started_at": "2026-10-18T10:23:15.164567+00:00",
    "ended_at": "2026-10-18T10:30:11.129478+00:00",
    "duration_seconds": 415.9640720830066,
    "exit_code": 0
  },
  "pgrn": {
    "file": "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/pgrn/qwen3-coder-next/Qwen3-Coder-Next-Q4_K_M.pgrn",
    "size_bytes": 46909751296,
    "allocated_bytes": 46925889536,
    "source_sha256_verified": true,
    "all_record_crcs_verified": true,
    "record_count": 24576,
    "sha256": "7c2638876bf7ecca53fc84f55a5803bf14405f817c1198698e8b2802417ab10e"
  },
  "conditions": [
    "Vor Inferenz Ports/RAM prüfen und effektives n_ubatch im Startlog bestätigen",
    "Kein Inferenzstart durch diesen Auftrag autorisiert"
  ],
  "finished_at": "2026-10-18T10:30:35.805504+00:00",
  "log_directory": "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3_coder_next_headercheck/download_conversion_runs/20261018T091238425764Z"
}
```

Fehlende Phasenfelder bedeuten: nicht ausgeführt bzw. nicht gemessen. Eine erfolgreiche Headerprüfung ist kein Download- oder Konvertierungsnachweis.

## Offline-Validierung [BELEGT]

20 Tests bestanden (test_headercheck und test_download_convert). Synthetische PGRN-Dateien prüfen vollständige CRC/SHA-Erfassung sowie die Zurückweisung beschädigter Payloads, falscher Verzeichniseinträge und Quellenidentitäten. Diese Tests starten weder Download noch Konverter oder Engine.

## Späterer Inferenzversuch: nur vorbereitet

4096 Kontext, 12 GiB Expertencache, batch=25, ubatch=25, eine Sequenz, spec-type=none, reasoning=off, Temperatur 0 und Seed 42. Prüfbare Argumentliste: inference_parameters_prepared.json; kein automatischer Start.

Die tatsächliche CLI ist in der vorhandenen, demselben Enginehash zugeordneten Hilfe belegt. llama-context.cpp am Pin 79bba02a6741 begrenzt n_ubatch auf n_batch und reicht es an die Memory-Batchzerlegung weiter. Die Hybridimplementierung verwendet den rekurrenten Batchsplitter; der PGRN-Callback verarbeitet dessen physische Tokenzeilen. Mit batch=ubatch=25 und parallel=1 sind bei top_k=10 höchstens 250 IDs pro Stagingaufruf möglich. Die angewendeten Werte müssen beim ersten tatsächlichen Start im Log bestätigt werden.

Quellnachweise: source_evidence/llama-memory-hybrid_79bba02a6741.cpp (init_batch, split_equal/split_seq) sowie source_evidence/converter_v0.3.4.cpp (Quellenhash, Dry-run, Recordlayout und CRC).

## Risiken und Empfehlung

Vor einem separat freizugebenden Inferenzstart freie Ports und aktuelle RAM-Belegung prüfen. Graph-/Prefillbuffer und andere laufende Modelle sind nicht in den statischen 15,32 GiB enthalten. MXFP4-Shared-Experts sind resident; tatsächliche Metal-Ausführung, Tool-Calling, numerische Qualität und Reviewpräzision bleiben ungeprüft. Für qwen3next ist kein bestätigter Compact-Slots-Pfad vorhanden.

## Fortsetzung im normalen macOS-Terminal

```sh
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3_coder_next_headercheck/download_convert_qwen3_coder_next.py'
```

Derselbe Befehl nimmt den externen .download-Stand wieder auf. Vorhandene finale Dateien werden geprüft und nicht überschrieben. Bei Fehlern bleibt der Ablauf stehen; kein automatischer Modellstart.
