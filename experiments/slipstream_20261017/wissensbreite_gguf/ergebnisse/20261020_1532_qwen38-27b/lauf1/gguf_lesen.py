#!/usr/bin/env python3
"""
gguf_lesen.py - Liest den Kopf einer GGUF-Datei (Version 3, little-endian)
und gibt die Struktur als JSON auf stdout aus.

Nur Python-Standardbibliothek (Python 3.11+).
"""

import sys
import json
import struct
import os

# GGUF magic
GGUF_MAGIC = b"GGUF"

# GGUF metadata value types (type_id)
GGUF_TYPE_UINT8 = 0
GGUF_TYPE_INT8 = 1
GGUF_TYPE_UINT16 = 2
GGUF_TYPE_INT16 = 3
GGUF_TYPE_UINT32 = 4
GGUF_TYPE_INT32 = 5
GGUF_TYPE_FLOAT32 = 6
GGUF_TYPE_BOOL = 7
GGUF_TYPE_STRING = 8
GGUF_TYPE_ARRAY = 9
GGUF_TYPE_UINT64 = 10
GGUF_TYPE_INT64 = 11
GGUF_TYPE_FLOAT64 = 12

# ggml tensor types (type_id) -> (name, bytes_per_element)
GGML_TYPES = {
    0: ("F32", 4),
    1: ("F16", 2),
    2: ("Q4_0", 2),
    3: ("Q4_1", 2),
    6: ("Q4_2", 2),
    7: ("Q8_0", 2),
    8: ("Q8_1", 2),
    9: ("Q5_0", 2),
    10: ("Q5_1", 2),
    11: ("Q2_K", 2),
    12: ("Q3_K", 2),
    13: ("Q4_K", 2),
    14: ("Q5_K", 2),
    15: ("Q6_K", 2),
    16: ("Q8_K", 2),
    17: ("IQ2_XXS", 2),
    18: ("IQ2_XS", 2),
    19: ("IQ3_XXS", 2),
    20: ("IQ1_S", 2),
    21: ("IQ4_NL", 2),
    22: ("IQ3_S", 2),
    23: ("IQ2_S", 2),
    24: ("IQ4_XS", 2),
    25: ("IQ1_M", 2),
    26: ("BF16", 2),
    27: ("IQ4_NL_1", 2),
    28: ("IQ3_M", 2),
    29: ("IQ2_M", 2),
    30: ("IQ1_L", 2),
    31: ("IQ4_XS_4", 2),
    32: ("IQ4_XS_8", 2),
    33: ("IQ4_XS_6", 2),
    34: ("TQ1_0", 2),
    35: ("TQ2_0", 2),
}

# Default alignment for GGUF v3
DEFAULT_ALIGNMENT = 32


def read_u32(f):
    """Read a uint32 from file."""
    data = f.read(4)
    if len(data) < 4:
        raise EOFError("Unexpected end of file reading uint32")
    return struct.unpack("<I", data)[0]


def read_i32(f):
    """Read an int32 from file."""
    data = f.read(4)
    if len(data) < 4:
        raise EOFError("Unexpected end of file reading int32")
    return struct.unpack("<i", data)[0]


def read_u64(f):
    """Read a uint64 from file."""
    data = f.read(8)
    if len(data) < 8:
        raise EOFError("Unexpected end of file reading uint64")
    return struct.unpack("<Q", data)[0]


def read_i64(f):
    """Read an int64 from file."""
    data = f.read(8)
    if len(data) < 8:
        raise EOFError("Unexpected end of file reading int64")
    return struct.unpack("<q", data)[0]


def read_f32(f):
    """Read a float32 from file."""
    data = f.read(4)
    if len(data) < 4:
        raise EOFError("Unexpected end of file reading float32")
    return struct.unpack("<f", data)[0]


def read_f64(f):
    """Read a float64 from file."""
    data = f.read(8)
    if len(data) < 8:
        raise EOFError("Unexpected end of file reading float64")
    return struct.unpack("<d", data)[0]


def read_string(f):
    """Read a length-prefixed UTF-8 string from file."""
    length = read_u64(f)
    if length > 1024 * 1024 * 1024:  # Sanity check: 1GB max
        raise ValueError(f"String length too large: {length}")
    data = f.read(length)
    if len(data) < length:
        raise EOFError("Unexpected end of file reading string")
    return data.decode("utf-8")


def read_metadata_value(f, type_id):
    """
    Read a metadata value of the given type_id.
    Returns (type_id, value) where value is the Python representation.
    For arrays, returns (type_id, item_type_id, len, value_list).
    """
    if type_id == GGUF_TYPE_UINT8:
        data = f.read(1)
        if len(data) < 1:
            raise EOFError("Unexpected end of file reading uint8")
        return (type_id, struct.unpack("<B", data)[0])
    elif type_id == GGUF_TYPE_INT8:
        data = f.read(1)
        if len(data) < 1:
            raise EOFError("Unexpected end of file reading int8")
        return (type_id, struct.unpack("<b", data)[0])
    elif type_id == GGUF_TYPE_UINT16:
        return (type_id, read_u32(f) & 0xFFFF)  # Actually need to read 2 bytes
    elif type_id == GGUF_TYPE_INT16:
        data = f.read(2)
        if len(data) < 2:
            raise EOFError("Unexpected end of file reading int16")
        return (type_id, struct.unpack("<h", data)[0])
    elif type_id == GGUF_TYPE_UINT32:
        return (type_id, read_u32(f))
    elif type_id == GGUF_TYPE_INT32:
        return (type_id, read_i32(f))
    elif type_id == GGUF_TYPE_FLOAT32:
        return (type_id, read_f32(f))
    elif type_id == GGUF_TYPE_BOOL:
        data = f.read(1)
        if len(data) < 1:
            raise EOFError("Unexpected end of file reading bool")
        return (type_id, struct.unpack("<B", data)[0] != 0)
    elif type_id == GGUF_TYPE_STRING:
        return (type_id, read_string(f))
    elif type_id == GGUF_TYPE_ARRAY:
        item_type_id = read_u32(f)
        length = read_u64(f)
        if length > 1000000:  # Sanity check
            raise ValueError(f"Array length too large: {length}")
        values = []
        for _ in range(length):
            _, val = read_metadata_value(f, item_type_id)
            values.append(val)
        return (type_id, item_type_id, length, values)
    elif type_id == GGUF_TYPE_UINT64:
        return (type_id, read_u64(f))
    elif type_id == GGUF_TYPE_INT64:
        return (type_id, read_i64(f))
    elif type_id == GGUF_TYPE_FLOAT64:
        return (type_id, read_f64(f))
    else:
        raise ValueError(f"Unknown metadata type_id: {type_id}")


def read_metadata_value_uint16(f):
    """Read a uint16 from file."""
    data = f.read(2)
    if len(data) < 2:
        raise EOFError("Unexpected end of file reading uint16")
    return struct.unpack("<H", data)[0]


def read_metadata_value_int16(f):
    """Read an int16 from file."""
    data = f.read(2)
    if len(data) < 2:
        raise EOFError("Unexpected end of file reading int16")
    return struct.unpack("<h", data)[0]


def read_metadata_value_correct(f, type_id):
    """
    Read a metadata value of the given type_id.
    Returns a tuple that can be converted to the JSON schema format.
    """
    if type_id == GGUF_TYPE_UINT8:
        data = f.read(1)
        if len(data) < 1:
            raise EOFError("Unexpected end of file reading uint8")
        return (type_id, struct.unpack("<B", data)[0])
    elif type_id == GGUF_TYPE_INT8:
        data = f.read(1)
        if len(data) < 1:
            raise EOFError("Unexpected end of file reading int8")
        return (type_id, struct.unpack("<b", data)[0])
    elif type_id == GGUF_TYPE_UINT16:
        return (type_id, read_metadata_value_uint16(f))
    elif type_id == GGUF_TYPE_INT16:
        return (type_id, read_metadata_value_int16(f))
    elif type_id == GGUF_TYPE_UINT32:
        return (type_id, read_u32(f))
    elif type_id == GGUF_TYPE_INT32:
        return (type_id, read_i32(f))
    elif type_id == GGUF_TYPE_FLOAT32:
        return (type_id, read_f32(f))
    elif type_id == GGUF_TYPE_BOOL:
        data = f.read(1)
        if len(data) < 1:
            raise EOFError("Unexpected end of file reading bool")
        return (type_id, struct.unpack("<B", data)[0] != 0)
    elif type_id == GGUF_TYPE_STRING:
        return (type_id, read_string(f))
    elif type_id == GGUF_TYPE_ARRAY:
        item_type_id = read_u32(f)
        length = read_u64(f)
        if length > 1000000:  # Sanity check
            raise ValueError(f"Array length too large: {length}")
        values = []
        for _ in range(length):
            _, val = read_metadata_value_correct(f, item_type_id)
            values.append(val)
        return (type_id, item_type_id, length, values)
    elif type_id == GGUF_TYPE_UINT64:
        return (type_id, read_u64(f))
    elif type_id == GGUF_TYPE_INT64:
        return (type_id, read_i64(f))
    elif type_id == GGUF_TYPE_FLOAT64:
        return (type_id, read_f64(f))
    else:
        raise ValueError(f"Unknown metadata type_id: {type_id}")


def tensor_nbytes(shape, type_id):
    """
    Calculate the number of bytes for tensor data given shape and type_id.
    Returns None if type is unknown.
    """
    if type_id not in GGML_TYPES:
        return None
    _, bytes_per_element = GGML_TYPES[type_id]
    total_elements = 1
    for dim in shape:
        total_elements *= dim
    return total_elements * bytes_per_element


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python3 gguf_lesen.py <pfad>"}))
        sys.exit(1)

    filepath = sys.argv[1]

    try:
        file_size = os.path.getsize(filepath)
    except OSError as e:
        print(json.dumps({"error": f"Cannot access file: {e}"}))
        sys.exit(1)

    try:
        with open(filepath, "rb") as f:
            # Read magic
            magic = f.read(4)
            if magic != GGUF_MAGIC:
                print(json.dumps({"error": "Invalid GGUF magic"}))
                sys.exit(1)

            # Read version
            version = read_u32(f)
            if version != 3:
                print(json.dumps({"error": f"Unsupported GGUF version: {version}"}))
                sys.exit(1)

            # Read tensor count
            tensor_count = read_u64(f)

            # Read kv count
            kv_count = read_u64(f)

            # Read metadata (kv pairs)
            metadata = {}
            for _ in range(kv_count):
                key = read_string(f)
                type_id = read_u32(f)
                result = read_metadata_value_correct(f, type_id)

                if type_id == GGUF_TYPE_ARRAY:
                    _, item_type_id, length, values = result
                    # For arrays, we need to handle nested arrays
                    # The value list contains the raw values, but nested arrays
                    # are represented as tuples. We need to convert them.
                    converted_values = []
                    for v in values:
                        if isinstance(v, tuple) and len(v) == 4:
                            # This is a nested array
                            nested_type_id, nested_item_type_id, nested_len, nested_values = v
                            converted_values.append({
                                "item_type_id": nested_item_type_id,
                                "len": nested_len,
                                "value": nested_values
                            })
                        else:
                            converted_values.append(v)
                    metadata[key] = {
                        "type_id": type_id,
                        "item_type_id": item_type_id,
                        "len": length,
                        "value": converted_values[:8]  # Only first 8 elements
                    }
                else:
                    _, value = result
                    metadata[key] = {
                        "type_id": type_id,
                        "value": value
                    }

            # Read tensor info
            tensors = []
            for _ in range(tensor_count):
                name = read_string(f)
                n_dims = read_u32(f)
                shape = []
                for _ in range(n_dims):
                    shape.append(read_u64(f))
                type_id = read_u32(f)
                offset = read_u64(f)

                # Determine type name and n_bytes
                if type_id in GGML_TYPES:
                    type_name = GGML_TYPES[type_id][0]
                    n_bytes = tensor_nbytes(shape, type_id)
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

            # Calculate alignment and data offset
            # In GGUF v3, the alignment is determined by the maximum alignment
            # of all tensor types. For simplicity, we use the default alignment
            # of 32 bytes, but we should check if there's a specific alignment
            # in the metadata.
            # Actually, in GGUF v3, the alignment is fixed at 32 bytes for the
            # tensor data section. Let's use that.
            alignment = DEFAULT_ALIGNMENT

            # The data offset is the current file position after reading all
            # tensor info, aligned to the alignment boundary.
            data_offset = f.tell()
            # Align to alignment boundary
            if data_offset % alignment != 0:
                data_offset = data_offset + (alignment - data_offset % alignment)

            # Calculate end position
            # The end is the maximum of (offset + n_bytes) for all tensors
            end = 0
            for t in tensors:
                if t["n_bytes"] is not None:
                    tensor_end = t["offset"] + t["n_bytes"]
                    if tensor_end > end:
                        end = tensor_end

            # Check ok condition
            ok = end <= file_size and (file_size - end) < alignment

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

    except (EOFError, ValueError, struct.error) as e:
        print(json.dumps({"error": f"Failed to parse GGUF file: {e}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
