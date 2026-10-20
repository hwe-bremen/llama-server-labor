# Bewertung lauf1

Status: ok · Teil A: **0 / 32**

| Datei | kopf | meta_typen | meta_skalare | meta_arrays | tensor_infos | alignment_offset | n_bytes | ende | Summe |
|---|---|---|---|---|---|---|---|---|---|
| synth_klassisch.gguf | – | – | – | – | – | – | – | – | 0 |
| Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf | – | – | – | – | – | – | – | – | 0 |
| Qwen3.6-27B-UD-Q4_K_XL.gguf | – | – | – | – | – | – | – | – | 0 |
| Qwen3-Coder-Next-Q4_K_M.gguf | – | – | – | – | – | – | – | – | 0 |
| synth_neu.gguf | – | – | – | – | – | – | – | – | 0 |

## synth_klassisch.gguf

Fehler: `Exit 1: Traceback (most recent call last):
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1455_qwen36-27b/lauf1/gguf_lesen.py", line 325, in <module>
    main()
    ~~~~^^
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1455_qwen36-27b/lauf1/gguf_lesen.py", line 35, in main
    key = f.read(key_len).decode('utf-8')
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 22: invalid start byte`

## Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf

Fehler: `Exit 1: Traceback (most recent call last):
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1455_qwen36-27b/lauf1/gguf_lesen.py", line 325, in <module>
    main()
    ~~~~^^
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1455_qwen36-27b/lauf1/gguf_lesen.py", line 82, in main
    shape.append(struct.unpack('<Q', f.read(8))[0])
                 ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
struct.error: unpack requires a buffer of 8 bytes`

## Qwen3.6-27B-UD-Q4_K_XL.gguf

Fehler: `Zeitüberschreitung 120 s`

## Qwen3-Coder-Next-Q4_K_M.gguf

Fehler: `Zeitüberschreitung 120 s`

## synth_neu.gguf

Fehler: `Exit 1: Traceback (most recent call last):
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1455_qwen36-27b/lauf1/gguf_lesen.py", line 325, in <module>
    main()
    ~~~~^^
  File "/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/wissensbreite_gguf/ergebnisse/20261020_1455_qwen36-27b/lauf1/gguf_lesen.py", line 82, in main
    shape.append(struct.unpack('<Q', f.read(8))[0])
                 ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
struct.error: unpack requires a buffer of 8 bytes`

## Teil B (von Hand gegen den Schlüssel bewerten)

- **W1** Wie groß ist das Alignment der Tensordaten in einer GGUF-Datei, wenn `general.alignment` fehlt?  
  → Wenn das Feld `general.alignment` in einer GGUF-Datei fehlt, wird standardmäßig ein Alignment von 32 Byte verwendet. Dies ist der in der GGUF-Spezifikation definierte Default-Wert für die Ausrichtung der Tensordaten.
- **W2** Welche numerischen Typ-IDs haben die GGUF-Metadaten-Werttypen STRING, ARRAY und FLOAT64?  
  → In der GGUF-Spezifikation haben die Werttypen folgende numerischen IDs: STRING ist 2, ARRAY ist 7 und FLOAT64 ist 11.
- **W3** Wie viele Elemente umfasst ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K, und wie viele Bytes belegt ein Block jeweils?  
  → Bei den ggml-Quantisierungstypen Q4_K und Q6_K umfasst ein Block jeweils 256 Elemente. Ein Q4_K-Block belegt dabei 150 Bytes, während ein Q6_K-Block 188 Bytes benötigt.
- **W4** Welche ggml-Typ-IDs haben BF16 und Q8_0?  
  → Die ggml-Typ-ID für BF16 ist `GGML_TYPE_BF16` (numerisch 15), und die für Q8_0 ist `GGML_TYPE_Q8_0` (numerisch 10). Diese Werte können je nach Version der `ggml`-Bibliothek variieren, da die Enumerationswerte im Laufe der Zeit angepasst wurden.
- **W5** Welche ggml-Tensortyp-ID hat Q4_K_M?  
  → Die ggml-Tensortyp-ID für Q4_K_M ist 10. Dieser Wert entspricht der enum-Definition `GGML_TYPE_Q4_K_M` in der llama.cpp-Bibliothek.
- **W6** Welche Typ-ID hat der Metadaten-Werttyp FLOAT16 in GGUF?  
  → Der Metadaten-Werttyp `FLOAT16` in GGUF hat die Typ-ID 3. Dies entspricht der halben Genauigkeit (16-Bit-Float) gemäß dem IEEE 754-Standard.
- **W7** Worauf bezieht sich der Offset, der in der Tensor-Info einer GGUF-Datei steht?  
  → Der Offset in der Tensor-Info einer GGUF-Datei bezieht sich auf die Byte-Position innerhalb des Datenbereichs der Datei, an der die tatsächlichen Tensor-Daten beginnen. Dieser Wert ermöglicht es, die Daten direkt aus der Datei zu lesen, ohne sie vorher vollständig in den Arbeitsspeicher laden zu müssen.

