# Bewertung lauf2

Status: kein Code · Teil A: **0 / 32**

## Teil B (von Hand gegen den Schlüssel bewerten)

- **W1** Wie groß ist das Alignment der Tensordaten in einer GGUF-Datei, wenn `general.alignment` fehlt?  
  → Wenn `general.alignment` in einer GGUF-Datei fehlt, ist das Alignment standardmäßig **8**. Das ist der typische Wert für viele Modelle, der nicht explizit anders angegeben ist.
- **W2** Welche numerischen Typ-IDs haben die GGUF-Metadaten-Werttypen STRING, ARRAY und FLOAT64?  
  → Die GGUF-Metadaten-Werttypen haben folgende numerische Typ-IDs: - **STRING**: 1 - **ARRAY**: 2 - **FLOAT64**: 3 Diese IDs sind Teil der internen Spezifikation der GGUF-Dateiformat-Version.
- **W3** Wie viele Elemente umfasst ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K, und wie viele Bytes belegt ein Block jeweils?  
  → Ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K umfasst 16 Elemente. Bei Q4_K belegt ein Block 8 Bytes, bei Q6_K 12 Bytes.
- **W4** Welche ggml-Typ-IDs haben BF16 und Q8_0?  
  → BF16: Keine ggml-Typ-ID (ggml verwendet "f16" als Typ, aber keine spezifische ID). Q8_0: ggml_type_id = 12 (Q8_0 entspelt ggml-Typ "q8_0").
- **W5** Welche ggml-Tensortyp-ID hat Q4_K_M?  
  → Q4_K_M hat die ggml-Tensortyp-ID `Q4_K_M` (ggml-type 4).
- **W6** Welche Typ-ID hat der Metadaten-Werttyp FLOAT16 in GGUF?  
  → In GGUF ist der Metadaten-Werttyp FLOAT16 mit der Typ-ID **16**.
- **W7** Worauf bezieht sich der Offset, der in der Tensor-Info einer GGUF-Datei steht?  
  → Der Offset in der Tensor-Info einer GGUF-Datei bezieht sich auf den physischen Speicherort der Tensor-Daten im Dateibereich. Er definiert, ab welcher Byteposition in der Datei die konkreten Gewichtsdaten für einen bestimmten Tensor beginnen. Dieser Offset ist entscheidend, um die Tensor-Daten korrekt aus der Datei zu lesen, da er die relative Position des Speicherorts innerhalb der GGUF-Datei angibt.

