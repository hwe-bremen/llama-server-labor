#!/usr/bin/env python3
"""
probe_mcp.py — Stufe-4-Messsonde (Experiment, kein Bestandteil des Lab-Servers)

Frage: Wie verhaelt sich die Web-UI (8092 -> 8091 -> 8080 --ui-mcp-proxy -> MCP)
bei einem Werkzeugaufruf, der lange dauert? Und wie zeigt sie eine sofortige
Rueckmeldung "Lauf gestartet" an, die man spaeter per Status abfragt?

Werkzeuge (nur diese vier, keine Datei-, Shell- oder Netzwerkzugriffe):
    probe_warten(sekunden)              blockiert N s, dann Antwort
    probe_warten_fortschritt(sekunden)  wie oben, meldet alle 5 s Fortschritt
    probe_start(sekunden)               kehrt sofort zurueck, "Lauf" im Hintergrund
    probe_status(lauf_id)               Stand des Hintergrund-Laufs

Messung: Jeder Aufruf schreibt Start und Ende (ok / abgebrochen / fehler, Dauer)
als JSON-Zeile nach ~/.lab_mcp/probe_calls.jsonl und live ins Terminal.
Vergleich "Server meldet fertig nach X s" vs. "UI zeigt Fehler nach Y s" verraet,
wo in der Kette das Zeitlimit sitzt.

Sicherheit: bindet fest an 127.0.0.1 (nicht per Umgebungsvariable aenderbar).
Keine Pfade, keine freien Strings ausser lauf_id (Muster [a-f0-9]{8}).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP

HOST = "127.0.0.1"  # bewusst fest: Sonde wird nie exponiert
PORT = int(os.environ.get("PROBE_PORT", "8789"))
MAX_SEK = 1800
FORTSCHRITT_TAKT = 5
LOG = Path(
    os.path.expanduser(os.environ.get("PROBE_LOG", "~/.lab_mcp/probe_calls.jsonl"))
)
_ID_MUSTER = re.compile(r"^[a-f0-9]{8}$")

mcp = FastMCP("stufe4-probe", host=HOST, port=PORT)

_LOCK = threading.Lock()
_LAEUFE: dict[str, dict] = {}


# --------------------------------------------------------------------------
# Hilfen
# --------------------------------------------------------------------------
def _jetzt() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _log(**rec) -> None:
    rec = {"ts": _jetzt(), **rec}
    zeile = json.dumps(rec, ensure_ascii=False)
    print(f"[probe] {zeile}", file=sys.stderr, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(zeile + "\n")
    except OSError as e:
        print(f"[probe] Log-Schreibfehler: {e}", file=sys.stderr)


def begrenzen(sekunden) -> int:
    """Sekunden auf 1..MAX_SEK zwingen; Unsinn -> ValueError (fail-loud)."""
    try:
        n = int(sekunden)
    except (TypeError, ValueError):
        raise ValueError(f"sekunden muss eine ganze Zahl sein, nicht {sekunden!r}")
    return max(1, min(MAX_SEK, n))


def lauf_id_pruefen(lauf_id: str) -> str:
    if not isinstance(lauf_id, str) or not _ID_MUSTER.match(lauf_id):
        raise ValueError("lauf_id muss 8 Hex-Zeichen sein (aus probe_start)")
    return lauf_id


async def _warten(tool: str, sek: int, ctx: Context | None) -> str:
    t0 = time.monotonic()
    _log(tool=tool, ereignis="start", sekunden=sek)
    try:
        for i in range(sek):
            await asyncio.sleep(1)
            if ctx is not None and (i + 1) % FORTSCHRITT_TAKT == 0:
                await ctx.report_progress(i + 1, sek, f"{i + 1}/{sek} s")
    except asyncio.CancelledError:
        _log(tool=tool, ereignis="abgebrochen", nach_s=round(time.monotonic() - t0, 1))
        raise
    except Exception as e:
        _log(tool=tool, ereignis="fehler", nach_s=round(time.monotonic() - t0, 1),
             fehler=f"{type(e).__name__}: {e}")
        raise
    dauer = round(time.monotonic() - t0, 1)
    _log(tool=tool, ereignis="ok", nach_s=dauer)
    return f"{tool}: fertig nach {dauer} s (Serverzeit {_jetzt()})."


# --------------------------------------------------------------------------
# Hintergrund-Lauf (Muster fuer kette_lauf / kette_status)
# --------------------------------------------------------------------------
def _hintergrund(lauf_id: str, sek: int) -> None:
    time.sleep(sek)
    with _LOCK:
        _LAEUFE[lauf_id]["ende"] = time.monotonic()
    _log(tool="probe_start", ereignis="lauf_fertig", lauf_id=lauf_id, sekunden=sek)


def lauf_starten(sek: int) -> tuple[bool, str]:
    """(True, id) bei Start; (False, id_des_laufenden) bei Sperre."""
    with _LOCK:
        for lid, l in _LAEUFE.items():
            if l["ende"] is None:
                return False, lid
        lid = uuid.uuid4().hex[:8]
        _LAEUFE[lid] = {"start": time.monotonic(), "ende": None, "sekunden": sek}
    threading.Thread(target=_hintergrund, args=(lid, sek), daemon=True).start()
    return True, lid


def lauf_stand(lauf_id: str) -> str:
    with _LOCK:
        l = _LAEUFE.get(lauf_id)
        if l is None:
            return f"Unbekannte lauf_id {lauf_id} (Server neu gestartet?)."
        if l["ende"] is None:
            seit = round(time.monotonic() - l["start"])
            return f"Lauf {lauf_id}: laeuft seit {seit} s von ca. {l['sekunden']} s."
        return (f"Lauf {lauf_id}: fertig nach "
                f"{round(l['ende'] - l['start'], 1)} s.")


# --------------------------------------------------------------------------
# Werkzeuge
# --------------------------------------------------------------------------
@mcp.tool()
async def probe_warten(sekunden: int) -> str:
    """Messwerkzeug: wartet `sekunden` (1-1800) und antwortet erst dann."""
    return await _warten("probe_warten", begrenzen(sekunden), None)


@mcp.tool()
async def probe_warten_fortschritt(sekunden: int, ctx: Context) -> str:
    """Messwerkzeug: wie probe_warten, meldet aber alle 5 s Fortschritt."""
    return await _warten("probe_warten_fortschritt", begrenzen(sekunden), ctx)


@mcp.tool()
def probe_start(sekunden: int) -> str:
    """Messwerkzeug: startet einen Hintergrund-Lauf und kehrt SOFORT zurueck.
    Danach probe_status mit der gemeldeten lauf_id aufrufen."""
    sek = begrenzen(sekunden)
    ok, lid = lauf_starten(sek)
    if not ok:
        _log(tool="probe_start", ereignis="gesperrt", laufend=lid)
        return f"Abgelehnt: Lauf {lid} laeuft noch. Erst probe_status {lid}."
    _log(tool="probe_start", ereignis="gestartet", lauf_id=lid, sekunden=sek)
    return (f"Lauf gestartet: lauf_id={lid}, Dauer ca. {sek} s. "
            f"Stand mit probe_status(lauf_id=\"{lid}\") abfragen.")


@mcp.tool()
def probe_status(lauf_id: str) -> str:
    """Messwerkzeug: Stand eines mit probe_start begonnenen Laufs."""
    text = lauf_stand(lauf_id_pruefen(lauf_id))
    _log(tool="probe_status", ereignis="abfrage", lauf_id=lauf_id, antwort=text)
    return text


if __name__ == "__main__":
    print("=" * 56, file=sys.stderr)
    print(" Stufe-4-Sonde (Experiment)", file=sys.stderr)
    print(f"  URL   : http://{HOST}:{PORT}/mcp  (nur lokal)", file=sys.stderr)
    print(f"  Log   : {LOG}", file=sys.stderr)
    print("  Tools : probe_warten, probe_warten_fortschritt,", file=sys.stderr)
    print("          probe_start, probe_status", file=sys.stderr)
    print("=" * 56, file=sys.stderr)
    mcp.run(transport="streamable-http")
