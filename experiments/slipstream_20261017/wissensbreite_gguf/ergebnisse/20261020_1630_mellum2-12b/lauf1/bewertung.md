# Bewertung lauf1

Status: kein Code · Teil A: **0 / 32**

## Teil B (von Hand gegen den Schlüssel bewerten)

- **W1** Wie groß ist das Alignment der Tensordaten in einer GGUF-Datei, wenn `general.alignment` fehlt?  
  → Wenn `general.alignment` in einer GGUF-Datei fehlt, ist das Alignment standardmäßig **8-basiert** (8-bit alignment). Das bedeutet, dass die Tensordaten in Blöcken von 8 Elementen gruppiert sind, was die Speicherlayout-Kompatibilität und die Performance bei der Verarbeitung durch die Inference-Engine sicherstellt. Dieser Standard ist bewährert und wird von den meisten GGUF-Implementierungen verwendet, solange keine explizite Angabe im Header vorliegt.
- **W2** Welche numerischen Typ-IDs haben die GGUF-Metadaten-Werttypen STRING, ARRAY und FLOAT64?  
  → Die GGUF-Metadaten-Werttypen haben folgende numerische Typ-IDs: - **STRING**: `1` - **ARRAY**: `2` - **FLOAT64**: `3`
- **W3** Wie viele Elemente umfasst ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K, und wie viele Bytes belegt ein Block jeweils?  
  → Ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K umfasst 4 oder 6 Bits. Da ein Byte 8 Bits hat, entspricht 4 Bits 0,5 Byte und 6 Bits 0,75 Byte. Antwort: Q4_K: 0,5 Byte pro Block; Q6_K: 0,75 Byte pro Block.
- **W4** Welche ggml-Typ-IDs haben BF16 und Q8_0?  
  → BF16: 1 Q8_0: 2
- **W5** Welche ggml-Tensortyp-ID hat Q4_K_M?  
  → Q4_K_M verwendet den ggml-Tensortyp-ID "Q4_K_M".
- **W6** Welche Typ-ID hat der Metadaten-Werttyp FLOAT16 in GGUF?  
  → In GGUF ist der Metadaten-Werttyp FLOAT16 mit der Typ-ID `0x0001` kodiert.
- **W7** Worauf bezieht sich der Offset, der in der Tensor-Info einer GGUF-Datei steht?  
  → Der Offset in der Tensor-Info einer GGUF-Datei bezieht sich auf den physischen Speicherort der Tensor-Daten im Dateistream. Er gibt an, ab welcher Byteposition in der Datei die konkreten Gewichtsdaten für diesen Tensor beginnen. Dieser Offset ist wichtig, um die Tensor-Daten korrekt aus der Datei zu lesen, da er die relative Positionierung innerhalb des gesamten Dateistreams angibt.

