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

Fehler: `Exit 1:  | stdout: {"error": ""}`

## Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf

Fehler: `Exit 1:  | stdout: {"error": ""}`

## Qwen3.6-27B-UD-Q4_K_XL.gguf

Fehler: `Exit 1:  | stdout: {"error": ""}`

## Qwen3-Coder-Next-Q4_K_M.gguf

Fehler: `Exit 1:  | stdout: {"error": ""}`

## synth_neu.gguf

Fehler: `Exit 1:  | stdout: {"error": ""}`

## Teil B (von Hand gegen den Schlüssel bewerten)

- **W1** Wie groß ist das Alignment der Tensordaten in einer GGUF-Datei, wenn `general.alignment` fehlt?  
  → In einer GGUF-Datei beträgt das Alignment standardmäßig **32 Bytes**, wenn `general.alignment` nicht explizit gesetzt ist. Dies ist in der GGUF-Spezifikation festgelegt.
- **W2** Welche numerischen Typ-IDs haben die GGUF-Metadaten-Werttypen STRING, ARRAY und FLOAT64?  
  → In GGUF sind die Typ-IDs wie folgt definiert: - `STRING` hat die ID **0**, - `ARRAY` hat die ID **1**, - `FLOAT64` hat die ID **5**.
- **W3** Wie viele Elemente umfasst ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K, und wie viele Bytes belegt ein Block jeweils?  
  → Bei Q4_K umfasst ein Block 256 Elemente und belegt 144 Bytes. Bei Q6_K umfasst ein Block 256 Elemente und belegt 192 Bytes.
- **W4** Welche ggml-Typ-IDs haben BF16 und Q8_0?  
  → BF16 hat die ggml-Typ-ID `10`, Q8_0 hat die ID `8`.
- **W5** Welche ggml-Tensortyp-ID hat Q4_K_M?  
  → Die ggml-Tensortyp-ID für `Q4_K_M` ist **14**. Sie wird in der `ggml_type`-Enumeration in `ggml.h` definiert. Dieser Typ ist Teil der quantisierten 4-Bit-Modelle mit K-Methode (z. B. für LLaMA-Modelle).
- **W6** Welche Typ-ID hat der Metadaten-Werttyp FLOAT16 in GGUF?  
  → Der Metadaten-Werttyp `FLOAT16` hat in GGUF die Typ-ID **11**.
- **W7** Worauf bezieht sich der Offset, der in der Tensor-Info einer GGUF-Datei steht?  
  → Der Offset in der Tensor-Info einer GGUF-Datei gibt die Position (in Bytes) innerhalb der Datei an, ab der die Rohdaten des jeweiligen Tensors beginnen. Er dient dazu, den Speicherort der Tensor-Daten relativ zum Dateianfang zu bestimmen.

