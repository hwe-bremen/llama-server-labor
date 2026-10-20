#!/usr/bin/env python3
import struct
import sys
import json
import os

# GGUF magic number
GGUF_MAGIC = b'GGUF'

# Known GGUF types (metadata value types)
GGUF_VALUE_TYPES = {
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

# Known GGML tensor types (ggml_type enum)
GGML_TYPE_NAMES = {
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
    39: "I4_0",
    40: "I4_1",
    41: "I4_2",
    42: "I4_3",
    43: "I8_0",
    44: "I16_0",
    45: "I32_0",
    46: "I64_0",
    47: "F8_0",
    48: "F16_0",
    49: "BF16_0",
    50: "Q4_0_4_4",
    51: "Q4_0_4_8",
    52: "Q4_0_8_8",
    53: "TQ1_0",
    54: "TQ2_0",
    55: "I4_0_4_4",
    56: "I4_0_4_8",
    57: "I4_0_8_8",
}

# Helper: compute bytes per element for a given ggml type
def compute_bytes_per_element(type_id):
    # Known formulas for common types
    # F32: 4 bytes
    # F16: 2 bytes
    # Q4_0: 4 bits per element => 0.5 bytes
    # Q4_1: 4 bits per element => 0.5 bytes
    # Q5_0: 5 bits per element => 0.625 bytes
    # Q5_1: 5 bits per element => 0.625 bytes
    # Q8_0: 8 bits per element => 1 byte
    # Q8_1: 8 bits per element => 1 byte
    # Q2_K: 2 bits per element (grouped) => 0.25 bytes
    # Q3_K: 3 bits per element (grouped) => 0.375 bytes
    # Q4_K: 4 bits per element (grouped) => 0.5 bytes
    # Q5_K: 5 bits per element (grouped) => 0.625 bytes
    # Q6_K: 6 bits per element (grouped) => 0.75 bytes
    # Q8_K: 8 bits per element (grouped) => 1 byte
    # I8, I16, I32, I64, F64: 1,2,4,8,8 bytes
    # IQ1_S, IQ1_M, IQ2_0, IQ2_1, IQ2_2, IQ3_0, IQ3_1, IQ3_2, IQ4_0, IQ4_1, IQ4_2, IQ4_3, IQ5_0, IQ5_1, IQ5_2, IQ6_0, IQ7_0, IQ7_1, IQ8_0, IQ8_1: various quantized types
    # F8_0, F16_0, BF16_0: 1,2,2 bytes
    # Newer types (50-57) are block quantized variants

    # For unknown types, return None
    if type_id not in GGML_TYPE_NAMES:
        return None

    # Handle known types
    if type_id == 0:  # F32
        return 4
    elif type_id == 1:  # F16
        return 2
    elif type_id in (2, 3):  # Q4_0, Q4_1
        return 0.5
    elif type_id in (4, 5):  # Q5_0, Q5_1
        return 5/8
    elif type_id in (6, 7):  # Q8_0, Q8_1
        return 1
    elif type_id == 8:  # Q2_K
        return 0.25
    elif type_id == 9:  # Q3_K
        return 3/8
    elif type_id == 10:  # Q4_K
        return 0.5
    elif type_id == 11:  # Q5_K
        return 5/8
    elif type_id == 12:  # Q6_K
        return 0.75
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
    elif type_id in (19, 20):  # IQ1_S, IQ1_M
        return 1/8
    elif type_id in (21, 22, 23):  # IQ2_0, IQ2_1, IQ2_2
        return 2/8
    elif type_id in (24, 25, 26):  # IQ3_0, IQ3_1, IQ3_2
        return 3/8
    elif type_id in (27, 28, 29, 30):  # IQ4_0, IQ4_1, IQ4_2, IQ4_3
        return 4/8
    elif type_id in (31, 32, 33):  # IQ5_0, IQ5_1, IQ5_2
        return 5/8
    elif type_id == 34:  # IQ6_0
        return 6/8
    elif type_id in (35, 36):  # IQ7_0, IQ7_1
        return 7/8
    elif type_id in (37, 38):  # IQ8_0, IQ8_1
        return 1
    elif type_id in (39, 40, 41, 42):  # I4_0, I4_1, I4_2, I4_3
        return 0.5
    elif type_id in (43, 44, 45, 46):  # I8_0, I16_0, I32_0, I64_0
        return 1 << (type_id - 43)  # 1,2,4,8
    elif type_id in (47, 48, 49):  # F8_0, F16_0, BF16_0
        return 1 if type_id == 47 else 2
    elif type_id in (50, 51, 52):  # Q4_0_4_4, Q4_0_4_8, Q4_0_8_8
        return 0.5
    elif type_id in (53, 54):  # TQ1_0, TQ2_0
        return 1/8
    elif type_id in (55, 56, 57):  # I4_0_4_4, I4_0_4_8, I4_0_8_8
        return 0.5
    else:
        return None

def read_uint64(f):
    return struct.unpack('<Q', f.read(8))[0]

def read_int64(f):
    return struct.unpack('<q', f.read(8))[0]

def read_uint32(f):
    return struct.unpack('<I', f.read(4))[0]

def read_int32(f):
    return struct.unpack('<i', f.read(4))[0]

def read_float32(f):
    return struct.unpack('<f', f.read(4))[0]

def read_float64(f):
    return struct.unpack('<d', f.read(8))[0]

def read_bool(f):
    return bool(struct.unpack('<B', f.read(1))[0])

def read_string(f):
    length = read_uint64(f)
    if length == 0:
        return ""
    data = f.read(length)
    return data.decode('utf-8')

def read_value(f, type_id):
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
        return read_bool(f)
    elif type_id == 8:  # STRING
        return read_string(f)
    elif type_id == 9:  # ARRAY
        item_type_id = read_uint32(f)
        length = read_uint64(f)
        items = []
        for _ in range(length):
            items.append(read_value(f, item_type_id))
        return {
            "item_type_id": item_type_id,
            "len": length,
            "value": items[:8]  # only first 8 items
        }
    elif type_id == 10:  # UINT64
        return read_uint64(f)
    elif type_id == 11:  # INT64
        return read_int64(f)
    elif type_id == 12:  # FLOAT64
        return read_float64(f)
    else:
        # Unknown type_id: return raw value as is
        # For safety, we'll try to read something reasonable
        # But per spec, we should not crash. We'll return a placeholder.
        return None

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python3 gguf_lesen.py <pfad>"}))
        sys.exit(1)

    filepath = sys.argv[1]

    try:
        file_size = os.path.getsize(filepath)
    except OSError as e:
        print(json.dumps({"error": f"Cannot get file size: {e}"}))
        sys.exit(1)

    try:
        with open(filepath, 'rb') as f:
            # Read magic
            magic = f.read(4)
            if magic != GGUF_MAGIC:
                print(json.dumps({"error": "Invalid GGUF magic number"}))
                sys.exit(1)

            # Read version
            version = read_uint32(f)
            if version != 3:
                print(json.dumps({"error": f"Unsupported GGUF version: {version}"}))
                sys.exit(1)

            # Read tensor_count and kv_count
            tensor_count = read_uint64(f)
            kv_count = read_uint64(f)

            # Read alignment
            alignment = read_uint32(f)

            # Read metadata
            metadata = {}
            for _ in range(kv_count):
                key = read_string(f)
                type_id = read_uint32(f)
                value = read_value(f, type_id)
                metadata[key] = {
                    "type_id": type_id,
                    "value": value
                }

            # Read tensor info
            tensors = []
            for _ in range(tensor_count):
                name = read_string(f)
                ndim = read_uint32(f)
                shape = []
                for _ in range(ndim):
                    shape.append(read_uint64(f))
                type_id = read_uint32(f)
                offset = read_uint64(f)

                # Determine type name
                type_name = GGML_TYPE_NAMES.get(type_id, "UNBEKANNT")

                # Compute n_bytes
                n_bytes = None
                if type_name != "UNBEKANNT":
                    bytes_per_elem = compute_bytes_per_element(type_id)
                    if bytes_per_elem is not None:
                        # Compute total elements
                        total_elements = 1
                        for dim in shape:
                            total_elements *= dim
                        n_bytes = int(total_elements * bytes_per_elem)

                tensors.append({
                    "name": name,
                    "shape": shape,
                    "type": type_name,
                    "type_id": type_id,
                    "offset": offset,
                    "n_bytes": n_bytes
                })

            # Compute data_offset: max(offset + n_bytes) for all tensors, or 0 if no tensors
            data_offset = 0
            end = 0
            if tensors:
                # Find the maximum end position
                for tensor in tensors:
                    tensor_end = tensor["offset"] + (tensor["n_bytes"] if tensor["n_bytes"] is not None else 0)
                    if tensor_end > end:
                        end = tensor_end
                # data_offset is the start of the first tensor (minimum offset)
                data_offset = min(tensor["offset"] for tensor in tensors)
            else:
                # If no tensors, data_offset = alignment-aligned position after metadata
                # But per spec, we compute it from tensor offsets if any, else 0
                # Actually, spec says: "data_offset: absolute Dateiposition, an der die Tensordaten beginnen"
                # So if no tensors, it's 0.
                data_offset = 0

            # Compute end: position directly after last tensor data
            # We need to consider alignment: data is padded to alignment
            # So actual end = end + (alignment - (end % alignment)) % alignment
            # But spec says: "end: absolute Dateiposition direkt hinter dem letzten Byte der Tensordaten"
            # So we use the raw end (without padding), because padding is part of the tensor data area
            # However, the tensor data area is padded to alignment, so end should be aligned
            # Let's compute the end as the maximum offset + n_bytes, then align it up
            if tensors:
                # Find the maximum end position (including padding)
                max_end = 0
                for tensor in tensors:
                    tensor_end = tensor["offset"] + (tensor["n_bytes"] if tensor["n_bytes"] is not None else 0)
                    if tensor_end > max_end:
                        max_end = tensor_end
                # Align up to alignment
                end = ((max_end + alignment - 1) // alignment) * alignment
            else:
                end = 0

            # Compute ok
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

            print(json.dumps(result, ensure_ascii=False, allow_nan=False))

    except Exception as e:
        # On any error, output error JSON and exit
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
