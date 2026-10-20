#!/usr/bin/env python3
import sys
import struct
import json
import os

def main():
    if len(sys.argv) != 2:
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        file_size = os.path.getsize(filepath)
    except OSError:
        sys.exit(1)

    try:
        with open(filepath, 'rb') as f:
            result = parse_gguf(f, file_size)
    except Exception:
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False))

def parse_gguf(f, file_size):
    # 1. Header lesen
    magic = f.read(4)
    if magic != b'GGUF':
        raise ValueError("Ungültige GGUF-Magic")
    
    version = struct.unpack('<I', f.read(4))[0]
    if version != 3:
        raise ValueError(f"Nur Version 3 unterstützt, gefunden: {version}")
    
    tensor_count = struct.unpack('<Q', f.read(8))[0]
    kv_count = struct.unpack('<Q', f.read(8))[0]
    
    # 2. Metadaten lesen
    metadata = {}
    for _ in range(kv_count):
        key_len = struct.unpack('<Q', f.read(8))[0]
        key = f.read(key_len).decode('utf-8')
        
        type_id = struct.unpack('<I', f.read(4))[0]
        value = read_value(f, type_id)
        
        metadata[key] = value

    # Alignment bestimmen (Standard 32, falls nicht in Metadata)
    alignment = 32
    if "general.alignment" in metadata:
        val = metadata["general.alignment"]
        if isinstance(val, dict) and "value" in val:
            alignment = val["value"]
        else:
            alignment = val

    # 3. Tensor-Infos lesen
    tensors = []
    for _ in range(tensor_count):
        name_len = struct.unpack('<Q', f.read(8))[0]
        name = f.read(name_len).decode('utf-8')
        
        n_dims = struct.unpack('<I', f.read(4))[0]
        shape = []
        for _ in range(n_dims):
            dim = struct.unpack('<Q', f.read(8))[0]
            shape.append(dim)
        
        type_id = struct.unpack('<I', f.read(4))[0]
        offset = struct.unpack('<Q', f.read(8))[0]
        
        type_name, n_bytes = get_tensor_info(type_id, shape)
        
        tensors.append({
            "name": name,
            "shape": shape,
            "type": type_name,
            "type_id": type_id,
            "offset": offset,
            "n_bytes": n_bytes
        })

    # 4. Daten-Offset und Ende berechnen
    # Der Offset der Tensordaten ist die aktuelle Position im Stream,
    # aufgerundet auf das Alignment.
    current_pos = f.tell()
    data_offset = align_up(current_pos, alignment)
    
    # Ende der Tensordaten berechnen
    # Wir müssen das Maximum aller (offset + n_bytes) finden.
    # Da die Offsets relativ zum data_offset sein können (oder absolut, je nach Interpretation, 
    # aber in GGUF v3 sind die Offsets in den Tensor-Infos absolut relativ zum Dateianfang? 
    # Nein, in GGUF v3 sind die Offsets in den Tensor-Infos relativ zum Anfang der Tensordaten?
    # Laut Spec: "The offset of the tensor data in the file." -> Absoluter Offset in der Datei.
    # Aber oft wird data_offset als Startpunkt definiert. 
    # In llama.cpp: tensor_info.offset ist relativ zum Anfang der Tensordaten? 
    # Nein, in der Spec steht: "offset: The offset of the tensor data in the file."
    # Das bedeutet absolut.
    
    max_end = 0
    for t in tensors:
        if t["n_bytes"] is not None:
            end = t["offset"] + t["n_bytes"]
            if end > max_end:
                max_end = end
    
    # Das Ende der Tensordaten muss auch auf das Alignment aufgerundet werden, 
    # wenn es das letzte Element ist, aber eigentlich ist "end" die Position direkt hinter dem letzten Byte.
    # Die Validierung "file_size - end < alignment" impliziert, dass end das Ende der nutzbaren Daten ist.
    # Wir nehmen das Maximum der Endpositionen aller Tensoren.
    
    end = max_end
    
    # Validierung
    ok = (end <= file_size) and ((file_size - end) < alignment)
    
    return {
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

def align_up(value, alignment):
    if alignment == 0:
        return value
    return (value + alignment - 1) // alignment * alignment

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
        # Nur die ersten 8 Elemente lesen, um Speicher/Zeit zu sparen bei großen Arrays
        limit = 8
        for i in range(len_):
            if i >= limit:
                # Rest überspringen
                # Wir müssen wissen, wie viele Bytes ein Element hat, um zu überspringen.
                # Das ist rekursiv kompliziert. 
                # Stattdessen: Wir lesen nur die ersten 8. Den Rest müssen wir überspringen.
                # Um den Rest zu überspringen, müssen wir die Größe der restlichen Elemente kennen.
                # Das ist bei variabler Länge (Strings, Arrays) schwierig.
                # Strategie: Wir lesen alle Elemente, aber speichern nur die ersten 8 im Output.
                # Aber die Anforderung sagt: "value": [<höchstens die ersten 8 Elemente>]
                # Und wir müssen den File-Pointer korrekt positionieren.
                # Also: Wir müssen alle Elemente durchgehen, um den Pointer zu bewegen.
                pass
            
            val = read_value(f, item_type_id)
            if i < limit:
                # Wir speichern den gesamten Wert-Objekt? 
                # Nein, das Schema sagt: "value": [<höchstens die ersten 8 Elemente>]
                # Was ist ein "Element"? Wenn es ein Array ist, ist das Element ein Dict.
                # Wenn es ein String ist, ist das Element ein String.
                # Das Schema für Arrays in metadata zeigt:
                # "<schluessel>": {"type_id": <int>, "item_type_id": <int>, "len": <int>, "value": [<höchstens die ersten 8 Elemente>]}
                # Also ist "value" eine Liste der Werte.
                # Wenn das Element selbst ein Array ist (verschachtelt), dann ist das Element ein Dict.
                values.append(val)
        
        return {
            "type_id": type_id,
            "item_type_id": item_type_id,
            "len": len_,
            "value": values
        }
    else:
        # Unbekannter Typ
        # Wir können nicht wissen, wie viele Bytes wir überspringen müssen.
        # Das Skript darf nicht abstürzen.
        # Wir geben einen Platzhalter zurück und hoffen, dass der Rest der Datei nicht kritisch ist,
        # oder wir brechen ab. Da wir aber den Pointer nicht korrekt verschieben können,
        # ist das Problematisch.
        # Für unbekannte Typen in Metadaten: Wir geben einen Fehlerwert zurück.
        # Da wir die Größe nicht kennen, können wir den Pointer nicht korrekt setzen.
        # Dies führt zu einem korrupten Parse.
        # Wir werfen eine Exception, die abgefangen wird.
        raise ValueError(f"Unbekannter Metadaten-Typ: {type_id}")

def get_tensor_info(type_id, shape):
    """
    Gibt (Typname, n_bytes) zurück.
    """
    # Bekannte GGML Typen (aus llama.cpp)
    # 0: GGML_TYPE_F32
    # 1: GGML_TYPE_F16
    # 2: GGML_TYPE_Q4_0
    # 3: GGML_TYPE_Q4_1
    # 4: GGML_TYPE_Q4_1_F16 (deprecated?)
    # 5: GGML_TYPE_Q4_2 (deprecated?)
    # 6: GGML_TYPE_Q4_3 (deprecated?)
    # 7: GGML_TYPE_Q5_0 (deprecated?)
    # 8: GGML_TYPE_Q5_1 (deprecated?)
    # 9: GGML_TYPE_Q5_1_F16 (deprecated?)
    # 10: GGML_TYPE_Q8_0
    # 11: GGML_TYPE_Q8_1
    # 12: GGML_TYPE_Q2_K
    # 13: GGML_TYPE_Q3_K
    # 14: GGML_TYPE_Q4_K
    # 15: GGML_TYPE_Q5_K
    # 16: GGML_TYPE_Q6_K
    # 17: GGML_TYPE_Q8_K
    # 18: GGML_TYPE_IQ2_XXS
    # 19: GGML_TYPE_IQ2_XS
    # 20: GGML_TYPE_IQ3_XXS
    # 21: GGML_TYPE_IQ1_S
    # 22: GGML_TYPE_IQ4_NL
    # 23: GGML_TYPE_IQ3_S
    # 24: GGML_TYPE_IQ2_S
    # 25: GGML_TYPE_IQ4_XS
    # 26: GGML_TYPE_I8
    # 27: GGML_TYPE_I16
    # 28: GGML_TYPE_I32
    # 29: GGML_TYPE_I64
    # 30: GGML_TYPE_F64
    # 31: GGML_TYPE_IQ1_M
    # 32: GGML_TYPE_BF16
    # ... und weitere
    
    # Blockgrößen und Bytes pro Block für Quantisierungstypen
    # Quelle: llama.cpp ggml.h
    
    type_info = {
        0: ("F32", 4, 1),       # float32
        1: ("F16", 2, 1),       # float16
        2: ("Q4_0", 2, 32),     # block_size 32, bytes_per_block 2 + 2 = 4? Nein. 
                                # Q4_0: 2 bytes scales, 16 bytes qs. Total 18? 
                                # In ggml.h: GGML_QK4_0 = 32. Size = (2 + 32/2) = 18? 
                                # Nein, die Struktur ist: int8_t qs[32/2]; int8_t d; 
                                # Actually: 
                                # typedef struct { 
                                #   ggml_fp16_t d; 
                                #   uint8_t qs[GGML_QK4_0/2]; 
                                # } block_q4_0; 
                                # Size = 2 + 16 = 18. 
                                # Aber ggml_type_size returns 18 for Q4_0? 
                                # Let's check standard sizes.
                                # Q4_0: 18 bytes per 32 elements.
        3: ("Q4_1", 2, 32),     # Q4_1: 2 bytes d, 2 bytes m, 16 bytes qs. Total 20? 
                                # typedef struct { 
                                #   ggml_fp16_t d, m; 
                                #   uint8_t qs[GGML_QK4_1/2]; 
                                # } block_q4_1; 
                                # Size = 2 + 2 + 16 = 20.
        10: ("Q8_0", 2, 32),    # Q8_0: 2 bytes d, 32 bytes qs. Total 34.
        11: ("Q8_1", 4, 32),    # Q8_1: 4 bytes d, 4 bytes m, 32 bytes qs. Total 40.
        12: ("Q2_K", 4, 256),   # Q2_K: block_size 256. Size = 78? 
        13: ("Q3_K", 4, 256),   # Q3_K: block_size 256. Size = 114?
        14: ("Q4_K", 4, 256),   # Q4_K: block_size 256. Size = 144?
        15: ("Q5_K", 4, 256),   # Q5_K: block_size 256. Size = 174?
        16: ("Q6_K", 4, 256),   # Q6_K: block_size 256. Size = 210?
        17: ("Q8_K", 4, 256),   # Q8_K: block_size 256. Size = 256?
        18: ("IQ2_XXS", 4, 256),
        19: ("IQ2_XS", 4, 256),
        20: ("IQ3_XXS", 4, 256),
        21: ("IQ1_S", 4, 256),
        22: ("IQ4_NL", 4, 256),
        23: ("IQ3_S", 4, 256),
        24: ("IQ2_S", 4, 256),
        25: ("IQ4_XS", 4, 256),
        26: ("I8", 1, 1),
        27: ("I16", 2, 1),
        28: ("I32", 4, 1),
        29: ("I64", 8, 1),
        30: ("F64", 8, 1),
        31: ("IQ1_M", 4, 256),
        32: ("BF16", 2, 1),
    }
    
    # Exakte Bytes pro Block für die gängigen Typen
    # Diese Werte müssen genau sein.
    bytes_per_block_map = {
        0: 4,   # F32
        1: 2,   # F16
        2: 18,  # Q4_0
        3: 20,  # Q4_1
        10: 34, # Q8_0
        11: 40, # Q8_1
        12: 78, # Q2_K
        13: 114,# Q3_K
        14: 144,# Q4_K
        15: 174,# Q5_K
        16: 210,# Q6_K
        17: 256,# Q8_K
        18: 78, # IQ2_XXS
        19: 90, # IQ2_XS
        20: 114,# IQ3_XXS
        21: 66, # IQ1_S
        22: 144,# IQ4_NL
        23: 126,# IQ3_S
        24: 90, # IQ2_S
        25: 156,# IQ4_XS
        26: 1,  # I8
        27: 2,  # I16
        28: 4,  # I32
        29: 8,  # I64
        30: 8,  # F64
        31: 70, # IQ1_M
        32: 2,  # BF16
    }
    
    block_size_map = {
        0: 1,
        1: 1,
        2: 32,
        3: 32,
        10: 32,
        11: 32,
        12: 256,
        13: 256,
        14: 256,
        15: 256,
        16: 256,
        17: 256,
        18: 256,
        19: 256,
        20: 256,
        21: 256,
        22: 256,
        23: 256,
        24: 256,
        25: 256,
        26: 1,
        27: 1,
        28: 1,
        29: 1,
        30: 1,
        31: 256,
        32: 1,
    }

    if type_id in type_info:
        name = type_info[type_id][0]
        bpb = bytes_per_block_map.get(type_id)
        bs = block_size_map.get(type_id)
        
        if bpb is None or bs is None:
            return name, None
            
        # Gesamtzahl der Elemente
        n_elements = 1
        for dim in shape:
            n_elements *= dim
            
        # Anzahl der Blöcke
        n_blocks = n_elements // bs
        
        # Restliche Elemente (falls nicht durch block_size teilbar)
        # Normalerweise sind Tensor-Größen durch Blockgrößen teilbar.
        # Wenn nicht, wird oft aufgerundet oder es gibt Padding.
        # Wir nehmen an, dass n_elements % bs == 0.
        
        n_bytes = n_blocks * bpb
        
        return name, n_bytes
    else:
        return "UNBEKANNT", None

if __name__ == "__main__":
    main()
