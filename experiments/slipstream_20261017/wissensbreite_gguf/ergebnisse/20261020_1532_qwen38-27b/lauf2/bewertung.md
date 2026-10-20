# Bewertung lauf2

Status: ok · Teil A: **23 / 32**

| Datei | kopf | meta_typen | meta_skalare | meta_arrays | tensor_infos | alignment_offset | n_bytes | ende | Summe |
|---|---|---|---|---|---|---|---|---|---|
| synth_klassisch.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | 5 |
| Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 6 |
| Qwen3.6-27B-UD-Q4_K_XL.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 6 |
| Qwen3-Coder-Next-Q4_K_M.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 6 |
| synth_neu.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | 5 |

## synth_klassisch.gguf
- meta_typen: 23/23
- meta_skalare: 15/15
- meta_arrays: 8/8
- tensor_infos: 27/27
- **alignment_offset**: {"kandidat": [32, 2432], "referenz": [64, 2432]}
- **n_bytes**: {"falsch": ["tensor_02_bf16 (BF16: IQ4_XS_6 512 statt 256)", "tensor_03_f64 (F64: IQ1_L 64 statt 512)", "tensor_04_i8 (I8: BF16 192 statt 96)", "tensor_05_i16 (I16: IQ4_NL_1 512 statt 256)", "tensor_06_i32 (I32: IQ3_M 192 statt 256)", "tensor_07_i64 (I64: IQ2_M 192 statt 768)", "tensor_08_q4_0 (Q4_0: Q4_0 256 statt 72)", "tensor_09_q4_1 (Q4_1: Q4_1 192 statt 40)"], "anteil": "2/27"}
- **ende**: {"kandidat": [12992, 10624, false], "referenz": [10592, 10624, true]}

## Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf
- meta_typen: 43/43
- meta_skalare: 37/37
- meta_arrays: 6/6
- tensor_infos: 339/339
- **n_bytes**: {"falsch": ["output.weight (Q6_K: Q8_K 1811939328 statt 185794560)", "token_embd.weight (Q4_K: Q5_K 1132462080 statt 127401984)", "blk.0.attn_k.weight (Q4_K: Q5_K 5898240 statt 663552)", "blk.0.attn_output.weight (Q4_K: Q5_K 47185920 statt 5308416)", "blk.0.attn_q.weight (Q4_K: Q5_K 47185920 statt 5308416)", "blk.0.attn_v.weight (Q6_K: Q8_K 9437184 statt 967680)", "blk.0.ffn_down_exps.weight (Q8_0: Q5_1 528482304 statt 140378112)", "blk.0.ffn_gate_exps.weight (Q4_K: Q5_K 660602880 statt 74317824)"], "anteil": "141/339"}
- **ende**: {"kandidat": [8653990912, 8071295040, false], "referenz": [8071295040, 8071295040, true]}

## Qwen3.6-27B-UD-Q4_K_XL.gguf
- meta_typen: 52/52
- meta_skalare: 47/47
- meta_arrays: 5/5
- tensor_infos: 866/866
- **n_bytes**: {"falsch": ["output.weight (Q6_K: Q8_K 10171187200 statt 1042944000)", "token_embd.weight (Q4_K: Q5_K 6356992000 statt 715161600)", "blk.0.attn_gate.weight (Q5_K: Q6_K 188743680 statt 21626880)", "blk.0.attn_qkv.weight (Q6_K: Q8_K 419430400 statt 43008000)", "blk.0.ffn_down.weight (Q6_K: Q8_K 713031680 statt 73113600)", "blk.0.ffn_gate.weight (Q4_K: Q5_K 445644800 statt 50135040)", "blk.0.ffn_up.weight (Q4_K: Q5_K 445644800 statt 50135040)", "blk.0.ssm_out.weight (Q8_0: Q5_1 125829120 statt 33423360)"], "anteil": "456/866"}
- **ende**: {"kandidat": [18237825024, 17909097600, false], "referenz": [17909097600, 17909097600, true]}

## Qwen3-Coder-Next-Q4_K_M.gguf
- meta_typen: 53/53
- meta_skalare: 49/49
- meta_arrays: 4/4
- tensor_infos: 843/843
- **n_bytes**: {"falsch": ["output.weight (Q6_K: Q8_K 2489319424 statt 255252480)", "token_embd.weight (Q4_K: Q5_K 1555824640 statt 175030272)", "blk.0.attn_gate.weight (Q4_K: Q5_K 41943040 statt 4718592)", "blk.0.attn_qkv.weight (Q5_K: Q6_K 100663296 statt 11534336)", "blk.0.ffn_down_exps.weight (Q6_K: Q8_K 4294967296 statt 440401920)", "blk.0.ffn_down_shexp.weight (Q6_K: Q8_K 8388608 statt 860160)", "blk.0.ffn_gate_exps.weight (Q4_K: Q5_K 2684354560 statt 301989888)", "blk.0.ffn_gate_shexp.weight (MXFP4: IQ1_S_1 1048576 statt 557056)"], "anteil": "361/843"}
- **ende**: {"kandidat": [51766731776, 48528320544, false], "referenz": [48528320544, 48528320544, true]}

## synth_neu.gguf
- meta_typen: 2/2
- meta_skalare: 2/2
- meta_arrays: 0/0
- tensor_infos: 3/3
- **alignment_offset**: {"kandidat": [32, 288], "referenz": [64, 320]}
- **n_bytes**: {"falsch": ["tensor_00_tq1_0 (TQ1_0: IQ2_XS_8 1024 statt 108)", "tensor_01_tq2_0 (TQ2_0: IQ3_XS_4 2304 statt 198)", "tensor_02_mxfp4 (MXFP4: IQ1_S_1 128 statt 68)"], "anteil": "0/3"}
- **ende**: {"kandidat": [2432, 832, false], "referenz": [772, 832, true]}

## Teil B (von Hand gegen den Schlüssel bewerten)

- **W1** Wie groß ist das Alignment der Tensordaten in einer GGUF-Datei, wenn `general.alignment` fehlt?  
  → Fehlt das Feld `general.alignment` in einer GGUF-Datei, wird standardmäßig ein Alignment von 32 Bytes verwendet. Dies ist der in der GGUF-Spezifikation definierte Default-Wert für die Ausrichtung der Tensordaten.
- **W2** Welche numerischen Typ-IDs haben die GGUF-Metadaten-Werttypen STRING, ARRAY und FLOAT64?  
  → Die numerischen Typ-IDs für die GGUF-Metadaten-Werttypen sind: STRING = 8, ARRAY = 9 und FLOAT64 = 7.
- **W3** Wie viele Elemente umfasst ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K, und wie viele Bytes belegt ein Block jeweils?  
  → Ein Block bei Q4_K umfasst 256 Elemente und belegt 144 Bytes, während ein Block bei Q6_K ebenfalls 256 Elemente umfasst und 416 Bytes belegt.
- **W4** Welche ggml-Typ-IDs haben BF16 und Q8_0?  
  → Die ggml-Typ-ID für BF16 ist 24 und für Q8_0 ist sie 8.
- **W5** Welche ggml-Tensortyp-ID hat Q4_K_M?  
  → Die ggml-Tensortyp-ID für Q4_K_M ist 23.
- **W6** Welche Typ-ID hat der Metadaten-Werttyp FLOAT16 in GGUF?  
  → Die Typ-ID für den Metadaten-Werttyp FLOAT16 in GGUF ist 11.
- **W7** Worauf bezieht sich der Offset, der in der Tensor-Info einer GGUF-Datei steht?  
  → Der Offset in der Tensor-Info einer GGUF-Datei bezieht sich auf die absolute Byte-Position innerhalb der Datei, an der die eigentlichen Daten dieses Tensors beginnen. Er wird relativ zum Anfang der Datei gemessen und ermöglicht es, die binären Daten direkt aus dem Speicher oder der Datei zu lesen, ohne die gesamte Struktur parsen zu müssen.

