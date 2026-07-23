# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A local lab for experimenting with llama.cpp models — MCP-based tool access (file + Git), local and remote (iPad/iPhone via Tailscale). Strictly separate from AskValentinAI and any production code or real customer data.

## Setup (once per machine)

```bash
# MCP-Server venv (required for all scenarios)
cd mcp-server && bash setup.sh

# Project venv (required for the llama harness)
source .venv/bin/activate
pip install openai mcp
```

## Running the lab

```bash
# Standard: start Router (8080) + MCP-Server (8787) together
bash scripts/launch_lab.command           # read-only (default, safe)
bash scripts/launch_lab.command write     # write + delete enabled

# Remote via iPad/iPhone (Tailscale Serve = HTTPS, recommended)
LAB_BIND=serve bash scripts/launch_lab.command
LAB_BIND=serve bash scripts/launch_lab.command write

# Remote via direct Tailscale IP bind (simpler, less robust)
LAB_BIND=tailscale bash scripts/launch_lab.command

# Separate components (if needed individually)
bash mcp-server/run_webui.sh              # MCP-Server only (read-only default)
MCP_READONLY=0 bash mcp-server/run_webui.sh
bash scripts/launch_router.command        # Router only
```

Ctrl+C stops all services (including Tailscale Serve cleanup).

## Running the llama harness (local model as MCP agent)

Router must be running first.

```bash
source .venv/bin/activate
python agents/llama_harness.py "Your task"
HARNESS_READONLY=1 python agents/llama_harness.py "Your task"
HARNESS_MODEL="JetBrains/Mellum2-…-Q6_K:Q6_K" python agents/llama_harness.py "…"
```

## Key environment variables

| Variable | Effect |
|---|---|
| `MCP_READONLY=0/1` | Enables/disables write+delete tools on the MCP server |
| `MCP_ALLOW_PYTHON=1` | Enables `run_python` tool (breaks the file sandbox — off by default) |
| `MCP_SCOPE_ROOT` | Root path the MCP server's scope guard enforces |
| `LAB_BIND=serve/tailscale/all` | Network exposure mode for the router |
| `HARNESS_MODEL` | Exact model ID for the harness (empty = auto-discovery, prefers Mellum) |
| `HARNESS_READONLY=1` | Starts the harness in read-only mode |
| `HARNESS_MAX_STEPS` | Tool-call loop limit (default 8) |

## Health checks

```bash
curl http://127.0.0.1:8787/mcp          # MCP-Server: 406 = running
curl -sI http://127.0.0.1:8080/health   # Router: 200 = running
```

## Architecture

```
  Claude Desktop ──stdio──┐
  llama-Harness  ──stdio──┤
                          ├──> mcp-server/lab_mcp_server.py ──> Files + Git (scope-guarded)
  Web-UI (Browser) ───────┘        (port 8787, streamable-http / stdio)
      │
      └── Browser connects to: llama-server Router (port 8080)
              │  --ui-mcp-proxy forwards MCP requests server-side
              └── Router loads models on-demand from config/models.ini

  Remote client (iPad/iPhone)
      └── Tailscale Serve (HTTPS via .ts.net) ──> Router (8080)
```

**The MCP server always stays on localhost.** Remote clients reach only the router, never the tool server directly. The router's `--ui-mcp-proxy` resolves MCP URLs server-side, so the Web UI's MCP entry (`http://127.0.0.1:8787/mcp`) works for both local and remote sessions.

### Key design decisions

- **One MCP server, two transports.** `stdio` for subprocess clients (Claude Desktop, harness); `streamable-http` for the browser Web UI (which cannot spawn stdio subprocesses). Same tools, same scope guard, both transports in the same server process.

- **Scope guard in `_resolve_in_scope()`.** Every path the MCP server handles is resolved against `SCOPE_ROOT` via `pathlib.resolve()`. `..` traversal, absolute paths, and symlink escapes all fail the containment check. This is the single chokepoint — nothing else enforces the boundary.

- **`core/mcp_agent.py` as shared base.** Session management, MCP↔OpenAI tool conversion, model auto-discovery, and the tool-call loop live here once. `agents/llama_harness.py` is just configuration + a `main()`. New agents inherit the same base without duplicating the loop.

- **Router mode, not a fixed model.** `llama-server --models-preset config/models.ini` loads models on-demand; the Web UI selects via dropdown. One endpoint, all models. Sampling parameters per model are in `models.ini`.

- **Write-before-run hygiene.** Both `launch_lab.command write` and `llama_harness.py` warn on a dirty git tree before enabling write access. The intended workflow is: commit → run write-enabled agent → review diff → commit or revert.

### Component map

| Path | Role |
|---|---|
| `mcp-server/lab_mcp_server.py` | MCP server: file/git tools with scope guard |
| `core/mcp_agent.py` | Reusable agent base (MCP client + OpenAI tool-call loop) |
| `agents/llama_harness.py` | Thin CLI consumer of `core` — local model as MCP agent |
| `agents/dev_agent*.py`, `excel_agent.py` | Older standalone experiments (no MCP) |
| `scripts/launch_lab.command` | Orchestrator: starts MCP server + router together |
| `scripts/launch_router.command` | Router launcher (bind-mode aware, opens browser) |
| `config/models.ini` | Per-model sampling presets for the router |
| `config/tailscale-acl-example.json` | Tag-based ACL template (`tag:llm-client → tag:llm-server:8080`) |
| `sandbox/` | Throwaway files, writable by agents |

### Two separate venvs

- `.venv/` — project-level; used by `agents/` and `core/`; needs `openai` + `mcp`
- `mcp-server/.venv/` — MCP server only; created by `mcp-server/setup.sh`; needs only `mcp`

The harness hard-codes `mcp-server/.venv/bin/python` as the interpreter for the MCP server subprocess — that path must exist before running the harness.

## Tailscale notes

- CLI path on macOS: `/Applications/Tailscale.app/Contents/MacOS/Tailscale` (not in PATH by default)
- Serve teardown: `tailscale serve reset`
- "background configuration already exists" error: run `tailscale serve reset` first
- Bind-change trap: if a prior instance is bound to a different address (e.g. localhost vs. Tailscale IP), `pkill -f llama-server` before restarting — check the `Bind:` line in the router banner
- Use `http://127.0.0.1:8080` in the browser, not `http://localhost:8080` (CORS issue with the MCP proxy)

## Model notes

- Mellum Q6 (`Mellum2-…-Q6_K`) is the default harness model — best tool-call reliability
- Mellum Q4 is faster but tool-calling is less reliable (empty argument edge cases); use Q6 for agentic tasks
- Large models (`Qwen3.6-27B`, `gemma-4-26B`) can cause OOM on on-demand load; pick the lightest model when the router shows "Server unavailable"
