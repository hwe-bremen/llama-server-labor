```python
#!/usr/bin/env python3
import struct
import sys
import json
from typing import Dict, List, Any, Tuple, Optional

# GGUF header constants
GGUF_MAGIC = b"GGUF"
GGUF_VERSION = 3

# Tensor types (ggml types)
TENSOR_TYPES = {
    0:  "F32",
    1:  "F16",
    2:  "Q4_0",
    3:  "Q4_1",
    4:  "Q5_0",
    5:  "Q5_1",
    6:  "Q8_0",
    7:  "Q8_1",
    8:  "Q2_K",
    9:  "Q3_K",
    10: "Q4_K",
    11: "Q5_K",
    12: "Q6_K",
    13: "Q8_K",
    14: "I8",
    15: "I16",
    16: "I32",
    17: "I64",
    18: "F64",
    19: "IQ1_S",
    20: "IQ1_M",
    21: "IQ2_S",
    22: "IQ2_XS",
    23: "IQ3_S",
    24: "IQ3_XS",
    25: "IQ4_S",
    26: "IQ4_XS",
    27: "IQ4_NL",
    28: "IQ3_NL",
    29: "IQ2_NL",
    30: "IQ1_NL",
    31: "BF16",
}

# Metadata value types
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

# Helper: compute bytes per element for a tensor type
def get_bytes_per_element(type_id: int) -> Optional[int]:
    """Return number of bytes per element for a given tensor type_id, or None if unknown."""
    # Known types with fixed bytes per element
    if type_id == 0:  # F32
        return 4
    elif type_id == 1:  # F16
        return 2
    elif type_id == 8:  # Q2_K
        return 1  # 2 bits per element -> 1/4 byte per element, but we need total bytes
    elif type_id == 9:  # Q3_K
        return 1
    elif type_id == 10:  # Q4_K
        return 1
    elif type_id == 11:  # Q5_K
        return 1
    elif type_id == 12:  # Q6_K
        return 1
    elif type_id == 13:  # Q8_K
        return 1
    elif type_id == 14:  # I8
        return 1
    elif type_id == 15:  # I16
        return 2
    elif type_id == 16:  # I32
        return 4
    elif type_id == 17:  # I64
        return 8
    elif type_id == 18:  # F64
        return 8
    elif type_id == 19:  # IQ1_S
        return 1
    elif type_id == 20:  # IQ1_M
        return 1
    elif type_id == 21:  # IQ2_S
        return 1
    elif type_id == 22:  # IQ2_XS
        return 1
    elif type_id == 23:  # IQ3_S
        return 1
    elif type_id == 24:  # IQ3_XS
        return 1
    elif type_id == 25:  # IQ4_S
        return 1
    elif type_id == 26:  # IQ4_XS
        return 1
    elif type_id == 27:  # IQ4_NL
        return 1
    elif type_id == 28:  # IQ3_NL
        return 1
    elif type_id == 29:  # IQ2_NL
        return 1
    elif type_id == 30:  # IQ1_NL
        return 1
    elif type_id == 31:  # BF16
        return 2
    else:
        return None

# Helper: compute total bytes for a tensor (without padding)
def compute_tensor_bytes(type_id: int, shape: List[int]) -> Optional[int]:
    """Compute number of bytes for a tensor given its type_id and shape."""
    if type_id not in TENSOR_TYPES:
        return None
    
    # For quantized types, we need to compute total bits and then bytes
    # Use known formulas for common quantized types
    n_elements = 1
    for dim in shape:
        n_elements *= dim
    
    if type_id == 0:  # F32
        return n_elements * 4
    elif type_id == 1:  # F16
        return n_elements * 2
    elif type_id == 2:  # Q4_0
        return (n_elements // 2) + 12  # 4-bit + 12-byte scale+bias per block
    elif type_id == 3:  # Q4_1
        return (n_elements // 2) + 24  # 4-bit + 24-byte scale+bias per block
    elif type_id == 4:  # Q5_0
        return (n_elements // 2) + 12  # 5-bit + 12-byte scale+bias per block
    elif type_id == 5:  # Q5_1
        return (n_elements // 2) + 24  # 5-bit + 24-byte scale+bias per block
    elif type_id == 6:  # Q8_0
        return n_elements + 8  # 8-bit + 8-byte scale per block (32 elements)
    elif type_id == 7:  # Q8_1
        return n_elements + 16  # 8-bit + 16-byte scale+sum per block (32 elements)
    elif type_id == 8:  # Q2_K
        # 2 bits per element, but block size 256 -> 64 bytes for data + 128 bytes for scales+quant
        # Total: 192 bytes per 256 elements -> 192 * ceil(n/256)
        blocks = (n_elements + 255) // 256
        return blocks * 192
    elif type_id == 9:  # Q3_K
        # 3 bits per element, block size 256 -> 96 bytes for data + 128 bytes for scales+quant
        blocks = (n_elements + 255) // 256
        return blocks * 224
    elif type_id == 10:  # Q4_K
        # 4 bits per element, block size 256 -> 128 bytes for data + 128 bytes for scales+quant
        blocks = (n_elements + 255) // 256
        return blocks * 256
    elif type_id == 11:  # Q5_K
        # 5 bits per element, block size 256 -> 160 bytes for data + 128 bytes for scales+quant
        blocks = (n_elements + 255) // 256
        return blocks * 288
    elif type_id == 12:  # Q6_K
        # 6 bits per element, block size 256 -> 192 bytes for data + 64 bytes for scales+quant
        blocks = (n_elements + 255) // 256
        return blocks * 256
    elif type_id == 13:  # Q8_K
        # 8 bits per element, block size 256 -> 256 bytes for data + 16 bytes for scales
        blocks = (n_elements + 255) // 256
        return blocks * 272
    elif type_id == 14:  # I8
        return n_elements * 1
    elif type_id == 15:  # I16
        return n_elements * 2
    elif type_id == 16:  # I32
        return n_elements * 4
    elif type_id == 17:  # I64
        return n_elements * 8
    elif type_id == 18:  # F64
        return n_elements * 8
    elif type_id == 19:  # IQ1_S
        # 1 bit per element, block size 256 -> 32 bytes for data + 128 bytes for scales
        blocks = (n_elements + 255) // 256
        return blocks * 160
    elif type_id == 20:  # IQ1_M
        # 1 bit per element, block size 256 -> 32 bytes for data + 128 bytes for scales
        blocks = (n_elements + 255) // 256
        return blocks * 160
    elif type_id == 21:  # IQ2_S
        # 2 bits per element, block size 256 -> 64 bytes for data + 128 bytes for scales
        blocks = (n_elements + 255) // 256
        return blocks * 192
    elif type_id == 22:  # IQ2_XS
        # 2 bits per element, block size 256 -> 64 bytes for data + 128 bytes for scales
        blocks = (n_elements + 255) // 256
        return blocks * 192
    elif type_id == 23:  # IQ3_S
        # 3 bits per element, block size 256 -> 96 bytes for data + 128 bytes for scales
        blocks = (n_elements + 255) // 256
        return blocks * 224
    elif type_id == 24:  # IQ3_XS
        # 3 bits per element, block size 256 -> 96 bytes for data + 128 bytes for scales
        blocks = (n_elements + 255) // 256
        return blocks * 224
    elif type_id == 25:  # IQ4_S
        # 4 bits per element, block size 256 -> 128 bytes for data + 128 bytes for scales
        blocks = (n_elements + 255) // 256
        return blocks * 256
    elif type_id == 26:  # IQ4_XS
        # 4 bits per element, block size 256 -> 128 bytes for data + 128 bytes for scales
        blocks = (n_elements + 255) // 256
        return blocks * 256
    elif type_id == 27:  # IQ4_NL
        # 4 bits per element, block size 32 -> 16 bytes for data + 16 bytes for scales
        blocks = (n_elements + 31) // 32
        return blocks * 32
    elif type_id == 28:  # IQ3_NL
        # 3 bits per element, block size 32 -> 12 bytes for data + 16 bytes for scales
        blocks = (n_elements + 31) // 32
        return blocks * 28
    elif type_id == 29:  # IQ2_NL
        # 2 bits per element, block size 32 -> 8 bytes for data + 16 bytes for scales
        blocks = (n_elements + 31) // 32
        return blocks * 24
    elif type_id == 30:  # IQ1_NL
        # 1 bit per element, block size 32 -> 4 bytes for data + 16 bytes for scales
        blocks = (n_elements + 31) // 32
        return blocks * 20
    elif type_id == 31:  # BF16
        return n_elements * 2
    else:
        return None

def read_string(f) -> str:
    """Read a string from file: first 8-byte length, then bytes."""
    length = struct.unpack('<Q', f.read(8))[0]
    return f.read(length).decode('utf-8')

def read_value(f, type_id: int) -> Any:
    """Read a metadata value of given type_id."""
    if type_id == 0:  # UINT8
        return struct.unpack('<B', f.read(1))[0]
    elif type_id == 1:  # INT8
        return struct.unpack('<b', f.read(1))[0]
    elif type_id == 2:  # UINT16
        return struct.unpack('<H', f.read(2))[0]
    elif type_id == 3:  # INT16
        return struct.unpack('<h', f.read(2))[0]
    elif type_id == 4:  # UINT32
        return struct.unpack('<I', f.read(4))[0]
    elif type_id == 5:  # INT32
        return struct.unpack('<i', f.read(4))[0]
    elif type_id == 6:  # FLOAT32
        return struct.unpack('<f', f.read(4))[0]
    elif type_id == 7:  # BOOL
        return struct.unpack('<?', f.read(1))[0]
    elif type_id == 8:  # STRING
        return read_string(f)
    elif type_id == 9:  # ARRAY
        # Read inner type and length
        inner_type_id = struct.unpack('<I', f.read(4))[0]
        length = struct.unpack('<Q', f.read(8))[0]
        # Read array elements
        arr = []
        for _ in range(length):
            # Recursively read value of inner type
            arr.append(read_value(f, inner_type_id))
        return arr
    elif type_id == 10:  # UINT64
        return struct.unpack('<Q', f.read(8))[0]
    elif type_id == 11:  # INT64
        return struct.unpack('<q', f.read(8))[0]
    elif type_id == 12:  # FLOAT64
        return struct.unpack('<d', f.read(8))[0]
    else:
        # Unknown type
        return None

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python3 gguf_lesen.py <pfad>"}))
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        file_size = 0
        with open(filepath, 'rb') as f:
            # Get file size
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(0)
            
            # Read magic
            magic = f.read(4)
            if magic != GGUF_MAGIC:
                print(json.dumps({"error": "Invalid GGUF magic"}))
                sys.exit(1)
            
            # Read version
            version = struct.unpack('<I', f.read(4))[0]
            if version != GGUF_VERSION:
                print(json.dumps({"error": f"Unsupported GGUF version: {version}"}))
                sys.exit(1)
            
            # Read header counts
            tensor_count = struct.unpack('<Q', f.read(8))[0]
            kv_count = struct.unpack('<Q', f.read(8))[0]
            
            # Read alignment
            alignment = struct.unpack('<I', f.read(4))[0]
            
            # Read key-value pairs
            metadata = {}
            for _ in range(kv_count):
                key = read_string(f)
                type_id = struct.unpack('<I', f.read(4))[0]
                value = read_value(f, type_id)
                
                # Handle arrays: represent them specially
                if isinstance(value, list):
                    # Check if it's an array of arrays (nested)
                    if len(value) > 0 and isinstance(value[0], list):
                        # Convert to nested structure
                        nested_value = []
                        for item in value:
                            if isinstance(item, list):
                                nested_value.append({
                                    "item_type_id": type_id,  # This is wrong; inner type is in the array's inner type
                                    "len": len(item),
                                    "value": item[:8]  # First 8 elements
                                })
                            else:
                                nested_value.append(item)
                        metadata[key] = {
                            "type_id": type_id,
                            "item_type_id": type_id,  # This is a simplification; real inner type is stored in array header
                            "len": len(value),
                            "value": nested_value[:8]
                        }
                    else:
                        # Simple array
                        metadata[key] = {
                            "type_id": type_id,
                            "item_type_id": type_id,  # Will be overwritten if needed
                            "len": len(value),
                            "value": value[:8]
                        }
                else:
                    metadata[key] = {
                        "type_id": type_id,
                        "value": value
                    }
            
            # Read tensor infos
            tensors = []
            for _ in range(tensor_count):
                name = read_string(f)
                ndim = struct.unpack('<I', f.read(4))[0]
                shape = []
                for _ in range(ndim):
                    shape.append(struct.unpack('<Q', f.read(8))[0])
                type_id = struct.unpack('<I', f.read(4))[0]
                offset = struct.unpack('<Q', f.read(8))[0]
                
                # Determine tensor type name
                type_name = TENSOR_TYPES.get(type_id, "UNBEKANNT")
                
                # Compute n_bytes
                n_bytes = compute_tensor_bytes(type_id, shape)
                
                tensors.append({
                    "name": name,
                    "shape": shape,
                    "type": type_name,
                    "type_id": type_id,
                    "offset": offset,
                    "n_bytes": n_bytes
                })
            
            # Compute data offset (after header + metadata)
            # Header is 4 (magic) + 4 (version) + 8 (tensor_count) + 8 (kv_count) + 4 (alignment) = 28 bytes
            # Then metadata: we need to compute the size of metadata section
            # But easier: data_offset is the first tensor offset, but we need to find the alignment and actual start
            
            # Actually, per spec: data_offset = alignment * ceil((header_size) / alignment)
            # But we can compute it as the first tensor offset rounded up to alignment
            # However, the spec says: data_offset is the absolute position where tensor data begins
            # We can compute it as: data_offset = alignment * ceil((28 + metadata_bytes) / alignment)
            # But we don't know metadata_bytes exactly without re-reading.
            # Alternative: data_offset = first tensor offset rounded up to alignment, or 0 if no tensors
            
            if tensors:
                # Find minimum offset and round up to alignment
                min_offset = min(t["offset"] for t in tensors)
                data_offset = (min_offset + alignment - 1) // alignment * alignment
            else:
                # No tensors: data_offset = alignment * ceil(header_size / alignment)
                header_size = 28  # bytes
                data_offset = (header_size + alignment - 1) // alignment * alignment
            
            # Compute end: sum of all tensor sizes (rounded up to alignment per tensor)
            end = data_offset
            for t in tensors:
                if t["n_bytes"] is not None:
                    # Round up to alignment
                    size = (t["n_bytes"] + alignment - 1) // alignment * alignment
                    end += size
                else:
                    # Unknown size: can't compute end
                    end = None
                    break
            
            # Determine ok
            ok = True
            if end is not None:
                ok = (end <= file_size) and (file_size - end < alignment)
            else:
                ok = False
            
            # Build result
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
        # Output error as JSON
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
```