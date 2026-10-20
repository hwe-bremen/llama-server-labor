# Bewertung lauf2

Status: ok · Teil A: **27 / 32**

| Datei | kopf | meta_typen | meta_skalare | meta_arrays | tensor_infos | alignment_offset | n_bytes | ende | Summe |
|---|---|---|---|---|---|---|---|---|---|
| synth_klassisch.gguf | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | 6 |
| Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | 7 |
| Qwen3.6-27B-UD-Q4_K_XL.gguf | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | 7 |
| Qwen3-Coder-Next-Q4_K_M.gguf | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | 7 |
| synth_neu.gguf | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 7 |

## synth_klassisch.gguf
- meta_typen: 23/23
- meta_skalare: 15/15
- **meta_arrays**: {"falsch": ["t.arr_u8", "t.arr_i32", "t.arr_f32", "t.arr_str", "t.arr_bool"], "anteil": "0/8"}
- tensor_infos: 27/27
- n_bytes: 27/27
- **ende**: {"kandidat": [9832, 10624, false], "referenz": [10592, 10624, true]}

## Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf
- meta_typen: 43/43
- meta_skalare: 37/37
- **meta_arrays**: {"falsch": ["general.tags", "general.languages", "mellum.attention.sliding_window_pattern", "tokenizer.ggml.tokens", "tokenizer.ggml.token_type"], "anteil": "0/6"}
- tensor_infos: 339/339
- n_bytes: 339/339

## Qwen3.6-27B-UD-Q4_K_XL.gguf
- meta_typen: 52/52
- meta_skalare: 47/47
- **meta_arrays**: {"falsch": ["general.tags", "qwen35.rope.dimension_sections", "tokenizer.ggml.tokens", "tokenizer.ggml.token_type", "tokenizer.ggml.merges"], "anteil": "0/5"}
- tensor_infos: 866/866
- n_bytes: 866/866

## Qwen3-Coder-Next-Q4_K_M.gguf
- meta_typen: 53/53
- meta_skalare: 49/49
- **meta_arrays**: {"falsch": ["general.tags", "tokenizer.ggml.tokens", "tokenizer.ggml.token_type", "tokenizer.ggml.merges"], "anteil": "0/4"}
- tensor_infos: 843/843
- n_bytes: 843/843

## synth_neu.gguf
- meta_typen: 2/2
- meta_skalare: 2/2
- meta_arrays: 0/0
- tensor_infos: 3/3
- n_bytes: 3/3
- **ende**: {"kandidat": [694, 832, false], "referenz": [772, 832, true]}

