```python
#!/usr/bin/env python3
import struct
import sys
import json
from typing import Dict, List, Any, Tuple, Optional

# GGUF header constants
GGUF_MAGIC = b"GGUF"
GGUF_VERSION = 3

# GGUF metadata types
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

# GGML tensor types
TENSOR_TYPES = {
    0: "F32",
    1: "F16",
    2: "Q4_0",
    3: "Q4_1",
    4: "Q5_0",
    5: "Q5_1",
    6: "Q8_0",
    7: "Q8_1",
    8: "Q2_K",
    9: "Q3_K",
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
    21: "IQ2_0",
    22: "IQ2_1",
    23: "IQ2_2",
    24: "IQ3_0",
    25: "IQ3_1",
    26: "IQ3_2",
    27: "IQ4_0",
    28: "IQ4_1",
    29: "IQ4_2",
    30: "IQ4_3",
    31: "IQ5_0",
    32: "IQ5_1",
    33: "IQ5_2",
    34: "IQ6_0",
    35: "IQ7_0",
    36: "IQ7_1",
    37: "IQ8_0",
    38: "IQ8_1",
    39: "IQ3_S",
    40: "IQ2_S",
    41: "IQ4_NL",
    42: "IQ3_NL",
    43: "IQ2_XS",
    44: "IQ3_XS",
    45: "IQ4_XS",
    46: "IQ1_XS",
    47: "IQ1_M",
    48: "BF16",
    49: "TQ1_0",
    50: "TQ2_0",
    51: "UNKNOWN",
    52: "UNKNOWN",
    53: "UNKNOWN",
    54: "UNKNOWN",
    55: "UNKNOWN",
    56: "UNKNOWN",
    57: "UNKNOWN",
    58: "UNKNOWN",
    59: "UNKNOWN",
    60: "UNKNOWN",
    61: "UNKNOWN",
    62: "UNKNOWN",
    63: "UNKNOWN",
    64: "UNKNOWN",
    65: "UNKNOWN",
    66: "UNKNOWN",
    67: "UNKNOWN",
    68: "UNKNOWN",
    69: "UNKNOWN",
    70: "UNKNOWN",
    71: "UNKNOWN",
    72: "UNKNOWN",
    73: "UNKNOWN",
    74: "UNKNOWN",
    75: "UNKNOWN",
    76: "UNKNOWN",
    77: "UNKNOWN",
    78: "UNKNOWN",
    79: "UNKNOWN",
    80: "UNKNOWN",
    81: "UNKNOWN",
    82: "UNKNOWN",
    83: "UNKNOWN",
    84: "UNKNOWN",
    85: "UNKNOWN",
    86: "UNKNOWN",
    87: "UNKNOWN",
    88: "UNKNOWN",
    89: "UNKNOWN",
    90: "UNKNOWN",
    91: "UNKNOWN",
    92: "UNKNOWN",
    93: "UNKNOWN",
    94: "UNKNOWN",
    95: "UNKNOWN",
    96: "UNKNOWN",
    97: "UNKNOWN",
    98: "UNKNOWN",
    99: "UNKNOWN",
    100: "UNKNOWN",
    101: "UNKNOWN",
    102: "UNKNOWN",
    103: "UNKNOWN",
    104: "UNKNOWN",
    105: "UNKNOWN",
    106: "UNKNOWN",
    107: "UNKNOWN",
    108: "UNKNOWN",
    109: "UNKNOWN",
    110: "UNKNOWN",
    111: "UNKNOWN",
    112: "UNKNOWN",
    113: "UNKNOWN",
    114: "UNKNOWN",
    115: "UNKNOWN",
    116: "UNKNOWN",
    117: "UNKNOWN",
    118: "UNKNOWN",
    119: "UNKNOWN",
    120: "UNKNOWN",
    121: "UNKNOWN",
    122: "UNKNOWN",
    123: "UNKNOWN",
    124: "UNKNOWN",
    125: "UNKNOWN",
    126: "UNKNOWN",
    127: "UNKNOWN",
    128: "UNKNOWN",
    129: "UNKNOWN",
    130: "UNKNOWN",
    131: "UNKNOWN",
    132: "UNKNOWN",
    133: "UNKNOWN",
    134: "UNKNOWN",
    135: "UNKNOWN",
    136: "UNKNOWN",
    137: "UNKNOWN",
    138: "UNKNOWN",
    139: "UNKNOWN",
    140: "UNKNOWN",
    141: "UNKNOWN",
    142: "UNKNOWN",
    143: "UNKNOWN",
    144: "UNKNOWN",
    145: "UNKNOWN",
    146: "UNKNOWN",
    147: "UNKNOWN",
    148: "UNKNOWN",
    149: "UNKNOWN",
    150: "UNKNOWN",
    151: "UNKNOWN",
    152: "UNKNOWN",
    153: "UNKNOWN",
    154: "UNKNOWN",
    155: "UNKNOWN",
    156: "UNKNOWN",
    157: "UNKNOWN",
    158: "UNKNOWN",
    159: "UNKNOWN",
    160: "UNKNOWN",
    161: "UNKNOWN",
    162: "UNKNOWN",
    163: "UNKNOWN",
    164: "UNKNOWN",
    165: "UNKNOWN",
    166: "UNKNOWN",
    167: "UNKNOWN",
    168: "UNKNOWN",
    169: "UNKNOWN",
    170: "UNKNOWN",
    171: "UNKNOWN",
    172: "UNKNOWN",
    173: "UNKNOWN",
    174: "UNKNOWN",
    175: "UNKNOWN",
    176: "UNKNOWN",
    177: "UNKNOWN",
    178: "UNKNOWN",
    179: "UNKNOWN",
    180: "UNKNOWN",
    181: "UNKNOWN",
    182: "UNKNOWN",
    183: "UNKNOWN",
    184: "UNKNOWN",
    185: "UNKNOWN",
    186: "UNKNOWN",
    187: "UNKNOWN",
    188: "UNKNOWN",
    189: "UNKNOWN",
    190: "UNKNOWN",
    191: "UNKNOWN",
    192: "UNKNOWN",
    193: "UNKNOWN",
    194: "UNKNOWN",
    195: "UNKNOWN",
    196: "UNKNOWN",
    197: "UNKNOWN",
    198: "UNKNOWN",
    199: "UNKNOWN",
    200: "UNKNOWN",
    201: "UNKNOWN",
    202: "UNKNOWN",
    203: "UNKNOWN",
    204: "UNKNOWN",
    205: "UNKNOWN",
    206: "UNKNOWN",
    207: "UNKNOWN",
    208: "UNKNOWN",
    209: "UNKNOWN",
    210: "UNKNOWN",
    211: "UNKNOWN",
    212: "UNKNOWN",
    213: "UNKNOWN",
    214: "UNKNOWN",
    215: "UNKNOWN",
    216: "UNKNOWN",
    217: "UNKNOWN",
    218: "UNKNOWN",
    219: "UNKNOWN",
    220: "UNKNOWN",
    221: "UNKNOWN",
    222: "UNKNOWN",
    223: "UNKNOWN",
    224: "UNKNOWN",
    225: "UNKNOWN",
    226: "UNKNOWN",
    227: "UNKNOWN",
    228: "UNKNOWN",
    229: "UNKNOWN",
    230: "UNKNOWN",
    231: "UNKNOWN",
    232: "UNKNOWN",
    233: "UNKNOWN",
    234: "UNKNOWN",
    235: "UNKNOWN",
    236: "UNKNOWN",
    237: "UNKNOWN",
    238: "UNKNOWN",
    239: "UNKNOWN",
    240: "UNKNOWN",
    241: "UNKNOWN",
    242: "UNKNOWN",
    243: "UNKNOWN",
    244: "UNKNOWN",
    245: "UNKNOWN",
    246: "UNKNOWN",
    247: "UNKNOWN",
    248: "UNKNOWN",
    249: "UNKNOWN",
    250: "UNKNOWN",
    251: "UNKNOWN",
    252: "UNKNOWN",
    253: "UNKNOWN",
    254: "UNKNOWN",
    255: "UNKNOWN",
}

# Helper: compute bytes per element for a tensor type
def bytes_per_element(type_id: int) -> Optional[int]:
    """Return number of bytes per element for a given tensor type ID, or None if unknown."""
    # Known types with fixed size
    if type_id == 0:  # F32
        return 4
    elif type_id == 1:  # F16
        return 2
    elif type_id == 18:  # F64
        return 8
    elif type_id == 14:  # I8
        return 1
    elif type_id == 15:  # I16
        return 2
    elif type_id == 16:  # I32
        return 4
    elif type_id == 17:  # I64
        return 8
    elif type_id == 19:  # IQ1_S
        return 1  # 1 bit per element, but rounded up to bytes
    elif type_id == 20:  # IQ1_M
        return 1
    elif type_id == 21:  # IQ2_0
        return 1
    elif type_id == 22:  # IQ2_1
        return 1
    elif type_id == 23:  # IQ2_2
        return 1
    elif type_id == 24:  # IQ3_0
        return 1
    elif type_id == 25:  # IQ3_1
        return 1
    elif type_id == 26:  # IQ3_2
        return 1
    elif type_id == 27:  # IQ4_0
        return 1
    elif type_id == 28:  # IQ4_1
        return 1
    elif type_id == 29:  # IQ4_2
        return 1
    elif type_id == 30:  # IQ4_3
        return 1
    elif type_id == 31:  # IQ5_0
        return 1
    elif type_id == 32:  # IQ5_1
        return 1
    elif type_id == 33:  # IQ5_2
        return 1
    elif type_id == 34:  # IQ6_0
        return 1
    elif type_id == 35:  # IQ7_0
        return 1
    elif type_id == 36:  # IQ7_1
        return 1
    elif type_id == 37:  # IQ8_0
        return 1
    elif type_id == 38:  # IQ8_1
        return 1
    elif type_id == 39:  # IQ3_S
        return 1
    elif type_id == 40:  # IQ2_S
        return 1
    elif type_id == 41:  # IQ4_NL
        return 1
    elif type_id == 42:  # IQ3_NL
        return 1
    elif type_id == 43:  # IQ2_XS
        return 1
    elif type_id == 44:  # IQ3_XS
        return 1
    elif type_id == 45:  # IQ4_XS
        return 1
    elif type_id == 46:  # IQ1_XS
        return 1
    elif type_id == 47:  # IQ1_M
        return 1
    elif type_id == 48:  # BF16
        return 2
    elif type_id == 49:  # TQ1_0
        return 1
    elif type_id == 50:  # TQ2_0
        return 1
    # Quantized types: need special handling
    elif type_id == 2:  # Q4_0
        return None  # will be computed from shape
    elif type_id == 3:  # Q4_1
        return None
    elif type_id == 4:  # Q5_0
        return None
    elif type_id == 5:  # Q5_1
        return None
    elif type_id == 6:  # Q8_0
        return None
    elif type_id == 7:  # Q8_1
        return None
    elif type_id == 8:  # Q2_K
        return None
    elif type_id == 9:  # Q3_K
        return None
    elif type_id == 10:  # Q4_K
        return None
    elif type_id == 11:  # Q5_K
        return None
    elif type_id == 12:  # Q6_K
        return None
    elif type_id == 13:  # Q8_K
        return None
    else:
        return None

def compute_tensor_bytes(type_id: int, shape: List[int]) -> Optional[int]:
    """Compute number of bytes for a tensor given its type and shape."""
    if type_id in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13):
        # Quantized types: need special formulas
        # Q4_0, Q4_1, Q5_0, Q5_1, Q8_0, Q8_1, Q2_K, Q3_K, Q4_K, Q5_K, Q6_K, Q8_K
        # Use known formulas from llama.cpp
        n = 1
        for d in shape:
            n *= d
        
        if type_id == 2:  # Q4_0
            block_size = 32
            return (n // block_size) * (2 + 16) + (2 if n % block_size != 0 else 0)
        elif type_id == 3:  # Q4_1
            block_size = 32
            return (n // block_size) * (2 + 2 + 16) + (4 if n % block_size != 0 else 0)
        elif type_id == 4:  # Q5_0
            block_size = 32
            return (n // block_size) * (2 + 4 + 16) + (6 if n % block_size != 0 else 0)
        elif type_id == 5:  # Q5_1
            block_size = 32
            return (n // block_size) * (2 + 2 + 4 + 16) + (8 if n % block_size != 0 else 0)
        elif type_id == 6:  # Q8_0
            block_size = 32
            return (n // block_size) * (2 + 32) + (34 if n % block_size != 0 else 0)
        elif type_id == 7:  # Q8_1
            block_size = 32
            return (n // block_size) * (2 + 4 + 32) + (38 if n % block_size != 0 else 0)
        elif type_id == 8:  # Q2_K
            block_size = 256
            return (n // block_size) * (1 + 1 + 64 + 64) + (129 if n % block_size != 0 else 0)
        elif type_id == 9:  # Q3_K
            block_size = 256
            return (n // block_size) * (1 + 1 + 32 + 64) + (97 if n % block_size != 0 else 0)
        elif type_id == 10:  # Q4_K
            block_size = 256
            return (n // block_size) * (2 + 2 + 128 + 64) + (194 if n % block_size != 0 else 0)
        elif type_id == 11:  # Q5_K
            block_size = 256
            return (n // block_size) * (2 + 2 + 128 + 64) + (194 if n % block_size != 0 else 0)
        elif type_id == 12:  # Q6_K
            block_size = 256
            return (n // block_size) * (1 + 1 + 64 + 128) + (193 if n % block_size != 0 else 0)
        elif type_id == 13:  # Q8_K
            block_size = 256
            return (n // block_size) * (4 + 256) + (260 if n % block_size != 0 else 0)
        else:
            return None
    else:
        bpe = bytes_per_element(type_id)
        if bpe is None:
            return None
        n = 1
        for d in shape:
            n *= d
        return n * bpe

def read_string(f) -> str:
    """Read a GGUF string (length-prefixed UTF-8)."""
    length = struct.unpack("<Q", f.read(8))[0]
    return f.read(length).decode('utf-8')

def read_value(f, type_id: int) -> Any:
    """Read a GGUF metadata value of given type."""
    if type_id == 0:  # UINT8
        return struct.unpack("<B", f.read(1))[0]
    elif type_id == 1:  # INT8
        return struct.unpack("<b", f.read(1))[0]
    elif type_id == 2:  # UINT16
        return struct.unpack("<H", f.read(2))[0]
    elif type_id == 3:  # INT16
        return struct.unpack("<h", f.read(2))[0]
    elif type_id == 4:  # UINT32
        return struct.unpack("<I", f.read(4))[0]
    elif type_id == 5:  # INT32
        return struct.unpack("<i", f.read(4))[0]
    elif type_id == 6:  # FLOAT32
        return struct.unpack("<f", f.read(4))[0]
    elif type_id == 7:  # BOOL
        return struct.unpack("<B", f.read(1))[0] != 0
    elif type_id == 8:  # STRING
        return read_string(f)
    elif type_id == 9:  # ARRAY
        # Read array metadata
        item_type_id = struct.unpack("<I", f.read(4))[0]
        length = struct.unpack("<Q", f.read(8))[0]
        # Read array elements
        arr = []
        for _ in range(length):
            arr.append(read_value(f, item_type_id))
        return arr
    elif type_id == 10:  # UINT64
        return struct.unpack("<Q", f.read(8))[0]
    elif type_id == 11:  # INT64
        return struct.unpack("<q", f.read(8))[0]
    elif type_id == 12:  # FLOAT64
        return struct.unpack("<d", f.read(8))[0]
    else:
        # Unknown type
        return None

def read_metadata_value(f, type_id: int, item_type_id: Optional[int] = None) -> Dict[str, Any]:
    """Read a metadata value and return as dict with type info."""
    if type_id == 9:  # ARRAY
        # Read array metadata
        inner_item_type_id = struct.unpack("<I", f.read(4))[0]
        length = struct.unpack("<Q", f.read(8))[0]
        # Read array elements
        arr = []
        for i in range(length):
            val = read_value(f, inner_item_type_id)
            # For nested arrays, convert to dict representation
            if isinstance(val, list):
                # Already handled recursively by read_value
                arr.append(val)
            else:
                arr.append(val)
        # Limit to first 8 elements
        limited_arr = arr[:8]
        return {
            "type_id": type_id,
            "item_type_id": inner_item_type_id,
            "len": length,
            "value": limited_arr
        }
    else:
        val = read_value(f, type_id)
        return {
            "type_id": type_id,
            "value": val
        }

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python3 gguf_lesen.py <pfad>"}))
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        file_size = 0
        with open(file_path, "rb") as f:
            # Read magic
            magic = f.read(4)
            if magic != GGUF_MAGIC:
                print(json.dumps({"error": "Invalid GGUF magic"}))
                sys.exit(1)
            
            # Read version
            version = struct.unpack("<I", f.read(4))[0]
            if version != GGUF_VERSION:
                print(json.dumps({"error": f"Unsupported GGUF version {version}"}))
                sys.exit(1)
            
            # Read header counts
            tensor_count = struct.unpack("<Q", f.read(8))[0]
            kv_count = struct.unpack("<Q", f.read(8))[0]
            
            # Read alignment
            alignment = struct.unpack("<I", f.read(4))[0]
            
            # Read metadata key-value pairs
            metadata = {}
            for _ in range(kv_count):
                key = read_string(f)
                type_id = struct.unpack("<I", f.read(4))[0]
                metadata[key] = read_metadata_value(f, type_id)
            
            # Calculate data offset
            # Header size = 4 (magic) + 4 (version) + 8 (tensor_count) + 8 (kv_count) + 4 (alignment) = 28
            # Plus size of metadata: each key-value pair has key string + type_id + value
            # We need to compute the total size of metadata section
            # Since we already read it, we can compute data_offset as:
            # data_offset = 28 + sum of sizes of all metadata entries
            
            # But easier: we know the file position after reading metadata
            # So we can just use f.tell() after reading all metadata
            data_offset = f.tell()
            
            # Align data_offset to alignment
            data_offset = (data_offset + alignment - 1) // alignment * alignment
            
            # Read tensor info
            tensors = []
            for _ in range(tensor_count):
                name = read_string(f)
                ndim = struct.unpack("<I", f.read(4))[0]
                shape = []
                for _ in range(ndim):
                    shape.append(struct.unpack("<Q", f.read(8))[0])
                type_id = struct.unpack("<I", f.read(4))[0]
                offset = struct.unpack("<Q", f.read(8))[0]
                
                # Get tensor type name
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
            
            # Calculate end position
            # end = data_offset + sum of tensor sizes (including padding)
            # But we don't know padding. Instead, we can compute max offset + n_bytes for each tensor
            # and align to alignment
            end = data_offset
            for tensor in tensors:
                # The tensor data starts at tensor['offset'] relative to data_offset
                # So absolute position is data_offset + tensor['offset']
                # But we need to consider padding: each tensor is padded to alignment
                tensor_size = tensor['n_bytes']
                if tensor_size is None:
                    tensor_size = 0
                # Compute padded size
                padded_size = (tensor_size + alignment - 1) // alignment * alignment
                tensor_end = data_offset + tensor['offset'] + padded_size
                if tensor_end > end:
                    end = tensor_end
            
            # Get actual file size
            file_size = 0
            with open(file_path, "rb") as f2:
                f2.seek(0, 2)
                file_size = f2.tell()
            
            # Determine ok flag
            ok = end <= file_size and (file_size - end) < alignment
            
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
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
```