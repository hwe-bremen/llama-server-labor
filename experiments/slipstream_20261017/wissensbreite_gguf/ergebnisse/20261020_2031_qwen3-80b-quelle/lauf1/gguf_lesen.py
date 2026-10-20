#!/usr/bin/env python3
import struct
import sys
import json
import os

# ggml type definitions
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

# Metadata type names
METADATA_TYPES = {
    0: "UINT8",
    1: "INT8",
    2: "UINT16",
    3: "INT16",
    4: "UINT32",
    5: "INT32",
    6: "FLOAT32",
    7: "BOOL",
    8: "STRING",
    9: "ARRAY",
    10: "UINT64",
    11: "INT64",
    12: "FLOAT64",
}

def read_u64(f):
    data = f.read(8)
    return struct.unpack('<Q', data)[0]

def read_u32(f):
    data = f.read(4)
    return struct.unpack('<I', data)[0]

def read_string(f):
    length = read_u64(f)
    if length == 0:
        return ""
    data = f.read(length)
    return data.decode('utf-8')

def read_value(f, type_id):
    """Read a metadata value given its type_id. Returns (value, type_id)."""
    if type_id == 0:  # UINT8
        return read_u32(f), type_id
    elif type_id == 1:  # INT8
        return struct.unpack('<b', f.read(1))[0], type_id
    elif type_id == 2:  # UINT16
        return read_u32(f), type_id
    elif type_id == 3:  # INT16
        return struct.unpack('<h', f.read(2))[0], type_id
    elif type_id == 4:  # UINT32
        return read_u32(f), type_id
    elif type_id == 5:  # INT32
        return struct.unpack('<i', f.read(4))[0], type_id
    elif type_id == 6:  # FLOAT32
        return struct.unpack('<f', f.read(4))[0], type_id
    elif type_id == 7:  # BOOL
        return bool(struct.unpack('<B', f.read(1))[0]), type_id
    elif type_id == 8:  # STRING
        return read_string(f), type_id
    elif type_id == 9:  # ARRAY
        item_type_id = read_u32(f)
        length = read_u64(f)
        items = []
        for _ in range(length):
            item = read_value(f, item_type_id)
            items.append(item[0])
        return items, type_id
    elif type_id == 10:  # UINT64
        return read_u64(f), type_id
    elif type_id == 11:  # INT64
        return struct.unpack('<q', f.read(8))[0], type_id
    elif type_id == 12:  # FLOAT64
        return struct.unpack('<d', f.read(8))[0], type_id
    else:
        # Unknown type
        return None, type_id

def read_tensor_info(f):
    name = read_string(f)
    n_dims = read_u32(f)
    shape = []
    for _ in range(n_dims):
        shape.append(read_u64(f))
    type_id = read_u32(f)
    offset = read_u64(f)
    return name, shape, type_id, offset

def get_tensor_size(type_id, shape):
    """Calculate tensor size in bytes without padding."""
    if type_id not in GGML_TYPES:
        return None
    name, elements_per_block, bytes_per_block = GGML_TYPES[type_id]
    total_elements = 1
    for dim in shape:
        total_elements *= dim
    # Number of blocks needed
    n_blocks = (total_elements + elements_per_block - 1) // elements_per_block
    return n_blocks * bytes_per_block

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python3 gguf_lesen.py <pfad>"}))
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        file_size = os.path.getsize(file_path)
    except OSError as e:
        print(json.dumps({"error": f"Dateigröße konnte nicht bestimmt werden: {e}"}))
        sys.exit(1)
    
    try:
        with open(file_path, 'rb') as f:
            # Read magic
            magic = f.read(4)
            if magic != b'GGUF':
                print(json.dumps({"error": "Keine gültige GGUF-Datei (falsches Magic)"})
                sys.exit(1)
            
            # Read header
            version = read_u32(f)
            tensor_count = read_u64(f)
            kv_count = read_u64(f)
            
            # Read key-value pairs
            metadata = {}
            for _ in range(kv_count):
                key = read_string(f)
                type_id = read_u32(f)
                value, _ = read_value(f, type_id)
                metadata[key] = {"type_id": type_id, "value": value}
            
            # Determine alignment
            alignment = 32
            if "general.alignment" in metadata:
                alignment = metadata["general.alignment"]["value"]
                if not isinstance(alignment, int) or alignment <= 0:
                    alignment = 32
            
            # Read tensor info
            tensors = []
            for _ in range(tensor_count):
                name, shape, type_id, offset = read_tensor_info(f)
                if type_id in GGML_TYPES:
                    type_name, _, _ = GGML_TYPES[type_id]
                    n_bytes = get_tensor_size(type_id, shape)
                else:
                    type_name = "UNBEKANNT"
                    n_bytes = None
                tensors.append({
                    "name": name,
                    "shape": shape,
                    "type": type_name,
                    "type_id": type_id,
                    "offset": offset,
                    "n_bytes": n_bytes
                })
            
            # Calculate data offset (after padding)
            # Position after last KV pair and tensor info
            # We need to calculate the position manually since we can't rely on file position
            # Instead, we'll compute it from the tensor offsets and sizes
            
            # First, find the maximum offset + size among tensors
            data_offset = 0
            if tensors:
                # We need to compute the minimum data_offset that satisfies alignment
                # and is >= max(offset + n_bytes for all tensors)
                max_end = 0
                for t in tensors:
                    end = t["offset"] + (t["n_bytes"] if t["n_bytes"] is not None else 0)
                    if end > max_end:
                        max_end = end
                
                # data_offset must be aligned
                data_offset = ((max_end + alignment - 1) // alignment) * alignment
            else:
                # No tensors: data_offset = 0
                data_offset = 0
            
            # Calculate end position
            end = data_offset
            for t in tensors:
                if t["n_bytes"] is not None:
                    end += t["n_bytes"]
            
            # Ensure end is aligned
            end = ((end + alignment - 1) // alignment) * alignment
            
            # Determine ok
            ok = end <= file_size and (file_size - end) < alignment
            
            # Build output
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
            
            # Convert metadata values to JSON-safe format
            # Handle nested arrays (e.g., array of arrays)
            def sanitize_metadata(md):
                result = {}
                for k, v in md.items():
                    val = v["value"]
                    # If it's an array, check if elements are arrays
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        # This is an array of arrays
                        sanitized_val = []
                        for item in val:
                            if isinstance(item, dict) and "type_id" in item and "value" in item:
                                # Already in our format
                                sanitized_val.append(item)
                            else:
                                sanitized_val.append(item)
                        result[k] = {
                            "type_id": v["type_id"],
                            "item_type_id": v.get("item_type_id", 9),  # Default to ARRAY
                            "len": len(val),
                            "value": sanitized_val[:8]  # First 8 elements
                        }
                    elif isinstance(val, list):
                        # Regular array
                        result[k] = {
                            "type_id": v["type_id"],
                            "item_type_id": v.get("item_type_id", 0),
                            "len": len(val),
                            "value": val[:8]  # First 8 elements
                        }
                    else:
                        result[k] = v
                return result
            
            result["metadata"] = sanitize_metadata(metadata)
            
            print(json.dumps(result))
    
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
