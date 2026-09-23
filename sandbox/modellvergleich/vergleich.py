#!/usr/bin/env python3
"""
Modellvergleich über die lokale Ollama-Schnittstelle — Nebenstrang, außerhalb des Repos.

Zweck: Zwei (oder mehr) lokale Modelle bekommen exakt denselben festgehaltenen
Kontext und dieselben Fragen. Gemessen wird nicht, wer klüger klingt, sondern:
  1. Treue zum gelieferten Kontext
  2. ehrliches "weiß ich nicht" bei dünner Grundlage
  3. deutsche Tonalität
Achse 1 und 3 bewertet ein Mensch (Bewertungsbogen im Bericht). Das Skript
liefert Tempo-Messwerte, Abschneide-Warnungen und zwei grobe Heuristiken —
Heuristiken sind Hinweise, kein Urteil.

Nur Standardbibliothek. Aufruf:
  python3 vergleich.py faelle.json
  python3 vergleich.py faelle.json --modelle mistral-small3.2:24b qwen3.6:35b-a3b --blind
"""

import argparse
import datetime as dt
import hashlib
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

STANDARD_MODELLE = ["mistral-small3.2:24b", "qwen3.6:35b-a3b"]

STANDARD_SYSTEMPROMPT = (
    "Du bist ein Assistent, der ausschließlich auf Grundlage des bereitgestellten "
    "Kontexts antwortet. Antworte auf Deutsch, sachlich und freundlich. "
    "Wenn der Kontext die Frage nicht beantwortet, sage das offen und erfinde nichts."
)

# Grobe Heuristik: Formulierungen, mit denen ein Modell Nichtwissen einräumt.
NICHTWISSEN_MUSTER = [
    r"nicht im (bereitgestellten |vorliegenden |gegebenen )?kontext",
    r"keine (genauen |konkreten )?(information|angabe|hinweis)",
    r"(liegen|habe) (mir )?keine",
    r"weiß ich nicht",
    r"kann ich (leider )?nicht (sagen|beantworten|entnehmen)",
    r"lässt sich (dem kontext )?nicht entnehmen",
    r"geht (aus dem kontext )?nicht hervor",
    r"nicht (genannt|erwähnt|enthalten)",
]


def ollama(basis, pfad, nutzlast=None, timeout=900):
    """Einfacher HTTP-Aufruf; gibt (status, json) zurück, wirft nicht bei 4xx."""
    daten = json.dumps(nutzlast).encode() if nutzlast is not None else None
    anfrage = urllib.request.Request(
        basis + pfad, data=daten,
        headers={"Content-Type": "application/json"},
        method="POST" if daten else "GET",
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=timeout) as antwort:
            return antwort.status, json.loads(antwort.read())
    except urllib.error.HTTPError as fehler:
        text = fehler.read().decode(errors="replace")
        try:
            return fehler.code, json.loads(text)
        except json.JSONDecodeError:
            return fehler.code, {"error": text}


def umgebung(basis, modelle):
    """Datenstand festhalten: Ollama-Version und Modell-Digests."""
    _, version = ollama(basis, "/api/version")
    _, tags = ollama(basis, "/api/tags")
    vorhanden = {m["name"]: m for m in tags.get("models", [])}
    info = {"ollama_version": version.get("version"), "modelle": {}}
    fehlend = []
    for m in modelle:
        eintrag = vorhanden.get(m) or vorhanden.get(m + ":latest")
        if not eintrag:
            fehlend.append(m)
            continue
        details = eintrag.get("details", {})
        info["modelle"][m] = {
            "digest": eintrag.get("digest", "")[:12],
            "groesse_gb": round(eintrag.get("size", 0) / 1e9, 1),
            "quantisierung": details.get("quantization_level"),
            "parameter": details.get("parameter_size"),
        }
    return info, fehlend


def nachricht(fall, systemprompt):
    kontext = fall.get("kontext", "").strip() or "(kein Kontext gefunden)"
    nutzer = f"Kontext:\n---\n{kontext}\n---\n\nFrage: {fall['frage']}"
    return [
        {"role": "system", "content": fall.get("systemprompt", systemprompt)},
        {"role": "user", "content": nutzer},
    ]


def frage_stellen(basis, modell, nachrichten, optionen, denken):
    nutzlast = {"model": modell, "messages": nachrichten, "stream": False,
                "options": optionen, "keep_alive": "10m"}
    if denken is not None:
        nutzlast["think"] = denken
    status, antwort = ollama(basis, "/api/chat", nutzlast)
    hinweis = None
    # Modelle ohne Denkmodus lehnen den Schalter ab -> einmal ohne wiederholen.
    if status == 400 and denken is not None and "think" in str(antwort.get("error", "")).lower():
        nutzlast.pop("think")
        status, antwort = ollama(basis, "/api/chat", nutzlast)
        hinweis = "Denk-Schalter vom Modell abgelehnt, ohne Schalter wiederholt"
    if status != 200:
        raise RuntimeError(f"{modell}: HTTP {status}: {antwort.get('error')}")
    return antwort, hinweis


def bereinigen(text):
    """Denkblöcke entfernen, falls ein Modell sie in den Inhalt schreibt."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def auswerten(fall, antwort, roh, num_ctx):
    text_klein = antwort.lower()
    raeumt_ein = any(re.search(m, text_klein) for m in NICHTWISSEN_MUSTER)
    erwartung = fall.get("erwartung", "antwortbar")
    befund = {
        "raeumt_nichtwissen_ein": raeumt_ein,
        "heuristik_nichtwissen": (
            "passt" if raeumt_ein == (erwartung == "nicht_antwortbar") else "prüfen"
        ),
    }
    muss = fall.get("muss_enthalten", [])
    if muss:
        fehlt = [s for s in muss if s.lower() not in text_klein]
        befund["muss_enthalten_fehlt"] = fehlt
    verboten = fall.get("darf_nicht_enthalten", [])
    if verboten:
        befund["verbotenes_gefunden"] = [s for s in verboten if s.lower() in text_klein]

    prompt_tokens = roh.get("prompt_eval_count", 0)
    befund["prompt_tokens"] = prompt_tokens
    befund["abschneide_warnung"] = prompt_tokens >= 0.95 * num_ctx
    eval_n, eval_ns = roh.get("eval_count", 0), roh.get("eval_duration", 0)
    pe_n, pe_ns = prompt_tokens, roh.get("prompt_eval_duration", 0)
    befund["antwort_tokens"] = eval_n
    befund["tok_s_generierung"] = round(eval_n / (eval_ns / 1e9), 1) if eval_ns else None
    befund["tok_s_prompt"] = round(pe_n / (pe_ns / 1e9), 1) if pe_ns else None
    befund["gesamt_s"] = round(roh.get("total_duration", 0) / 1e9, 1)
    return befund


def modell_entladen(basis, modell):
    ollama(basis, "/api/generate", {"model": modell, "keep_alive": 0})


def bericht_schreiben(pfad, meta, faelle, ergebnisse, blind, schluessel):
    z = []
    z.append(f"# Modellvergleich — {meta['zeitpunkt']}\n")
    z.append("Nebenstrang, außerhalb des Repos. Heuristiken sind Hinweise, kein Urteil.\n")
    z.append("## Datenstand\n")
    z.append(f"- Fälle: `{meta['faelle_datei']}` (SHA-256 {meta['faelle_hash']})")
    z.append(f"- Ollama {meta['umgebung']['ollama_version']}, Optionen: `{json.dumps(meta['optionen'])}`, "
             f"Denkmodus: {meta['denken']}")
    for m, d in meta["umgebung"]["modelle"].items():
        z.append(f"- `{m}` — Digest {d['digest']}, {d['parameter']}, {d['quantisierung']}, {d['groesse_gb']} GB")
    z.append("")

    if not blind:
        z.append("## Tempo und Heuristiken je Modell\n")
        z.append("| Modell | Ø tok/s Antwort | Ø tok/s Prompt | Ø Sekunden | Nichtwissen-Heuristik „prüfen“ | Abschneide-Warnungen |")
        z.append("|---|---|---|---|---|---|")
        for m in meta["modelle"]:
            reihe = [e for e in ergebnisse if e["modell"] == m and "fehler" not in e]
            if not reihe:
                z.append(f"| `{m}` | – | – | – | – | – |")
                continue
            def mittel(schl):
                werte = [e["befund"][schl] for e in reihe if e["befund"].get(schl)]
                return round(sum(werte) / len(werte), 1) if werte else "–"
            pruefen = sum(e["befund"]["heuristik_nichtwissen"] == "prüfen" for e in reihe)
            warn = sum(e["befund"]["abschneide_warnung"] for e in reihe)
            z.append(f"| `{m}` | {mittel('tok_s_generierung')} | {mittel('tok_s_prompt')} | "
                     f"{mittel('gesamt_s')} | {pruefen}/{len(reihe)} | {warn} |")
        z.append("")

    z.append("## Antworten und Bewertungsbogen\n")
    z.append("Bewertung je Antwort 0–2: **K** Kontexttreue (0 = erfindet, 2 = nur Belegtes) · "
             "**N** Nichtwissen (bei nicht antwortbaren Fällen: 0 = erfindet, 2 = sagt es offen; sonst n/a) · "
             "**T** Tonalität Deutsch (0 = hölzern/übersetzt, 2 = natürlich).\n")
    for fall in faelle:
        z.append(f"### {fall['id']} — {fall['frage']}\n")
        z.append(f"Erwartung: *{fall.get('erwartung', 'antwortbar')}*"
                 + (f" · Notiz: {fall['notiz']}" if fall.get("notiz") else "") + "\n")
        eintraege = [e for e in ergebnisse if e["fall"] == fall["id"]]
        if blind:
            random.shuffle(eintraege)
        for i, e in enumerate(eintraege, 1):
            etikett = f"Antwort {i}" if blind else f"`{e['modell']}`"
            if blind:
                schluessel.setdefault(fall["id"], {})[f"Antwort {i}"] = e["modell"]
            z.append(f"**{etikett}**\n")
            if "fehler" in e:
                z.append(f"> Fehler: {e['fehler']}\n")
                continue
            z.append("> " + e["antwort"].replace("\n", "\n> ") + "\n")
            b = e["befund"]
            hinweise = [f"Heuristiken Nichtwissen: {b['heuristik_nichtwissen']}"]
            if not blind:
                hinweise.append(f"{b['tok_s_generierung']} tok/s, {b['gesamt_s']} s")
            if b.get("muss_enthalten_fehlt"):
                hinweise.append(f"fehlt: {', '.join(b['muss_enthalten_fehlt'])}")
            if b.get("verbotenes_gefunden"):
                hinweise.append(f"verboten gefunden: {', '.join(b['verbotenes_gefunden'])}")
            if b["abschneide_warnung"]:
                hinweise.append("⚠ Prompt nahe num_ctx — Kontext evtl. abgeschnitten")
            z.append("*" + " · ".join(hinweise) + "*\n")
            z.append("K: __ · N: __ · T: __ · Anmerkung: \n")
    pfad.write_text("\n".join(z), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Lokaler Modellvergleich über Ollama")
    p.add_argument("faelle", type=Path, help="JSON-Datei mit Fällen")
    p.add_argument("--modelle", nargs="+", default=STANDARD_MODELLE)
    p.add_argument("--basis", default="http://localhost:11434")
    p.add_argument("--num-ctx", type=int, default=16384)
    p.add_argument("--temperatur", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--denken", choices=["aus", "an", "standard"], default="aus",
                   help="Denkmodus: aus (fair für Modelle ohne Denkmodus), an, standard (Schalter weglassen)")
    p.add_argument("--systemprompt", type=Path, help="Datei mit eigenem Systemprompt")
    p.add_argument("--blind", action="store_true",
                   help="Bericht ohne Modellnamen, zufällige Reihenfolge; Schlüssel in separater Datei")
    p.add_argument("--ausgabe", type=Path, default=Path("ergebnisse"))
    a = p.parse_args()

    faelle_roh = a.faelle.read_bytes()
    faelle = json.loads(faelle_roh)
    systemprompt = a.systemprompt.read_text(encoding="utf-8") if a.systemprompt else STANDARD_SYSTEMPROMPT
    optionen = {"num_ctx": a.num_ctx, "temperature": a.temperatur,
                "seed": a.seed, "num_predict": a.max_tokens}
    denken = {"aus": False, "an": True, "standard": None}[a.denken]

    try:
        info, fehlend = umgebung(a.basis, a.modelle)
    except urllib.error.URLError as fehler:
        sys.exit(f"Ollama unter {a.basis} nicht erreichbar: {fehler}")
    if fehlend:
        sys.exit("Nicht installiert: " + ", ".join(fehlend) + "\n-> ollama pull <name>")

    zeit = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    a.ausgabe.mkdir(parents=True, exist_ok=True)
    meta = {"zeitpunkt": zeit, "faelle_datei": str(a.faelle),
            "faelle_hash": hashlib.sha256(faelle_roh).hexdigest()[:12],
            "umgebung": info, "optionen": optionen, "denken": a.denken,
            "modelle": a.modelle}
    ergebnisse = []

    # Modelle strikt nacheinander: 48 GB tragen nicht beide samt Kontext-Cache.
    for modell in a.modelle:
        print(f"\n== {modell}: aufwärmen (Ladezeit zählt nicht) ...", flush=True)
        try:
            frage_stellen(a.basis, modell, [{"role": "user", "content": "Hallo"}],
                          {**optionen, "num_predict": 8}, denken)
        except RuntimeError as fehler:
            print(f"   Aufwärmen fehlgeschlagen: {fehler}")
        for fall in faelle:
            print(f"   {fall['id']} ...", end=" ", flush=True)
            eintrag = {"modell": modell, "fall": fall["id"]}
            try:
                roh, hinweis = frage_stellen(a.basis, modell, nachricht(fall, systemprompt),
                                             optionen, denken)
                text = bereinigen(roh.get("message", {}).get("content", ""))
                eintrag.update(antwort=text, befund=auswerten(fall, text, roh, a.num_ctx),
                               denkanteil_zeichen=len(roh.get("message", {}).get("thinking", "") or ""))
                if hinweis:
                    eintrag["hinweis"] = hinweis
                print(f"{eintrag['befund']['tok_s_generierung']} tok/s")
            except RuntimeError as fehler:
                eintrag["fehler"] = str(fehler)
                print("Fehler")
            ergebnisse.append(eintrag)
        modell_entladen(a.basis, modell)
        time.sleep(2)

    roh_pfad = a.ausgabe / f"{zeit}_roh.jsonl"
    with roh_pfad.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"meta": meta}, ensure_ascii=False) + "\n")
        for e in ergebnisse:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    schluessel = {}
    bericht_pfad = a.ausgabe / f"{zeit}_bericht.md"
    bericht_schreiben(bericht_pfad, meta, faelle, ergebnisse, a.blind, schluessel)
    print(f"\nRohdaten: {roh_pfad}\nBericht:  {bericht_pfad}")
    if a.blind:
        schl_pfad = a.ausgabe / f"{zeit}_schluessel.json"
        schl_pfad.write_text(json.dumps(schluessel, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Schlüssel: {schl_pfad}  (erst nach der Bewertung öffnen)")


if __name__ == "__main__":
    main()
