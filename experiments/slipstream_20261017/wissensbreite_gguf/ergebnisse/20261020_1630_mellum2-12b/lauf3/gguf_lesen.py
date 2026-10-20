import sys
import json
import struct
from typing import Any, Dict, List, Optional, Tuple

# Mapping from ggml type IDs to names and byte sizes
GGML_TYPE_TO_NAME = {
    0: "F32",
    1: "F16",
    2: "Q4_0",
    3: "Q4_1",
    4: "Q4_2",
    5: "Q4_3",
    6: "Q5_0",
    7: "Q5_1",
    8: "Q5_2",
    9: "Q5_3",
    10: "Q6_0",
    11: "Q6_1",
    12: "Q6_2",
    13: "Q6_3",
    14: "Q8_0",
    15: "Q8_1",
    16: "Q8_2",
    17: "Q8_3",
    18: "Q2_K",
    19: "Q3_K",
    20: "Q4_K",
    21: "Q5_K",
    22: "Q6_K",
    23: "Q8_K",
    24: "BF16",
    25: "Q4_0_2",
    26: "Q4_1_2",
    27: "Q4_2_2",
    28: "Q4_3_2",
    29: "Q5_0_2",
    30: "Q5_1_2",
    31: "Q5_2_2",
    32: "Q5_3_2",
    33: "Q6_0_2",
    34: "Q6_1_2",
    35: "Q6_2_2",
    36: "Q6_3_2",
    37: "Q8_0_2",
    38: "Q8_1_2",
    39: "Q8_2_2",
    40: "Q8_3_2",
    41: "Q2_K_2",
    42: "Q3_K_2",
    43: "Q4_K_2",
    44: "Q5_K_2",
    45: "Q6_K_2",
    46: "Q8_K_2",
}

GGML_TYPE_TO_BYTES = {
    0: 4,
    1: 2,
    2: 1,
    3: 1,
    4: 1,
    5: 1,
    6: 1,
    7: 1,
    8: 1,
    9: 1,
    10: 1,
    11: 1,
    12: 1,
    13: 1,
    14: 1,
    15: 1,
    16: 1,
    17: 1,
    18: 1,
    19: 1,
    20: 1,
    21: 1,
    22: 1,
    23: 1,
    24: 2,
    25: 1,
    26: 1,
    27: 1,
    28: 1,
    29: 1,
    30: 1,
    31: 1,
    32: 1,
    33: 1,
    34: 1,
    35: 1,
    36: 1,
    37: 1,
    38: 1,
    39: 1,
    40: 1,
    41: 1,
    42: 1,
    43: 1,
    44: 1,
    45: 1,
    46: 1,
}

def read_u32(f) -> int:
    return struct.unpack("<I", f.read(4))[0]

def read_u64(f) -> int:
    return struct.unpack("<Q", f.read(8))[0]

def read_string(f) -> str:
    length = read_u32(f)
    data = f.read(length)
    return data.decode("utf-8")

def read_metadata(f) -> Dict[str, Any]:
    metadata = {}
    count = read_u32(f)
    for _ in range(count):
        key = read_string(f)
        type_id = read_u32(f)
        if type_id in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46):
            # scalar
            value = read_scalar(f, type_id)
            metadata[key] = {"type_id": type_id, "value": value}
        else:
            # array
            item_type_id = read_u32(f)
            length = read_u32(f)
            value = []
            for i in range(min(length, 8)):
                item = read_scalar(f, item_type_id)
                value.append(item)
            metadata[key] = {"type_id": type_id, "item_type_id": item_type_id, "len": length, "value": value}
    return metadata

def read_scalar(f, type_id: int) -> Any:
    if type_id == 0:  # F32
        return struct.unpack("<f", f.read(4))[0]
    elif type_id == 1:  # F16
        return struct.unpack("<e", f.read(2))[0]
    elif type_id == 24:  # BF16
        return struct.unpack("<H", f.read(2))[0]  # treat as float
    else:
        # For other types, we don't have a direct mapping, but we can try to read as integer
        # Since we only need metadata values, and they are stored as scalars, we can read as integer
        # but the actual type might be different. We'll read as integer for simplicity.
        # However, the metadata might contain booleans, strings, etc.
        # For this script, we'll read as integer and hope it's correct.
        try:
            if type_id in (0, 1, 24):
                # These are floats, but we already handled them
                pass
            elif type_id == 3:  # Q4_0
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 4:  # Q4_1
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 5:  # Q4_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 6:  # Q4_3
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 7:  # Q5_0
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 8:  # Q5_1
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 9:  # Q5_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 10:  # Q5_3
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 11:  # Q6_0
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 12:  # Q6_1
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 13:  # Q6_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 14:  # Q8_0
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 15:  # Q8_1
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 16:  # Q8_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 17:  # Q8_3
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 18:  # Q2_K
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 19:  # Q3_K
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 20:  # Q4_K
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 21:  # Q5_K
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 22:  # Q6_K
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 23:  # Q8_K
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 25:  # Q4_0_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 26:  # Q4_1_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 27:  # Q4_2_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 28:  # Q4_3_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 29:  # Q5_0_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 30:  # Q5_1_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 31:  # Q5_2_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 32:  # Q5_3_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 33:  # Q6_0_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 34:  # Q6_1_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 35:  # Q6_2_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 36:  # Q6_3_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 37:  # Q8_0_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 38:  # Q8_1_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 39:  # Q8_2_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 40:  # Q8_3_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 41:  # Q2_K_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 42:  # Q3_K_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 43:  # Q4_K_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 44:  # Q5_K_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 45:  # Q6_K_2
                return struct.unpack("<B", f.read(1))[0]
            elif type_id == 46:  # Q8_K_2
                return struct.unpack("<B", f.read(1))[0]
            else:
                # Unknown type, try to read as integer
                return struct.unpack("<I", f.read(4))[0]
        except Exception:
            return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 gguf_lesen.py <pfad>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]

    try:
        with open(path, "rb") as f:
            # Read header
            magic = read_u32(f)
            if magic != 0x67677566:  # "gguf"
                raise ValueError("Invalid magic number")

            version = read_u32(f)
            tensor_count = read_u32(f)
            kv_count = read_u32(f)
            alignment = read_u32(f)
            data_offset = read_u64(f)

            # Read metadata
            metadata = read_metadata(f)

            # Read tensors
            tensors = []
            for _ in range(tensor_count):
                name = read_string(f)
                type_id = read_u32(f)
                shape = []
                for _ in range(8):  # max 8 dimensions
                    dim = read_u64(f)
                    if dim == 0:
                        break
                    shape.append(dim)

                # Calculate n_bytes
                if type_id in GGML_TYPE_TO_BYTES:
                    n_bytes = GGML_TYPE_TO_BYTES[type_id]
                    for dim in shape:
                        n_bytes *= dim
                    # Apply alignment
                    n_bytes = ((n_bytes + alignment - 1) // alignment) * alignment
                else:
                    n_bytes = None

                tensors.append({
                    "name": name,
                    "shape": shape,
                    "type": GGML_TYPE_TO_NAME.get(type_id, "UNBEKANNT"),
                    "type_id": type_id,
                    "offset": data_offset,
                    "n_bytes": n_bytes
                })

            # Calculate end position
            end = data_offset
            for tensor in tensors:
                end = max(end, tensor["offset"] + (tensor["n_bytes"] if tensor["n_bytes"] is not None else 0))

            # Get file size
            file_size = os.path.getsize(path)

            # Check ok condition
            ok = end <= file_size and (file_size - end) < alignment

            # Output JSON
            output = {
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

            print(json.dumps(output, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}), ensure_ascii=False)
        sys.exit(1)

if __name__ == "__main__":
    import os
    main()
