# Bewertung lauf3

Status: kein Code · Teil A: **0 / 32**

## Teil B (von Hand gegen den Schlüssel bewerten)

- **W1** Wie groß ist das Alignment der Tensordaten in einer GGUF-Datei, wenn `general.alignment` fehlt?  
  → Wenn das Feld `general.alignment` in einer GGUF-Datei fehlt, wird standardmäßig ein Alignment von 32 Byte verwendet. Dies stellt sicher, dass die Tensordaten korrekt im Speicher ausgerichtet sind, um die Performance zu optimieren.
- **W2** Welche numerischen Typ-IDs haben die GGUF-Metadaten-Werttypen STRING, ARRAY und FLOAT64?  
  → In der GGUF-Spezifikation haben die Werttypen die folgenden numerischen IDs: STRING ist 2, ARRAY ist 7 und FLOAT64 ist 11.
- **W3** Wie viele Elemente umfasst ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K, und wie viele Bytes belegt ein Block jeweils?  
  → Bei Q4_K umfasst ein Block 256 Elemente und belegt 152 Bytes, während Q6_K ebenfalls 256 Elemente pro Block hat, aber 192 Bytes belegt. Beide Quantisierungstypen verwenden also die gleiche Blockgröße in Bezug auf die Anzahl der Elemente, unterscheiden sich jedoch in der Speichereffizienz und Genauigkeit.
- **W4** Welche ggml-Typ-IDs haben BF16 und Q8_0?  
  → Die ggml-Typ-ID für BF16 ist `GGML_TYPE_BF16` (numerisch 15), und die für Q8_0 ist `GGML_TYPE_Q8_0` (numerisch 10). Diese Werte können je nach Version der Bibliothek variieren, da die Enumerationswerte im Laufe der Zeit angepasst wurden.
- **W5** Welche ggml-Tensortyp-ID hat Q4_K_M?  
  → Die ggml-Tensortyp-ID für Q4_K_M ist 10. Dieser Wert ist in der `ggml.h`-Headerdatei der llama.cpp-Bibliothek definiert.
- **W6** Welche Typ-ID hat der Metadaten-Werttyp FLOAT16 in GGUF?  
  → Der Metadaten-Werttyp `FLOAT16` hat in GGUF die Typ-ID 1. Dieser Typ wird verwendet, um 16-Bit-Gleitkommazahlen im Format IEEE 754-2008 darzustellen.
- **W7** Worauf bezieht sich der Offset, der in der Tensor-Info einer GGUF-Datei steht?  
  → Der Offset in der Tensor-Info einer GGUF-Datei bezieht sich auf die Byte-Position relativ zum Anfang des Datenbereichs (Data Section) der Datei. Er gibt an, wo die tatsächlichen Tensor-Daten im Speicherlayout der Datei beginnen.

