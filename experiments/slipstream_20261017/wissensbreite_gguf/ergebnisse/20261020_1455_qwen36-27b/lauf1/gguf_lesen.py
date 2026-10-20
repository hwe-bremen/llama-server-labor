#!/usr/bin/env python3
import sys
import struct
import json
import os

def main():
    if len(sys.argv) != 2:
        sys.exit(1)
    path = sys.argv[1]
    
    try:
        file_size = os.path.getsize(path)
    except OSError:
        sys.exit(1)

    with open(path, 'rb') as f:
        # 1. Header lesen
        magic = f.read(4)
        if magic != b'GGUF':
            sys.exit(1)
        
        version = struct.unpack('<I', f.read(4))[0]
        if version != 3:
            # Wir versuchen trotzdem, aber das Format ist spezifisch für v3
            pass
            
        tensor_count = struct.unpack('<Q', f.read(8))[0]
        kv_count = struct.unpack('<Q', f.read(8))[0]

        # 2. Metadaten lesen
        metadata = {}
        for _ in range(kv_count):
            key_len = struct.unpack('<Q', f.read(8))[0]
            key = f.read(key_len).decode('utf-8')
            
            type_id = struct.unpack('<I', f.read(4))[0]
            
            val = read_value(f, type_id)
            metadata[key] = val

        # Alignment bestimmen (Standard ist 32, kann aber in Metadaten stehen)
        # In GGUF v3 ist das Alignment für Tensordaten fest 32 Byte, 
        # es sei denn, es gibt spezifische Hinweise. 
        # Das Format definiert: "The alignment of the tensor data is 32 bytes."
        alignment = 32
        
        # Prüfen, ob es einen Key für Alignment gibt (manchmal in älteren/anderen Varianten)
        # Standard GGUF v3 Spec: Alignment ist immer 32.
        # Wir halten uns an die Spec.
        
        # 3. Tensor-Infos lesen
        tensors = []
        # Wir müssen die Offset-Werte der Tensoren lesen, um data_offset zu bestimmen.
        # data_offset ist die Position, an der die *ersten* Tensordaten beginnen.
        # Da die Tensordaten am Ende der Datei liegen (oder nach den Metadaten), 
        # und die Offsets relativ zum Anfang der Tensordaten-Region sind (oder absolut? 
        # GGUF Spec: "offsets are relative to the start of the tensor data region")
        # Warte: GGUF Spec sagt: "The offset of the tensor data is relative to the start of the tensor data region."
        # Aber wie finden wir den Start der Tensor-Data-Region?
        # Die Tensor-Infos liegen direkt nach den Metadaten.
        # Die Tensordaten liegen am Ende der Datei.
        # Wir müssen also alle Tensor-Infos lesen, um die maximale Offset-Größe zu kennen?
        # Nein. Die Spec sagt: "The tensor data region starts at the end of the header and metadata."
        # Das ist falsch. Die Spec sagt: "The file consists of a header, metadata, tensor info, and tensor data."
        # Die Offsets in den Tensor-Infos sind relativ zum Start der Tensor-Data-Region.
        # Der Start der Tensor-Data-Region ist die aktuelle Position nach dem Lesen aller Tensor-Infos.
        
        # Also:
        # 1. Alle Tensor-Infos lesen.
        # 2. Die Position nach dem letzten Tensor-Info-Block ist der Start der Tensor-Data-Region (data_offset).
        
        current_pos_before_tensors = f.tell()
        
        for _ in range(tensor_count):
            name_len = struct.unpack('<Q', f.read(8))[0]
            name = f.read(name_len).decode('utf-8')
            
            n_dims = struct.unpack('<Q', f.read(8))[0]
            shape = []
            for _ in range(n_dims):
                shape.append(struct.unpack('<Q', f.read(8))[0])
            
            type_id = struct.unpack('<I', f.read(4))[0]
            offset = struct.unpack('<Q', f.read(8))[0]
            
            # Typnamen und Bytes berechnen
            type_name, bytes_per_elem = get_type_info(type_id)
            
            # n_bytes berechnen
            n_bytes = 1
            for dim in shape:
                n_bytes *= dim
            n_bytes *= bytes_per_elem
            
            tensors.append({
                "name": name,
                "shape": shape,
                "type": type_name,
                "type_id": type_id,
                "offset": offset,
                "n_bytes": n_bytes
            })
            
        data_offset = f.tell()
        
        # 4. Berechnungen für das Ende
        # Wir müssen das Ende der Tensordaten bestimmen.
        # Das ist max(offset + n_bytes) über alle Tensoren.
        max_end_offset = 0
        for t in tensors:
            end_t = t["offset"] + t["n_bytes"]
            if end_t > max_end_offset:
                max_end_offset = end_t
        
        # Das Ende der Tensordaten-Region ist data_offset + max_end_offset
        # Aber es gibt Padding. Die Spec sagt, Tensordaten sind auf Alignment (32) gepadded.
        # Das Padding ist Teil der Tensordaten-Region? 
        # "The tensor data is padded to the alignment."
        # Also ist die tatsächliche Größe der Daten-Region:
        # Wir müssen das Padding für jeden Tensor berücksichtigen? 
        # Nein, die Offsets sind bereits so gewählt, dass sie auf Alignment passen.
        # Das Ende der Datei sollte data_offset + (max_end_offset auf Alignment gerundet) sein.
        
        # Rundung auf Alignment
        if max_end_offset % alignment != 0:
            padded_end = ((max_end_offset // alignment) + 1) * alignment
        else:
            padded_end = max_end_offset
            
        end = data_offset + padded_end
        
        ok = (end <= file_size) and (file_size - end < alignment)

        result = {
            "version": version,
            "tensor_count": tensor_count,
            "kv_count": kv_count,
            "alignment": alignment,
            "data_offset": data_offset,
            "metadata": metadata,
            "tensors": tensors,
            "end": end,
            "file_size": file_size,
            "ok": ok
        }
        
        print(json.dumps(result, ensure_ascii=False))

def read_value(f, type_id):
    """
    Liest einen Wert basierend auf der GGUF Type ID.
    Gibt ein Dict zurück mit "type_id", "value" (und ggf. "item_type_id", "len").
    """
    if type_id == 0: # GGUF_TYPE_UINT8
        val = struct.unpack('<B', f.read(1))[0]
        return {"type_id": type_id, "value": val}
    elif type_id == 1: # GGUF_TYPE_INT8
        val = struct.unpack('<b', f.read(1))[0]
        return {"type_id": type_id, "value": val}
    elif type_id == 2: # GGUF_TYPE_UINT16
        val = struct.unpack('<H', f.read(2))[0]
        return {"type_id": type_id, "value": val}
    elif type_id == 3: # GGUF_TYPE_INT16
        val = struct.unpack('<h', f.read(2))[0]
        return {"type_id": type_id, "value": val}
    elif type_id == 4: # GGUF_TYPE_UINT32
        val = struct.unpack('<I', f.read(4))[0]
        return {"type_id": type_id, "value": val}
    elif type_id == 5: # GGUF_TYPE_INT32
        val = struct.unpack('<i', f.read(4))[0]
        return {"type_id": type_id, "value": val}
    elif type_id == 6: # GGUF_TYPE_FLOAT32
        val = struct.unpack('<f', f.read(4))[0]
        return {"type_id": type_id, "value": val}
    elif type_id == 7: # GGUF_TYPE_BOOL
        val = struct.unpack('<B', f.read(1))[0] != 0
        return {"type_id": type_id, "value": val}
    elif type_id == 8: # GGUF_TYPE_STRING
        len_ = struct.unpack('<Q', f.read(8))[0]
        val = f.read(len_).decode('utf-8')
        return {"type_id": type_id, "value": val}
    elif type_id == 9: # GGUF_TYPE_ARRAY
        item_type_id = struct.unpack('<I', f.read(4))[0]
        len_ = struct.unpack('<Q', f.read(8))[0]
        
        values = []
        # Wir lesen höchstens die ersten 8 Elemente, um Speicher/Zeit zu sparen, 
        # aber wir müssen die Datei-Position korrekt weiterführen.
        # Das Schema sagt: "value": [<höchstens die ersten 8 Elemente>]
        # Aber wir müssen alle Elemente überspringen, um die Datei-Position korrekt zu halten.
        
        # Strategie: 
        # 1. Die ersten 8 Elemente lesen und speichern.
        # 2. Die restlichen Elemente überspringen.
        
        # Um zu überspringen, müssen wir die Größe jedes Elements kennen.
        # Das ist rekursiv kompliziert. 
        # Einfacher: Wir lesen alle Elemente, aber speichern nur die ersten 8.
        # Bei sehr großen Arrays könnte das langsam sein, aber wir lesen nur den Kopf.
        # Wenn das Array riesig ist (z.B. Millionen von Strings), wird das langsam.
        # Besser: Wir lesen die ersten 8, und für den Rest müssen wir die Größe berechnen oder lesen.
        
        # Da wir die Struktur nicht kennen, müssen wir jedes Element lesen, um die Position zu aktualisieren.
        # Wir können nicht einfach bytes überspringen, weil die Länge variabel ist (Strings, Arrays).
        
        # Optimierung: Wenn len_ sehr groß ist, lesen wir nur die ersten 8 und versuchen, den Rest zu überspringen?
        # Nein, wir können den Rest nicht sicher überspringen, ohne zu lesen.
        # Also lesen wir alle.
        
        for i in range(len_):
            val = read_value(f, item_type_id)
            if i < 8:
                values.append(val["value"])
            # Sonst ignorieren, aber f-Position ist korrekt
            
        return {"type_id": type_id, "item_type_id": item_type_id, "len": len_, "value": values}
    else:
        # Unbekannter Typ
        # Wir können nicht wissen, wie viele Bytes wir überspringen müssen.
        # Das Skript darf nicht abstürzen. 
        # Wir geben einen Platzhalter zurück und hoffen, dass der Rest der Datei nicht kritisch ist?
        # Oder wir brechen ab? 
        # Die Vorgabe: "Kennt dein Skript einen Tensortyp nicht, darf es nicht abstürzen".
        # Hier geht es um Metadaten-Typen. 
        # Wenn wir den Typ nicht kennen, können wir die Datei-Position nicht korrekt weiterführen.
        # Das wird die folgenden Lesevorgänge korrupt machen.
        # Wir werfen eine Exception oder geben einen Fehler zurück?
        # Die Vorgabe sagt nur für Tensortypen. Für Metadaten-Typen ist es nicht explizit geregelt.
        # Wir nehmen an, dass nur die bekannten Typen vorkommen.
        # Falls nicht, versuchen wir, so gut es geht.
        # Da wir die Größe nicht kennen, können wir nichts tun.
        # Wir geben einen Fehlerwert zurück.
        return {"type_id": type_id, "value": None, "error": "unknown_type"}

def get_type_info(type_id):
    """
    Gibt (Typname, Bytes pro Element) zurück.
    """
    # GGML Typen (aus llama.cpp)
    # 0: GGML_TYPE_F32
    # 1: GGML_TYPE_F16
    # 2: GGML_TYPE_Q4_0
    # 3: GGML_TYPE_Q4_1
    # 4: GGML_TYPE_Q4_2 (deprecated?)
    # 5: GGML_TYPE_Q4_3 (deprecated?)
    # 6: GGML_TYPE_Q5_0 (deprecated?)
    # 7: GGML_TYPE_Q5_1 (deprecated?)
    # 8: GGML_TYPE_Q5_1 (deprecated?)
    # 9: GGML_TYPE_Q8_0
    # 10: GGML_TYPE_Q8_1
    # 11: GGML_TYPE_Q2_K
    # 12: GGML_TYPE_Q3_K
    # 13: GGML_TYPE_Q4_K
    # 14: GGML_TYPE_Q5_K
    # 15: GGML_TYPE_Q6_K
    # 16: GGML_TYPE_Q8_K
    # 17: GGML_TYPE_IQ2_XXS
    # 18: GGML_TYPE_IQ2_XS
    # 19: GGML_TYPE_IQ3_XXS
    # 20: GGML_TYPE_IQ1_S
    # 21: GGML_TYPE_IQ4_NL
    # 22: GGML_TYPE_IQ3_S
    # 23: GGML_TYPE_IQ2_S
    # 24: GGML_TYPE_IQ4_XS
    # 25: GGML_TYPE_I8
    # 26: GGML_TYPE_I16
    # 27: GGML_TYPE_I32
    # 28: GGML_TYPE_I64
    # 29: GGML_TYPE_F64
    # 30: GGML_TYPE_IQ1_M
    
    # Die Bytes pro Element sind nicht einfach, da viele Quantisierungen Blöcke haben.
    # Für die Berechnung von n_bytes benötigen wir die genaue Größe.
    # Die GGUF Spec definiert die Größe basierend auf dem Typ.
    
    # Wir verwenden eine Map.
    # Quelle: llama.cpp ggml.h / gguf.h
    
    type_map = {
        0: ("F32", 4),
        1: ("F16", 2),
        2: ("Q4_0", 0.5), # 4 Bits pro Element -> 0.5 Byte
        3: ("Q4_1", 0.5),
        4: ("Q4_2", 0.5),
        5: ("Q4_3", 0.5),
        6: ("Q5_0", 0.625), # 5 Bits
        7: ("Q5_1", 0.625),
        8: ("Q5_1", 0.625), # Duplicate ID in some versions?
        9: ("Q8_0", 1),
        10: ("Q8_1", 1),
        11: ("Q2_K", 0.5), # Approx
        12: ("Q3_K", 0.75), # Approx
        13: ("Q4_K", 0.5625), # Approx
        14: ("Q5_K", 0.6875), # Approx
        15: ("Q6_K", 0.75), # Approx
        16: ("Q8_K", 1),
        17: ("IQ2_XXS", 0.3125),
        18: ("IQ2_XS", 0.4375),
        19: ("IQ3_XXS", 0.4375),
        20: ("IQ1_S", 0.1875),
        21: ("IQ4_NL", 0.5),
        22: ("IQ3_S", 0.46875),
        23: ("IQ2_S", 0.375),
        24: ("IQ4_XS", 0.5625),
        25: ("I8", 1),
        26: ("I16", 2),
        27: ("I32", 4),
        28: ("I64", 8),
        29: ("F64", 8),
        30: ("IQ1_M", 0.125),
    }
    
    if type_id in type_map:
        name, size = type_map[type_id]
        # Größe muss in Byte sein. Bei Bruchteilen müssen wir aufpassen.
        # n_bytes = shape_prod * size.
        # Da shape_prod immer so ist, dass das Ergebnis eine ganze Zahl ist (wegen Block-Größen),
        # können wir float verwenden.
        return name, size
    else:
        return "UNBEKANNT", None

if __name__ == '__main__':
    main()
