# Quellen Schritt 2 (2 ok, 1 schlecht)

- UNKLAR - `role-split/kette/spec_pruefen.py` PFLICHT – Liste der Pflichtabschnitte, die geprüft werden müssen

### `role-split/kette/kette.py` def pruefen (Zeilen 619–646) – Hauptfunktion für die Prüfung (vergleicht mit alter `abgleich`/`tests_laufen`)

```python
619| def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> int:
620|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
621|         print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
622|     commit = commit or spec_commit(kurztitel)
623|     if not commit:
624|         print(f"Kein Commit 'Spec {kurztitel}' gefunden. Ruecksetzpunkt mit --commit angeben "
625|               f"(git log --oneline -10)."); return 2
626|     teile_dict = _pruefen_teile(kurztitel, commit, timeout)
627|     codes = {k: v[0] for k, v in teile_dict.items()}
628|     teile = []
629|     for titel_key in ("abgleich", "unittest", "gegenprobe"):
630|         code, out = teile_dict[titel_key]
631|         # Titel wiederherstellen: gegenprobe braucht {commit}
632|         titel = f"gegenprobe gegen {commit}" if titel_key == "gegenprobe" else titel_key
633|         teile.append(f"## {titel}  (Exit {code})\n\n```\n{out.rstrip()}\n```\n")
634|     kurz = " | ".join(f"{k.split()[0]}: {'ok' if v == 0 else ('Abweichung' if v == 1 else 'FEHLER')}"
635|                       for k, v in codes.items())
636|     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
637|     kopf = (f"# Pruefung {kurztitel}\n\n- Zeit: {dt.datetime.now():%Y-%m-%d %H:%M}\n"
638|             f"- Ruecksetzpunkt: {commit}\n- Kurz: {kurz}\n\n")
639|     ziel = ablage(kurztitel) / f"pruefung_{datum}_{kurztitel}.md"
640|     ziel.write_text(kopf + "\n".join(teile), encoding="utf-8")
641|     print("\n".join(teile))
642|     print(f"\n==> {kurz}")
643|     print(f"==> Ausgabe gespeichert: {ziel.relative_to(ROOT)}  (dem Gegenpruefer nur noch Bescheid sagen)")
644|     return max(codes.values())
645| 
646| # ---------------------------------------------------------------- Review-Paket
```

### `role-split/kette/spec_pruefen.py` def pruefe (Zeilen 194–226) – Mechanische Prüfung der Spec-Struktur (Ziel, Schreibbereich, Quellen etc.)

```python
194| def pruefe(spec_text: str) -> tuple[list[str], list[str], dict]:
195|     """Spec mechanisch pruefen. Gibt (befunde, hinweise, groesse) zurueck."""
196|     # HTML-Kommentare entfernen
197|     text = re.sub(r"<!--.*?-->", "", spec_text, flags=re.S)
198| 
199|     befunde: list[str] = []
200|     hinweise: list[str] = []
201| 
202|     # A2.1: Pflichtabschnitte
203|     _abschnitte(text, befunde)
204| 
205|     # A2.2: Platzhalter
206|     for p in PLATZHALTER:
207|         if p in text:
208|             befunde.append(f"Platzhalter aus der Vorlage: {p}")
209| 
210|     # A2.3: Offene Fragen
211|     offene = kette.abschnitt(text, "Offene Fragen").strip()
212|     if offene:
213|         zeilen = [z.strip() for z in offene.splitlines() if z.strip()]
214|         if len(zeilen) == 1 and re.match(r"^(?:[-*]\s*)?Keine\b", zeilen[0], re.I):
215|             pass  # geklärt
216|         else:
217|             befunde.append("Offene Fragen nicht geklärt – erst beantworten, dann „Keine“")
218| 
219|     # A3: Groesse und Zuordnung
220|     _zuordnung(text, befunde, hinweise)
221| 
222|     # A4: Schreibbereich und Quellen
223|     _bereich_quellen(text, befunde, hinweise)
224| 
225|     g = _groesse(text)
226|     return befunde, hinweise, g
```
