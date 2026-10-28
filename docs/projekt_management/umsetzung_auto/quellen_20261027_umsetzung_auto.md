# Quellen: umsetzung_auto

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen umsetzung_auto` (2026-10-27 12:36, Stand `c7a81af`), nach dem Abschnitt „Quellen“ in `spec_20261027_umsetzung_auto.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` (Zeilen 437–445) – `spec_commit(kurztitel)`: findet den Commit „Spec <kurztitel>" (Rücksetzpunkt, A2.2, A7a)

```python
437| def spec_commit(kurztitel: str) -> str | None:
438|     """Aeltester Commit, dessen Betreffzeile genau "Spec <kurztitel>" ist (= Ruecksetzpunkt)."""
439|     r = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h%x09%s"],
440|                        capture_output=True, text=True)
441|     if r.returncode != 0:
442|         return None
443|     treffer = [z.split("\t", 1)[0] for z in r.stdout.splitlines()
444|                if "\t" in z and z.split("\t", 1)[1].strip() == f"Spec {kurztitel}"]
445|     return treffer[-1] if treffer else None
```

### `role-split/kette/kette.py` (Zeilen 487–512) – `pruefen(kurztitel)`: abgleich + unittest + gegenprobe, liefert Exit-Code und schreibt `pruefung_<datum>_<kurztitel>.md` (A7d)

```python
487| def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> int:
488|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
489|         print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
490|     commit = commit or spec_commit(kurztitel)
491|     if not commit:
492|         print(f"Kein Commit 'Spec {kurztitel}' gefunden. Ruecksetzpunkt mit --commit angeben "
493|               f"(git log --oneline -10)."); return 2
494|     teile_dict = _pruefen_teile(kurztitel, commit, timeout)
495|     codes = {k: v[0] for k, v in teile_dict.items()}
496|     teile = []
497|     for titel_key in ("abgleich", "unittest", "gegenprobe"):
498|         code, out = teile_dict[titel_key]
499|         # Titel wiederherstellen: gegenprobe braucht {commit}
500|         titel = f"gegenprobe gegen {commit}" if titel_key == "gegenprobe" else titel_key
501|         teile.append(f"## {titel}  (Exit {code})\n\n```\n{out.rstrip()}\n```\n")
502|     kurz = " | ".join(f"{k.split()[0]}: {'ok' if v == 0 else ('Abweichung' if v == 1 else 'FEHLER')}"
503|                       for k, v in codes.items())
504|     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
505|     kopf = (f"# Pruefung {kurztitel}\n\n- Zeit: {dt.datetime.now():%Y-%m-%d %H:%M}\n"
506|             f"- Ruecksetzpunkt: {commit}\n- Kurz: {kurz}\n\n")
507|     ziel = PM / f"pruefung_{datum}_{kurztitel}.md"
508|     ziel.write_text(kopf + "\n".join(teile), encoding="utf-8")
509|     print("\n".join(teile))
510|     print(f"\n==> {kurz}")
511|     print(f"==> Ausgabe gespeichert: {ziel.relative_to(ROOT)}  (dem Gegenpruefer nur noch Bescheid sagen)")
512|     return max(codes.values())
```

### `role-split/kette/kette.py` (Zeilen 525–526) – `_git(*a)`: git-Wrapper mit `git -C ROOT` (A2, A7)

```python
525| def _git(*a: str) -> str:
526|     return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
```

### `role-split/kette/kette.py` (Zeilen 78–81) – `ROOT`, `PM`, `PROMPTS`: Pfade (A1, A3, A6)

```python
78| HERE = Path(__file__).resolve().parent
79| ROOT = HERE.parent.parent
80| PM = ROOT / "docs" / "projekt_management"
81| PROMPTS = HERE / "prompts"
```

### `role-split/kette/kette.py` (Zeilen 1194–1202) – `KETTE_HERZSCHLAG_S` (Default 60) und Umgebungsmuster für Env-Variablen (A5, A9)

```python
1194| KETTE_LLM_URL = os.environ.get("KETTE_LLM_URL", "http://127.0.0.1:8080")
1195| KETTE_LLM_MODEL = os.environ.get("KETTE_LLM_MODEL", "unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL")
1196| KETTE_LLM_TIMEOUT = int(os.environ.get("KETTE_LLM_TIMEOUT", "1800"))
1197| KETTE_LLM_MAX_TOKENS = int(os.environ.get("KETTE_LLM_MAX_TOKENS", "8000"))
1198| # Leer = Sampling-Werte des Servers (config/models.ini, fuer Qwen 0.6/0.95/20). Frueher fest 0.1:
1199| # niedrige Temperatur ohne Denkphase fuehrte beim 35B zu Wiederholungsschleifen bis max_tokens.
1200| KETTE_LLM_TEMPERATURE = os.environ.get("KETTE_LLM_TEMPERATURE", "")
1201| KETTE_ABGESCHNITTEN = Path(os.environ.get("KETTE_ABGESCHNITTEN", "/tmp"))
1202| KETTE_HERZSCHLAG_S = int(os.environ.get("KETTE_HERZSCHLAG_S", "60"))
```

### `role-split/kette/kette.py` (Zeilen 1216–1229) – `_herzschlag_stopp_event`: Herzschlag-Thread als Muster (A9)

```python
1216| def _herzschlag_stopp_event(lauf_nummer: int):
1217|     """Starter fuer den Herzschlag-Thread. Gibt (event, thread) zurueck."""
1218|     stop = threading.Event()
1219| 
1220|     def pulse():
1221|         start = dt.datetime.now()
1222|         while not stop.is_set():
1223|             elapsed = int((dt.datetime.now() - start).total_seconds())
1224|             print(f"Lauf {lauf_nummer}: {elapsed // 60} min …", flush=True)
1225|             stop.wait(KETTE_HERZSCHLAG_S)
1226| 
1227|     t = threading.Thread(target=pulse, daemon=True)
1228|     t.start()
1229|     return stop, t
```

### `role-split/kette/kette.py` (Zeilen 1326–1328) – `review_auto`: Kurztitel-Prüfung und Funktionsmuster für `umsetzung_auto` (A1, A2.1)

```python
1326| def review_auto(kurztitel: str) -> int:
1327|     """Review-Paket bauen, zwei API-Laeufe, Verdikte speichern, zusammenfuehren."""
1328|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
```

### `role-split/kette/kette.py` (Zeilen 1463–1512) – `main`: argparse-Struktur, hier `umsetzung-auto`-Subparser ergänzen (Einstiegspunkte)

```python
1463| def main(argv=None) -> int:
1464|     ap = argparse.ArgumentParser(description="Werkzeug fuer die Kette Spec -> Umsetzung -> Review")
1465|     sub = ap.add_subparsers(dest="cmd", required=True)
1466|     p = sub.add_parser("prompt"); p.add_argument("schritt", choices=SCHRITTE); p.add_argument("kurztitel")
1467|     p.add_argument("--datum"); p.add_argument("--commit")
1468|     p.add_argument("--lauf", type=int, help="Review-Lauf-Nummer (eigener Verdikt-Dateiname je Lauf)")
1469|     q = sub.add_parser("quellen"); q.add_argument("kurztitel"); q.add_argument("--datum")
1470|     n = sub.add_parser("anforderung"); n.add_argument("kurztitel")
1471|     n.add_argument("--aufgabe"); n.add_argument("--antwort"); n.add_argument("--frage"); n.add_argument("--datum")
1472|     a = sub.add_parser("abgleich"); a.add_argument("kurztitel"); a.add_argument("--datum")
1473|     u = sub.add_parser("urteil"); u.add_argument("verdikt"); u.add_argument("--anhaengen", action="store_true")
1474|     g = sub.add_parser("gegenprobe"); g.add_argument("kurztitel")
1475|     g.add_argument("--commit", required=True, help="Ruecksetzpunkt vor der Umsetzung")
1476|     g.add_argument("--timeout", type=int, default=300)
1477|     zf = sub.add_parser("zusammenfuehren", help="Befunde mehrerer Review-Laeufe mechanisch zusammenfuehren")
1478|     zf.add_argument("verdikte", nargs="+")
1479|     pk = sub.add_parser("paket", help="Review-Paket bauen (eine Datei fuers Review)")
1480|     pk.add_argument("kurztitel"); pk.add_argument("--commit"); pk.add_argument("--datum")
1481|     pr = sub.add_parser("pruefen", help="abgleich + unittest + gegenprobe, Ausgabe in Datei")
1482|     pr.add_argument("kurztitel"); pr.add_argument("--commit"); pr.add_argument("--timeout", type=int, default=300)
1483|     ra = sub.add_parser("review-auto", help="Review-Paket, zwei API-Laeufe, Verdikte, Zusammenfassung")
1484|     ra.add_argument("kurztitel")
1485|     args = ap.parse_args(argv)
1486|     if args.cmd == "zusammenfuehren":
1487|         return zusammenfuehren([Path(v) if Path(v).is_absolute() or Path(v).exists() else PM / Path(v).name
1488|                                 for v in args.verdikte])
1489|     if args.cmd == "paket":
1490|         return paket(args.kurztitel, args.commit, args.datum)
1491|     if args.cmd == "pruefen":
1492|         return pruefen(args.kurztitel, args.commit, args.timeout)
1493|     if args.cmd == "review-auto":
1494|         return review_auto(args.kurztitel)
1495|     if args.cmd == "gegenprobe":
1496|         return gegenprobe(args.kurztitel, args.commit, args.timeout)
1497|     if args.cmd == "quellen":
1498|         return quellen(args.kurztitel, args.datum)
1499|     if args.cmd == "anforderung":
1500|         return anforderung(args.kurztitel, args.aufgabe, args.antwort, args.frage, args.datum)
1501|     if args.cmd == "prompt":
1502|         return prompt(args.schritt, args.kurztitel, args.datum, args.commit, args.lauf)
1503|     if args.cmd == "abgleich":
1504|         return abgleich(args.kurztitel, args.datum)
1505|     pfad = Path(args.verdikt)
1506|     if not pfad.is_absolute() and not pfad.exists():
1507|         pfad = PM / pfad.name
1508|     return urteil(pfad, args.anhaengen)
1509| 
1510| 
1511| if __name__ == "__main__":
1512|     sys.exit(main())
```

### `.opencode/agents/umsetzung_nacht.md` (Zeilen 1–27) – bestehendes Frontmatter mit `bash: "*": deny` und Allow-Liste (A4)

```markdown
 1| ---
 2| description: Wie "umsetzung", aber unbeaufsichtigt (Nachtlauf) – keine Rueckfragen, nur Positivliste
 3| mode: primary
 4| temperature: 0.2
 5| permission:
 6|   edit: allow
 7|   read: allow
 8|   glob: allow
 9|   grep: allow
10|   list: allow
11|   external_directory: deny
12|   webfetch: deny
13|   websearch: deny
14|   task: deny
15|   skill: deny
16|   question: deny
17|   doom_loop: deny
18|   bash:
19|     "*": deny
20|     "python3 -m py_compile *": allow
21|     "bash -n *": allow
22|     "python3 -m unittest*": allow
23|     ".venv/bin/python -m unittest*": allow
24|     "git status*": allow
25|     "git diff*": allow
26|     "git log*": allow
27| ---
```

### `role-split/kette/prompts/umsetzung.md` (Zeilen 1–12) – Prompt-Vorlage für `umsetzung_nacht.md` (A3)

```markdown
 1| <!-- Schritt 2, OpenCode, Agent „umsetzung" (Tab). Rücksetzpunkt = aktueller Commit. -->
 2| Setz docs/projekt_management/spec_{datum}_{kurztitel}.md um.
 3| 
 4| Konstanten, Formate, Schnittstellen und Optionen nimmst du ausschließlich aus {quellen} und dem Code selbst, nie aus dem Gedächtnis. Fehlt dort etwas, setz nichts Erfundenes ein, sondern nenne es im Handover unter „Abweichungen".
 5| Verbindliche Vorgabe ist {anforderung}. Widerspricht die Spec ihr an einer Stelle, setzt du die Spec um und nennst den Widerspruch im Handover unter „Abweichungen".
 6| 
 7| - Rücksetzpunkt ist Commit {commit}; nicht selbst committen.
 8| - Die Tests der Spec schreibst du als tests/test_{kurztitel}.py (unittest), je Test-ID eine Methode test_<id>_… (z. B. test_t1_timeout). Kein Test darf Außenwirkung haben: keine echten Server außer 127.0.0.1, keine echten Datenordner (immer temporäres Verzeichnis), kein echter Versand.
 9| - Ein Test, der sich nicht wie in der Spec bauen lässt, wird NICHT durch einen anderen ersetzt: unter „Abweichungen" und „Nicht getestet" nennen.
10| - Befehle mit Außenwirkung führst du nie aus, auch nicht nach Freigabe. Nenne sie im Handover unter „Hawe muss ausführen".
11| - Nach jeder Datei: python3 -m py_compile bzw. bash -n.
12| - Handover nach docs/projekt_management/handover_{datum}_{kurztitel}.md, Vorlage _vorlage_handover.md. Testtitel exakt wie in der Spec, darunter die echte Ausgabe von python3 -m unittest -v tests/test_{kurztitel}.py.
```

### `docs/projekt_management/_vorlage_spec.md` (Zeilen 1–80) – Spec-Vorlage, um `## Schreibbereich` zu ergänzen (A11)

```markdown
 1| # Spec: <kurztitel>
 2| 
 3| - **Datum:** <JJJJ-MM-TT>
 4| - **Modell:** <Modellname aus dem System-Prompt>
 5| - **Betroffene Dateien:** <nur Dateien, die du gelesen hast>
 6| 
 7| ## Ziel
 8| 
 9| <1–3 Sätze>
10| 
11| ## Nicht-Ziele
12| 
13| - <…>
14| 
15| ## Außenwirkung und Sperre
16| 
17| - **Was kann die Aufgabe außerhalb des Repos auslösen?** <Mail, Netzwerk, echte Daten/DB, Schlüsselbund, launchd … oder „nichts">
18| - **Technische Sperre für Tests:** <z. B. Variable, die echten Versand erst erlaubt; temporäres Datenverzeichnis. Eine Regel im Prompt reicht nicht.>
19| 
20| ## Einstiegspunkte
21| 
22| Welche geänderten Dateien werden **wie** gestartet (Pipeline, launchd, von Hand, als Modul importiert)?
23| Für jeden Einstiegspunkt gibt es einen Test, der ihn so startet wie im Betrieb (ohne Außenwirkung, z. B.
24| `runpy.run_path(…, run_name="kein_main")` für Imports, Ersatzskripte für Pipelines).
25| Anlass 18.10.: Ein relativer Import ließ den Scout bei jedem Lauf abstürzen; alle Funktionstests waren grün.
26| 
27| | Datei | Wie gestartet | Test |
28| |---|---|---|
29| | `pfad/skript.py` | `python3 pfad/skript.py` aus `run_x.sh` | T… |
30| 
31| ## Quellen
32| 
33| Jede Konstante, jedes Dateiformat, jede Schnittstelle oder Option, die die Umsetzung braucht, als Fundstelle im Repo –
34| **nichts aus dem Gedächtnis**. Eine Zeile je Quelle, Pfad in Backticks, dann `Zeilen a–b` oder `def Name` / `class Name`
35| (ohne Angabe: ganze Datei, max. 400 Zeilen), dann Zweck. `kette.py quellen <kurztitel>` holt die Auszüge danach
36| maschinell und wörtlich nach `quellen_<JJJJMMTT>_<kurztitel>.md`. Was nicht im Repo steht (externe Doku, Format
37| eines Fremdprogramms), kommt unter „Offene Fragen" – Hawe legt die Quelle dann als Datei ins Repo.
38| 
39| - `pfad/datei.py` def funktion – wofür gebraucht
40| - `pfad/datei.py` Zeilen 10–40 – wofür gebraucht
41| 
42| ## Anforderungen
43| 
44| ### A1: <Titel>
45| - **Anforderung:** <prüfbar formuliert>
46| - **Stelle:** <Datei, Funktion>
47| - **Akzeptanz:** <beobachtbares Ergebnis>
48| 
49| ## Fehlerpfade
50| 
51| Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").
52| 
53| | Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
54| |---|---|---|---|---|
55| | A1 | Gegenstelle antwortet nicht oder schweigt (Netz, Server, Router) | | | T… |
56| | A1 | Eingabe leer oder ungültig (Variable, Datei, Argument) | | | |
57| | A1 | Ziel existiert schon (Datei, Eintrag) — wird etwas überschrieben? | | | |
58| | A1 | Schalter kombiniert (z. B. Trockenlauf + anderer Modus) | | | |
59| | A1 | Lauf ohne Testschalter / gegen echte Daten | | | |
60| | A1 | Absturz mitten im Lauf | | | |
61| 
62| ## Testplan
63| 
64| Alle Tests werden als `tests/test_<kurztitel>.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.
65| Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.
66| 
67| ### T1: <Titel>
68| - **Prüft:** A1, Fehlerpfad „…"
69| - **Aufbau:** <Testserver, temporäres Verzeichnis, Umgebungsvariablen>
70| - **Erwartung:** <prüfbare Bedingung: Exit-Code, Datei existiert, Dauer ≥ x s …>
71| - **Warum misst der Test das Richtige?** <ein Satz: woran würde der Test scheitern, wenn die Anforderung NICHT erfüllt ist?>
72| - **Gegenprobe:** <welche Datei bzw. welche Codezeile muss im alten Zustand sein, damit dieser Test rot wird? „keine" = Test prüft Bestehendes, dann begründen>
73| 
74| ## Offene Fragen
75| 
76| - <… oder „Keine">
77| 
78| ## Abweichende Meinung
79| 
80| - <… oder „Keine">
```

### `role-split/kette/RUNBOOK.md` (Zeilen 111–123) – Phase B, um `umsetzung-auto` zu ergänzen (A11)

```markdown
111| ## Phase B – Umsetzung (OpenCode)
112| 
113| 1. Prompt holen (landet automatisch in der Zwischenablage):
114|    ```bash
115|    python3 role-split/kette/kette.py prompt umsetzung <kurztitel>
116|    ```
117| 2. `opencode` im Projektordner starten, Modell **Qwen3.6**, mit **Tab** Agent **`umsetzung`** wählen, Prompt einfügen.
118|    Provider: Läuft `start_rollen` → beliebig. Läuft `start_eval` → **„M4 direkt (8080)"** (sonst „Cannot connect").
119| 3. **Nicht nachhelfen.** Shell-Freigaben nur ohne Außenwirkung (Tests, Syntax-Checks, `git status/diff`), im Zweifel ablehnen.
120|    `umsetzung_nacht` nur, wenn du bewusst nicht dabei bist.
121| 4. **Nicht committen.**
122| 
123| **Fertig, wenn:** OpenCode meldet, `handover_<datum>_<kurztitel>.md` ist geschrieben.
```

### `tests/test_kette_review_auto.py` (Zeilen 78–150) – Testmuster: `sys.path.insert`, `setattr`/`addCleanup`, `kette.PM` → Tempdir (Testplan)

```python
 78| class ReviewAutoTests(unittest.TestCase):
 79| 
 80|     def setUp(self):
 81|         self.tmp = tempfile.TemporaryDirectory()
 82|         self.addCleanup(self.tmp.cleanup)
 83|         kette.PM = Path(self.tmp.name)
 84|         self.addCleanup(setattr, kette, "KETTE_ABGESCHNITTEN", kette.KETTE_ABGESCHNITTEN)
 85|         kette.KETTE_ABGESCHNITTEN = Path(self.tmp.name)
 86|         self._orig_url = os.environ.get("KETTE_LLM_URL")
 87|         self._orig_model = os.environ.get("KETTE_LLM_MODEL")
 88|         self._orig_timeout = os.environ.get("KETTE_LLM_TIMEOUT")
 89|         self._orig_heartbeat = os.environ.get("KETTE_HERZSCHLAG_S")
 90|         self._orig_kette_url = getattr(kette, "KETTE_LLM_URL", None)
 91|         os.environ["KETTE_LLM_TIMEOUT"] = "3"
 92|         os.environ["KETTE_HERZSCHLAG_S"] = "1"
 93|         _MiniServer.antworten = []
 94|         _MiniServer.anzahl_rufe = 0
 95|         _MiniServer.koerper = []
 96| 
 97|     def tearDown(self):
 98|         if self._orig_url is not None:
 99|             os.environ["KETTE_LLM_URL"] = self._orig_url
100|         elif "KETTE_LLM_URL" in os.environ:
101|             del os.environ["KETTE_LLM_URL"]
102|         if self._orig_model is not None:
103|             os.environ["KETTE_LLM_MODEL"] = self._orig_model
104|         elif "KETTE_LLM_MODEL" in os.environ:
105|             del os.environ["KETTE_LLM_MODEL"]
106|         if self._orig_timeout is not None:
107|             os.environ["KETTE_LLM_TIMEOUT"] = self._orig_timeout
108|         elif "KETTE_LLM_TIMEOUT" in os.environ:
109|             del os.environ["KETTE_LLM_TIMEOUT"]
110|         if self._orig_heartbeat is not None:
111|             os.environ["KETTE_HERZSCHLAG_S"] = self._orig_heartbeat
112|         elif "KETTE_HERZSCHLAG_S" in os.environ:
113|             del os.environ["KETTE_HERZSCHLAG_S"]
114|         if self._orig_kette_url is not None:
115|             kette.KETTE_LLM_URL = self._orig_kette_url
116|         elif hasattr(kette, "KETTE_LLM_URL"):
117|             delattr(kette, "KETTE_LLM_URL")
118| 
119|     # --- T1: Endergebnis bei zwei gültigen Läufen ---
120| 
121|     def test_t1_endergebnis_zwei_gueltige_laeufe(self):
122|         port = _freier_port()
123|         url = f"http://127.0.0.1:{port}"
124|         os.environ["KETTE_LLM_URL"] = url
125|         kette.KETTE_LLM_URL = url
126|         _MiniServer.antworten = [
127|             {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 1 | nein | nein | ja | niedrig | x.py:1 | x | y |")}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}},
128|             {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 2 | nein | nein | nein | niedrig | x.py:2 | x | y |")}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}},
129|         ]
130|         _server_thread(port)
131|         # pruefen patchen auf Exit 0
132|         orig_teile = kette._pruefen_teile
133|         kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
134|         self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
135|         # paket patchen auf Exit 0
136|         orig_paket = kette.paket
137|         kette.paket = lambda *a: 0
138|         self.addCleanup(setattr, kette, "paket", orig_paket)
139| 
140|         buf = io.StringIO()
141|         with redirect_stdout(buf):
142|             code = kette.review_auto("test1")
143|         out = buf.getvalue()
144|         self.assertIn("Ergebnis", out)
145|         self.assertIn("gesamt_", out)
146|         self.assertEqual(_MiniServer.anzahl_rufe, 2)
147|         gesamt = list(kette.PM.glob("gesamt_*.md"))
148|         self.assertTrue(bool(gesamt))
149| 
150|     # --- K3 (K9): max_tokens wird im API-Aufruf mitgeschickt ---
```

### `docs/projekt_management/anforderung_20261027_umsetzung_auto.md` (Zeilen 1–31) – verbindliche Vorgabe, alle Anforderungen P1–P10

```markdown
 1| # Anforderung: umsetzung_auto
 2| 
 3| Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
 4| die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.
 5| 
 6| ## Aufgabe
 7| 
 8| > Die Umsetzung soll ohne TUI laufen, damit ich nicht mehr Prompts kopieren und Befehle freigeben muss.
 9| > 1. Neuer Befehl `kette.py umsetzung-auto <kurztitel>`: startet `opencode run --format json` mit Agent `umsetzung_nacht` und Modell aus `KETTE_UMSETZUNG_MODEL` (Vorgabe `llamacpp/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL`). Prompt wie `prompt umsetzung`, aber ohne Ausgabe/Zwischenablage. Jeder Lauf ist eine neue Sitzung (kein `--continue`).
10| > 2. Vor dem Start prüfen, sonst Exit 2 ohne Lauf: Commit „Spec <kurztitel>" existiert; die Spec hat einen Abschnitt `## Schreibbereich` (Dateien/Ordner, die die Umsetzung ändern darf); Arbeitsstand sauber (erster Lauf) bzw. nur Änderungen im Schreibbereich (Nacharbeit); `opencode` ist installiert; das Modell beginnt mit `llamacpp/`.
11| > 3. `umsetzung_nacht` verbietet zusätzlich ausdrücklich (deny): `git commit`, `reset`, `checkout`, `restore`, `clean`, `stash`, `push`, `rm`, `mv`. Kein `ask` im Agenten.
12| > 4. Zeitlimits: ganzer Lauf `KETTE_UMSETZUNG_TIMEOUT` (Vorgabe 7200 s), danach OpenCode samt Unterprozessen beenden, Exit 1; Einzelbefehl über `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS` (Vorgabe 300000).
13| > 5. Ausgewertet wird nur das JSON, nie der Exit-Code von OpenCode: Dauer, Werkzeugaufrufe, fehlgeschlagene und abgelehnte Befehle (mit Wortlaut), Tokens, letzter `reason`, Schlusstext. Ohne `reason: stop` am Ende gilt der Lauf als „nicht abgeschlossen" (Exit 1). Rohdaten nach `role-split/results/`, je Lauf eine Protokollzeile in `docs/projekt_management/umsetzung_<datum>_<kurztitel>.md`.
14| > 6. Danach mechanisch: (a) HEAD unverändert, sonst lauter Fehler „Selbst-Commit"; (b) jede in diesem Lauf geänderte oder neue Datei liegt im Schreibbereich, ist `tests/test_<kurztitel>.py` oder der Handover der Kette – Spec, Anforderung, Quellen und Vorlagen nie; bei Verstoß Liste, Exit 1, nichts zurücksetzen (entscheide ich); (c) Handover wurde in diesem Lauf geschrieben oder ergänzt; (d) `pruefen`.
15| > 7. Nacharbeit: `kette.py umsetzung-auto <kurztitel> --nacharbeit <datei.md>` – Auftrag aus der Datei, Handover wird unter „## Nachbesserung n" ergänzt. Zwei Nachbesserungen in Folge ohne Fortschritt (rote Tests nicht weniger, `pruefen` nicht besser) ⇒ keine weitere starten, Exit 1, „Übergabe an Hawe".
16| > 8. Während des Laufs: je Werkzeugaufruf eine kurze Zeile, dazu jede Minute ein Lebenszeichen.
17| > 9. Exit 0 nur, wenn der Lauf abgeschlossen ist, kein Verstoß vorliegt und `pruefen` 0 meldet. RUNBOOK Phase B und die Spec-Vorlage (`## Schreibbereich`) werden ergänzt.
18| > 10. Der Prompt von `umsetzung-auto` verweist auf `docs/learnings/LERNREGELN.md`, Abschnitte „Umsetzung" und „Tests", als Pflichtlektüre vor der ersten Änderung.
19| > Tests nutzen eine Attrappe statt `opencode` (Pfad über `KETTE_OPENCODE`), nie ein echtes Modell. Bestehende Tests bleiben grün, Code läuft unter Python 3.10. Abnahme: echter Lauf mit dem 35B an einer Mini-Spec, die Claude schreibt; Dauer wird gemessen.
20| > Lies NUR zwei Dateien: diese Anforderung und docs/projekt_management/spec_paket_20261027_umsetzung_auto.md. Weitere Stellen nur, wenn wirklich etwas fehlt: search_files, dann read_file mit start_line/end_line, höchstens drei Mal.
21| 
22| ## Antworten auf Rueckfragen
23| 
24| **2026-10-27 09:56** — Frage (Hawe): Dann läuft alles ohne Gedächtnis?
25| 
26| > Verstehe ich, kein Gedächtnis! Nimm Punkt 10 auf!
27| > (Von Claude nach Hawes Zustimmung am 27.10. 09:59 eingetragen: neue Sitzung je Lauf und kein Gedächtnis-Proxy sind gewollt; Zustand liegt in Dateien, Kettenwissen kommt über Punkt 10.)
28| **2026-10-27 10:08** — Frage: Globale ~/.config/opencode/AGENTS.md verlangt Erklärung vor Architekturänderungen und englische Bezeichner – Widerspruch zum Automatikbetrieb?
29| 
30| > Ja. Die globale AGENTS.md bleibt unverändert. Zu Punkt 3: umsetzung_nacht sagt ausdrücklich, dass er Vorrang vor allgemeinen Kommunikationsregeln hat: nicht vorab erklären oder auf Freigabe warten, sondern umsetzen und Begründungen ins Handover schreiben; Bezeichner wie in Spec und bestehendem Code (in diesem Repo deutsch).
31| 
```
