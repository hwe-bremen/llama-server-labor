## Referenz zum Format (aus gguf-py, llama.cpp)

Alle Zahlen little-endian. `str` = u64 Länge in Byte, danach UTF-8-Bytes (ohne Nullbyte).

Dateiaufbau:
1. Magic: 4 Byte `GGUF` (als u32: 0x46554747)
2. u32 Version
3. u64 Anzahl Tensoren, u64 Anzahl Schlüssel-Wert-Paare
4. Je Schlüssel-Wert-Paar: `str` Schlüssel, u32 Werttyp-ID, Wert
   - Skalar: Wert in der Größe des Typs (BOOL = 1 Byte, 0 oder 1)
   - STRING: `str`
   - ARRAY: u32 Elementtyp-ID, u64 Anzahl, danach die Elemente ohne eigene Typ-ID
     (Elemente vom Typ ARRAY tragen wieder u32 Elementtyp-ID + u64 Anzahl)
5. Je Tensor: `str` Name, u32 Anzahl Dimensionen, je Dimension u64, u32 ggml-Typ-ID, u64 Offset
6. Danach Auffüllung bis zur nächsten durch das Alignment teilbaren Position: dort beginnen die Tensordaten.
   Alignment = Wert von `general.alignment` (UINT32), wenn vorhanden, sonst 32.
7. Der Offset eines Tensors zählt ab dem Beginn der Tensordaten (nicht ab Dateianfang).
8. Größe eines Tensors in Byte = Anzahl Elemente × Bytes je Block ÷ Elemente je Block.

Werttyp-IDs (Metadaten):

| ID | Typ |
|---|---|
| 0 | UINT8 |
| 1 | INT8 |
| 2 | UINT16 |
| 3 | INT16 |
| 4 | UINT32 |
| 5 | INT32 |
| 6 | FLOAT32 |
| 7 | BOOL |
| 8 | STRING |
| 9 | ARRAY |
| 10 | UINT64 |
| 11 | INT64 |
| 12 | FLOAT64 |

ggml-Tensortypen:

| ID | Name | Elemente je Block | Bytes je Block |
|---|---|---|---|
| 0 | F32 | 1 | 4 |
| 1 | F16 | 1 | 2 |
| 2 | Q4_0 | 32 | 18 |
| 3 | Q4_1 | 32 | 20 |
| 6 | Q5_0 | 32 | 22 |
| 7 | Q5_1 | 32 | 24 |
| 8 | Q8_0 | 32 | 34 |
| 9 | Q8_1 | 32 | 40 |
| 10 | Q2_K | 256 | 84 |
| 11 | Q3_K | 256 | 110 |
| 12 | Q4_K | 256 | 144 |
| 13 | Q5_K | 256 | 176 |
| 14 | Q6_K | 256 | 210 |
| 15 | Q8_K | 256 | 292 |
| 16 | IQ2_XXS | 256 | 66 |
| 17 | IQ2_XS | 256 | 74 |
| 18 | IQ3_XXS | 256 | 98 |
| 19 | IQ1_S | 256 | 50 |
| 20 | IQ4_NL | 32 | 18 |
| 21 | IQ3_S | 256 | 110 |
| 22 | IQ2_S | 256 | 82 |
| 23 | IQ4_XS | 256 | 136 |
| 24 | I8 | 1 | 1 |
| 25 | I16 | 1 | 2 |
| 26 | I32 | 1 | 4 |
| 27 | I64 | 1 | 8 |
| 28 | F64 | 1 | 8 |
| 29 | IQ1_M | 256 | 56 |
| 30 | BF16 | 1 | 2 |
| 34 | TQ1_0 | 256 | 54 |
| 35 | TQ2_0 | 256 | 66 |
| 39 | MXFP4 | 32 | 17 |
| 40 | NVFP4 | 64 | 36 |
| 41 | Q1_0 | 128 | 18 |
| 42 | Q2_0 | 64 | 18 |
