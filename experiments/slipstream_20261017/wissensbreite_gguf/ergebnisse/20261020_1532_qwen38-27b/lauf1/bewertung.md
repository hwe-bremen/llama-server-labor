# Bewertung lauf1

Status: ok · Teil A: **18 / 32**

| Datei | kopf | meta_typen | meta_skalare | meta_arrays | tensor_infos | alignment_offset | n_bytes | ende | Summe |
|---|---|---|---|---|---|---|---|---|---|
| synth_klassisch.gguf | – | – | – | – | – | – | – | – | 0 |
| Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 6 |
| Qwen3.6-27B-UD-Q4_K_XL.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 6 |
| Qwen3-Coder-Next-Q4_K_M.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 6 |
| synth_neu.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | 5 |

## synth_klassisch.gguf

Fehler: `Exit 1:  | stdout: {"error": "Failed to parse GGUF file: too many values to unpack (expected 2)"}`

## Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf
- meta_typen: 43/43
- meta_skalare: 37/37
- meta_arrays: 6/6
- tensor_infos: 339/339
- **n_bytes**: {"falsch": ["output.weight (Q6_K: Q5_K 452984832 statt 185794560)", "token_embd.weight (Q4_K: Q3_K 452984832 statt 127401984)", "blk.0.attn_k.weight (Q4_K: Q3_K 2359296 statt 663552)", "blk.0.attn_output.weight (Q4_K: Q3_K 18874368 statt 5308416)", "blk.0.attn_q.weight (Q4_K: Q3_K 18874368 statt 5308416)", "blk.0.attn_v.weight (Q6_K: Q5_K 2359296 statt 967680)", "blk.0.ffn_down_exps.weight (Q8_0: Q8_1 264241152 statt 140378112)", "blk.0.ffn_gate_exps.weight (Q4_K: Q3_K 264241152 statt 74317824)"], "anteil": "141/339"}
- **ende**: {"kandidat": [8257629184, 8071295040, false], "referenz": [8071295040, 8071295040, true]}

## Qwen3.6-27B-UD-Q4_K_XL.gguf
- meta_typen: 52/52
- meta_skalare: 47/47
- meta_arrays: 5/5
- tensor_infos: 866/866
- **n_bytes**: {"falsch": ["output.weight (Q6_K: Q5_K 2542796800 statt 1042944000)", "token_embd.weight (Q4_K: Q3_K 2542796800 statt 715161600)", "blk.0.attn_gate.weight (Q5_K: Q4_K 62914560 statt 21626880)", "blk.0.attn_qkv.weight (Q6_K: Q5_K 104857600 statt 43008000)", "blk.0.ffn_down.weight (Q6_K: Q5_K 178257920 statt 73113600)", "blk.0.ffn_gate.weight (Q4_K: Q3_K 178257920 statt 50135040)", "blk.0.ffn_up.weight (Q4_K: Q3_K 178257920 statt 50135040)", "blk.0.ssm_out.weight (Q8_0: Q8_1 62914560 statt 33423360)"], "anteil": "456/866"}
- **ende**: {"kandidat": [17970438144, 17909097600, false], "referenz": [17909097600, 17909097600, true]}

## Qwen3-Coder-Next-Q4_K_M.gguf
- meta_typen: 53/53
- meta_skalare: 49/49
- meta_arrays: 4/4
- tensor_infos: 843/843
- **n_bytes**: {"falsch": ["output.weight (Q6_K: Q5_K 622329856 statt 255252480)", "token_embd.weight (Q4_K: Q3_K 622329856 statt 175030272)", "blk.0.attn_gate.weight (Q4_K: Q3_K 16777216 statt 4718592)", "blk.0.attn_qkv.weight (Q5_K: Q4_K 33554432 statt 11534336)", "blk.0.ffn_down_exps.weight (Q6_K: Q5_K 1073741824 statt 440401920)", "blk.0.ffn_down_shexp.weight (Q6_K: Q5_K 2097152 statt 860160)", "blk.0.ffn_gate_exps.weight (Q4_K: Q3_K 1073741824 statt 301989888)", "blk.0.ffn_gate_shexp.weight (MXFP4: UNBEKANNT None statt 557056)"], "anteil": "361/843"}
- **ende**: {"kandidat": [49293517824, 48528320544, false], "referenz": [48528320544, 48528320544, true]}

## synth_neu.gguf
- meta_typen: 2/2
- meta_skalare: 2/2
- meta_arrays: 0/0
- tensor_infos: 3/3
- **alignment_offset**: {"kandidat": [32, 288], "referenz": [64, 320]}
- **n_bytes**: {"falsch": ["tensor_00_tq1_0 (TQ1_0: TQ1_0 1024 statt 108)", "tensor_01_tq2_0 (TQ2_0: TQ2_0 1536 statt 198)", "tensor_02_mxfp4 (MXFP4: UNBEKANNT None statt 68)"], "anteil": "0/3"}
- **ende**: {"kandidat": [1664, 832, false], "referenz": [772, 832, true]}

## Teil B (von Hand gegen den Schlüssel bewerten)

- **W1** Wie groß ist das Alignment der Tensordaten in einer GGUF-Datei, wenn `general.alignment` fehlt?  
  → Wenn das Feld `general.alignment` in der GGUF-Datei fehlt, wird standardmäßig ein Alignment von 32 Bytes für die Tensordaten verwendet.
- **W2** Welche numerischen Typ-IDs haben die GGUF-Metadaten-Werttypen STRING, ARRAY und FLOAT64?  
  → Die numerischen Typ-IDs für die GGUF-Metadaten-Werttypen sind: STRING = 8, ARRAY = 9 und FLOAT64 = 10.
- **W3** Wie viele Elemente umfasst ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K, und wie viele Bytes belegt ein Block jeweils?  
  → Ein Block bei Q4_K umfasst 256 Elemente und belegt 144 Bytes, während ein Block bei Q6_K 256 Elemente umfasst und 416 Bytes belegt.
- **W4** Welche ggml-Typ-IDs haben BF16 und Q8_0?  
  → Die ggml-Typ-ID für BF16 ist 22 und für Q8_0 ist sie 8.
- **W5** Welche ggml-Tensortyp-ID hat Q4_K_M?  
  → Die ggml-Tensortyp-ID für Q4_K_M ist 23.
- **W6** Welche Typ-ID hat der Metadaten-Werttyp FLOAT16 in GGUF?  
  → Die Typ-ID für den Metadaten-Werttyp FLOAT16 in GGUF ist 11.
- **W7** Worauf bezieht sich der Offset, der in der Tensor-Info einer GGUF-Datei steht?  
  → Der Offset in der Tensor-Info einer GGUF-Datei gibt die absolute Byte-Position innerhalb der Datei an, an der die eigentlichen Daten des Tensors beginnen. Er dient dazu, die binären Daten des Tensors schnell und direkt aus der Datei zu lesen, ohne die gesamte Struktur durchsuchen zu müssen.

