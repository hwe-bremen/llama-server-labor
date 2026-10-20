#!/usr/bin/env python3
import struct
import sys
import json

# ggml tensor types mapping: type_id -> (name, elements_per_block, bytes_per_block)
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

# Metadata value types mapping: type_id -> (name, read_func)
METADATA_TYPES = {
    0:  ("UINT8", lambda f: struct.unpack('<B', f.read(1))[0]),
    1:  ("INT8", lambda f: struct.unpack('<b', f.read(1))[0]),
    2:  ("UINT16", lambda f: struct.unpack('<H', f.read(2))[0]),
    3:  ("INT16", lambda f: struct.unpack('<h', f.read(2))[0]),
    4:  ("UINT32", lambda f: struct.unpack('<I', f.read(4))[0]),
    5:  ("INT32", lambda f: struct.unpack('<i', f.read(4))[0]),
    6:  ("FLOAT32", lambda f: struct.unpack('<f', f.read(4))[0]),
    7:  ("BOOL", lambda f: struct.unpack('<B', f.read(1))[0] != 0),
    8:  ("STRING", lambda f: read_string(f)),
    9:  ("ARRAY", None),  # handled specially
    10: ("UINT64", lambda f: struct.unpack('<Q', f.read(8))[0]),
    11: ("INT64", lambda f: struct.unpack('<q', f.read(8))[0]),
    12: ("FLOAT64", lambda f: struct.unpack('<d', f.read(8))[0]),
}

def read_string(f):
    """Read a GGUF string: u64 length, then UTF-8 bytes (no null terminator)."""
    length = struct.unpack('<Q', f.read(8))[0]
    if length == 0:
        return ""
    data = f.read(length)
    if len(data) < length:
        raise EOFError("Unexpected end of file while reading string")
    return data.decode('utf-8')

def read_value(f, type_id):
    """Read a GGUF value of the given type_id."""
    if type_id == 9:  # ARRAY
        # Read element type ID (u32)
        elem_type_id = struct.unpack('<I', f.read(4))[0]
        # Read array length (u64)
        length = struct.unpack('<Q', f.read(8))[0]
        # Read array elements
        elements = []
        for _ in range(length):
            if elem_type_id == 9:  # nested array
                nested_elem_type_id = struct.unpack('<I', f.read(4))[0]
                nested_length = struct.unpack('<Q', f.read(8))[0]
                nested_elements = []
                for _ in range(nested_length):
                    nested_elements.append(read_value(f, nested_elem_type_id))
                elements.append({
                    "item_type_id": nested_elem_type_id,
                    "len": nested_length,
                    "value": nested_elements[:8]  # max 8 elements
                })
            else:
                elements.append(read_value(f, elem_type_id))
        return {
            "item_type_id": elem_type_id,
            "len": length,
            "value": elements[:8]  # max 8 elements
        }
    elif type_id in METADATA_TYPES:
        return METADATA_TYPES[type_id][1](f)
    else:
        raise ValueError(f"Unknown metadata type_id: {type_id}")

def read_tensor_info(f):
    """Read a tensor info record: name, shape, type_id, offset."""
    name = read_string(f)
    # Number of dimensions (u32)
    n_dims = struct.unpack('<I', f.read(4))[0]
    # Read dimensions (u64 each)
    shape = []
    for _ in range(n_dims):
        dim = struct.unpack('<Q', f.read(8))[0]
        shape.append(dim)
    # Tensor type ID (u32)
    type_id = struct.unpack('<I', f.read(4))[0]
    # Offset (u64)
    offset = struct.unpack('<Q', f.read(8))[0]
    return name, shape, type_id, offset

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python3 gguf_lesen.py <path>"}), file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        file_size = 0
        with open(file_path, 'rb') as f:
            # Get file size
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(0)
            
            # Read magic
            magic = f.read(4)
            if len(magic) < 4 or magic != b'GGUF':
                print(json.dumps({"error": "Invalid GGUF magic"}), file=sys.stderr)
                sys.exit(1)
            
            # Read version (u32)
            version = struct.unpack('<I', f.read(4))[0]
            
            # Read tensor count and kv count (u64 each)
            tensor_count = struct.unpack('<Q', f.read(8))[0]
            kv_count = struct.unpack('<Q', f.read(8))[0]
            
            # Read metadata (key-value pairs)
            metadata = {}
            for _ in range(kv_count):
                key = read_string(f)
                type_id = struct.unpack('<I', f.read(4))[0]
                value = read_value(f, type_id)
                metadata[key] = {"type_id": type_id, "value": value}
            
            # Read tensor info
            tensors = []
            for _ in range(tensor_count):
                name, shape, type_id, offset = read_tensor_info(f)
                
                # Get tensor type info
                if type_id in GGML_TYPES:
                    type_name, elements_per_block, bytes_per_block = GGML_TYPES[type_id]
                    # Calculate number of elements
                    n_elements = 1
                    for dim in shape:
                        n_elements *= dim
                    # Calculate bytes: (n_elements / elements_per_block) * bytes_per_block
                    n_blocks = (n_elements + elements_per_block - 1) // elements_per_block
                    n_bytes = n_blocks * bytes_per_block
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
            
            # Determine alignment
            alignment = 32
            if "general.alignment" in metadata:
                align_val = metadata["general.alignment"]["value"]
                if isinstance(align_val, int) and align_val > 0:
                    alignment = align_val
            
            # Calculate data offset (after metadata and padding)
            # Current position after reading all metadata and tensor info
            current_pos = f.tell()
            # Pad to alignment
            data_offset = (current_pos + alignment - 1) // alignment * alignment
            
            # Calculate end position
            end = data_offset
            for tensor in tensors:
                if tensor["n_bytes"] is not None:
                    end += tensor["n_bytes"]
                    # Add padding for next tensor (not needed for end calculation, but for correctness)
                    # Actually, tensors are packed with alignment, but the spec says offset is from data_offset
                    # So we just add the n_bytes for the tensor itself
                else:
                    # Unknown type: can't determine size, so end is undefined
                    end = None
                    break
            
            # Determine ok flag
            ok = False
            if end is not None and file_size >= end:
                ok = (file_size - end) < alignment
            
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
            
            print(json.dumps(result))
    
    except Exception as e:
        # Output error as JSON to stderr, but stdout must be clean JSON
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
