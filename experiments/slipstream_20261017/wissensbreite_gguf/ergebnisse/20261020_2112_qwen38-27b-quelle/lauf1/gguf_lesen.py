#!/usr/bin/env python3
import sys
import json
import struct
import math

# ggml tensor types: id -> (name, elements_per_block, bytes_per_block)
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

# Metadata value type IDs
# 0: UINT8, 1: INT8, 2: UINT16, 3: INT16, 4: UINT32, 5: INT32,
# 6: FLOAT32, 7: BOOL, 8: STRING, 9: ARRAY, 10: UINT64, 11: INT64, 12: FLOAT64

SCALAR_STRUCT_FORMATS = {
    0:  ('<B', 1),   # UINT8
    1:  ('<b', 1),   # INT8
    2:  ('<H', 2),   # UINT16
    3:  ('<h', 2),   # INT16
    4:  ('<I', 4),   # UINT32
    5:  ('<i', 4),   # INT32
    6:  ('<f', 4),   # FLOAT32
    7:  ('<B', 1),   # BOOL (stored as 0 or 1)
    10: ('<Q', 8),   # UINT64
    11: ('<q', 8),   # INT64
    12: ('<d', 8),   # FLOAT64
}

def read_u8(f):
    b = f.read(1)
    if len(b) != 1:
        raise EOFError("unexpected end of file")
    return b[0]

def read_u16(f):
    b = f.read(2)
    if len(b) != 2:
        raise EOFError("unexpected end of file")
    return struct.unpack('<H', b)[0]

def read_u32(f):
    b = f.read(4)
    if len(b) != 4:
        raise EOFError("unexpected end of file")
    return struct.unpack('<I', b)[0]

def read_u64(f):
    b = f.read(8)
    if len(b) != 8:
        raise EOFError("unexpected end of file")
    return struct.unpack('<Q', b)[0]

def read_str(f):
    length = read_u64(f)
    data = f.read(length)
    if len(data) != length:
        raise EOFError("unexpected end of file while reading string")
    return data.decode('utf-8')

def read_scalar_value(f, type_id):
    """Read a scalar value of the given metadata type ID. Returns the Python value."""
    if type_id in SCALAR_STRUCT_FORMATS:
        fmt, size = SCALAR_STRUCT_FORMATS[type_id]
        data = f.read(size)
        if len(data) != size:
            raise EOFError("unexpected end of file while reading scalar")
        val = struct.unpack(fmt, data)[0]
        if type_id == 7:  # BOOL
            return bool(val)
        return val
    elif type_id == 8:  # STRING
        return read_str(f)
    else:
        raise ValueError(f"unknown scalar type_id: {type_id}")

def read_value(f, type_id):
    """
    Read a value of the given metadata type ID.
    Returns a tuple (type_id, value) where value is the Python representation.
    For arrays, value is a list of (type_id, value) tuples for elements? 
    No, the spec says:
    - Scalar: value is the Python value
    - STRING: value is the string
    - ARRAY: value is a list of elements, where each element is read without its own type ID
      But nested arrays: "Elemente vom Typ ARRAY tragen wieder u32 Elementtyp-ID + u64 Anzahl"
    
    The JSON schema says:
    - Scalar: {"type_id": <int>, "value": <wert>}
    - Array: {"type_id": <int>, "item_type_id": <int>, "len": <int>, "value": [<höchstens die ersten 8 Elemente>]}
    - Inner array: "ein inneres Array wird als Objekt mit item_type_id, len, value dargestellt"
    
    So for the top-level metadata value:
    - If scalar/string: return (type_id, python_value)
    - If array: return (type_id, (item_type_id, len, [elements]))
      where each element is either a python_value (if scalar/string) or a nested array object
    
    Let me re-read the spec:
    "value": Zahlen als JSON-Zahl, Wahrheitswerte als JSON-Boolean, Zeichenketten als JSON-String (UTF-8). 
    Verschachtelte Arrays (Array von Arrays) müssen gelesen werden können; ein inneres Array wird als Objekt mit item_type_id, len, value dargestellt.
    
    So for an array, the "value" field contains a list. Each element in that list is:
    - If the element is a scalar/string: the Python value directly
    - If the element is an array: an object {"item_type_id": ..., "len": ..., "value": [...]}
    
    Let me define read_value to return a structure that can be converted to the JSON format.
    
    I'll return:
    - For scalar/string: (type_id, python_value)
    - For array: (type_id, (item_type_id, len, elements_list))
      where elements_list is a list of:
        - For scalar/string elements: the python_value
        - For array elements: (item_type_id, len, elements_list)  -- but this needs to be distinguishable
    
    Actually, let me just build the JSON-ready structure directly.
    
    For a scalar/string: return (type_id, value) where value is the Python value
    For an array: return (type_id, (item_type_id, len, elements)) where elements is a list of:
        - For scalar/string: the Python value
        - For array: a dict-like structure that we'll convert later
    
    Let me use a different approach: return a tuple that indicates the kind.
    - ('scalar', type_id, value)
    - ('array', type_id, item_type_id, len, elements)
      where elements is a list of ('scalar', ...) or ('array', ...) tuples
    """
    if type_id == 9:  # ARRAY
        item_type_id = read_u32(f)
        count = read_u64(f)
        elements = []
        for _ in range(count):
            elem = read_value(f, item_type_id)
            elements.append(elem)
        return ('array', type_id, item_type_id, count, elements)
    else:
        val = read_scalar_value(f, type_id)
        return ('scalar', type_id, val)

def value_to_json(v):
    """Convert the internal value representation to JSON-ready format."""
    kind = v[0]
    if kind == 'scalar':
        _, type_id, val = v
        return val
    elif kind == 'array':
        _, type_id, item_type_id, count, elements = v
        # Convert each element
        json_elements = []
        for elem in elements[:8]:  # only first 8
            json_elements.append(value_to_json(elem))
        return json_elements
    else:
        raise ValueError(f"unknown kind: {kind}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 gguf_lesen.py <pfad>", file=sys.stderr)
        sys.exit(1)
    
    path = sys.argv[1]
    
    try:
        with open(path, 'rb') as f:
            # 1. Magic
            magic = f.read(4)
            if magic != b'GGUF':
                raise ValueError("invalid magic")
            
            # 2. Version
            version = read_u32(f)
            
            # 3. Counts
            tensor_count = read_u64(f)
            kv_count = read_u64(f)
            
            # 4. Key-value pairs
            metadata = {}
            alignment = 32  # default
            
            for _ in range(kv_count):
                key = read_str(f)
                type_id = read_u32(f)
                val = read_value(f, type_id)
                
                # Check if this is general.alignment
                if key == "general.alignment":
                    if val[0] == 'scalar':
                        alignment = val[2]
                
                # Convert to JSON format
                kind = val[0]
                if kind == 'scalar':
                    _, tid, v = val
                    metadata[key] = {"type_id": tid, "value": v}
                elif kind == 'array':
                    _, tid, item_tid, count, elements = val
                    json_elements = []
                    for elem in elements[:8]:
                        json_elements.append(value_to_json(elem))
                    metadata[key] = {
                        "type_id": tid,
                        "item_type_id": item_tid,
                        "len": count,
                        "value": json_elements
                    }
            
            # 5. Tensors
            tensors = []
            for _ in range(tensor_count):
                name = read_str(f)
                ndim = read_u32(f)
                shape = []
                for _ in range(ndim):
                    shape.append(read_u64(f))
                ggml_type_id = read_u32(f)
                offset = read_u64(f)
                
                # Determine type name and n_bytes
                if ggml_type_id in GGML_TYPES:
                    type_name, elems_per_block, bytes_per_block = GGML_TYPES[ggml_type_id]
                    # n_bytes = product(shape) * bytes_per_block / elems_per_block
                    n_elements = 1
                    for d in shape:
                        n_elements *= d
                    n_bytes = (n_elements * bytes_per_block) // elems_per_block
                else:
                    type_name = "UNBEKANNT"
                    n_bytes = None
                
                tensors.append({
                    "name": name,
                    "shape": shape,
                    "type": type_name,
                    "type_id": ggml_type_id,
                    "offset": offset,
                    "n_bytes": n_bytes
                })
            
            # 6. Calculate data_offset
            # Current position is after all tensor info
            data_offset = f.tell()
            # Pad to alignment
            if data_offset % alignment != 0:
                data_offset += alignment - (data_offset % alignment)
            
            # 7. Calculate end position
            # end = data_offset + max(offset + n_bytes) for all tensors
            # But we need to be careful: some tensors might have n_bytes = None
            max_end = data_offset
            for t in tensors:
                if t["n_bytes"] is not None:
                    t_end = data_offset + t["offset"] + t["n_bytes"]
                    if t_end > max_end:
                        max_end = t_end
            end = max_end
            
            # 8. File size
            file_size = f.seek(0, 2)
            
            # 9. ok
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
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
