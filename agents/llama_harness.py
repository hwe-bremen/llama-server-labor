"""
llama_harness.py — lokales Modell (llama-server) als MCP-Agent (CLI).

Duenner Konsument von core.mcp_agent.MCPAgent: verbindet das lokale Modell mit
den scope-geschuetzten Tools des mcp-server/ und faehrt die Tool-Call-Schleife.
Die eigentliche Logik lebt in core/mcp_agent.py (auch von anderen Agenten
nutzbar).

Konfiguration ueber Env:
  LLAMA_BASE_URL     (Default http://localhost:8080/v1)
  HARNESS_MODEL      exakte Modell-ID; leer/local -> Auto-Discovery
  HARNESS_MODEL_HINT bevorzugtes Modell bei Auto-Wahl (Default Mellum)
  HARNESS_MAX_STEPS  (Default 8)
  HARNESS_READONLY=1 nur lesende Tools
  HARNESS_SYSTEM_PROMPT       eigener Systemprompt (ersetzt den Default)
  HARNESS_NO_SYSTEM_PROMPT=1  gar kein Systemprompt (schlaegt SYSTEM_PROMPT)

Hintergrund zum Systemprompt (Befund 23.09.2026):
  Der Default-Systemprompt in core/mcp_agent.py weist Modelle an, beim
  Schreiben von Dateien IMMER content_b64 (Base64) zu nutzen — gedacht gegen
  JSON-Escaping-Fehler. Mellum2-12B-Q4 befolgt das zwar, erzeugt aber
  ungueltiges Base64: write_file scheitert wiederholt, das Modell gibt danach
  eine LEERE Antwort zurueck. Qwen3.6-27B loest dieselbe Aufgabe mit content
  im Klartext fehlerfrei. Die Anweisung ist also modellabhaengig hilfreich
  oder schaedlich -> hier pro Lauf umschaltbar, statt global fest.

Voraussetzung:
  - llama-server (Router) auf 8080 MIT --jinja
  - mcp-server/.venv existiert (mcp-server/setup.sh)
  - im Ausfuehrungs-venv: pip install openai mcp

Start:
  python agents/llama_harness.py "Deine Aufgabe"
  python agents/llama_harness.py            # read-only Default-Task

  # Gegentest ohne die Base64-Anweisung:
  HARNESS_MODEL_HINT=Mellum HARNESS_NO_SYSTEM_PROMPT=1 \\
    python agents/llama_harness.py "Schreibe X nach sandbox/y.md"
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Projekt-Root in den Pfad, damit 'core' ohne Package-Installation importierbar
# ist (Standalone-Lab-Struktur).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.mcp_agent import MCPAgent, DEFAULT_BASE_URL  # noqa: E402


DEFAULT_TASK = (
    "Liste die Dateien im Projekt-Root. Lies dann config/models.ini und fasse "
    "in zwei Saetzen zusammen, welche Modelle konfiguriert sind."
)


def _git_clean_hint() -> None:
    """Warnt, wenn uncommittete Aenderungen vorliegen (Rollback-Hygiene)."""
    try:
        r = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            print("Hinweis: kein Git-Repo erkannt — Rollback dann manuell.")
        elif r.stdout.strip():
            print("WARNUNG: uncommittete Aenderungen. Fuer sauberen Rollback zuerst committen.")
        else:
            print("Git-Status sauber — guter Rollback-Punkt.")
    except Exception as e:
        print(f"Git-Check uebersprungen: {e}")


def _system_prompt_from_env() -> tuple[str | None, str]:
    """Systemprompt-Modus aus Env ableiten.

    Rueckgabe: (wert_fuer_MCPAgent, klartext_label_fuers_log).
    MCPAgent-Konvention: None -> Default-Prompt, "" -> bewusst KEIN Prompt,
    eigener String -> ersetzt den Default.
    """
    if os.environ.get("HARNESS_NO_SYSTEM_PROMPT") == "1":
        return "", "aus (HARNESS_NO_SYSTEM_PROMPT=1)"
    custom = os.environ.get("HARNESS_SYSTEM_PROMPT")
    if custom:
        return custom, f"eigener ({len(custom)} Zeichen)"
    return None, "Default (inkl. content_b64-Anweisung)"


def main() -> None:
    task = " ".join(sys.argv[1:]).strip() or DEFAULT_TASK
    base_url = os.environ.get("LLAMA_BASE_URL", DEFAULT_BASE_URL)
    system_prompt, prompt_label = _system_prompt_from_env()
    agent = MCPAgent(
        scope_root=PROJECT_ROOT,
        base_url=base_url,
        model=os.environ.get("HARNESS_MODEL") or None,
        model_hint=os.environ.get("HARNESS_MODEL_HINT", "Mellum"),
        max_steps=int(os.environ.get("HARNESS_MAX_STEPS", "8")),
        readonly=os.environ.get("HARNESS_READONLY", "0") == "1",
        system_prompt=system_prompt,
    )
    print(f"Modell-Endpoint: {base_url}")
    print(f"Scope-Root     : {PROJECT_ROOT}")
    print(f"Systemprompt   : {prompt_label}")
    _git_clean_hint()
    print(f"{'='*70}\nAUFGABE: {task}\n{'='*70}")
    answer = asyncio.run(agent.run(task))
    print(f"\nANTWORT:\n{answer}")


if __name__ == "__main__":
    main()
