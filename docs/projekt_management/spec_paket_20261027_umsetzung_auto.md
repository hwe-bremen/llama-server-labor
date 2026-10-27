# Spec-Paket: umsetzung_auto (gebaut 27.10. von Claude, Stand Commit c7a81af)

Alles, was die Spec braucht. **Lies nur diese Datei und die Anforderung.** Weitere Stellen nur, wenn wirklich etwas fehlt: search_files + read_file mit start_line/end_line, höchstens drei Nachlesungen. Zeilennummern sind echte Zeilen der jeweiligen Datei am Stand `c7a81af`.

## 1. Gemessene Fakten: `opencode run` 1.19.3 an Hawes Mac (Probeläufe 27.10.)

Installiert: `/opt/homebrew/bin/opencode`, Version **1.19.3**. Modellname für das 35B laut `opencode models`:
`llamacpp/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL`.

**Flags von `opencode run` (aus `opencode run --help`, wörtlich gekürzt):**
```
  message  message to send                                                     [array]
      --command      the command to run, use message for args
  -c, --continue     continue the last session
  -s, --session      session id to continue
      --fork         fork the session before continuing (requires --continue or --session)
  -m, --model        model to use in the format of provider/model
      --agent        agent to use
      --format       format: default (formatted) or json (raw JSON events)  [choices: "default", "json"]
  -f, --file         file(s) to attach to message
      --title        title for the session
      --attach       attach to a running opencode server
      --dir          directory to run in
      --variant      model variant (provider-specific reasoning effort)
      --thinking     show thinking blocks
      --auto         auto-approve permissions that are not explicitly denied (dangerous!)
```

**Gemessenes Verhalten (sechs Probeläufe, Agent-Rechte aus der Frontmatter):**

| Probe | Aufbau | Ergebnis |
|---|---|---|
| P1 | Agent `umsetzung`, Befehl fällt unter `"*": ask` | sofort abgelehnt, stderr: `permission requested: bash (touch …); auto-rejecting`. Danach **endet der Lauf ohne Antworttext** (letztes Ereignis `step_finish` mit `reason: tool-calls`). |
| P2 | wie P1 + `OPENCODE_PERMISSION={"bash":{"touch*":"deny"}}` | identisch mit P1 – Env-Regel wirkungslos gegen die Agent-Regel |
| P3 | erlaubter Unittest, der 60 s schläft, `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS=10000` | nach 10 s abgebrochen; Werkzeugergebnis enthält `shell tool terminated command after exceeding timeout 10000 ms`; Modell meldet das und endet mit `reason: stop` |
| P4 | Agent `umsetzung` (`"*": ask`) + Env `touch*: allow` | abgelehnt wie P1 – Env lockert Agent-Regel nicht |
| P5 | Agent mit `bash: "*": deny` | Fehler `The user has specified a rule which prevents you from using this specific tool call. Here are some of the relevant rules [...]`; **Modell läuft weiter** und antwortet (`reason: stop`) |
| P6 | Agent `"*": deny` + Env `touch*: allow` | bleibt verboten |

- **Exit-Code von `opencode run` war in allen sechs Läufen 0** – auch nach Ablehnung und ohne Antwort. Erfolg ist nur aus den JSON-Ereignissen ablesbar.
- **Regelreihenfolge** laut Regelliste in P6: `{"permission":"*","action":"allow","pattern":"*"}` (Grundeinstellung) → Regeln aus `OPENCODE_PERMISSION` → Regeln der Agent-Datei; die **letzte passende Regel gewinnt**. `OPENCODE_PERMISSION` taugt daher weder als Schreibgrenze noch als Commit-Sperre.
- Vermutung (nicht gemessen): Kategorien, die die Agent-Datei nicht nennt, fallen auf die Grundeinstellung `allow`.
- Dauer der Probeläufe: erster Lauf 35 s (Modell laden), danach 3–23 s.

**JSON-Ereignisse (`--format json`, eine Zeile je Ereignis, echte Beispiele gekürzt):**
```json
{"type":"step_start","timestamp":1793088760917,"sessionID":"ses_e839…","part":{"type":"step-start","snapshot":"4c56…"}}
{"type":"tool_use","timestamp":1793088762972,"sessionID":"ses_e839…","part":{"type":"tool","tool":"bash","callID":"PPR0…","state":{"status":"error","input":{"command":"touch sandbox/k10_probe/p1_ask","workdir":"/Users/…/llama-server"},"error":"The user rejected permission to use this specific tool call."}}}
{"type":"tool_use",…,"part":{"type":"tool","tool":"bash","state":{"status":"completed","input":{"command":"python3 -m unittest -v …"},"output":"…<shell_metadata>\nshell tool terminated command after exceeding timeout 10000 ms…","metadata":{"exit":null}}}}
{"type":"step_finish",…,"part":{"type":"step-finish","reason":"tool-calls","tokens":{"total":12629,"input":12532,"output":97,"reasoning":0,"cache":{"write":0,"read":0}},"cost":0}}
{"type":"text",…,"part":{"type":"text","text":"Der Befehl wurde ausgeführt, …"}}
{"type":"step_finish",…,"part":{"type":"step-finish","reason":"stop","tokens":{…}}}
```
Unterscheidbare Fälle: `tool_use` mit `state.status` = `completed` / `error`; Ablehnung durch `ask` („user rejected permission"), Ablehnung durch `deny` („rule which prevents"). Ein Lauf ist regulär beendet, wenn das letzte `step_finish` `reason: stop` hat.

## 2. Messwerte Umsetzer (aus K9, `docs/learnings/kette_paket_vollstaendig.md`)
- 27B in OpenCode: Erstumsetzung 2 h 45, NB1 ~4,5 h, NB2 ~4,5 h ohne Abschluss.
- OpenCode-Commit `1b2e74c` („checkpoint") trotz „Kein Commit". Vermutung (Claude, nicht belegt): Er stammt aus Schritt 2 des Agenten `umsetzung` („Lege … einen Git-Commit als Rücksetzpunkt an … Frag vorher") und wurde im TUI bestätigt.
- 35B als Umsetzer: noch keine Messung (Ziel dieser Kette).

## 3. kette.py – Übersicht (Funktionen und Konstanten)
```
  78| HERE = Path(__file__).resolve().parent
  79| ROOT = HERE.parent.parent
  80| PM = ROOT / "docs" / "projekt_management"
  81| PROMPTS = HERE / "prompts"
  82| SCHRITTE = ("spec", "umsetzung", "review", "review2", "tief")
  86| def abschnitt(text: str, titel: str) -> str:
  92| def tabelle(block: str) -> list[dict]:
 108| def spalte(zeile: dict, *namen: str) -> str | None:
 116| def ja(wert: str | None) -> bool:
 121| def urteil(pfad: Path, anhaengen: bool = False) -> int:
 191| TEST_ID = r"[A-Z]{0,3}T\d+"
 192| STOP = {"mit", "ohne", "und", "im", "in", "der", "die", "das", "den", "dem", "des", "ein", "eine",
 194| TAG = re.compile(r"^[a-z]\d+$")   # Anforderungs-Kuerzel wie n6, a3, e1
 197| def tests_finden(text: str) -> dict[str, str]:
 211| def woerter(titel: str) -> set[str]:
 216| def passt(spec_titel: str, ho_titel: str) -> float:
 223| PRUEF_AUFRUFE = re.compile(r"^(assert\w*|fail\w*)$")
 226| def methoden_pruefen(code: str) -> list[str]:
 255| def datei_suchen(typ: str, kurztitel: str, datum: str | None) -> Path | None:
 265| def abgleich(kurztitel: str, datum: str | None = None, schwelle: float = 0.6) -> int:
 316| LAEUFER = r"""
 320| def name(t): return t.id().split(".")[-1].split(" ")[0]
 322| def alle(s):
 338| def tests_laufen(skript: Path, timeout: int) -> dict[str, str] | None:
 355| def _zuruecksetzen_und_testen(skript: Path, d: str, commit: str, timeout: int) -> dict[str, str] | None:
 382| def gegenprobe(kurztitel: str, commit: str, timeout: int = 300) -> int:
 437| def spec_commit(kurztitel: str) -> str | None:
 448| def _pruefen_teile(kurztitel: str, commit: str | None = None, timeout: int = 300) -> dict:
 487| def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> int:
 516| PAKET_DIFF_ZEILEN = 700        # je Datei; Rest liest das Review gezielt nach
 517| PAKET_DATEI_ZEILEN = 900       # bei Umbau: ganze aktuelle Datei statt Diff, hoechstens so viele Zeilen
 518| PAKET_WARNUNG_ZEICHEN = 80000  # ~23k Token: darueber wird es fuer 64K Kontext eng
 520| PAKET_NIE = ("docs/", "experiments/",)
 522| KETTE_PAKET_MAX = int(os.environ.get("KETTE_PAKET_MAX", "150000"))
 525| def _git(*a: str) -> str:
 529| def _aenderungen(commit: str, kurztitel: str | None, nur: set[str] | None = None
 564| def _bloecke(text: str, muster: str) -> str:
 581| def _testplan_kurz(spec: str) -> str:
 591| def _testliste(skript: Path) -> str:
 606| def _auffaellige_tests(pruefung: str) -> set[str]:
 616| def _testcode(skript: Path, auffaellig: set[str], grenze: int = 60) -> str:
 639| def _vorrang(d: str, nur: set[str] | None) -> int:
 646| def _diff(commit: str, nur: set[str] | None = None, kurztitel: str | None = None
 672| def _kappen(datei: str, zeilen: list[str], art: str, grenze: int, nicht_genannt: bool = False) -> str:
 686| def _handover_dateien(text: str) -> set[str] | None:
 693| def _pruefung_kurz(pfad: Path | None) -> str:
 707| def paket(kurztitel: str, commit: str | None = None, datum: str | None = None, still: bool = False) -> int:
 812| def _befunde(text: str) -> list[dict]:
 816| def _ist_hoch(zeile: dict) -> bool:
 821| def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
 893| def _datum_aus(pfad: Path | None) -> str | None:
 898| def aufgabe_lesen(pfad: Path) -> str:
 905| def anforderung(kurztitel: str, aufgabe: str | None, antwort: str | None, frage: str | None,
 937| QUELLE_RE = re.compile(
 943| _TRENNER = r"\s*(?:[–—:]|-(?=\s))\s*"
 944| _ZEILEN = r"(?:Zeilen?|Z\.)\s*(\d+)\s*(?:[–—-]\s*(\d+))?"
 947| def quelle_lesen(z: str) -> dict | None:
 985| def _block_name(zeilen: list[str], name: str) -> tuple[tuple[int, int] | None, str]:
1002| def _textstelle(zeilen: list[str], text: str, umfeld: int = 12) -> tuple[int, int] | None:
1009| def _passt(code_zeilen: list[str], zweck: str | None) -> list[str]:
1023| QUELLE_MAX = 400
1024| SPRACHE = {".py": "python", ".sh": "bash", ".command": "bash", ".json": "json", ".md": "markdown",
1028| def _block(zeilen: list[str], art: str, name: str) -> tuple[int, int] | None:
1051| def quellen(kurztitel: str, datum: str | None = None) -> int:
1138| def prompt(schritt: str, kurztitel: str, datum: str | None, commit: str | None, lauf: int | None = None) -> int:
1194| KETTE_LLM_URL = os.environ.get("KETTE_LLM_URL", "http://127.0.0.1:8080")
1195| KETTE_LLM_MODEL = os.environ.get("KETTE_LLM_MODEL", "unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL")
1196| KETTE_LLM_TIMEOUT = int(os.environ.get("KETTE_LLM_TIMEOUT", "1800"))
1197| KETTE_LLM_MAX_TOKENS = int(os.environ.get("KETTE_LLM_MAX_TOKENS", "8000"))
1200| KETTE_LLM_TEMPERATURE = os.environ.get("KETTE_LLM_TEMPERATURE", "")
1201| KETTE_ABGESCHNITTEN = Path(os.environ.get("KETTE_ABGESCHNITTEN", "/tmp"))
1202| KETTE_HERZSCHLAG_S = int(os.environ.get("KETTE_HERZSCHLAG_S", "60"))
1205| def _rel(pfad):
1216| def _herzschlag_stopp_event(lauf_nummer: int):
1232| def _api_ruf(prompt_text: str, lauf_nummer: int) -> tuple[str | None, dict]:
1294| def _freier_verdiktpfad(datum: str, kurztitel: str, lauf: int) -> Path:
1311| def _ist_auswertbar(verdikt_text: str) -> bool:
1326| def review_auto(kurztitel: str) -> int:
1463| def main(argv=None) -> int:
```

## 4. kette.py – prompt (Zeilen 1138–1191)
Gibt den Prompt auf stdout aus und kopiert ihn per `pbcopy`; liefert nur den Exit-Code, nicht den Text.
```python
1138| def prompt(schritt: str, kurztitel: str, datum: str | None, commit: str | None, lauf: int | None = None) -> int:
1139|     vorlage = PROMPTS / f"{schritt}.md"
1140|     if not vorlage.is_file():
1141|         print(f"Keine Vorlage: {vorlage}"); return 2
1142|     anf = datei_suchen("anforderung", kurztitel, datum)
1143|     if not datum:
1144|         # Datum der vorhandenen Spec (Kette 4: "heute" passte nicht mehr am Folgetag)
1145|         datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or _datum_aus(anf) \
1146|             or dt.date.today().strftime("%Y%m%d")
1147|         anf = anf or datei_suchen("anforderung", kurztitel, datum)
1148|     if not commit and schritt != "spec":
1149|         commit = spec_commit(kurztitel)          # Ruecksetzpunkt = Commit "Spec <kurztitel>" (22.10.)
1150|         if commit:
1151|             print(f"Ruecksetzpunkt = Commit 'Spec {kurztitel}' ({commit}).", file=sys.stderr)
1152|     if not commit:
1153|         try:
1154|             commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
1155|                                     capture_output=True, text=True, check=True).stdout.strip()
1156|         except Exception:
1157|             commit = "<HASH>"
1158|         if schritt != "spec":
1159|             print(f"Hinweis: Ruecksetzpunkt = HEAD von {ROOT} ({commit}). Stimmt das (Worktree?)? "
1160|                   "Sonst --commit angeben.", file=sys.stderr)
1161|     paket_pfad = f"docs/projekt_management/review_paket_{datum}_{kurztitel}.md"
1162|     if schritt in ("review", "review2", "tief"):
1163|         if paket(kurztitel, commit if commit != "<HASH>" else None, None, still=False) != 0:
1164|             print("Hinweis: Review-Paket nicht gebaut (siehe oben) – Prompt verweist trotzdem darauf.",
1165|                   file=sys.stderr)
1166|     anf_pfad = f"docs/projekt_management/{anf.name}" if anf else \
1167|         f"docs/projekt_management/anforderung_{datum}_{kurztitel}.md"
1168|     if not anf:
1169|         print(f"Hinweis: {anf_pfad} fehlt. Anlegen mit: kette.py anforderung {kurztitel} --aufgabe \"…\"",
1170|               file=sys.stderr)
1171|     text = (vorlage.read_text(encoding="utf-8")
1172|             .replace("{kurztitel}", kurztitel)
1173|             .replace("{datum}", datum)
1174|             .replace("{commit}", commit)
1175|             .replace("{anforderung}", anf_pfad)
1176|             .replace("{quellen}", f"docs/projekt_management/quellen_{datum}_{kurztitel}.md")
1177|             .replace("{paket}", paket_pfad))
1178|     if anf:
1179|         text = re.sub(r"<AUFGABE[^>]*>", lambda _m: aufgabe_lesen(anf), text)
1180|     text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
1181|     if lauf:
1182|         # Eigener Dateiname je Review-Lauf: sonst findet Lauf 2 das Verdikt von Lauf 1 (geschuetzt),
1183|         # liest es und haengt an (Probe K4, 22.10.) -> Laeufe nicht mehr unabhaengig.
1184|         text = text.replace("_<modellkürzel>.md", f"_<modellkürzel>_lauf{lauf}.md")
1185|         text += "Verdikte anderer Läufe liest du nicht.\n"
1186|     print(text)
1187|     if shutil.which("pbcopy"):
1188|         subprocess.run(["pbcopy"], input=text, text=True)
1189|         print("(in die Zwischenablage kopiert)", file=sys.stderr)
1190|     return 0
1191| 
```

## 5. kette.py – spec_commit, _pruefen_teile, pruefen (Zeilen 437–514)
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
 446| 
 447| 
 448| def _pruefen_teile(kurztitel: str, commit: str | None = None, timeout: int = 300) -> dict:
 449|     """Teilergebnisse von abgleich, unittest, gegenprobe. Rueckgabe: dict mit den drei Schlüsseln."""
 450|     import contextlib
 451|     import io
 452|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
 453|         return {"abgleich": (2, "Kurztitel ungueltig"), "unittest": (2, ""), "gegenprobe": (2, "")}
 454|     commit = commit or spec_commit(kurztitel)
 455|     if not commit:
 456|         return {"abgleich": (2, f"Kein Commit 'Spec {kurztitel}'"),
 457|                 "unittest": (2, ""), "gegenprobe": (2, "")}
 458|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
 459| 
 460|     def schritt(titel: str, fn):
 461|         puffer = io.StringIO()
 462|         with contextlib.redirect_stdout(puffer):
 463|             try:
 464|                 code = fn()
 465|             except Exception as e:
 466|                 print(f"!!! Werkzeugfehler: {type(e).__name__}: {e}")
 467|                 code = 2
 468|         return code, puffer.getvalue()
 469| 
 470|     def unittest_lauf():
 471|         if not skript.is_file():
 472|             print(f"Kein Testskript {skript.relative_to(ROOT)}")
 473|             return 2
 474|         r = subprocess.run([sys.executable, "-m", "unittest", "-v", f"tests/test_{kurztitel}.py"],
 475|                            cwd=ROOT, capture_output=True, text=True, timeout=timeout)
 476|         print((r.stdout + r.stderr).rstrip())
 477|         return 0 if r.returncode == 0 else 1
 478| 
 479|     abgl_code, abgl_out = schritt("abgleich", lambda: abgleich(kurztitel))
 480|     unit_code, unit_out = schritt("unittest", unittest_lauf)
 481|     gegen_code, gegen_out = schritt(f"gegenprobe gegen {commit}",
 482|                                     lambda: gegenprobe(kurztitel, commit, timeout))
 483|     return {"abgleich": (abgl_code, abgl_out), "unittest": (unit_code, unit_out),
 484|             "gegenprobe": (gegen_code, gegen_out)}
 485| 
 486| 
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
 513| 
 514| # ---------------------------------------------------------------- Review-Paket
```

## 6. kette.py – _git und _aenderungen (Zeilen 525–562)
```python
 525| def _git(*a: str) -> str:
 526|     return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
 527| 
 528| 
 529| def _aenderungen(commit: str, kurztitel: str | None, nur: set[str] | None = None
 530|                  ) -> tuple[list[str], list[tuple[str, list[tuple[str, str]]]]]:
 531|     """A1: Alle seit <commit> geaenderten/neuen Dateien (ausser PAKET_NIE), getrennt nach
 532|     zur Kette gehoerig / fremd. Gemeinsame Auswahl fuer paket und gegenprobe (A5).
 533| 
 534|     Quellen: Commits <commit>..HEAD, nicht committete Aenderungen (auch vorgemerkt),
 535|     unversionierte Dateien. Zur Kette gehoert eine Datei, wenn sie (a) in einem Commit mit dem
 536|     Kurztitel in der Nachricht geaendert wurde, (b) nicht committete oder unversionierte
 537|     Aenderungen hat oder (c) in der Uebergabe genannt wird. Sonst fremd.
 538|     Rueckgabe: (kette, fremd) mit fremd = [(datei, [(kurzhash, betreff), ...]), ...]."""
 539|     committet = set(_git("diff", "--name-only", commit, "HEAD").split())
 540|     offen = set(_git("diff", "--name-only", "HEAD").split())          # unstaged + staged
 541|     neu = set(_git("ls-files", "--others", "--exclude-standard").split())
 542|     alle = sorted(d for d in committet | offen | neu
 543|                   if not d.startswith(PAKET_NIE) and (ROOT / d).is_file())
 544|     log = [z.split("\t", 1) for z in _git("log", "--format=%H%x09%s", f"{commit}..HEAD").splitlines()
 545|            if "\t" in z]
 546|     # Kurztitel als ganzes Wort (nicht "g" in "gross"): links/rechts kein a-z, 0-9, _
 547|     muster = re.compile(rf"(?<![a-z0-9_]){re.escape(kurztitel)}(?![a-z0-9_])") if kurztitel else None
 548|     eigene = {h for h, betreff in log if muster and muster.search(betreff)}
 549|     kette: list[str] = []
 550|     fremd: list[tuple[str, list[tuple[str, str]]]] = []
 551|     for d in alle:
 552|         if d in offen or d in neu or (nur and d in nur):
 553|             kette.append(d)
 554|             continue
 555|         dc = [z.split("\t", 1) for z in
 556|               _git("log", "--format=%H%x09%s", f"{commit}..HEAD", "--", d).splitlines() if "\t" in z]
 557|         if any(h in eigene for h, _ in dc):
 558|             kette.append(d)
 559|         else:
 560|             fremd.append((d, [(h[:7], b) for h, b in dc]))
 561|     return kette, fremd
 562| 
```

## 7. kette.py – Konstanten für API-Läufe und Herzschlag (Zeilen 1194–1202, 1216–1229)
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

## 8. kette.py – Anfang von review_auto als Muster (Zeilen 1326–1345)
```python
1326| def review_auto(kurztitel: str) -> int:
1327|     """Review-Paket bauen, zwei API-Laeufe, Verdikte speichern, zusammenfuehren."""
1328|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
1329|         print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
1330| 
1331|     # A2: Pruefung, Abbruch bei roten Unit-Tests
1332|     teile_dict = _pruefen_teile(kurztitel)
1333|     unit_code = teile_dict["unittest"][0]
1334|     if unit_code != 0:
1335|         if unit_code == 2:
1336|             print(f"Pruefung-Fehler (Exit 2) – Review nicht moeglich."); return 2
1337|         print("Unit-Tests rot – direkt nachbessern, kein Review nötig"); return 1
1338| 
1339|     # A3: Review-Paket bauen
1340|     if paket(kurztitel) != 0:
1341|         print("Review-Paket nicht gebaut – Voraussetzung fehlt (Exit 2)."); return 2
1342|     paket_pfad = PM / f"review_paket_{_datum_aus(datei_suchen('spec', kurztitel, None)) or dt.date.today().strftime('%Y%m%d')}_{kurztitel}.md"
1343|     paket_text = paket_pfad.read_text(encoding="utf-8") if paket_pfad.exists() else ""
1344| 
1345|     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
```

## 9. kette.py – main (Zeilen 1463–1512)
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

## 10. Prompt `role-split/kette/prompts/umsetzung.md` (ganz)
```markdown
<!-- Schritt 2, OpenCode, Agent „umsetzung" (Tab). Rücksetzpunkt = aktueller Commit. -->
Setz docs/projekt_management/spec_{datum}_{kurztitel}.md um.

Konstanten, Formate, Schnittstellen und Optionen nimmst du ausschließlich aus {quellen} und dem Code selbst, nie aus dem Gedächtnis. Fehlt dort etwas, setz nichts Erfundenes ein, sondern nenne es im Handover unter „Abweichungen".
Verbindliche Vorgabe ist {anforderung}. Widerspricht die Spec ihr an einer Stelle, setzt du die Spec um und nennst den Widerspruch im Handover unter „Abweichungen".

- Rücksetzpunkt ist Commit {commit}; nicht selbst committen.
- Die Tests der Spec schreibst du als tests/test_{kurztitel}.py (unittest), je Test-ID eine Methode test_<id>_… (z. B. test_t1_timeout). Kein Test darf Außenwirkung haben: keine echten Server außer 127.0.0.1, keine echten Datenordner (immer temporäres Verzeichnis), kein echter Versand.
- Ein Test, der sich nicht wie in der Spec bauen lässt, wird NICHT durch einen anderen ersetzt: unter „Abweichungen" und „Nicht getestet" nennen.
- Befehle mit Außenwirkung führst du nie aus, auch nicht nach Freigabe. Nenne sie im Handover unter „Hawe muss ausführen".
- Nach jeder Datei: python3 -m py_compile bzw. bash -n.
- Handover nach docs/projekt_management/handover_{datum}_{kurztitel}.md, Vorlage _vorlage_handover.md. Testtitel exakt wie in der Spec, darunter die echte Ausgabe von python3 -m unittest -v tests/test_{kurztitel}.py.
```

## 11. Agent `.opencode/agents/umsetzung_nacht.md` – Frontmatter (Zeilen 1–27)
Unbeaufsichtigter Agent, existiert seit K7; Text: „Niemand beantwortet Rückfragen … Lege keinen Commit an … Eine Ablehnung ist kein Fehler: such keinen Umweg".
```yaml
---
description: Wie "umsetzung", aber unbeaufsichtigt (Nachtlauf) – keine Rueckfragen, nur Positivliste
mode: primary
temperature: 0.2
permission:
  edit: allow
  read: allow
  glob: allow
  grep: allow
  list: allow
  external_directory: deny
  webfetch: deny
  websearch: deny
  task: deny
  skill: deny
  question: deny
  doom_loop: deny
  bash:
    "*": deny
    "python3 -m py_compile *": allow
    "bash -n *": allow
    "python3 -m unittest*": allow
    ".venv/bin/python -m unittest*": allow
    "git status*": allow
    "git diff*": allow
    "git log*": allow
---
```
Zum Vergleich: Agent `umsetzung` (Handbetrieb) hat `bash: "*": ask`, `git push*`/`sudo *` deny, und in Schritt 2 „Lege vor der ersten Dateiänderung einen Git-Commit als Rücksetzpunkt an … Frag vorher".
`git commit` ist in `umsetzung_nacht` nur über `"*": deny` verboten, nicht ausdrücklich genannt.

## 12. Vorlagen
- `docs/projekt_management/_vorlage_handover.md`, Abschnitte: Umgesetzt · Geänderte und neue Dateien · Abweichungen von der Spec · Annahmen · Getestet (mit echter Ausgabe) · Gegenprobe · Außenwirkung · Hawe muss ausführen · Nicht getestet · Offene Punkte / bekannte Schwächen.
- `docs/projekt_management/_vorlage_spec.md`, Kopf: `- **Betroffene Dateien:** <nur Dateien, die du gelesen hast>` – es gibt **keinen Abschnitt, der festlegt, welche Dateien die Umsetzung ändern darf**. Abschnitte: Ziel · Nicht-Ziele · Außenwirkung und Sperre · Einstiegspunkte · Quellen · Anforderungen · Fehlerpfade · Testplan · Offene Fragen · Abweichende Meinung.

## 13. Testmuster für kette.py (aus `tests/test_kette_review_auto.py`)
- Import: `sys.path.insert(0, …/"role-split"/"kette")`, dann `import kette`.
- Abhängigkeiten werden je Test ersetzt und per `addCleanup(setattr, kette, …)` zurückgesetzt, z. B.
  `kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}`, `kette.paket = lambda *a: 0`.
- `kette.PM` zeigt im Test auf ein `tempfile.TemporaryDirectory()`; Ausgabe über `redirect_stdout(io.StringIO())`.
- Git-Repos für Tests: `role-split/kette/test_kette.py` Klasse `PruefenTests.setUp` (temporäres Repo, `git init`, Commit „Spec g", `kette.ROOT`/`kette.PM` umgebogen).
- Für OpenCode gibt es noch keine Attrappe; ein echter `opencode`-Aufruf im Unittest wäre Außenwirkung (Modell, Laufzeit).

## 14. Relevante Lernregeln (wörtlich gekürzt aus `docs/learnings/LERNREGELN.md`)
- **R07** Nur die im Auftrag genannten Dateien ändern; Nachbesserungen additiv.
- **R14** Wo es eine Außenwelt gibt, ist ein echter Lauf Pflichtphase.
- **R20** Teilerfolg ⇒ Exit ≠ 0.
- **R27/R36** Netz- und Testaufrufe immer mit Zeitlimit; ein hängender Test sieht aus wie langsames Arbeiten.
- **R32** Rücksetzpunkt vor jeder agentischen Änderung committen.
- **R40** Wer Arbeit zurücksetzt, korrigiert auch den Handover.
- **R42** Zwei Nachbesserungen ohne Fortschritt ⇒ Gegenprüfer übernimmt; Selbst-Commits des Umsetzers melden.

## 15. Umgebung
- Repo: `~/PycharmProjects/llama-server`, Git-Zweig `main`. `.gitignore` enthält u. a. `tmp/`, `sandbox/`, `*.log`, `role-split/results/`.
- Python am Mac 3.13/3.14, Claudes Geräte-Shell 3.10 → Code muss unter 3.10 laufen (keine 3.11+-Module wie `tomllib`).
- `kette.py` nutzt nur die Standardbibliothek.
- Router/llama-server auf `127.0.0.1:8080`.
- OpenCode-Konfiguration (gemessen 27.10., außerhalb des Repos): `~/.config/opencode/opencode.json`, `OPENCODE_CONFIG` leer. Provider-Adressen: `llamacpp` → `http://127.0.0.1:8080/v1`, `gedaechtnis` → `http://127.0.0.1:8091/v1` (Gedächtnis-Proxy), `slipstream` → `:8083/v1`, `diagnose` → `:8085/v1`. Das Präfix `llamacpp/` bedeutet also: direkt am Router, ohne Gedächtnis.
- Im selben Ordner liegt eine globale `AGENTS.md` (375 Byte), die OpenCode vermutlich in jede Sitzung einblendet – Inhalt hier nicht bekannt.
- `opencode debug agent <name>` zeigt die aufgelöste Agent-Konfiguration, `opencode debug config` die aufgelöste Gesamtkonfiguration (aus `opencode debug --help`; Ausgabeformat nicht gemessen).
- Sitzungsdaten: `~/.local/share/opencode/opencode.db`, derzeit ca. 1,6 GB; jeder `opencode run` legt eine Sitzung dort ab.
