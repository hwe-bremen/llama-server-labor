"""Dry-Run-Test fuer das Tool-Call-Log (synthetische Daten, Temp-Scope).

Aufruf: python test_tool_log.py <pfad/zu/lab_mcp_server.py>
"""
import asyncio
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

server_path = Path(sys.argv[1]).resolve()
tmp = Path(tempfile.mkdtemp())
scope = tmp / "scope"
scope.mkdir()
(scope / "a.txt").write_text("hallo welt\n", encoding="utf-8")
log_in_scope = scope / "logs" / "tool_calls.jsonl"

os.environ.update(
    MCP_SCOPE_ROOT=str(scope),
    MCP_TOOL_LOG=str(log_in_scope),
    MCP_AGENT="testlauf",
    MCP_ALLOW_WEB="0",
)
spec = importlib.util.spec_from_file_location("lab_srv", server_path)
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)


async def main():
    tools = {t.name: t for t in await srv.mcp.list_tools()}
    # 1) Registrierung + Schema unveraendert (Wrapper darf Parameter nicht verschlucken)
    assert "write_file" in tools and "read_file" in tools, tools.keys()
    props = tools["write_file"].inputSchema["properties"]
    assert set(props) >= {"path", "content", "content_b64"}, props
    assert "Base64" in (tools["write_file"].description or ""), "Docstring verloren"

    # 2) normale Aufrufe
    await srv.mcp.call_tool("read_file", {"path": "a.txt"})
    await srv.mcp.call_tool("write_file", {"path": "b.txt", "content": "GEHEIM" * 100})
    # 3) Scope-Verletzung -> muss als error geloggt werden
    try:
        await srv.mcp.call_tool("read_file", {"path": "../../etc/passwd"})
    except Exception:
        pass
    # 4) Log liegt im Scope -> muss gesperrt sein
    try:
        r = await srv.mcp.call_tool("read_file", {"path": "logs/tool_calls.jsonl"})
        print("read_file auf Log lieferte:", r)
    except Exception:
        pass


asyncio.run(main())

lines = [json.loads(l) for l in log_in_scope.read_text(encoding="utf-8").splitlines()]
for l in lines:
    print(json.dumps(l, ensure_ascii=False))

assert len(lines) == 4, f"erwartet 4 Logzeilen, habe {len(lines)}"
r0, w, esc, lg = lines
assert r0["tool"] == "read_file" and r0["status"] == "ok" and r0["agent"] == "testlauf"
assert r0["result_head"].startswith("hallo welt")
assert w["args"]["content"] == {"len": 600, "sha256_12": w["args"]["content"]["sha256_12"]}
assert "GEHEIM" not in json.dumps(w), "Inhalt nicht redigiert!"
assert esc["status"] == "error" and "ScopeError" in esc["error"], esc
assert lg["status"] == "error" and "gesperrt" in lg["error"], lg
assert (scope / "b.txt").read_text() == "GEHEIM" * 100, "Tool-Wirkung kaputt"
print("\nALLE CHECKS OK")
