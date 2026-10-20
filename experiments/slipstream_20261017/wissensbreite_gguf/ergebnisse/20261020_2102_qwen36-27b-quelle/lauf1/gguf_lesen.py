import sys
import os
import json
import struct

# --- Konfiguration & Konstanten ---

# ggml-Tensortypen: ID -> (Name, Elemente je Block, Bytes je Block)
# Basierend auf der Referenz und gängigen llama.cpp Definitionen.
GGML_TYPES = {
    0:  ("F32", 1, 4),
    1:  ("F16", 1, 2),
    2:  ("Q4_0", 32, 18),
    3:  ("Q4_1", 32, 20),
    6:  ("Q5_0", 32, 22),
    7:  ("Q5_1", 32, 24),
    8:  ("Q8_0", 32, 34),
    9:  ("Q8_1", 32, 40),
    10: ("Q2_K", 256, 84),
    11: ("Q3_K", 256, 110),
    12: ("Q4_K", 256, 144),
    13: ("Q5_K", 256, 176),
    14: ("Q6_K", 256, 210),
    15: ("Q8_K", 256, 292),
    16: ("IQ2_XXS", 256, 66),
    17: ("IQ2_XS", 256, 74),
    18: ("IQ3_XXS", 256, 98),
    19: ("IQ1_S", 256, 50),
    20: ("IQ4_NL", 32, 18),
    21: ("IQ3_S", 256, 110),
    22: ("IQ2_S", 256, 82),
    23: ("IQ4_XS", 256, 136),
    24: ("I8", 1, 1),
    25: ("I16", 1, 2),
    26: ("I32", 1, 4),
    27: ("I64", 1, 8),
    28: ("F64", 1, 8),
    29: ("IQ1_M", 256, 56),
    30: ("BF16", 1, 2),
    34: ("TQ1_0", 256, 54),
    35: ("TQ2_0", 256, 66),
    39: ("MXFP4", 32, 17),
    40: ("NVFP4", 64, 36),
    41: ("Q1_0", 128, 18),
    42: ("Q2_0", 64, 18),
}

# Metadaten-Typen: ID -> (Name, Format-String für struct, Größe in Byte)
# BOOL ist 1 Byte. STRING und ARRAY werden separat behandelt.
META_TYPES = {
    0:  ("UINT8", "B", 1),
    1:  ("INT8", "b", 1),
    2:  ("UINT16", "H", 2),
    3:  ("INT16", "h", 2),
    4:  ("UINT32", "I", 4),
    5:  ("INT32", "i", 4),
    6:  ("FLOAT32", "f", 4),
    7:  ("BOOL", "B", 1),
    8:  ("STRING", None, None),
    9:  ("ARRAY", None, None),
    10: ("UINT64", "Q", 8),
    11: ("INT64", "q", 8),
    12: ("FLOAT64", "d", 8),
}

def read_gguf(path):
    try:
        file_size = os.path.getsize(path)
    except OSError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    with open(path, "rb") as f:
        # 1. Magic
        magic = f.read(4)
        if magic != b'GGUF':
            print(json.dumps({"error": "Invalid magic"}))
            sys.exit(1)
        
        # 2. Version
        version = struct.unpack('<I', f.read(4))[0]
        
        # 3. Counts
        tensor_count = struct.unpack('<Q', f.read(8))[0]
        kv_count = struct.unpack('<Q', f.read(8))[0]
        
        # 4. Metadata
        metadata = {}
        alignment = 32 # Default
        
        for _ in range(kv_count):
            # Key
            key_len = struct.unpack('<Q', f.read(8))[0]
            key = f.read(key_len).decode('utf-8')
            
            # Type ID
            type_id = struct.unpack('<I', f.read(4))[0]
            
            # Value
            if type_id == 8: # STRING
                val_len = struct.unpack('<Q', f.read(8))[0]
                val = f.read(val_len).decode('utf-8')
                metadata[key] = {"type_id": type_id, "value": val}
            elif type_id == 9: # ARRAY
                item_type_id = struct.unpack('<I', f.read(4))[0]
                array_len = struct.unpack('<Q', f.read(8))[0]
                
                # Wir lesen nur die ersten 8 Elemente für die Ausgabe, 
                # müssen aber alle überspringen, um den Pointer korrekt zu halten.
                # Um den Pointer korrekt zu halten, müssen wir die Größe jedes Elements kennen.
                # Da wir verschachtelte Arrays unterstützen müssen, ist das rekursiv komplex.
                # Strategie: Wir lesen die Elemente einzeln und überspringen sie, 
                # aber speichern nur die ersten 8.
                
                values_preview = []
                
                for i in range(array_len):
                    # Prüfen, ob wir noch im Preview-Bereich sind
                    is_preview = len(values_preview) < 8
                    
                    # Element lesen/überspringen
                    # Wir brauchen eine Funktion, die ein Element liest und seine Größe zurückgibt,
                    # oder direkt den File-Pointer bewegt.
                    # Da wir den File-Pointer bewegen müssen, ist eine rekursive Funktion, die 
                    # (value, size) zurückgibt, am sichersten.
                    
                    if is_preview:
                        val, _ = read_meta_element(f, item_type_id)
                        values_preview.append(val)
                    else:
                        _, size = read_meta_element(f, item_type_id)
                        # Da read_meta_element den Pointer bereits bewegt hat, müssen wir nichts tun.
                        # Aber wait: read_meta_element muss den Pointer bewegen.
                        # Meine Implementierung von read_meta_element bewegt den Pointer.
                        pass

                metadata[key] = {
                    "type_id": type_id,
                    "item_type_id": item_type_id,
                    "len": array_len,
                    "value": values_preview
                }
            else:
                # Scalar
                type_info = META_TYPES.get(type_id)
                if type_info:
                    fmt = type_info[1]
                    size = type_info[2]
                    raw = f.read(size)
                    val = struct.unpack('<' + fmt, raw)[0]
                    
                    # BOOL Konvertierung
                    if type_id == 7:
                        val = bool(val)
                        
                    metadata[key] = {"type_id": type_id, "value": val}
                else:
                    # Unbekannter Typ -> Überspringen? 
                    # Das Format definiert keine unbekannten Skalartypen.
                    # Falls doch, können wir nicht wissen, wie groß er ist.
                    # Wir gehen davon aus, dass nur die definierten Typen vorkommen.
                    # Falls nicht, ist die Datei kaputt oder wir haben einen Fehler.
                    # Um robust zu sein: Wenn wir den Typ nicht kennen, können wir nicht weitermachen.
                    # Aber die Vorgabe sagt: "Kennt dein Skript einen Tensortyp nicht...". 
                    # Für Metadata gibt es keine explizite Vorgabe für unbekannte Typen.
                    # Wir nehmen an, dass nur die gelisteten Typen vorkommen.
                    pass

            # Alignment Check für general.alignment
            if key == "general.alignment":
                if isinstance(metadata[key]["value"], (int, float)):
                    alignment = int(metadata[key]["value"])

        # 5. Tensors
        tensors = []
        for _ in range(tensor_count):
            # Name
            name_len = struct.unpack('<Q', f.read(8))[0]
            name = f.read(name_len).decode('utf-8')
            
            # N-Dims
            n_dims = struct.unpack('<I', f.read(4))[0]
            
            # Shape
            shape = []
            for _ in range(n_dims):
                dim = struct.unpack('<Q', f.read(8))[0]
                shape.append(dim)
                
            # Type ID
            type_id = struct.unpack('<I', f.read(4))[0]
            
            # Offset
            offset = struct.unpack('<Q', f.read(8))[0]
            
            # Tensor Info
            type_info = GGML_TYPES.get(type_id)
            if type_info:
                t_name, elems_per_block, bytes_per_block = type_info
                # n_bytes berechnen
                # Anzahl Elemente = Produkt der Shape-Dimensionen
                num_elements = 1
                for d in shape:
                    num_elements *= d
                
                # n_bytes = (num_elements / elems_per_block) * bytes_per_block
                # Da num_elements immer durch elems_per_block teilbar sein sollte bei korrekten Daten:
                n_bytes = (num_elements // elems_per_block) * bytes_per_block
                
                tensors.append({
                    "name": name,
                    "shape": shape,
                    "type": t_name,
                    "type_id": type_id,
                    "offset": offset,
                    "n_bytes": n_bytes
                })
            else:
                # Unbekannter Tensortyp
                tensors.append({
                    "name": name,
                    "shape": shape,
                    "type": "UNBEKANNT",
                    "type_id": type_id,
                    "offset": offset,
                    "n_bytes": None
                })

        # 6. Data Offset & End
        # Der aktuelle File-Pointer ist direkt nach den Tensor-Infos.
        # Das ist der Beginn des Puffers für die Tensordaten, aber noch vor dem Alignment-Padding.
        # "data_offset" ist die absolute Dateiposition, an der die Tensordaten beginnen.
        # Das bedeutet: data_offset = current_pos + padding
        
        current_pos = f.tell()
        
        # Padding berechnen
        # Alignment ist die Größe, auf die aufgerundet werden muss.
        # padding = (alignment - (current_pos % alignment)) % alignment
        padding = (alignment - (current_pos % alignment)) % alignment
        
        data_offset = current_pos + padding
        
        # "end" ist die absolute Dateiposition direkt hinter dem letzten Byte der Tensordaten.
        # Wir müssen das Maximum aus (offset + n_bytes) für alle Tensoren finden.
        # Achtung: offset ist relativ zum data_offset.
        
        max_end_offset = 0
        for t in tensors:
            if t["n_bytes"] is not None:
                end_rel = t["offset"] + t["n_bytes"]
                if end_rel > max_end_offset:
                    max_end_offset = end_rel
            else:
                # Wenn n_bytes null ist, können wir das Ende nicht genau bestimmen.
                # Wir nehmen an, dass es innerhalb der Datei liegt, oder ignorieren es für die Berechnung von 'end'?
                # Die Vorgabe sagt: "end: absolute Dateiposition direkt hinter dem letzten Byte der Tensordaten".
                # Wenn wir es nicht wissen, können wir es nicht genau angeben.
                # Wir setzen es auf 0 oder ignorieren es? 
                # Wenn ein Tensor unbekannt ist, ist die Validierung schwierig.
                # Wir nehmen das Maximum der bekannten. Wenn alle unbekannt, 0.
                pass
        
        end = data_offset + max_end_offset
        
        # Ausgabe zusammenstellen
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
            "ok": end <= file_size and (file_size - end) < alignment
        }
        
        print(json.dumps(result, ensure_ascii=False))

def read_meta_element(f, type_id):
    """
    Liest ein einzelnes Metadaten-Element vom Typ type_id.
    Gibt (value, size) zurück, wobei size die Anzahl der gelesenen Bytes ist.
    value ist der Python-Wert (oder None, wenn wir ihn nicht speichern wollen, aber wir brauchen ihn für Preview).
    """
    if type_id == 8: # STRING
        len_bytes = f.read(8)
        if not len_bytes:
            return None, 0
        val_len = struct.unpack('<Q', len_bytes)[0]
        val = f.read(val_len).decode('utf-8')
        return val, 8 + val_len
        
    elif type_id == 9: # ARRAY
        # Array Header: item_type_id (4) + len (8)
        header = f.read(12)
        if not header:
            return None, 0
        item_type_id = struct.unpack('<I', header[:4])[0]
        array_len = struct.unpack('<Q', header[4:])[0]
        
        # Elemente lesen
        # Wir geben das Array als Objekt zurück, wie in der Vorgabe gefordert:
        # {"item_type_id": ..., "len": ..., "value": [...]}
        # Aber wait: Die Vorgabe für verschachtelte Arrays im Metadata-Wert ist:
        # "Verschachtelte Arrays (Array von Arrays) müssen gelesen werden können; 
        #  ein inneres Array wird als Objekt mit item_type_id, len, value dargestellt."
        
        # Wir müssen also die Elemente rekursiv lesen.
        elements = []
        total_size = 12 # Header
        
        for _ in range(array_len):
            elem_val, elem_size = read_meta_element(f, item_type_id)
            elements.append(elem_val)
            total_size += elem_size
            
        val = {
            "item_type_id": item_type_id,
            "len": array_len,
            "value": elements
        }
        return val, total_size
        
    else:
        # Scalar
        type_info = META_TYPES.get(type_id)
        if type_info:
            fmt = type_info[1]
            size = type_info[2]
            raw = f.read(size)
            if not raw:
                return None, 0
            val = struct.unpack('<' + fmt, raw)[0]
            if type_id == 7:
                val = bool(val)
            return val, size
        else:
            # Unbekannter Typ
            return None, 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python3 gguf_lesen.py <pfad>"}))
        sys.exit(1)
        
    path = sys.argv[1]
    read_gguf(path)
