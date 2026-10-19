# Qwen3-Coder-Next: isolierter Inferenztest

## Status: FAIL

[BELEGT] RuntimeError: Effektive Parameter fehlen/weichen ab: {}

## Vorprüfung und Modellidentität

Dateigrößen, Prüfprotokoll, Enginehash und Speichermessungen stehen im folgenden Ergebnis. Historische SHA-/CRC-Nachweise sind [DOKUMENTIERT]; aktuelle Größen und Änderungszeiten [BELEGT].

## Start und effektive Parameter

```sh
/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/runtime/Slipstream.app/Contents/Resources/resources/llama-server --model '/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf' --pgrn /Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/pgrn/qwen3-coder-next/Qwen3-Coder-Next-Q4_K_M.pgrn --host 127.0.0.1 --port 8083 --ctx-size 4096 --pgrn-cache-gb 12 --pgrn-headroom-gb 8 --batch-size 25 --ubatch-size 25 --parallel 1 --spec-type none --reasoning off --temp 0 --seed 42 --gpu-layers 99 --jinja
```

Effektive Werte gelten ausschließlich bei vorhandenem effective_parameters-Nachweis. Kein erfolgreicher Start wird aus vorbereiteten Argumenten abgeleitet.

## Speicherbeobachtung

Rohmessungen: memory.jsonl. Prozentwerte sind keine exakte Allokationsgarantie; RSS erfasst nicht den gesamten Unified-Memory-Bedarf. Swapouts sind kumulativ; nur Differenzen beschreiben Änderungen. Laufzeitgrenzen: Laden 20 Minuten, Anfrage 10 Minuten, insgesamt 60 Minuten.

## Funktionstests

A: 42; B: Kennwort und mindestens 200 tatsächliche Prompttokens; C: Null ausgeschlossen und leere Auswahl behandelt. Request-/Response-Dateien nur für tatsächlich vorbereitete bzw. gesendete Anfragen. Kein umfassender Nachweis der Reviewqualität.

## Offene Fragen und Abschluss

[HYPOTHESE] Nicht getestete Metal-/PGRN-Pfade bleiben offen. Ausschließlich die eigene Prozessreferenz wird beendet. Kein Download, keine Konvertierung, keine Modellentladung und keine Änderung bestehender Dienste. Listenervergleich ist keine umfassende Funktionsprüfung. Ein BLOCKED erfordert einen erneuten bewussten Aufruf im normalen Terminal.

## Vollständiges Ergebnis

```json
{
  "status": "FAIL",
  "started_at": "2026-10-18T11:54:44.243912+00:00",
  "run_directory": "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3_coder_next_headercheck/first_inference_runs/20261018T115444243739Z",
  "server_started": true,
  "requests_sent": 0,
  "existing_processes_changed": false,
  "memory_before": {
    "at": "2026-10-18T11:54:44.271178+00:00",
    "vm_stat": {
      "argv": [
        "/usr/bin/vm_stat"
      ],
      "exit_code": 0,
      "stdout": "Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free:                                   663753.\nPages active:                                1009760.\nPages inactive:                              1130658.\nPages speculative:                              8246.\nPages throttled:                                   0.\nPages wired down:                             208929.\nPages purgeable:                               40714.\n\"Translation faults\":                     1949059819.\nPages copy-on-write:                       112365824.\nPages zero filled:                        1945156782.\nPages reactivated:                         395519271.\nPages purged:                               32272300.\nFile-backed pages:                           1303684.\nAnonymous pages:                              844980.\nPages stored in compressor:                   135424.\nPages occupied by compressor:                  68638.\nDecompressions:                            296983661.\nCompressions:                              358429687.\nPageins:                                   174067486.\nPageouts:                                     237555.\nSwapins:                                     8615408.\nSwapouts:                                   14275454.\n",
      "stderr": ""
    },
    "pressure": {
      "argv": [
        "/usr/bin/memory_pressure",
        "-Q"
      ],
      "exit_code": 0,
      "stdout": "The system has 51539607552 (3145728 pages with a page size of 16384).\nSystem-wide memory free percentage: 90%\n",
      "stderr": ""
    },
    "free_percentage": 90,
    "page_size": 16384,
    "counts": {
      "Pages free": 663753,
      "Pages active": 1009760,
      "Pages inactive": 1130658,
      "Pages speculative": 8246,
      "Pages throttled": 0,
      "Pages wired down": 208929,
      "Pages purgeable": 40714,
      "Pages copy-on-write": 112365824,
      "Pages zero filled": 1945156782,
      "Pages reactivated": 395519271,
      "Pages purged": 32272300,
      "File-backed pages": 1303684,
      "Anonymous pages": 844980,
      "Pages stored in compressor": 135424,
      "Pages occupied by compressor": 68638,
      "Decompressions": 296983661,
      "Compressions": 358429687,
      "Pageins": 174067486,
      "Pageouts": 237555,
      "Swapins": 8615408,
      "Swapouts": 14275454
    }
  },
  "verification_record": "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3_coder_next_headercheck/download_conversion_runs/20261018T091238425764Z/result.json",
  "files": {
    "gguf": {
      "path": "/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf",
      "size": 48528320544,
      "verified_sha256": "9e6032d2f3b50a60f17ce8bf5a1d85c71af9b53b89c7978020ae7c660f29b090"
    },
    "pgrn": {
      "path": "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/pgrn/qwen3-coder-next/Qwen3-Coder-Next-Q4_K_M.pgrn",
      "size": 46909751296,
      "verified_sha256": "7c2638876bf7ecca53fc84f55a5803bf14405f817c1198698e8b2802417ab10e"
    }
  },
  "engine_sha256": "7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e",
  "argv": [
    "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/runtime/Slipstream.app/Contents/Resources/resources/llama-server",
    "--model",
    "/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf",
    "--pgrn",
    "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/pgrn/qwen3-coder-next/Qwen3-Coder-Next-Q4_K_M.pgrn",
    "--host",
    "127.0.0.1",
    "--port",
    "8083",
    "--ctx-size",
    "4096",
    "--pgrn-cache-gb",
    "12",
    "--pgrn-headroom-gb",
    "8",
    "--batch-size",
    "25",
    "--ubatch-size",
    "25",
    "--parallel",
    "1",
    "--spec-type",
    "none",
    "--reasoning",
    "off",
    "--temp",
    "0",
    "--seed",
    "42",
    "--gpu-layers",
    "99",
    "--jinja"
  ],
  "phase": "startup",
  "environment_note": "Inherited LLAMA_ARG_* defaults excluded for this subprocess only",
  "pid": 64726,
  "server_started_at": "2026-10-18T11:54:44.325073+00:00",
  "load_seconds": 288.89189454203006,
  "reason": "RuntimeError: Effektive Parameter fehlen/weichen ab: {}",
  "own_process_ended": true,
  "own_process_exit_code": 0,
  "finished_at": "2026-10-18T11:59:33.403729+00:00",
  "same_observed_lab_listeners": true,
  "port_8083_free_after": true
}
```
