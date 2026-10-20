#!/usr/bin/env python3
import sys
import json
import struct
import os

# ggml tensor type definitions: id -> (name, elements_per_block, bytes_per_block)
GGML_TYPES = {
    0: ("F32", 1, 4),
    1: ("F16", 1, 2),
    2: ("Q4_0", 32, 18),
    3: ("Q4_1", 32, 20),
    6: ("Q5_0", 32, 22),
    7: ("Q5_1", 32, 24),
    8: ("Q8_0", 32, 34),
    9: ("Q8_1", 32, 40),
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

# Metadata value type IDs and their struct format and size
# 0: UINT8, 1: INT8, 2: UINT16, 3: INT16, 4: UINT32, 5: INT32,
# 6: FLOAT32, 7: BOOL, 8: STRING, 9: ARRAY, 10: UINT64, 11: INT64, 12: FLOAT64
METADATA_TYPE_FORMATS = {
    0: ('B', 1),   # UINT8
    1: ('b', 1),   # INT8
    2: ('H', 2),   # UINT16
    3: ('h', 2),   # INT16
    4: ('I', 4),   # UINT32
    5: ('i', 4),   # INT32
    6: ('f', 4),   # FLOAT32
    7: ('B', 1),   # BOOL
    8: None,       # STRING (special)
    9: None,       # ARRAY (special)
    10: ('Q', 8),  # UINT64
    11: ('q', 8),  # INT64
    12: ('d', 8),  # FLOAT64
}


def read_u8(f):
    return struct.unpack('<B', f.read(1))[0]


def read_u16(f):
    return struct.unpack('<H', f.read(2))[0]


def read_u32(f):
    return struct.unpack('<I', f.read(4))[0]


def read_u64(f):
    return struct.unpack('<Q', f.read(8))[0]


def read_str(f):
    length = read_u64(f)
    data = f.read(length)
    return data.decode('utf-8')


def read_metadata_value(f, type_id):
    """
    Reads a metadata value of the given type_id from the file.
    Returns a tuple (type_id, value_representation) where value_representation
    is either a scalar value or a dict for arrays.
    """
    if type_id == 8:  # STRING
        s = read_str(f)
        return (type_id, s)
    elif type_id == 9:  # ARRAY
        item_type_id = read_u32(f)
        count = read_u64(f)
        elements = []
        for _ in range(count):
            _, elem = read_metadata_value(f, item_type_id)
            elements.append(elem)
        # For the JSON output, we need to represent this array
        # The schema says: {"type_id": <int>, "item_type_id": <int>, "len": <int>, "value": [<höchstens die ersten 8 Elemente>]}
        # But wait, the return value here is used to build the metadata dict.
        # Let's return a special structure that the caller can interpret.
        # Actually, the function returns (type_id, value). For arrays, value should be the list of elements.
        # But the JSON schema requires specific keys for arrays in the metadata dict.
        # So the caller (main loop) will need to know it's an array to format it correctly.
        # Let's return the list of elements as the value.
        return (type_id, elements)
    else:
        fmt, size = METADATA_TYPE_FORMATS.get(type_id, (None, 0))
        if fmt is None:
            # Unknown type, skip? Or raise? The spec says "Kennt dein Skript einen Tensortyp nicht, darf es nicht abstürzen"
            # But this is for metadata types. Let's assume we know all metadata types.
            # If not, we might need to handle it. But the spec lists all 0-12.
            raise ValueError(f"Unknown metadata type ID: {type_id}")
        data = f.read(size)
        if type_id == 7:  # BOOL
            val = struct.unpack(fmt, data)[0]
            return (type_id, bool(val))
        else:
            val = struct.unpack(fmt, data)[0]
            return (type_id, val)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 gguf_lesen.py <pfad>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]

    try:
        file_size = os.path.getsize(path)
    except OSError as e:
        print(f"Error: Cannot get file size: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(path, 'rb') as f:
            # 1. Magic
            magic = f.read(4)
            if magic != b'GGUF':
                print("Error: Invalid magic number", file=sys.stderr)
                sys.exit(1)

            # 2. Version
            version = read_u32(f)

            # 3. Counts
            tensor_count = read_u64(f)
            kv_count = read_u64(f)

            # 4. Metadata
            metadata = {}
            alignment = 32  # default
            for _ in range(kv_count):
                key = read_str(f)
                type_id = read_u32(f)
                _, value = read_metadata_value(f, type_id)

                # Check for general.alignment
                if key == "general.alignment" and type_id == 4:  # UINT32
                    alignment = value

                # Store in metadata dict
                if type_id == 9:  # ARRAY
                    # value is a list of elements
                    # We need to determine the item_type_id.
                    # Wait, read_metadata_value for ARRAY reads the item_type_id internally.
                    # But it doesn't return it. We need to modify read_metadata_value or handle it differently.
                    # Let's re-read the logic.
                    # For ARRAY, we read item_type_id and count, then elements.
                    # The JSON schema requires: {"type_id": <int>, "item_type_id": <int>, "len": <int>, "value": [...]}
                    # So we need the item_type_id.
                    # Let's change read_metadata_value to return more info or handle arrays in the main loop.
                    # Actually, let's just re-implement the reading for arrays in the main loop to get item_type_id.
                    pass
                else:
                    metadata[key] = {"type_id": type_id, "value": value}

            # The above loop has a problem with arrays. Let's rewrite the metadata reading part.
            # We need to reset the file position? No, we are in the middle of the file.
            # We need to read the metadata correctly.
            # Let's restart the metadata reading with a corrected approach.
            # Actually, we already read the metadata. But we didn't store arrays correctly.
            # Let's re-read the file from the beginning? No, that's inefficient but for header it's fine.
            # Or better, let's just fix the logic in the first pass.
            # Since we can't easily "undo" the read, let's just re-open and re-read the header properly.
            # It's a small part of the file.

            # Let's close and re-open to be safe and clean.
            f.close()

        with open(path, 'rb') as f:
            # Re-read header
            magic = f.read(4)
            if magic != b'GGUF':
                print("Error: Invalid magic number", file=sys.stderr)
                sys.exit(1)

            version = read_u32(f)
            tensor_count = read_u64(f)
            kv_count = read_u64(f)

            metadata = {}
            alignment = 32

            for _ in range(kv_count):
                key = read_str(f)
                type_id = read_u32(f)

                if type_id == 9:  # ARRAY
                    item_type_id = read_u32(f)
                    count = read_u64(f)
                    elements = []
                    for _ in range(count):
                        _, elem = read_metadata_value(f, item_type_id)
                        elements.append(elem)
                    # Store as per schema
                    metadata[key] = {
                        "type_id": type_id,
                        "item_type_id": item_type_id,
                        "len": count,
                        "value": elements[:8]  # Only first 8 elements
                    }
                    if key == "general.alignment" and item_type_id == 4:
                        # This is an array of UINT32? Unlikely for alignment.
                        # Alignment is usually a scalar UINT32.
                        pass
                else:
                    _, value = read_metadata_value(f, type_id)
                    metadata[key] = {"type_id": type_id, "value": value}
                    if key == "general.alignment" and type_id == 4:
                        alignment = value

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
                    # Calculate n_bytes
                    # n_elements = product of shape
                    n_elements = 1
                    for dim in shape:
                        n_elements *= dim
                    # n_bytes = n_elements * bytes_per_block / elems_per_block
                    # Must be integer
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
            # Current position is after the last tensor info.
            # We need to pad to the next alignment boundary.
            current_pos = f.tell()
            # data_offset is the position where tensor data starts.
            # It is the smallest number >= current_pos that is divisible by alignment.
            if current_pos % alignment == 0:
                data_offset = current_pos
            else:
                data_offset = current_pos + (alignment - (current_pos % alignment))

            # 7. Calculate end position
            # end = data_offset + sum of all tensor data sizes (including padding between tensors?)
            # The spec says: "end: absolute Fileposition direkt hinter dem letzten Byte der Tensordaten"
            # And "ok: true, wenn end <= file_size und file_size - end < alignment"
            # This implies that the tensor data is contiguous, but each tensor might be padded to alignment?
            # Actually, in GGUF, the tensor data is stored sequentially.
            # The offset of each tensor is relative to the start of the tensor data.
            # The size of each tensor is n_bytes.
            # However, there might be padding between tensors to align them?
            # The spec says: "Größe eines Tensors in Byte = Anzahl Elemente × Bytes je Block ÷ Elemente je Block."
            # And "offset: der Offset-Wert aus der Tensor-Info, unverändert."
            # So the offset is given in the file.
            # The end of the tensor data is the maximum (offset + n_bytes) over all tensors?
            # Or is it the sum?
            # In GGUF, tensors are stored one after another, but each tensor's data is aligned to the alignment boundary?
            # Actually, the offset is the offset from the start of the tensor data section.
            # So the end of the tensor data section is the maximum of (offset + n_bytes) for all tensors.
            # But wait, if tensors are not contiguous, there might be gaps.
            # The spec says "end: absolute Fileposition direkt hinter dem letzten Byte der Tensordaten".
            # This suggests that the tensor data section is a contiguous block.
            # So end = data_offset + total_size_of_tensor_data.
            # But how to calculate total_size_of_tensor_data?
            # It is the maximum (offset + n_bytes) over all tensors, because the data is stored sequentially with possible padding.
            # Actually, the offset is the position of the tensor within the data section.
            # So the end of the data section is the maximum (offset + n_bytes) for all tensors.
            # Let's assume that.

            max_end = 0
            for t in tensors:
                if t["n_bytes"] is not None:
                    end_of_tensor = t["offset"] + t["n_bytes"]
                    if end_of_tensor > max_end:
                        max_end = end_of_tensor

            end = data_offset + max_end

            # 8. Build output
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
                "ok": end <= file_size and (file_size - end) < alignment
            }

            print(json.dumps(output, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
