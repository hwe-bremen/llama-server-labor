# Quellen: alle_tests

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen alle_tests` (2026-10-29 08:24, Stand `a126789`), nach dem Abschnitt „Quellen“ in `spec_20261029_alle_tests.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/test_role_proxy.py` (Zeilen 1–20) – importiert das Nachbarmodul `role_proxy` (Suchpfad = Ordner der Datei)

```python
 1| #!/usr/bin/env python3
 2| """Tests für role_proxy.py: Trigger-Logik plus echter Durchlauf mit Fake-Upstream."""
 3| import datetime as dt
 4| import gzip
 5| import http.client
 6| import json
 7| import tempfile
 8| import threading
 9| import unittest
10| from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
11| from pathlib import Path
12| 
13| import role_proxy as rp
14| 
15| ROLES = {"review": "REVIEW-PROMPT", "research": "RESEARCH-PROMPT"}
16| TODAY = dt.date(2026, 10, 14)
17| 
18| 
19| def u(text):
20|     return {"role": "user", "content": text}
```

### `mcp-server/test_tool_log.py` (Zeilen 1–30) – Skript-Test, erwartet den Server-Pfad als erstes Argument

```python
 1| """Dry-Run-Test fuer das Tool-Call-Log (synthetische Daten, Temp-Scope).
 2| 
 3| Aufruf: python test_tool_log.py <pfad/zu/lab_mcp_server.py>
 4| """
 5| import asyncio
 6| import importlib.util
 7| import json
 8| import os
 9| import sys
10| import tempfile
11| from pathlib import Path
12| 
13| server_path = Path(sys.argv[1]).resolve()
14| tmp = Path(tempfile.mkdtemp())
15| scope = tmp / "scope"
16| scope.mkdir()
17| (scope / "a.txt").write_text("hallo welt\n", encoding="utf-8")
18| log_in_scope = scope / "logs" / "tool_calls.jsonl"
19| 
20| os.environ.update(
21|     MCP_SCOPE_ROOT=str(scope),
22|     MCP_TOOL_LOG=str(log_in_scope),
23|     MCP_AGENT="testlauf",
24|     MCP_ALLOW_WEB="0",
25| )
26| spec = importlib.util.spec_from_file_location("lab_srv", server_path)
27| srv = importlib.util.module_from_spec(spec)
28| spec.loader.exec_module(srv)
29| 
30| 
```

### `mcp-server/test_append_file.py` (Zeilen 1–15) – importiert das Nachbarmodul `test_search_files`

```python
 1| #!/usr/bin/env python3
 2| """Tests: append_file (abschnittsweises Speichern) und schreibgeschuetzte Vorgaben der Kette.
 3| 
 4| Aufruf:  cd mcp-server && .venv/bin/python -m unittest test_append_file -v
 5| Anlass 22.10.: Verdikte/Specs gingen beim vollen Kontext komplett verloren, weil nur ganze
 6| Dateien geschrieben werden konnten.
 7| """
 8| import tempfile
 9| import unittest
10| from pathlib import Path
11| 
12| from test_search_files import load, tool_names
13| 
14| 
15| class AppendFileTests(unittest.TestCase):
```

### `scripts/test_mcp_deny.py` (Zeilen 1–20) – Skript-Test, läuft aus dem Repo-Root (`Path("mcp-server/...")`)

```python
 1| #!/usr/bin/env python3
 2| """
 3| Dry-Run-Test fuer den gepatchten lab_mcp_server.py — mit synthetischem
 4| Scope-Ordner in /tmp, NICHT mit dem echten Kirby-Projekt.
 5| 
 6| Aufruf aus dem Repo-Root:  .venv/bin/python ~/Downloads/test_mcp_deny.py
 7| """
 8| import asyncio
 9| import importlib.util
10| import os
11| import sys
12| import tempfile
13| from pathlib import Path
14| 
15| SERVER = Path("mcp-server/lab_mcp_server.py").resolve()
16| src = SERVER.read_text(encoding="utf-8")
17| if 'if __name__ == "__main__"' not in src and "if __name__ == '__main__'" not in src:
18|     sys.exit("Abbruch: kein __main__-Guard — Import wuerde den Server starten.")
19| 
20| # --- Synthetischer Scope ---
```

### `role-split/kette/kette.py` def tests_laufen (Zeilen 388–402) – so startet die Kette heute Tests (nur zur Orientierung, nicht ändern)

```python
388| def tests_laufen(skript: Path, timeout: int) -> dict[str, str] | None:
389|     """Laesst das Testskript in einem eigenen Prozess laufen; Ergebnis je Testmethode."""
390|     modul = ".".join(skript.relative_to(ROOT).with_suffix("").parts)
391|     # Eigener, frischer Bytecode-Cache je Lauf: sonst kann Python eine alte .pyc weiterverwenden,
392|     # wenn die zurueckgesetzte Datei gleich gross ist und in derselben Sekunde geschrieben wurde.
393|     with tempfile.TemporaryDirectory(prefix="kette_pyc_") as cache:
394|         try:
395|             r = subprocess.run([sys.executable, "-X", f"pycache_prefix={cache}", "-c", LAEUFER, modul],
396|                                cwd=ROOT, capture_output=True, text=True, timeout=timeout)
397|         except subprocess.TimeoutExpired:
398|             return None
399|     for zeile in reversed(r.stdout.splitlines()):
400|         if zeile.startswith("@@KETTE@@"):
401|             return json.loads(zeile[len("@@KETTE@@"):])
402|     return {"<Testskript laedt nicht>": "ERROR"}
```
