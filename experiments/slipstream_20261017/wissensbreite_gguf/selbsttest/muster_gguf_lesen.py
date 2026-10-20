#!/usr/bin/env python3
"""Musterlösung (Claude) – nur für den Selbsttest des Prüfers. Nur Standardbibliothek.

Die Konstanten stammen aus gguf-py (constants.py) im lokalen llama.cpp-Baum. Wird kein Modell
gezeigt; die Läufe sind Einzelanfragen ohne Werkzeuge.
"""
import json
import os
import struct
import sys

SKALAR = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i", 6: "<f", 7: "<?", 10: "<Q", 11: "<q", 12: "<d"}
STRING, ARRAY = 8, 9
# id: (name, blockgroesse, bytes je block)
GGML = {0: ("F32", 1, 4), 1: ("F16", 1, 2), 2: ("Q4_0", 32, 18), 3: ("Q4_1", 32, 20), 6: ("Q5_0", 32, 22),
        7: ("Q5_1", 32, 24), 8: ("Q8_0", 32, 34), 9: ("Q8_1", 32, 40), 10: ("Q2_K", 256, 84),
        11: ("Q3_K", 256, 110), 12: ("Q4_K", 256, 144), 13: ("Q5_K", 256, 176), 14: ("Q6_K", 256, 210),
        15: ("Q8_K", 256, 292), 16: ("IQ2_XXS", 256, 66), 17: ("IQ2_XS", 256, 74), 18: ("IQ3_XXS", 256, 98),
        19: ("IQ1_S", 256, 50), 20: ("IQ4_NL", 32, 18), 21: ("IQ3_S", 256, 110), 22: ("IQ2_S", 256, 82),
        23: ("IQ4_XS", 256, 136), 24: ("I8", 1, 1), 25: ("I16", 1, 2), 26: ("I32", 1, 4), 27: ("I64", 1, 8),
        28: ("F64", 1, 8), 29: ("IQ1_M", 256, 56), 30: ("BF16", 1, 2), 34: ("TQ1_0", 256, 54),
        35: ("TQ2_0", 256, 66), 39: ("MXFP4", 32, 17)}


class Leser:
    def __init__(self, f):
        self.f = f

    def lies(self, fmt):
        n = struct.calcsize(fmt)
        b = self.f.read(n)
        if len(b) != n:
            raise EOFError("Datei zu kurz")
        return struct.unpack(fmt, b)[0]

    def text(self):
        n = self.lies("<Q")
        return self.f.read(n).decode("utf-8", errors="replace")

    def wert(self, typ, voll=True):
        if typ in SKALAR:
            return {"value": self.lies(SKALAR[typ])}
        if typ == STRING:
            return {"value": self.text()}
        if typ == ARRAY:
            item = self.lies("<I")
            n = self.lies("<Q")
            werte = []
            for i in range(n):
                w = self.wert(item)
                if i < 8:
                    werte.append(w if item == ARRAY else w["value"])
            return {"item_type_id": item, "len": n, "value": werte}
        raise ValueError(f"unbekannter Werttyp {typ}")


def main(pfad):
    groesse = os.path.getsize(pfad)
    with open(pfad, "rb") as f:
        r = Leser(f)
        if f.read(4) != b"GGUF":
            raise SystemExit("keine GGUF-Datei")
        version = r.lies("<I")
        n_t = r.lies("<Q")
        n_kv = r.lies("<Q")
        meta = {}
        for _ in range(n_kv):
            k = r.text()
            typ = r.lies("<I")
            meta[k] = {"type_id": typ, **r.wert(typ)}
        tensoren = []
        for _ in range(n_t):
            name = r.text()
            nd = r.lies("<I")
            shape = [r.lies("<Q") for _ in range(nd)]
            tid = r.lies("<I")
            off = r.lies("<Q")
            n_elem = 1
            for d in shape:
                n_elem *= d
            if tid in GGML:
                tn, bs, ts = GGML[tid]
                nb = n_elem * ts // bs
            else:
                tn, nb = "UNBEKANNT", None
            tensoren.append({"name": name, "shape": shape, "type": tn, "type_id": tid, "offset": off, "n_bytes": nb})
        pos = f.tell()
    align = meta.get("general.alignment", {}).get("value", 32)
    data_offset = (pos + align - 1) // align * align
    ende = data_offset + max((t["offset"] + (t["n_bytes"] or 0) for t in tensoren), default=0)
    print(json.dumps({"version": version, "tensor_count": n_t, "kv_count": n_kv, "alignment": align,
                      "data_offset": data_offset, "metadata": meta, "tensors": tensoren, "end": ende,
                      "file_size": groesse, "ok": ende <= groesse and groesse - ende < align},
                     ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
