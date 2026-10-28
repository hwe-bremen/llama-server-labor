# Quellen: mcp_kette

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen mcp_kette` (2026-10-28 21:23, Stand `6a1e513`), nach dem Abschnitt „Quellen“ in `spec_20261028_mcp_kette.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` (Zeilen 1629–1643) – `_schreibbereich`, `_im_schreibbereich` (Dateien, die `kette_commit` mitnehmen darf)

```python
1629| def _schreibbereich(spec_text: str) -> list[str] | None:
1630|     """Eintraege unter '## Schreibbereich' (je '- pfad', Backticks erlaubt). None, wenn der Abschnitt fehlt."""
1631|     if not re.search(r"^##\s+Schreibbereich\s*$", spec_text, re.M):
1632|         return None
1633|     eintraege = []
1634|     for z in abschnitt(spec_text, "Schreibbereich").splitlines():
1635|         m = re.match(r"^\s*[-*]\s+`?([^`\s]+)`?", z)
1636|         if m:
1637|             eintraege.append(m.group(1)[2:] if m.group(1).startswith("./") else m.group(1))
1638|     return eintraege
1639| 
1640| 
1641| def _im_schreibbereich(pfad: str, eintraege: list[str]) -> bool:
1642|     """Exakter Dateipfad oder Ordner-Eintrag mit '/' am Ende als Praefix."""
1643|     return any(pfad == e or (e.endswith("/") and pfad.startswith(e)) for e in eintraege)
```

### `role-split/kette/automatik.py` def lauf (Zeilen 137–190) – was `kette.py lauf` tut, Exit-Codes, `HALT`

```python
137| def lauf(kurztitel: str) -> int:
138|     """Kette: Groesse -> umsetzung-auto -> review-auto -> status -> HALT."""
139|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
140|         print(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).", file=sys.stderr)
141|         return 2
142| 
143|     commit = kette.spec_commit(kurztitel)
144|     if not commit:
145|         print(f'Kein Commit "Spec {kurztitel}" gefunden – erst die Spec committen.')
146|         return 2
147| 
148|     spec_p = kette.datei_suchen("spec", kurztitel, None)
149|     if not spec_p:
150|         print(f"Keine Spec spec_<datum>_{kurztitel}.md gefunden.")
151|         return 2
152| 
153|     spec_text = spec_p.read_text(encoding="utf-8")
154|     if not kette._vorgabe_tests(spec_text):
155|         print(
156|             "Spec hat keinen Abschnitt '## Vorgabe-Tests'. "
157|             "Vorgabe-Tests vorab schreiben (R48), sonst kein Start."
158|         )
159|         return 2
160| 
161|     g = groesse(spec_text)
162|     print(
163|         f"Größe: {g['dateien']} Datei(en), {g['anforderungen']} Anforderungen, "
164|         f"{g['tests']} Tests (Schwellen 2/6/8, vorläufig)"
165|     )
166| 
167|     if (
168|         g["dateien"] > GROESSE_DATEIEN
169|         or g["anforderungen"] > GROESSE_ANFORDERUNGEN
170|         or g["tests"] > GROESSE_TESTS
171|     ):
172|         print(
173|             "HALT – zu groß für den lokalen Umsetzer: Spec teilen oder "
174|             "Claude übernimmt (R43)."
175|         )
176|         return 3
177| 
178|     print(f"Umsetzer: {UMSETZER_VORSCHLAG}")
179|     exit_umsetzung = kette.umsetzung_auto(kurztitel)
180|     exit_code = exit_umsetzung
181| 
182|     if exit_umsetzung == 0:
183|         exit_review = kette.review_auto(kurztitel)
184|         exit_code = exit_review
185| 
186|     print()
187|     status(kurztitel)
188|     print("HALT – Entscheidung Hawe.")
189| 
190|     return exit_code
```

### `role-split/kette/automatik.py` def status (Zeilen 91–134) – Ausgabe von `kette.py status`

```python
 91| def status(kurztitel: str) -> int:
 92|     """Status ausgeben und naechsten Schritt bestimmen."""
 93|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
 94|         print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _).", file=sys.stderr)
 95|         return 2
 96| 
 97|     s = stand(kurztitel)
 98| 
 99|     # Naechster Schritt, erste zutreffende Regel
100|     if not s["spec"]:
101|         next_text = "Spec fehlt."
102|     elif not s["spec_commit"]:
103|         next_text = f'Spec committen: git commit -m "Spec {kurztitel}"'
104|     elif not s["laeufe"]:
105|         next_text = f"kette.py lauf {kurztitel}"
106|     elif s["laeufe"][-1][1] != 0:
107|         next_text = (
108|             "Nacharbeit notwendig – Umsetzer aufgerufen und nicht in Ordnung, "
109|             "dann Übernahme durch Claude."
110|         )
111|     elif not s["review"]:
112|         next_text = f"kette.py review-auto {kurztitel}"
113|     elif s["review"] != "PASS":
114|         next_text = f"Review {s['review']} – gegenprüfen."
115|     elif s["offen"]:
116|         next_text = "Alle Testdateien laufen lassen (R50), dann committen."
117|     else:
118|         next_text = "Abgeschlossen – nichts offen."
119| 
120|     # Ausgabe
121|     print(f"Status {kurztitel}")
122|     print(f"  Spec:          {Path(s['spec']).name if s['spec'] else 'fehlt'}")
123|     print(f"  Spec-Commit:   {s['spec_commit'] or 'fehlt'}")
124|     print(f"  Vorgabe-Tests: {'ja' if s['vorgabe'] else 'nein'}")
125|     if s["laeufe"]:
126|         lauf_text = ", ".join(f"{a} Exit {e}" for a, e in s["laeufe"])
127|     else:
128|         lauf_text = "keiner"
129|     print(f"  Umsetzung:     {lauf_text}")
130|     print(f"  Review:        {s['review'] or 'keins'}")
131|     print(f"  Offen:         {len(s['offen'])} Datei(en)")
132|     print(f"Nächster Schritt: {next_text}")
133| 
134|     return 0 if s["spec"] else 2
```

### `mcp-server/lab_mcp_server.py` (Zeilen 187–208) – `_logged_tool`: `mcp.tool()` protokolliert automatisch

```python
187| _orig_tool = mcp.tool
188| 
189| 
190| def _logged_tool(*args, **kwargs):
191|     """Ersatz fuer mcp.tool(): registriert die geloggte Variante des Tools."""
192|     register = _orig_tool(*args, **kwargs)
193| 
194|     def deco(fn):
195|         register(_with_log(fn))
196|         return fn
197| 
198|     return deco
199| 
200| 
201| mcp.tool = _logged_tool
202| 
203| 
204| def _tool_if(enabled: bool):
205|     """Wie @mcp.tool(), registriert das Tool aber nur, wenn enabled True ist."""
206|     if enabled:
207|         return mcp.tool()
208|     return lambda fn: fn
```

### `mcp-server/lab_mcp_server.py` (Zeilen 698–767) – Einfügestelle vor „Start“, `_banner`

```python
698| # --------------------------------------------------------------------------
699| # Python-Ausfuehrung (STANDARDMAESSIG AUS — bricht die Sandbox auf)
700| # --------------------------------------------------------------------------
701| if ALLOW_PYTHON:
702| 
703|     @mcp.tool()
704|     def run_python(code: str, timeout: int = 60) -> str:
705|         """Python-Code in einem Subprozess ausfuehren (cwd = Scope-Root).
706| 
707|         WARNUNG: Dieses Tool umgeht den Datei-Scope-Guard konstruktionsbedingt —
708|         beliebiger Python-Code kann alles tun, was der Startnutzer darf. Nur im
709|         vertrauenswuerdigen Lab aktivieren (MCP_ALLOW_PYTHON=1).
710| 
711|         Args:
712|             code: Python-Quelltext.
713|             timeout: Zeitlimit in Sekunden (Default 60).
714|         """
715|         try:
716|             r = subprocess.run(
717|                 [sys.executable, "-c", code],
718|                 cwd=str(SCOPE_ROOT),
719|                 capture_output=True,
720|                 text=True,
721|                 timeout=timeout,
722|             )
723|         except subprocess.TimeoutExpired:
724|             return f"Abgebrochen: Zeitlimit ({timeout}s) ueberschritten."
725|         out = (r.stdout or "")
726|         err = (r.stderr or "")
727|         parts = []
728|         if out:
729|             parts.append("STDOUT:\n" + out)
730|         if err:
731|             parts.append("STDERR:\n" + err)
732|         parts.append(f"(rc={r.returncode})")
733|         return "\n".join(parts)
734| 
735| 
736| # --------------------------------------------------------------------------
737| # Start
738| # --------------------------------------------------------------------------
739| def _banner() -> None:
740|     print("=" * 60, file=sys.stderr)
741|     print(" llama-server-lab MCP", file=sys.stderr)
742|     print(f"  Scope-Root : {SCOPE_ROOT}", file=sys.stderr)
743|     print(f"  Transport  : {TRANSPORT}", file=sys.stderr)
744|     if TRANSPORT != "stdio":
745|         print(f"  Bind       : {HOST}:{PORT}", file=sys.stderr)
746|     print(f"  readonly   : {READONLY}", file=sys.stderr)
747|     print(f"  delete     : {ALLOW_DELETE}", file=sys.stderr)
748|     print(f"  run_python : {ALLOW_PYTHON}", file=sys.stderr)
749|     print(f"  web_search : {ALLOW_WEB}", file=sys.stderr)
750|     print(f"  git_log    : {ALLOW_GITLOG}", file=sys.stderr)
751|     print(f"  name       : {SERVER_NAME}", file=sys.stderr)
752|     print(f"  deny       : {[_rel(d) for d in DENY_PATHS] or '-'}", file=sys.stderr)
753|     print(f"  write_roots: {[_rel(r) for r in WRITE_ROOTS] or '- (ganzer Scope)'}", file=sys.stderr)
754|     print(f"  tool_log   : {TOOL_LOG or 'aus'}", file=sys.stderr)
755|     print(f"  agent      : {AGENT_LABEL or '-'}", file=sys.stderr)
756|     if TRANSPORT != "stdio" and HOST not in ("127.0.0.1", "localhost"):
757|         print(
758|             "  ! WARNUNG: gebunden ausserhalb localhost — kein Auth-Layer!\n"
759|             "  ! Nur im privaten Tailnet mit Geraete-ACL betreiben.",
760|             file=sys.stderr,
761|         )
762|     print("=" * 60, file=sys.stderr)
763| 
764| 
765| if __name__ == "__main__":
766|     _banner()
767|     mcp.run(transport=TRANSPORT)
```

### `experiments/stufe4_probe/README.md` (Zeilen 1–72) – Messung: Abbruch nach ~5 min, Start → Status trägt

```markdown
 1| # Stufe-4-Sonde: lange Werkzeugaufrufe in der Web-UI (8092)
 2| 
 3| Ziel: vor der Stufe-4-Spec **messen**, nicht raten – wo sitzt das Zeitlimit für
 4| MCP-Werkzeugaufrufe, und wie stellt die UI „Lauf gestartet → Status abfragen" dar.
 5| 
 6| Kette eines Werkzeugaufrufs mit „use llama-server proxy":
 7| `Browser → 8092 role_proxy → 8091 local-memory → 8080 --ui-mcp-proxy → 8789 Sonde`
 8| 
 9| Bekannte bzw. vermutete Zeitlimits (kürzestes gewinnt):
10| 
11| | Glied | Limit | Status |
12| |---|---|---|
13| | role_proxy.py | Socket-Timeout 900 s | im Code gelesen |
14| | local-memory 8091 | ? | nicht geprüft (anderes Repo) |
15| | llama-server `--timeout` | Vermutung: 600 s Default | mit `llama-server --help \| grep -i timeout` prüfen |
16| | MCP-Client der Web-UI | ? | genau das misst die Sonde |
17| | Tailscale Serve (iPad) | ? | nur Schritt 5 |
18| 
19| ## Start
20| 
21| ```bash
22| bash start_rollen.command                          # Fenster 1, wie immer
23| bash experiments/stufe4_probe/start_probe.command  # Fenster 2
24| ```
25| 
26| Web-UI `http://127.0.0.1:8092` → MCP-Server hinzufügen: `http://127.0.0.1:8789/mcp`,
27| per Stift „use llama-server proxy" **AN**, Seite neu laden, **neuer Chat**.
28| Den Lab-Eintrag (8787) für die Messung ausschalten, damit das Modell nur die Sonde sieht.
29| 
30| ## Messreihe (je ein neuer Chat, Uhrzeit notieren)
31| 
32| 1. `Rufe probe_warten mit sekunden=30 auf.` → Gegenprobe, sollte glatt gehen
33| 2. `probe_warten` mit **120**, dann **330**, dann **620** – bis die UI einen Fehler zeigt
34| 3. Bei der ersten Fehlerstufe: dasselbe mit `probe_warten_fortschritt`
35|    (verlängert Fortschritt das Limit? zeigt die UI ihn an?)
36| 4. `Starte probe_start mit sekunden=300.` → dann im selben Chat mehrfach
37|    `Wie ist der Stand?` – ruft das Modell `probe_status` mit der richtigen ID selbst?
38|    Zweiter `probe_start` während des Laufs → kommt „Abgelehnt" sauber an?
39| 5. Optional iPad über `.ts.net`: Schritt 2 mit der Stufe knapp unter dem Mac-Limit
40| 
41| ## Auswertung
42| 
43| ```bash
44| tail -n 40 ~/.lab_mcp/probe_calls.jsonl
45| ```
46| 
47| Lesart: `abgebrochen` im Log = der Client hat aktiv `notifications/cancelled` geschickt
48| (so macht es die Web-UI). `ok` nach dem UI-Fehler hieße: ein Glied hat nur aufgehört zu
49| warten, ohne abzubrechen (so verhält sich ein einfacher Python-Client).
50| 
51| ## Ergebnis 28.10.2026 (Mac, 8092, Qwen3.6-27B-MTP Q4_K_XL)
52| 
53| | Schritt | Ergebnis |
54| |---|---|
55| | 1 `probe_warten` 30 s | ok |
56| | 2 `probe_warten` 120 s | ok (120,1 s) |
57| | 2 `probe_warten` 330 s | UI: `MCP error -32001: Request timed out`; Sonde: `abgebrochen nach 322,7 s` nach `POST 202` (Cancel der UI) |
58| | 3 `probe_warten_fortschritt` 330 s | gleicher Fehler – Fortschritt verlängert das Limit **nicht** |
59| | 4 `probe_start` 300 s + `probe_status` | ok: ID gemerkt, Status selbst abgefragt, Sperre korrekt erklärt, „fertig nach 300,0 s" |
60| 
61| Folgerungen für die Stufe-4-Spec:
62| - Das Limit sitzt im **MCP-Client der Web-UI** (~5 min; Vermutung: 300-s-Zähler, der vor dem
63|   eigentlichen Aufruf startet). Proxys (900 s) und llama-server greifen vorher nicht.
64| - Die UI **bricht aktiv ab** – ein blockierendes Werkzeug wird mittendrin abgewürgt.
65|   → `kette_lauf` startet einen **eigenen Prozess** (nicht Thread im Werkzeugaufruf),
66|   kehrt sofort zurück, Sperrdatei gegen Doppelstart. Faustregel: kein Werkzeug > ~4 min blockierend.
67| - Bedienmuster Start → Status trägt mit dem 27B; das Modell deutet Fehler aber selbstbewusst
68|   falsch („Server hat eine Obergrenze") → eindeutige, selbsterklärende Rückmeldetexte.
69| - Bei MCP-Eintrag „Connection timed out after 10s" direkt nach Start: einmal ↻ – Sonde war
70|   noch nicht bereit. curl über `/cors-proxy` liefert `Invalid Content-Type: text/plain`
71|   auch für 8787 – als Test ungeeignet.
72| - Offen: iPad über `.ts.net` (Schritt 5) nicht gemessen.
```
