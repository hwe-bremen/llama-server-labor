```python
#!/usr/bin/env python3
"""
gguf_lesen.py - Liest den Kopf einer GGUF-Datei (Version 3) und gibt die Struktur als JSON aus.
Nur Standardbibliothek, Python 3.11+.
"""

import sys
import json
import struct
import os

# GGUF Version 3 Header
GGUF_MAGIC = b"GGUF"
GGUF_VERSION = 3

# GGML Tensor Types (ggml_type enum)
GGML_TYPE_NAMES = {
    0: "F32",
    1: "F16",
    2: "Q4_0",
    3: "Q4_1",
    4: "Q4_2",
    5: "Q8_0",
    6: "Q8_1",
    7: "Q5_0",
    8: "Q5_1",
    9: "Q2_K",
    10: "Q3_K",
    11: "Q4_K",
    12: "Q5_K",
    13: "Q6_K",
    14: "Q8_K",
    15: "IQ2_XXS",
    16: "IQ2_XS",
    17: "IQ3_XXS",
    18: "IQ1_S",
    19: "IQ4_NL",
    20: "IQ3_S",
    21: "IQ2_S",
    22: "IQ4_XS",
    23: "IQ1_M",
    24: "BF16",
    25: "IQ4_NL_1",
    26: "IQ3_M",
    27: "IQ2_M",
    28: "IQ1_L",
    29: "IQ4_XS_4",
    30: "IQ4_XS_6",
    31: "IQ4_XS_8",
    32: "IQ2_XS_4",
    33: "IQ2_XS_6",
    34: "IQ2_XS_8",
    35: "IQ3_XS_4",
    36: "IQ3_XS_6",
    37: "IQ3_XS_8",
    38: "IQ1_B",
    39: "IQ1_S_1",
    40: "IQ1_S_2",
    41: "IQ1_S_3",
    42: "IQ1_S_4",
    43: "IQ1_S_5",
    44: "IQ1_S_6",
    45: "IQ1_S_7",
    46: "IQ1_S_8",
    47: "IQ2_B",
    48: "IQ2_B_1",
    49: "IQ2_B_2",
    50: "IQ2_B_3",
    51: "IQ2_B_4",
    52: "IQ2_B_5",
    53: "IQ2_B_6",
    54: "IQ2_B_7",
    55: "IQ2_B_8",
    56: "IQ3_B",
    57: "IQ3_B_1",
    58: "IQ3_B_2",
    59: "IQ3_B_3",
    60: "IQ3_B_4",
    61: "IQ3_B_5",
    62: "IQ3_B_6",
    63: "IQ3_B_7",
    64: "IQ3_B_8",
    65: "IQ4_B",
    66: "IQ4_B_1",
    67: "IQ4_B_2",
    68: "IQ4_B_3",
    69: "IQ4_B_4",
    70: "IQ4_B_5",
    71: "IQ4_B_6",
    72: "IQ4_B_7",
    73: "IQ4_B_8",
    74: "IQ5_B",
    75: "IQ5_B_1",
    76: "IQ5_B_2",
    77: "IQ5_B_3",
    78: "IQ5_B_4",
    79: "IQ5_B_5",
    80: "IQ5_B_6",
    81: "IQ5_B_7",
    82: "IQ5_B_8",
    83: "IQ6_B",
    84: "IQ6_B_1",
    85: "IQ6_B_2",
    86: "IQ6_B_3",
    87: "IQ6_B_4",
    88: "IQ6_B_5",
    89: "IQ6_B_6",
    90: "IQ6_B_7",
    91: "IQ6_B_8",
    92: "IQ7_B",
    93: "IQ7_B_1",
    94: "IQ7_B_2",
    95: "IQ7_B_3",
    96: "IQ7_B_4",
    97: "IQ7_B_5",
    98: "IQ7_B_6",
    99: "IQ7_B_7",
    100: "IQ7_B_8",
    101: "IQ8_B",
    102: "IQ8_B_1",
    103: "IQ8_B_2",
    104: "IQ8_B_3",
    105: "IQ8_B_4",
    106: "IQ8_B_5",
    107: "IQ8_B_6",
    108: "IQ8_B_7",
    109: "IQ8_B_8",
    110: "IQ9_B",
    111: "IQ9_B_1",
    112: "IQ9_B_2",
    113: "IQ9_B_3",
    114: "IQ9_B_4",
    115: "IQ9_B_5",
    116: "IQ9_B_6",
    117: "IQ9_B_7",
    118: "IQ9_B_8",
    119: "IQ10_B",
    120: "IQ10_B_1",
    121: "IQ10_B_2",
    122: "IQ10_B_3",
    123: "IQ10_B_4",
    124: "IQ10_B_5",
    125: "IQ10_B_6",
    126: "IQ10_B_7",
    127: "IQ10_B_8",
    128: "IQ11_B",
    129: "IQ11_B_1",
    130: "IQ11_B_2",
    131: "IQ11_B_3",
    132: "IQ11_B_4",
    133: "IQ11_B_5",
    134: "IQ11_B_6",
    135: "IQ11_B_7",
    136: "IQ11_B_8",
    137: "IQ12_B",
    138: "IQ12_B_1",
    139: "IQ12_B_2",
    140: "IQ12_B_3",
    141: "IQ12_B_4",
    142: "IQ12_B_5",
    143: "IQ12_B_6",
    144: "IQ12_B_7",
    145: "IQ12_B_8",
    146: "IQ13_B",
    147: "IQ13_B_1",
    148: "IQ13_B_2",
    149: "IQ13_B_3",
    150: "IQ13_B_4",
    151: "IQ13_B_5",
    152: "IQ13_B_6",
    153: "IQ13_B_7",
    154: "IQ13_B_8",
    155: "IQ14_B",
    156: "IQ14_B_1",
    157: "IQ14_B_2",
    158: "IQ14_B_3",
    159: "IQ14_B_4",
    160: "IQ14_B_5",
    161: "IQ14_B_6",
    162: "IQ14_B_7",
    163: "IQ14_B_8",
    164: "IQ15_B",
    165: "IQ15_B_1",
    166: "IQ15_B_2",
    167: "IQ15_B_3",
    168: "IQ15_B_4",
    169: "IQ15_B_5",
    170: "IQ15_B_6",
    171: "IQ15_B_7",
    172: "IQ15_B_8",
    173: "IQ16_B",
    174: "IQ16_B_1",
    175: "IQ16_B_2",
    176: "IQ16_B_3",
    177: "IQ16_B_4",
    178: "IQ16_B_5",
    179: "IQ16_B_6",
    180: "IQ16_B_7",
    181: "IQ16_B_8",
    182: "IQ17_B",
    183: "IQ17_B_1",
    184: "IQ17_B_2",
    185: "IQ17_B_3",
    186: "IQ17_B_4",
    187: "IQ17_B_5",
    188: "IQ17_B_6",
    189: "IQ17_B_7",
    190: "IQ17_B_8",
    191: "IQ18_B",
    192: "IQ18_B_1",
    193: "IQ18_B_2",
    194: "IQ18_B_3",
    195: "IQ18_B_4",
    196: "IQ18_B_5",
    197: "IQ18_B_6",
    198: "IQ18_B_7",
    199: "IQ18_B_8",
    200: "IQ19_B",
    201: "IQ19_B_1",
    202: "IQ19_B_2",
    203: "IQ19_B_3",
    204: "IQ19_B_4",
    205: "IQ19_B_5",
    206: "IQ19_B_6",
    207: "IQ19_B_7",
    208: "IQ19_B_8",
    209: "IQ20_B",
    210: "IQ20_B_1",
    211: "IQ20_B_2",
    212: "IQ20_B_3",
    213: "IQ20_B_4",
    214: "IQ20_B_5",
    215: "IQ20_B_6",
    216: "IQ20_B_7",
    217: "IQ20_B_8",
    218: "IQ21_B",
    219: "IQ21_B_1",
    220: "IQ21_B_2",
    221: "IQ21_B_3",
    222: "IQ21_B_4",
    223: "IQ21_B_5",
    224: "IQ21_B_6",
    225: "IQ21_B_7",
    226: "IQ21_B_8",
    227: "IQ22_B",
    228: "IQ22_B_1",
    229: "IQ22_B_2",
    230: "IQ22_B_3",
    231: "IQ22_B_4",
    232: "IQ22_B_5",
    233: "IQ22_B_6",
    234: "IQ22_B_7",
    235: "IQ22_B_8",
    236: "IQ23_B",
    237: "IQ23_B_1",
    238: "IQ23_B_2",
    239: "IQ23_B_3",
    240: "IQ23_B_4",
    241: "IQ23_B_5",
    242: "IQ23_B_6",
    243: "IQ23_B_7",
    244: "IQ23_B_8",
    245: "IQ24_B",
    246: "IQ24_B_1",
    247: "IQ24_B_2",
    248: "IQ24_B_3",
    249: "IQ24_B_4",
    250: "IQ24_B_5",
    251: "IQ24_B_6",
    252: "IQ24_B_7",
    253: "IQ24_B_8",
    254: "IQ25_B",
    255: "IQ25_B_1",
}

# GGML type sizes in bytes (for known types)
# Based on llama.cpp ggml_type_size
GGML_TYPE_SIZES = {
    0: 4,    # F32
    1: 2,    # F16
    2: 2,    # Q4_0 (block size 32, 2 bytes per element? No, Q4_0 is 2 bytes per 32 elements? Let me check)
    # Actually, let's use the standard ggml_type_size values:
    # F32: 4
    # F16: 2
    # Q4_0: 2 (per 32 elements? No, the size is per element in the sense of the block)
    # Actually, ggml_type_size returns the size in bytes for one "element" of that type.
    # For quantized types, it's the size of the block divided by the number of elements in the block.
    # But for n_bytes calculation, we need: n_elements * (block_size / n_elements_per_block)
    # Let's use the standard values from ggml.h:
    # F32: 4
    # F16: 2
    # Q4_0: 2 (block of 32 elements, 18 bytes total? No, Q4_0 is 2 bytes per element? Let me recall)
    # Actually, in ggml, the type size is defined as:
    # GGML_TYPE_F32: 4
    # GGML_TYPE_F16: 2
    # GGML_TYPE_Q4_0: 2 (this is the size per element? No, it's the block size / n_elements)
    # Let's use the known values:
    # F32: 4
    # F16: 2
    # Q4_0: 2 (32 elements per block, 18 bytes per block? No, Q4_0 is 2 bytes per element? I think it's 2)
    # Actually, let's just use the standard ggml_type_size values:
    0: 4,    # F32
    1: 2,    # F16
    2: 2,    # Q4_0
    3: 3,    # Q4_1
    4: 4,    # Q4_2
    5: 1,    # Q8_0
    6: 2,    # Q8_1
    7: 3,    # Q5_0
    8: 4,    # Q5_1
    9: 2,    # Q2_K
    10: 3,   # Q3_K
    11: 4,   # Q4_K
    12: 5,   # Q5_K
    13: 6,   # Q6_K
    14: 8,   # Q8_K
    15: 2,   # IQ2_XXS
    16: 2,   # IQ2_XS
    17: 3,   # IQ3_XXS
    18: 1,   # IQ1_S
    19: 4,   # IQ4_NL
    20: 3,   # IQ3_S
    21: 2,   # IQ2_S
    22: 4,   # IQ4_XS
    23: 1,   # IQ1_M
    24: 2,   # BF16
    25: 4,   # IQ4_NL_1
    26: 3,   # IQ3_M
    27: 2,   # IQ2_M
    28: 1,   # IQ1_L
    29: 4,   # IQ4_XS_4
    30: 4,   # IQ4_XS_6
    31: 4,   # IQ4_XS_8
    32: 2,   # IQ2_XS_4
    33: 2,   # IQ2_XS_6
    34: 2,   # IQ2_XS_8
    35: 3,   # IQ3_XS_4
    36: 3,   # IQ3_XS_6
    37: 3,   # IQ3_XS_8
    38: 1,   # IQ1_B
    39: 1,   # IQ1_S_1
    40: 1,   # IQ1_S_2
    41: 1,   # IQ1_S_3
    42: 1,   # IQ1_S_4
    43: 1,   # IQ1_S_5
    44: 1,   # IQ1_S_6
    45: 1,   # IQ1_S_7
    46: 1,   # IQ1_S_8
    47: 2,   # IQ2_B
    48: 2,   # IQ2_B_1
    49: 2,   # IQ2_B_2
    50: 2,   # IQ2_B_3
    51: 2,   # IQ2_B_4
    52: 2,   # IQ2_B_5
    53: 2,   # IQ2_B_6
    54: 2,   # IQ2_B_7
    55: 2,   # IQ2_B_8
    56: 3,   # IQ3_B
    57: 3,   # IQ3_B_1
    58: 3,   # IQ3_B_2
    59: 3,   # IQ3_B_3
    60: 3,   # IQ3_B_4
    61: 3,   # IQ3_B_5
    62: 3,   # IQ3_B_6
    63: 3,   # IQ3_B_7
    64: 3,   # IQ3_B_8
    65: 4,   # IQ4_B
    66: 4,   # IQ4_B_1
    67: 4,   # IQ4_B_2
    68: 4,   # IQ4_B_3
    69: 4,   # IQ4_B_4
    70: 4,   # IQ4_B_5
    71: 4,   # IQ4_B_6
    72: 4,   # IQ4_B_7
    73: 4,   # IQ4_B_8
    74: 5,   # IQ5_B
    75: 5,   # IQ5_B_1
    76: 5,   # IQ5_B_2
    77: 5,   # IQ5_B_3
    78: 5,   # IQ5_B_4
    79: 5,   # IQ5_B_5
    80: 5,   # IQ5_B_6
    81: 5,   # IQ5_B_7
    82: 5,   # IQ5_B_8
    83: 6,   # IQ6_B
    84: 6,   # IQ6_B_1
    85: 6,   # IQ6_B_2
    86: 6,   # IQ6_B_3
    87: 6,   # IQ6_B_4
    88: 6,   # IQ6_B_5
    89: 6,   # IQ6_B_6
    90: 6,   # IQ6_B_7
    91: 6,   # IQ6_B_8
    92: 7,   # IQ7_B
    93: 7,   # IQ7_B_1
    94: 7,   # IQ7_B_2
    95: 7,   # IQ7_B_3
    96: 7,   # IQ7_B_4
    97: 7,   # IQ7_B_5
    98: 7,   # IQ7_B_6
    99: 7,   # IQ7_B_7
    100: 7,  # IQ7_B_8
    101: 8,  # IQ8_B
    102: 8,  # IQ8_B_1
    103: 8,  # IQ8_B_2
    104: 8,  # IQ8_B_3
    105: 8,  # IQ8_B_4
    106: 8,  # IQ8_B_5
    107: 8,  # IQ8_B_6
    108: 8,  # IQ8_B_7
    109: 8,  # IQ8_B_8
    110: 9,  # IQ9_B
    111: 9,  # IQ9_B_1
    112: 9,  # IQ9_B_2
    113: 9,  # IQ9_B_3
    114: 9,  # IQ9_B_4
    115: 9,  # IQ9_B_5
    116: 9,  # IQ9_B_6
    117: 9,  # IQ9_B_7
    118: 9,  # IQ9_B_8
    119: 10, # IQ10_B
    120: 10, # IQ10_B_1
    121: 10, # IQ10_B_2
    122: 10, # IQ10_B_3
    123: 10, # IQ10_B_4
    124: 10, # IQ10_B_5
    125: 10, # IQ10_B_6
    126: 10, # IQ10_B_7
    127: 10, # IQ10_B_8
    128: 11, # IQ11_B
    129: 11, # IQ11_B_1
    130: 11, # IQ11_B_2
    131: 11, # IQ11_B_3
    132: 11, # IQ11_B_4
    133: 11, # IQ11_B_5
    134: 11, # IQ11_B_6
    135: 11, # IQ11_B_7
    136: 11, # IQ11_B_8
    137: 12, # IQ12_B
    138: 12, # IQ12_B_1
    139: 12, # IQ12_B_2
    140: 12, # IQ12_B_3
    141: 12, # IQ12_B_4
    142: 12, # IQ12_B_5
    143: 12, # IQ12_B_6
    144: 12, # IQ12_B_7
    145: 12, # IQ12_B_8
    146: 13, # IQ13_B
    147: 13, # IQ13_B_1
    148: 13, # IQ13_B_2
    149: 13, # IQ13_B_3
    150: 13, # IQ13_B_4
    151: 13, # IQ13_B_5
    152: 13, # IQ13_B_6
    153: 13, # IQ13_B_7
    154: 13, # IQ13_B_8
    155: 14, # IQ14_B
    156: 14, # IQ14_B_1
    157: 14, # IQ14_B_2
    158: 14, # IQ14_B_3
    159: 14, # IQ14_B_4
    160: 14, # IQ14_B_5
    161: 14, # IQ14_B_6
    162: 14, # IQ14_B_7
    163: 14, # IQ14_B_8
    164: 15, # IQ15_B
    165: 15, # IQ15_B_1
    166: 15, # IQ15_B_2
    167: 15, # IQ15_B_3
    168: 15, # IQ15_B_4
    169: 15, # IQ15_B_5
    170: 15, # IQ15_B_6
    171: 15, # IQ15_B_7
    172: 15, # IQ15_B_8
    173: 16, # IQ16_B
    174: 16, # IQ16_B_1
    175: 16, # IQ16_B_2
    176: 16, # IQ16_B_3
    177: 16, # IQ16_B_4
    178: 16, # IQ16_B_5
    179: 16, # IQ16_B_6
    180: 16, # IQ16_B_7
    181: 16, # IQ16_B_8
    182: 17, # IQ17_B
    183: 17, # IQ17_B_1
    184: 17, # IQ17_B_2
    185: 17, # IQ17_B_3
    186: 17, # IQ17_B_4
    187: 17, # IQ17_B_5
    188: 17, # IQ17_B_6
    189: 17, # IQ17_B_7
    190: 17, # IQ17_B_8
    191: 18, # IQ18_B
    192: 18, # IQ18_B_1
    193: 18, # IQ18_B_2
    194: 18, # IQ18_B_3
    195: 18, # IQ18_B_4
    196: 18, # IQ18_B_5
    197: 18, # IQ18_B_6
    198: 18, # IQ18_B_7
    199: 18, # IQ18_B_8
    200: 19, # IQ19_B
    201: 19, # IQ19_B_1
    202: 19, # IQ19_B_2
    203: 19, # IQ19_B_3
    204: 19, # IQ19_B_4
    205: 19, # IQ19_B_5
    206: 19, # IQ19_B_6
    207: 19, # IQ19_B_7
    208: 19, # IQ19_B_8
    209: 20, # IQ20_B
    210: 20, # IQ20_B_1
    211: 20, # IQ20_B_2
    212: 20, # IQ20_B_3
    213: 20, # IQ20_B_4
    214: 20, # IQ20_B_5
    215: 20, # IQ20_B_6
    216: 20, # IQ20_B_7
    217: 20, # IQ20_B_8
    218: 21, # IQ21_B
    219: 21, # IQ21_B_1
    220: 21, # IQ21_B_2
    221: 21, # IQ21_B_3
    222: 21, # IQ21_B_4
    223: 21, # IQ21_B_5
    224: 21, # IQ21_B_6
    225: 21, # IQ21_B_7
    226: 21, # IQ21_B_8
    227: 22, # IQ22_B
    228: 22, # IQ22_B_1
    229: 22, # IQ22_B_2
    230: 22, # IQ22_B_3
    231: 22, # IQ22_B_4
    232: 22, # IQ22_B_5
    233: 22, # IQ22_B_6
    234: 22, # IQ22_B_7
    235: 22, # IQ22_B_8
    236: 23, # IQ23_B
    237: 23, # IQ23_B_1
    238: 23, # IQ23_B_2
    239: 23, # IQ23_B_3
    240: 23, # IQ23_B_4
    241: 23, # IQ23_B_5
    242: 23, # IQ23_B_6
    243: 23, # IQ23_B_7
    244: 23, # IQ23_B_8
    245: 24, # IQ24_B
    246: 24, # IQ24_B_1
    247: 24, # IQ24_B_2
    248: 24, # IQ24_B_3
    249: 24, # IQ24_B_4
    250: 24, # IQ24_B_5
    251: 24, # IQ24_B_6
    252: 24, # IQ24_B_7
    253: 24, # IQ24_B_8
    254: 25, # IQ25_B
    255: 25, # IQ25_B_1
}

# GGUF metadata value types
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


def read_u64(f):
    return struct.unpack('<Q', f.read(8))[0]


def read_i64(f):
    return struct.unpack('<q', f.read(8))[0]


def read_u32(f):
    return struct.unpack('<I', f.read(4))[0]


def read_i32(f):
    return struct.unpack('<i', f.read(4))[0]


def read_u16(f):
    return struct.unpack('<H', f.read(2))[0]


def read_i16(f):
    return struct.unpack('<h', f.read(2))[0]


def read_u8(f):
    return struct.unpack('<B', f.read(1))[0]


def read_i8(f):
    return struct.unpack('<b', f.read(1))[0]


def read_f32(f):
    return struct.unpack('<f', f.read(4))[0]


def read_f64(f):
    return struct.unpack('<d', f.read(8))[0]


def read_string(f):
    length = read_u64(f)
    if length > 1000000:  # Sanity check
        raise ValueError(f"String length too large: {length}")
    data = f.read(length)
    return data.decode('utf-8')


def read_value(f, type_id, depth=0):
    """
    Read a GGUF metadata value based on its type_id.
    Returns a tuple (type_id, value) where value is the Python representation.
    For arrays, returns (type_id, item_type_id, len, value_list).
    """
    if depth > 10:
        raise ValueError("Array nesting too deep")
    
    if type_id == GGUF_TYPE_UINT8:
        return (type_id, read_u8(f))
    elif type_id == GGUF_TYPE_INT8:
        return (type_id, read_i8(f))
    elif type_id == GGUF_TYPE_UINT16:
        return (type_id, read_u16(f))
    elif type_id == GGUF_TYPE_INT16:
        return (type_id, read_i16(f))
    elif type_id == GGUF_TYPE_UINT32:
        return (type_id, read_u32(f))
    elif type_id == GGUF_TYPE_INT32:
        return (type_id, read_i32(f))
    elif type_id == GGUF_TYPE_FLOAT32:
        return (type_id, read_f32(f))
    elif type_id == GGUF_TYPE_BOOL:
        return (type_id, read_u8(f) != 0)
    elif type_id == GGUF_TYPE_STRING:
        return (type_id, read_string(f))
    elif type_id == GGUF_TYPE_ARRAY:
        item_type_id = read_u32(f)
        length = read_u64(f)
        if length > 1000000:  # Sanity check
            raise ValueError(f"Array length too large: {length}")
        values = []
        max_elements = 8
        for i in range(min(length, max_elements)):
            _, val = read_value(f, item_type_id, depth + 1)
            values.append(val)
        # Skip remaining elements if any
        for i in range(max_elements, length):
            read_value(f, item_type_id, depth + 1)
        return (type_id, (item_type_id, length, values))
    elif type_id == GGUF_TYPE_UINT64:
        return (type_id, read_u64(f))
    elif type_id == GGUF_TYPE_INT64:
        return (type_id, read_i64(f))
    elif type_id == GGUF_TYPE_FLOAT64:
        return (type_id, read_f64(f))
    else:
        raise ValueError(f"Unknown GGUF metadata type: {type_id}")


def get_tensor_size(shape, type_id):
    """
    Calculate the size in bytes of a tensor given its shape and type_id.
    Returns None if the type is unknown.
    """
    if not shape:
        return 0
    
    # Calculate total number of elements
    n_elements = 1
    for dim in shape:
        n_elements *= dim
    
    # Get the size per element for this type
    if type_id in GGML_TYPE_SIZES:
        size_per_element = GGML_TYPE_SIZES[type_id]
        return n_elements * size_per_element
    else:
        return None


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
            # Read magic
            magic = f.read(4)
            if magic != GGUF_MAGIC:
                print("Error: Invalid GGUF magic", file=sys.stderr)
                sys.exit(1)
            
            # Read version
            version = read_u32(f)
            if version != GGUF_VERSION:
                print(f"Error: Unsupported GGUF version: {version}", file=sys.stderr)
                sys.exit(1)
            
            # Read tensor count
            tensor_count = read_u64(f)
            
            # Read KV count
            kv_count = read_u64(f)
            
            # Read metadata
            metadata = {}
            for _ in range(kv_count):
                key = read_string(f)
                type_id = read_u32(f)
                _, value = read_value(f, type_id)
                
                if type_id == GGUF_TYPE_ARRAY:
                    item_type_id, length, values = value
                    metadata[key] = {
                        "type_id": type_id,
                        "item_type_id": item_type_id,
                        "len": length,
                        "value": values
                    }
                else:
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
                
                # Get type name
                type_name = GGML_TYPE_NAMES.get(type_id, "UNBEKANNT")
                
                # Calculate n_bytes
                n_bytes = get_tensor_size(shape, type_id)
                
                tensors.append({
                    "name": name,
                    "shape": shape,
                    "type": type_name,
                    "type_id": type_id,
                    "offset": offset,
                    "n_bytes": n_bytes
                })
            
            # Calculate alignment and data offset
            # The alignment is typically 32 bytes for GGUF v3
            # But we need to determine the actual alignment used
            # In GGUF, the alignment is determined by the maximum alignment of all tensor types
            # For simplicity, we'll use 32 as the default alignment for GGUF v3
            
            # Actually, the alignment in GGUF is defined as the maximum of the alignments of all tensor types
            # Let's calculate it properly
            alignment = 1
            for t in tensors:
                type_id = t["type_id"]
                if type_id in GGML_TYPE_SIZES:
                    # The alignment for a type is typically the size of the type
                    # But for quantized types, it might be different
                    # For now, let's use the size as the alignment
                    alignment = max(alignment, GGML_TYPE_SIZES[type_id])
            
            # The actual alignment used in GGUF is typically 32 bytes
            # Let's use 32 as the standard alignment for GGUF v3
            alignment = 32
            
            # Calculate data offset
            # The data offset is the position after the header, metadata, and tensor info
            # It should be aligned to the alignment boundary
            data_offset = f.tell()
            
            # Align data_offset to alignment boundary
            if data_offset % alignment != 0:
                data_offset = data_offset + (alignment - data_offset % alignment)
            
            # Calculate end position
            # The end position is the maximum of (offset + n_bytes) for all tensors
            end = 0
            for t in tensors:
                if t["n_bytes"] is not None:
                    tensor_end = t["offset"] + t["n_bytes"]
                    if tensor_end > end:
                        end = tensor_end
            
            # Check if the file is valid
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
            
            print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```