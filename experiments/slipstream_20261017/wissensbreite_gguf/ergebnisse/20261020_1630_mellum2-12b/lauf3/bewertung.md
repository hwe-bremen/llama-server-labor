# Bewertung lauf3

Status: ok · Teil A: **0 / 32**

| Datei | kopf | meta_typen | meta_skalare | meta_arrays | tensor_infos | alignment_offset | n_bytes | ende | Summe |
|---|---|---|---|---|---|---|---|---|---|
| synth_klassisch.gguf | – | – | – | – | – | – | – | – | 0 |
| Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf | – | – | – | – | – | – | – | – | 0 |
| Qwen3.6-27B-UD-Q4_K_XL.gguf | – | – | – | – | – | – | – | – | 0 |
| Qwen3-Coder-Next-Q4_K_M.gguf | – | – | – | – | – | – | – | – | 0 |
| synth_neu.gguf | – | – | – | – | – | – | – | – | 0 |

## synth_klassisch.gguf

Fehler: `Exit 1: File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1630_mellum2-12b/lauf3/gguf_lesen.py", line 335, in <module>
    main()
    ~~~~^^
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1630_mellum2-12b/lauf3/gguf_lesen.py", line 330, in main
    print(json.dumps({"error": str(e)}), ensure_ascii=False)
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: print() got an unexpected keyword argument 'ensure_ascii'`

## Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf

Fehler: `Exit 1: File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1630_mellum2-12b/lauf3/gguf_lesen.py", line 335, in <module>
    main()
    ~~~~^^
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1630_mellum2-12b/lauf3/gguf_lesen.py", line 330, in main
    print(json.dumps({"error": str(e)}), ensure_ascii=False)
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: print() got an unexpected keyword argument 'ensure_ascii'`

## Qwen3.6-27B-UD-Q4_K_XL.gguf

Fehler: `Exit 1: File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1630_mellum2-12b/lauf3/gguf_lesen.py", line 335, in <module>
    main()
    ~~~~^^
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1630_mellum2-12b/lauf3/gguf_lesen.py", line 330, in main
    print(json.dumps({"error": str(e)}), ensure_ascii=False)
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: print() got an unexpected keyword argument 'ensure_ascii'`

## Qwen3-Coder-Next-Q4_K_M.gguf

Fehler: `Exit 1: File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1630_mellum2-12b/lauf3/gguf_lesen.py", line 335, in <module>
    main()
    ~~~~^^
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1630_mellum2-12b/lauf3/gguf_lesen.py", line 330, in main
    print(json.dumps({"error": str(e)}), ensure_ascii=False)
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: print() got an unexpected keyword argument 'ensure_ascii'`

## synth_neu.gguf

Fehler: `Exit 1: File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1630_mellum2-12b/lauf3/gguf_lesen.py", line 335, in <module>
    main()
    ~~~~^^
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1630_mellum2-12b/lauf3/gguf_lesen.py", line 330, in main
    print(json.dumps({"error": str(e)}), ensure_ascii=False)
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: print() got an unexpected keyword argument 'ensure_ascii'`

## Teil B (von Hand gegen den Schlüssel bewerten)

- **W1** Wie groß ist das Alignment der Tensordaten in einer GGUF-Datei, wenn `general.alignment` fehlt?  
  → Wenn `general.alignment` in einer GGUF-Datei fehlt, ist das Alignment standardmäßig 8. Dies ist der typische Wert, wenn keine spezifische Angabe im Header vorliegt.
- **W2** Welche numerischen Typ-IDs haben die GGUF-Metadaten-Werttypen STRING, ARRAY und FLOAT64?  
  → Die GGUF-Metadaten-Werttypen haben folgende numerische Typ-IDs: - **STRING**: `1` - **ARRAY**: `2` - **FLOAT64**: `3`
- **W3** Wie viele Elemente umfasst ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K, und wie viele Bytes belegt ein Block jeweils?  
  → Ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K umfasst 4 oder 6 Bits. Da ein Byte 8 Bits hat, belegt ein Block Q4_K 0,5 Byte und ein Block Q6_K 0,75 Byte.
- **W4** Welche ggml-Typ-IDs haben BF16 und Q8_0?  
  → BF16: 1 Q8_0: 2
- **W5** Welche ggml-Tensortyp-ID hat Q4_K_M?  
  → Q4_K_M hat die ggml-Tensortyp-ID 19.
- **W6** Welche Typ-ID hat der Metadaten-Werttyp FLOAT16 in GGUF?  
  → In GGUF ist der Metadaten-Werttyp FLOAT16 mit der Typ-ID **1**.
- **W7** Worauf bezieht sich der Offset, der in der Tensor-Info einer GGUF-Datei steht?  
  → Der Offset in der Tensor-Info einer GGUF-Datei bezieht sich auf die Position (im Dateistream) der GPUTransition-Tabelle, die für die Tensor-Konfiguration steht. Diese Tabelle enthält Informationen, wie die GPUTransition-Parameter für verschiedene Tensor-Layer-Konfigurationen verwaltet werden.

