# Bewertung lauf2

Status: ok · Teil A: **15 / 32**

| Datei | kopf | meta_typen | meta_skalare | meta_arrays | tensor_infos | alignment_offset | n_bytes | ende | Summe |
|---|---|---|---|---|---|---|---|---|---|
| synth_klassisch.gguf | – | – | – | – | – | – | – | – | 0 |
| Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | 5 |
| Qwen3.6-27B-UD-Q4_K_XL.gguf | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | 5 |
| Qwen3-Coder-Next-Q4_K_M.gguf | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | 5 |
| synth_neu.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 6 |

## synth_klassisch.gguf

Fehler: `Exit 1: `

## Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf
- meta_typen: 43/43
- meta_skalare: 37/37
- **meta_arrays**: {"falsch": ["general.tags", "general.languages", "mellum.attention.sliding_window_pattern", "tokenizer.ggml.tokens", "tokenizer.ggml.token_type"], "anteil": "0/6"}
- tensor_infos: 339/339
- **n_bytes**: {"falsch": ["output.weight (Q6_K: Q4_K 127401984 statt 185794560)", "token_embd.weight (Q4_K: Q2_K 69009408 statt 127401984)", "blk.0.attn_k.weight (Q4_K: Q2_K 359424 statt 663552)", "blk.0.attn_output.weight (Q4_K: Q2_K 2875392 statt 5308416)", "blk.0.attn_q.weight (Q4_K: Q2_K 2875392 statt 5308416)", "blk.0.attn_v.weight (Q6_K: Q4_K 663552 statt 967680)", "blk.0.ffn_down_exps.weight (Q8_0: UNBEKANNT None statt 140378112)", "blk.0.ffn_gate_exps.weight (Q4_K: Q2_K 40255488 statt 74317824)"], "anteil": "141/339"}
- **ende**: {"kandidat": [8033643520, 8071295040, false], "referenz": [8071295040, 8071295040, true]}

## Qwen3.6-27B-UD-Q4_K_XL.gguf
- meta_typen: 52/52
- meta_skalare: 47/47
- **meta_arrays**: {"falsch": ["general.tags", "qwen35.rope.dimension_sections", "tokenizer.ggml.tokens", "tokenizer.ggml.token_type", "tokenizer.ggml.merges"], "anteil": "0/5"}
- tensor_infos: 866/866
- **n_bytes**: {"falsch": ["output.weight (Q6_K: Q4_K 715161600 statt 1042944000)", "token_embd.weight (Q4_K: Q2_K 387379200 statt 715161600)", "blk.0.attn_gate.weight (Q5_K: Q3_K 14008320 statt 21626880)", "blk.0.attn_qkv.weight (Q6_K: Q4_K 29491200 statt 43008000)", "blk.0.ffn_down.weight (Q6_K: Q4_K 50135040 statt 73113600)", "blk.0.ffn_gate.weight (Q4_K: Q2_K 27156480 statt 50135040)", "blk.0.ffn_up.weight (Q4_K: Q2_K 27156480 statt 50135040)", "blk.0.ssm_out.weight (Q8_0: UNBEKANNT None statt 33423360)"], "anteil": "456/866"}
- **ende**: {"kandidat": [17898102784, 17909097600, false], "referenz": [17909097600, 17909097600, true]}

## Qwen3-Coder-Next-Q4_K_M.gguf
- meta_typen: 53/53
- meta_skalare: 49/49
- **meta_arrays**: {"falsch": ["general.tags", "tokenizer.ggml.tokens", "tokenizer.ggml.token_type", "tokenizer.ggml.merges"], "anteil": "0/4"}
- tensor_infos: 843/843
- **n_bytes**: {"falsch": ["output.weight (Q6_K: Q4_K 175030272 statt 255252480)", "token_embd.weight (Q4_K: Q2_K 94808064 statt 175030272)", "blk.0.attn_gate.weight (Q4_K: Q2_K 2555904 statt 4718592)", "blk.0.attn_qkv.weight (Q5_K: Q3_K 7471104 statt 11534336)", "blk.0.ffn_down_exps.weight (Q6_K: Q4_K 301989888 statt 440401920)", "blk.0.ffn_down_shexp.weight (Q6_K: Q4_K 589824 statt 860160)", "blk.0.ffn_gate_exps.weight (Q4_K: Q2_K 163577856 statt 301989888)", "blk.0.ffn_gate_shexp.weight (MXFP4: UNBEKANNT None statt 557056)"], "anteil": "361/843"}
- **ende**: {"kandidat": [48522331136, 48528320544, false], "referenz": [48528320544, 48528320544, true]}

## synth_neu.gguf
- meta_typen: 2/2
- meta_skalare: 2/2
- meta_arrays: 0/0
- tensor_infos: 3/3
- **n_bytes**: {"falsch": ["tensor_00_tq1_0 (TQ1_0: UNBEKANNT None statt 108)", "tensor_01_tq2_0 (TQ2_0: UNBEKANNT None statt 198)", "tensor_02_mxfp4 (MXFP4: UNBEKANNT None statt 68)"], "anteil": "0/3"}
- **ende**: {"kandidat": [0, 832, false], "referenz": [772, 832, true]}

## Teil B (von Hand gegen den Schlüssel bewerten)

- **W1** Wie groß ist das Alignment der Tensordaten in einer GGUF-Datei, wenn `general.alignment` fehlt?  
  → Wenn der Schlüssel `general.alignment` in einer GGUF-Datei fehlt, wird standardmäßig ein Alignment von 32 Byte verwendet. Dies ist der in der GGUF-Spezifikation festgelegte Default-Wert für die Ausrichtung von Tensor-Daten.
- **W2** Welche numerischen Typ-IDs haben die GGUF-Metadaten-Werttypen STRING, ARRAY und FLOAT64?  
  → Die GGUF-Spezifikation definiert keine festen numerischen IDs für die Typen STRING, ARRAY und FLOAT64, da diese als komplexe oder variable Typen behandelt werden. STRING und ARRAY sind keine atomaren Datentypen mit einer einzelnen ID, sondern werden durch ihre Struktur und Länge codiert, während FLOAT64 (ggml_type) in der Regel die ID 11 hat, aber nicht direkt als einfacher Metadatenwerttyp in der gleichen Kategorie wie INT32 oder FLOAT32 steht.
- **W3** Wie viele Elemente umfasst ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K, und wie viele Bytes belegt ein Block jeweils?  
  → Bei den ggml-Quantisierungstypen Q4_K und Q6_K umfasst ein Block jeweils 256 Elemente. Ein Q4_K-Block belegt dabei 150 Bytes, während ein Q6_K-Block 180 Bytes benötigt.
- **W4** Welche ggml-Typ-IDs haben BF16 und Q8_0?  
  → Die ggml-Typ-ID für BF16 ist `GGML_TYPE_BF16` (numerisch 15), und die für Q8_0 ist `GGML_TYPE_Q8_0` (numerisch 10). Diese Werte können je nach Version der Bibliothek variieren, da die Enumerationswerte im Laufe der Zeit angepasst wurden.
- **W5** Welche ggml-Tensortyp-ID hat Q4_K_M?  
  → Die ggml-Tensortyp-ID für Q4_K_M ist 10. Dieser Wert ist in der `ggml.h`-Headerdatei der llama.cpp-Bibliothek definiert.
- **W6** Welche Typ-ID hat der Metadaten-Werttyp FLOAT16 in GGUF?  
  → Der Metadaten-Werttyp `FLOAT16` in GGUF hat die Typ-ID 1. Dieser Typ entspricht einem 16-Bit-Gleitkommawert im IEEE 754-Format.
- **W7** Worauf bezieht sich der Offset, der in der Tensor-Info einer GGUF-Datei steht?  
  → Der Offset in der Tensor-Info einer GGUF-Datei bezieht sich auf die Byte-Position innerhalb der Datei, an der die tatsächlichen Tensor-Daten beginnen. Er ermöglicht es, die Daten direkt aus der Datei zu lesen, ohne sie vorher vollständig in den Arbeitsspeicher laden zu müssen. Dieser Wert ist relativ zum Anfang der Datei oder einem spezifischen Datenbereich, je nach GGUF-Version und Implementierung.

