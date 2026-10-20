#!/usr/bin/env python3
"""
Wissensbreite GGUF — Prüfer.

Erzeugt die synthetischen Prüfdateien, führt die von den Modellen geschriebenen GGUF-Leser aus und
vergleicht ihre JSON-Ausgabe mit gguf-py aus dem lokalen llama.cpp-Baum (Referenz). Die Antworten
auf die Wissensfragen werden nur gesammelt (Bewertung von Hand gegen den Schlüssel im Claude-Projekt).

Aufrufe (aus dem Repo-Root, mit der .venv, die numpy + pyyaml hat):
    .venv/bin/python experiments/slipstream_20261017/wissensbreite_gguf/pruefen.py synth
    .venv/bin/python experiments/slipstream_20261017/wissensbreite_gguf/pruefen.py referenz DATEI.gguf ...
    .venv/bin/python experiments/slipstream_20261017/wissensbreite_gguf/pruefen.py bewerten \
        ergebnisse/<lauf-ordner> [weitere] --dateien D2.gguf D3.gguf D4.gguf
    .venv/bin/python experiments/slipstream_20261017/wissensbreite_gguf/pruefen.py tabelle ergebnisse/*/

Sicherheit: Der Kandidatencode ist modellgeschrieben. Vor dem Ausführen prüft eine AST-Analyse die
Imports und gefährliche Aufrufe; Auffälliges wird NICHT ausgeführt (Überschreiben mit --trotzdem).
Ausgeführt wird mit `python3 -I`, in einem leeren Temp-Ordner, mit Zeitgrenze.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRUEFDATEIEN = HERE / "pruefdateien"            # .gitignore: *.gguf und ref_*.json
GGUF_PY_DEFAULT = HERE.parent / "qwen3next_reproducible_build" / "upstream" / "gguf-py"

# Klassische Speichertypen für D1 (gewertet) und neuere für die Bonusdatei (nicht gewertet).
KLASSISCH = ["F32", "F16", "BF16", "F64", "I8", "I16", "I32", "I64",
             "Q4_0", "Q4_1", "Q5_0", "Q5_1", "Q8_0",
             "Q2_K", "Q3_K", "Q4_K", "Q5_K", "Q6_K",
             "IQ2_XXS", "IQ2_XS", "IQ2_S", "IQ3_XXS", "IQ3_S", "IQ1_S", "IQ1_M", "IQ4_NL", "IQ4_XS"]
NEU = ["TQ1_0", "TQ2_0", "MXFP4"]

BONUS = "synth_neu.gguf"                      # wird berichtet, zählt nicht
ZEITGRENZE = 120
PUNKTE = ["kopf", "meta_typen", "meta_skalare", "meta_arrays", "tensor_infos", "alignment_offset",
          "n_bytes", "ende"]

# Module, deren Import den Lauf disqualifiziert (keine Standardbibliothek) prüft is_stdlib();
# zusätzlich werden diese Standardmodule/Aufrufe nicht ohne --trotzdem ausgeführt:
RISKANTE_MODULE = {"subprocess", "socket", "shutil", "urllib", "http", "ftplib", "smtplib", "ctypes",
                   "multiprocessing", "asyncio", "webbrowser", "telnetlib", "ssl", "pty", "signal"}
RISKANTE_OS = {"system", "popen", "remove", "unlink", "rmdir", "removedirs", "rename", "replace", "execv",
               "execve", "execvp", "spawnv", "kill", "truncate", "chmod", "chown", "fork", "startfile"}
RISKANTE_METHODEN = {"unlink", "rmdir", "write_text", "write_bytes", "touch", "chmod", "symlink_to", "hardlink_to"}
RISKANTE_NAMEN = {"eval", "exec", "__import__", "breakpoint"}


# ---------------------------------------------------------------- gguf-py laden

def lade_gguf():
    pfad = Path(os.environ.get("GGUF_PY", GGUF_PY_DEFAULT))
    if pfad.exists():
        sys.path.insert(0, str(pfad))
    try:
        import gguf  # noqa: F401
        from gguf import GGUFReader, GGUFWriter, GGMLQuantizationType, GGUFValueType, GGML_QUANT_SIZES
    except ImportError as e:
        sys.exit(f"ABBRUCH: gguf-py nicht ladbar ({e}).\n"
                 f"  Erwartet unter {pfad} (oder GGUF_PY=...), dazu numpy und pyyaml:\n"
                 f"  .venv/bin/pip install numpy pyyaml")
    return GGUFReader, GGUFWriter, GGMLQuantizationType, GGUFValueType, GGML_QUANT_SIZES


# ---------------------------------------------------------------- synthetische Dateien

def _tensor_bytes(np, name_idx: int, ne: list[int], qtype, sizes) -> tuple:
    """Rohbytes + numpy-Byteform (umgekehrte Reihenfolge, letzte Dim in Bytes) für ggml-Form `ne`."""
    bs, ts = sizes[qtype]
    assert ne[0] % bs == 0, (qtype, ne)
    n_elem = math.prod(ne)
    n_bytes = n_elem * ts // bs
    byte_shape = list(reversed(ne))
    byte_shape[-1] = ne[0] // bs * ts
    rng = np.random.default_rng(1000 + name_idx)
    data = rng.integers(0, 256, size=n_bytes, dtype=np.uint8).reshape(byte_shape)
    return data


def erzeuge_synth(ziel: Path, typen: list[str], mit_metadaten: bool) -> Path:
    import numpy as np
    _, GGUFWriter, Q, V, sizes = lade_gguf()
    ziel.parent.mkdir(parents=True, exist_ok=True)
    w = GGUFWriter(str(ziel), arch="synth")
    w.add_custom_alignment(64)
    if mit_metadaten:
        w.add_uint8("t.u8", 200)
        w.add_int8("t.i8", -5)
        w.add_uint16("t.u16", 60000)
        w.add_int16("t.i16", -30000)
        w.add_uint32("t.u32", 4_000_000_000)
        w.add_int32("t.i32", -123456)
        w.add_float32("t.f32", 3.140625)
        w.add_bool("t.bool_wahr", True)
        w.add_bool("t.bool_falsch", False)
        w.add_string("t.str", "Grüße aus dem Lab ✓")
        w.add_uint64("t.u64", 2**40 + 3)
        w.add_int64("t.i64", -(2**40))
        w.add_float64("t.f64", 2.718281828459045)
        w.add_key_value("t.arr_u8", [1, 2, 250], V.ARRAY, sub_type=V.UINT8)
        w.add_key_value("t.arr_i32", list(range(-3, 9)), V.ARRAY, sub_type=V.INT32)
        w.add_key_value("t.arr_f32", [0.5, -1.25, 8.0], V.ARRAY, sub_type=V.FLOAT32)
        w.add_key_value("t.arr_str", ["eins", "zwei", "drei", "ä", "", "fünf", "6", "sieben", "acht", "neun"],
                        V.ARRAY, sub_type=V.STRING)
        w.add_key_value("t.arr_bool", [True, False, True], V.ARRAY, sub_type=V.BOOL)
        w.add_key_value("t.arr_u64", [2**33, 1], V.ARRAY, sub_type=V.UINT64)
        w.add_key_value("t.arr_f64", [1.0e-300, 7.5], V.ARRAY, sub_type=V.FLOAT64)
        w.add_key_value("t.arr_verschachtelt", [[1, 2], [3, 4, 5]], V.ARRAY)
    formen = []
    for i, name in enumerate(typen):
        bs, _ = sizes[Q[name]]
        k = max(bs, 32)
        formen.append([k * 2] if i % 3 == 0 else ([k, 3] if i % 3 == 1 else [k, 2, 2]))
    for i, (name, ne) in enumerate(zip(typen, formen)):
        q = Q[name]
        data = _tensor_bytes(np, i, ne, q, sizes)
        w.add_tensor(f"tensor_{i:02d}_{name.lower()}", data, raw_shape=data.shape, raw_dtype=q)
    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()
    return ziel


def cmd_synth(_a) -> int:
    d1 = erzeuge_synth(PRUEFDATEIEN / "synth_klassisch.gguf", KLASSISCH, True)
    bonus = erzeuge_synth(PRUEFDATEIEN / "synth_neu.gguf", NEU, False)
    for p in (d1, bonus):
        r = referenz(p, neu_rechnen=True)
        print(f"{p.name}: {r['tensor_count']} Tensoren, {r['kv_count']} KV, alignment {r['alignment']}, "
              f"{p.stat().st_size} Byte, ok={r['ok']}")
    return 0


# ---------------------------------------------------------------- Referenz aus gguf-py

def _str(part) -> str:
    return bytes(part).decode("utf-8", errors="replace")


def referenz_berechnen(pfad: Path) -> dict:
    GGUFReader, _, _, V, _ = lade_gguf()
    r = GGUFReader(str(pfad))
    meta = {}
    for name, f in r.fields.items():
        if name.startswith("GGUF."):
            continue
        t0 = int(f.types[0])
        if t0 == int(V.ARRAY):
            item = int(f.parts[3][0])
            laenge = int(f.parts[4][0])
            eintrag = {"type_id": t0, "item_type_id": item, "len": laenge}
            if item == int(V.ARRAY):
                eintrag["value"] = None                       # verschachtelt: nur len gewertet
            elif item == int(V.STRING):
                eintrag["value"] = [_str(f.parts[i]) for i in f.data[:8]]
            else:
                eintrag["value"] = [f.parts[i].tolist()[0] for i in f.data[:8]]
            meta[name] = eintrag
        elif t0 == int(V.STRING):
            meta[name] = {"type_id": t0, "value": _str(f.parts[-1])}
        else:
            meta[name] = {"type_id": t0, "value": f.parts[-1].tolist()[0]}
    tensoren = []
    for t in r.tensors:
        tensoren.append({"name": t.name, "shape": [int(x) for x in t.field.parts[3]],
                         "type": t.tensor_type.name, "type_id": int(t.tensor_type),
                         "offset": int(t.field.parts[5][0]), "n_bytes": int(t.n_bytes)})
    data_offset = int(r.data_offset)
    alignment = int(r.alignment)
    ende = data_offset + max((t["offset"] + t["n_bytes"] for t in tensoren), default=0)
    groesse = pfad.stat().st_size
    return {"version": int(r.fields["GGUF.version"].parts[0][0]),
            "tensor_count": int(r.fields["GGUF.tensor_count"].parts[0][0]),
            "kv_count": int(r.fields["GGUF.kv_count"].parts[0][0]),
            "alignment": alignment, "data_offset": data_offset, "metadata": meta, "tensors": tensoren,
            "end": ende, "file_size": groesse, "ok": ende <= groesse and groesse - ende < alignment}


def referenz(pfad: Path, neu_rechnen: bool = False) -> dict:
    """Referenz je Datei zwischenspeichern (Schlüssel: Name + Größe + mtime)."""
    st = pfad.stat()
    cache = PRUEFDATEIEN / f"ref_{pfad.name}_{st.st_size}_{int(st.st_mtime)}.json"
    if cache.exists() and not neu_rechnen:
        return json.loads(cache.read_text(encoding="utf-8"))
    ref = referenz_berechnen(pfad)
    PRUEFDATEIEN.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(ref, ensure_ascii=False), encoding="utf-8")
    return ref


def cmd_referenz(a) -> int:
    for p in a.dateien:
        p = Path(p)
        r = referenz(p, neu_rechnen=True)
        typen = sorted({t["type"] for t in r["tensors"]})
        print(f"{p.name}: v{r['version']}, {r['tensor_count']} Tensoren, {r['kv_count']} KV, "
              f"alignment {r['alignment']}, data_offset {r['data_offset']}, Rest {r['file_size'] - r['end']}, "
              f"ok={r['ok']}, Typen {', '.join(typen)}")
    return 0


# ---------------------------------------------------------------- Kandidat prüfen und ausführen

def is_stdlib(modul: str) -> bool:
    return modul.split(".")[0] in sys.stdlib_module_names


def code_pruefen(code: str) -> dict:
    """Statische Prüfung: verbotene (Nicht-Standard-)Imports und riskante Module/Aufrufe."""
    try:
        baum = ast.parse(code)
    except SyntaxError as e:
        return {"syntax": f"{e.msg} (Zeile {e.lineno})", "verboten": [], "riskant": []}
    verboten, riskant = set(), set()
    for k in ast.walk(baum):
        module = []
        if isinstance(k, ast.Import):
            module = [n.name for n in k.names]
        elif isinstance(k, ast.ImportFrom) and k.module and k.level == 0:
            module = [k.module]
        for m in module:
            if not is_stdlib(m):
                verboten.add(m)
            elif m.split(".")[0] in RISKANTE_MODULE:
                riskant.add(f"import {m}")
        if isinstance(k, ast.Call):
            f = k.func
            if isinstance(f, ast.Name) and f.id in RISKANTE_NAMEN:
                riskant.add(f"Aufruf {f.id}() Zeile {k.lineno}")
            elif isinstance(f, ast.Attribute):
                os_aufruf = isinstance(f.value, ast.Name) and f.value.id == "os" and f.attr in RISKANTE_OS
                if os_aufruf or f.attr in RISKANTE_METHODEN:
                    riskant.add(f"Aufruf .{f.attr}() Zeile {k.lineno}")
        if isinstance(k, ast.Call) and isinstance(k.func, ast.Name) and k.func.id == "open":
            for arg in k.args[1:2]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and set(arg.value) & set("wax+"):
                    riskant.add(f"open(..., {arg.value!r}) Zeile {k.lineno}")
    return {"syntax": None, "verboten": sorted(verboten), "riskant": sorted(riskant)}


def kandidat_ausfuehren(skript: Path, gguf: Path, zeitgrenze: int = ZEITGRENZE) -> dict:
    skript, gguf = Path(skript).resolve(), Path(gguf).resolve()     # cwd wird der Temp-Ordner
    with tempfile.TemporaryDirectory(prefix="wb_gguf_") as tmp:
        try:
            p = subprocess.run([sys.executable, "-I", str(skript), str(gguf)], cwd=tmp,
                               capture_output=True, timeout=zeitgrenze, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return {"fehler": f"Zeitüberschreitung {zeitgrenze} s"}
    if p.returncode != 0:
        return {"fehler": f"Exit {p.returncode}: " + p.stderr.decode("utf-8", "replace").strip()[-600:]}
    text = p.stdout.decode("utf-8", "replace").strip()
    try:
        return {"json": json.loads(text)}
    except json.JSONDecodeError as e:
        return {"fehler": f"kein gültiges JSON ({e.msg}); Anfang: {text[:200]!r}"}


# ---------------------------------------------------------------- Vergleich

def _gleich(a, b) -> bool:
    """Werte vergleichen: bool streng, Zahlen numerisch (float32-genau), Listen elementweise."""
    if isinstance(b, bool) or isinstance(a, bool):
        return type(a) is type(b) and a == b
    if isinstance(b, (int, float)) and isinstance(a, (int, float)):
        if isinstance(b, float) or isinstance(a, float):
            if math.isnan(b):
                return isinstance(a, float) and math.isnan(a)
            return a == b or math.isclose(a, b, rel_tol=1e-6, abs_tol=0.0)
        return a == b
    if isinstance(b, list) and isinstance(a, list):
        return len(a) == len(b) and all(_gleich(x, y) for x, y in zip(a, b))
    return a == b


def _int(x):
    return x if isinstance(x, int) and not isinstance(x, bool) else None


def vergleichen(k: dict, r: dict) -> dict:
    """8 binäre Punkte + Anteile + Beispiele für Abweichungen."""
    p, info = {}, {}
    p["kopf"] = all(_int(k.get(x)) == r[x] for x in ("version", "tensor_count", "kv_count"))

    km = k.get("metadata") if isinstance(k.get("metadata"), dict) else {}
    rm = r["metadata"]
    fehlend = sorted(set(rm) - set(km))
    extra = sorted(set(km) - set(rm))
    typ_falsch = [s for s in rm if s in km and (not isinstance(km[s], dict) or _int(km[s].get("type_id")) != rm[s]["type_id"])]
    p["meta_typen"] = not fehlend and not extra and not typ_falsch
    info["meta_typen"] = {"fehlend": fehlend[:5], "extra": extra[:5], "typ_falsch": typ_falsch[:5],
                          "anteil": f"{len(rm) - len(set(fehlend) | set(typ_falsch))}/{len(rm)}"}

    skalare = [s for s in rm if "item_type_id" not in rm[s]]
    sk_falsch = [s for s in skalare if not (isinstance(km.get(s), dict) and _gleich(km[s].get("value"), rm[s]["value"]))]
    p["meta_skalare"] = not sk_falsch
    info["meta_skalare"] = {"falsch": [(s, (km.get(s) or {}).get("value") if isinstance(km.get(s), dict) else None,
                                        rm[s]["value"]) for s in sk_falsch[:5]],
                            "anteil": f"{len(skalare) - len(sk_falsch)}/{len(skalare)}"}

    arrays = [s for s in rm if "item_type_id" in rm[s]]
    ar_falsch = []
    for s in arrays:
        kv = km.get(s) if isinstance(km.get(s), dict) else {}
        ok = _int(kv.get("item_type_id")) == rm[s]["item_type_id"] and _int(kv.get("len")) == rm[s]["len"]
        if ok and rm[s]["value"] is not None:
            kw = kv.get("value")
            ok = isinstance(kw, list) and _gleich(kw[:8], rm[s]["value"])
        if not ok:
            ar_falsch.append(s)
    p["meta_arrays"] = not ar_falsch
    info["meta_arrays"] = {"falsch": ar_falsch[:5], "anteil": f"{len(arrays) - len(ar_falsch)}/{len(arrays)}"}

    kt = k.get("tensors") if isinstance(k.get("tensors"), list) else []
    rt = r["tensors"]
    ti_falsch, nb_falsch = [], []
    for i, t in enumerate(rt):
        c = kt[i] if i < len(kt) and isinstance(kt[i], dict) else {}
        if not (c.get("name") == t["name"] and _gleich(c.get("shape"), t["shape"])
                and _int(c.get("type_id")) == t["type_id"] and _int(c.get("offset")) == t["offset"]):
            ti_falsch.append(t["name"])
        if not (_int(c.get("n_bytes")) == t["n_bytes"]
                and str(c.get("type", "")).upper() == t["type"].upper()):
            nb_falsch.append(f"{t['name']} ({t['type']}: {c.get('type')} {c.get('n_bytes')} statt {t['n_bytes']})")
    if len(kt) != len(rt):
        ti_falsch.append(f"Anzahl {len(kt)} statt {len(rt)}")
    p["tensor_infos"] = not ti_falsch
    p["n_bytes"] = not nb_falsch and len(kt) == len(rt)
    info["tensor_infos"] = {"falsch": ti_falsch[:5], "anteil": f"{len(rt) - len(ti_falsch)}/{len(rt)}"}
    info["n_bytes"] = {"falsch": nb_falsch[:8], "anteil": f"{len(rt) - len(nb_falsch)}/{len(rt)}"}

    p["alignment_offset"] = _int(k.get("alignment")) == r["alignment"] and _int(k.get("data_offset")) == r["data_offset"]
    info["alignment_offset"] = {"kandidat": [k.get("alignment"), k.get("data_offset")],
                                "referenz": [r["alignment"], r["data_offset"]]}
    p["ende"] = (_int(k.get("end")) == r["end"] and _int(k.get("file_size")) == r["file_size"]
                 and k.get("ok") is r["ok"])
    info["ende"] = {"kandidat": [k.get("end"), k.get("file_size"), k.get("ok")],
                    "referenz": [r["end"], r["file_size"], r["ok"]]}
    return {"punkte": p, "summe": sum(1 for v in p.values() if v), "info": info}


# ---------------------------------------------------------------- Bewertung eines Laufordners

def lauf_bewerten(lauf: Path, dateien: list[Path], trotzdem: bool) -> dict:
    skript = lauf / "gguf_lesen.py"
    gewertet = [d for d in dateien if d.name != BONUS]
    erg = {"lauf": str(lauf), "dateien": {}, "summe": 0, "max": 8 * len(gewertet), "status": "ok"}
    if not skript.exists():
        erg["status"] = "kein Code"
        return erg
    pruef = code_pruefen(skript.read_text(encoding="utf-8"))
    erg["code"] = pruef
    if pruef["syntax"]:
        erg["status"] = f"Syntaxfehler: {pruef['syntax']}"
        return erg
    if pruef["verboten"]:
        erg["status"] = f"DISQUALIFIZIERT: Import {', '.join(pruef['verboten'])}"
        return erg
    if pruef["riskant"] and not trotzdem:
        erg["status"] = f"NICHT AUSGEFÜHRT (riskant: {'; '.join(pruef['riskant'])}) – Code lesen, dann --trotzdem"
        return erg
    for d in dateien:
        ref = referenz(d)
        lauf_e = kandidat_ausfuehren(skript, d)
        if "fehler" in lauf_e:
            erg["dateien"][d.name] = {"summe": 0, "fehler": lauf_e["fehler"]}
            continue
        v = vergleichen(lauf_e["json"], ref)
        erg["dateien"][d.name] = v
        if d.name != BONUS:
            erg["summe"] += v["summe"]
    return erg


def bericht_md(erg: dict) -> str:
    z = [f"# Bewertung {Path(erg['lauf']).name}", "", f"Status: {erg['status']} · Teil A: **{erg['summe']} / {erg['max']}**", ""]
    if erg.get("code", {}).get("riskant"):
        z += [f"Riskant markiert: {'; '.join(erg['code']['riskant'])}", ""]
    if erg["dateien"]:
        z += ["| Datei | " + " | ".join(PUNKTE) + " | Summe |", "|---|" + "---|" * (len(PUNKTE) + 1)]
        for name, v in erg["dateien"].items():
            if "fehler" in v:
                z.append(f"| {name} | " + " | ".join("–" for _ in PUNKTE) + " | 0 |")
            else:
                z.append(f"| {name} | " + " | ".join("✓" if v["punkte"][x] else "✗" for x in PUNKTE)
                         + f" | {v['summe']} |")
        z.append("")
        for name, v in erg["dateien"].items():
            z.append(f"## {name}")
            if "fehler" in v:
                z += ["", f"Fehler: `{v['fehler']}`", ""]
                continue
            for x in PUNKTE:
                if not v["punkte"][x] and x in v["info"]:
                    z.append(f"- **{x}**: {json.dumps(v['info'][x], ensure_ascii=False)[:600]}")
                elif x in v["info"] and "anteil" in v["info"][x]:
                    z.append(f"- {x}: {v['info'][x]['anteil']}")
            z.append("")
    wissen = Path(erg["lauf"]) / "wissen.json"
    if wissen.exists():
        w = json.loads(wissen.read_text(encoding="utf-8"))
        z += ["## Teil B (von Hand gegen den Schlüssel bewerten)", ""]
        for eintrag in w:
            antwort = " ".join((eintrag.get("antwort") or eintrag.get("fehler") or "(leer)").split())
            z.append(f"- **{eintrag['id']}** {eintrag['frage']}  \n  → {antwort[:700]}")
        z.append("")
    return "\n".join(z) + "\n"


def cmd_bewerten(a) -> int:
    dateien = [PRUEFDATEIEN / "synth_klassisch.gguf"] + [Path(d) for d in a.dateien]
    if not dateien[0].exists():
        print("synth_klassisch.gguf fehlt -> erst `pruefen.py synth`."); return 1
    if a.bonus:
        dateien.append(PRUEFDATEIEN / BONUS)
    for d in dateien:
        if not d.exists():
            print(f"ABBRUCH: {d} fehlt (externe SSD?)"); return 1
    for d in dateien:
        referenz(d)                                     # einmal vorab, damit Fehler früh auffallen
    laeufe = []
    for o in a.ordner:
        o = Path(o)
        if o.suffix == ".gguf":
            print(f"ABBRUCH: {o} steht bei den Ergebnisordnern – Ordner zuerst, dann --dateien"); return 1
        laeufe += sorted(p for p in o.glob("lauf*") if p.is_dir()) if not (o / "gguf_lesen.py").exists() else [o]
    for lauf in laeufe:
        erg = lauf_bewerten(lauf, dateien, a.trotzdem)
        (lauf / "bewertung.json").write_text(json.dumps(erg, ensure_ascii=False, indent=1), encoding="utf-8")
        (lauf / "bewertung.md").write_text(bericht_md(erg), encoding="utf-8")
        print(f"{lauf}: {erg['status']} · Teil A {erg['summe']}/{erg['max']} · "
              + " ".join(f"{n}={v.get('summe', 0)}" for n, v in erg["dateien"].items()))
    return 0


def cmd_tabelle(a) -> int:
    zeilen = ["| Lauf | Status | Teil A | D1 Quant-Größen (n_bytes) |", "|---|---|---|---|"]
    for o in a.ordner:
        for b in sorted(Path(o).glob("**/bewertung.json")):
            e = json.loads(b.read_text(encoding="utf-8"))
            d1 = e["dateien"].get("synth_klassisch.gguf", {})
            nb = "✓" if d1.get("punkte", {}).get("n_bytes") else ("–" if "fehler" in d1 or not d1 else
                                                                  "✗ " + d1["info"]["n_bytes"]["anteil"])
            zeilen.append(f"| {b.parent.relative_to(HERE) if HERE in b.parents else b.parent} | {e['status'][:40]} | "
                          f"{e['summe']}/{e['max']} | {nb} |")
    print("\n".join(zeilen))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Wissensbreite GGUF – Prüfer")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("synth", help="synthetische Prüfdateien erzeugen")
    r = sub.add_parser("referenz", help="Referenz für echte Dateien rechnen und anzeigen")
    r.add_argument("dateien", nargs="+")
    b = sub.add_parser("bewerten", help="Laufordner bewerten")
    b.add_argument("--dateien", nargs="*", default=[],
                   help="echte GGUF-Dateien (D2–D4); NACH den Ergebnisordnern angeben")
    b.add_argument("--bonus", action="store_true", help="synth_neu.gguf zusätzlich (nicht gewertet)")
    b.add_argument("--trotzdem", action="store_true", help="auch riskant markierten Code ausführen")
    b.add_argument("ordner", nargs="+", help="Ergebnisordner eines Modells oder einzelne lauf*-Ordner")
    t = sub.add_parser("tabelle", help="Übersicht über bewertete Läufe")
    t.add_argument("ordner", nargs="+")
    a = ap.parse_args(argv)
    return {"synth": cmd_synth, "referenz": cmd_referenz, "bewerten": cmd_bewerten, "tabelle": cmd_tabelle}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
