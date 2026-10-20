# Bewertung lauf3

Status: kein Code · Teil A: **0 / 32**

## Teil B (von Hand gegen den Schlüssel bewerten)

- **W1** Wie groß ist das Alignment der Tensordaten in einer GGUF-Datei, wenn `general.alignment` fehlt?  
  → Fehlt das Feld `general.alignment` in einer GGUF-Datei, wird standardmäßig ein Alignment von 32 Bytes verwendet. Dies ist der in der GGUF-Spezifikation definierte Default-Wert für die Ausrichtung von Tensor-Daten.
- **W2** Welche numerischen Typ-IDs haben die GGUF-Metadaten-Werttypen STRING, ARRAY und FLOAT64?  
  → Die numerischen Typ-IDs für die GGUF-Metadaten-Werttypen sind: STRING = 8, ARRAY = 9 und FLOAT64 = 7.
- **W3** Wie viele Elemente umfasst ein Block bei den ggml-Quantisierungstypen Q4_K und Q6_K, und wie viele Bytes belegt ein Block jeweils?  
  → Ein Q4_K-Block umfasst 256 Elemente und belegt 144 Bytes, während ein Q6_K-Block ebenfalls 256 Elemente umfasst und 416 Bytes belegt.
- **W4** Welche ggml-Typ-IDs haben BF16 und Q8_0?  
  → Die genaue Zuordnung der numerischen IDs für BF16 und Q8_0 ist in der ggml-Quellcode-Definition (ggml.h) festgelegt, wobei BF16 typischerweise die ID 14 und Q8_0 die ID 8 hat. Da sich diese Werte mit neuen Versionen der Bibliothek ändern können, ist eine direkte Prüfung der aktuellen Header-Datei erforderlich, um die korrekten Werte für dein spezifisches Setup zu bestätigen.
- **W5** Welche ggml-Tensortyp-ID hat Q4_K_M?  
  → Die ggml-Tensortyp-ID für Q4_K_M ist 23.
- **W6** Welche Typ-ID hat der Metadaten-Werttyp FLOAT16 in GGUF?  
  → Die Typ-ID für den Metadaten-Werttyp FLOAT16 in GGUF ist 12.
- **W7** Worauf bezieht sich der Offset, der in der Tensor-Info einer GGUF-Datei steht?  
  → Der Offset in der Tensor-Info einer GGUF-Datei bezieht sich auf die absolute Byte-Position innerhalb der Datei, an der die eigentlichen Daten des Tensors beginnen. Er wird relativ zum Anfang der Datei gemessen und dient dazu, die Speicherorte der Tensor-Daten im Binärformat zu identifizieren.

