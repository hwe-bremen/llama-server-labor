#!/usr/bin/env python3
"""
Dry-Run-Test fuer den gepatchten lab_mcp_server.py — mit synthetischem
Scope-Ordner in /tmp, NICHT mit dem echten Kirby-Projekt.

Aufruf aus dem Repo-Root:  .venv/bin/python ~/Downloads/test_mcp_deny.py
"""
import asyncio
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

SERVER = Path("mcp-server/lab_mcp_server.py").resolve()
src = SERVER.read_text(encoding="utf-8")
if 'if __name__ == "__main__"' not in src and "if __name__ == '__main__'" not in src:
    sys.exit("Abbruch: kein __main__-Guard — Import wuerde den Server starten.")

# --- Synthetischer Scope ---
tmp = Path(tempfile.mkdtemp())
scope = tmp / "scope"
(scope / "site/accounts/admin").mkdir(parents=True)
(scope / "site/templates").mkdir(parents=True)
(scope / "site/accounts/admin/index.php").write_text("GEHEIM account\n")
(scope / "site/templates/home.php").write_text("GEHEIM ok-template\n")
(scope / ".env").write_text("GEHEIM env\n")
outside = tmp / "outside.txt"
outside.write_text("GEHEIM draussen\n")
(scope / "link-nach-draussen.txt").symlink_to(outside)

os.environ.update(
    MCP_SCOPE_ROOT=str(scope),
    MCP_DENY="site/accounts,.env",
    MCP_ALLOW_WEB="0",
    MCP_NAME="test-instanz",
    MCP_READONLY="1",
)
spec = importlib.util.spec_from_file_location("labsrv", SERVER)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

fails = 0
def check(name, ok):
    global fails
    print(("PASS " if ok else "FAIL ") + name)
    fails += not ok

def blocked(fn, *a):
    try:
        fn(*a)
        return False
    except m.ScopeError:
        return True

check("read_file site/accounts/... gesperrt", blocked(m.read_file, "site/accounts/admin/index.php"))
check("read_file .env gesperrt", blocked(m.read_file, ".env"))
check("read_file via ../ auf Sperrpfad gesperrt", blocked(m.read_file, "site/templates/../accounts/admin/index.php"))
check("list_directory site/accounts gesperrt", blocked(m.list_directory, "site/accounts"))
check("read_file ausserhalb Scope gesperrt", blocked(m.read_file, "../outside.txt"))
check("read_file erlaubte Datei lesbar", "ok-template" in m.read_file("site/templates/home.php"))

hits = m.search_files("GEHEIM")
check("search_files findet erlaubtes Template", "ok-template" in hits)
check("search_files ohne Account-Treffer", "account" not in hits)
check("search_files ohne .env-Treffer", " env" not in hits)
check("search_files ohne Symlink-nach-draussen", "draussen" not in hits)
check("search_files ab site/ ohne Account-Treffer", "account" not in m.search_files("GEHEIM", "site"))

tools = [t.name for t in asyncio.run(m.mcp.list_tools())]
check("web_search nicht registriert", "web_search" not in tools)
check("Servername gesetzt", m.mcp.name == "test-instanz")
print(f"Tools: {tools}")

print("\nALLES OK" if fails == 0 else f"\n{fails} FEHLER")
sys.exit(1 if fails else 0)
