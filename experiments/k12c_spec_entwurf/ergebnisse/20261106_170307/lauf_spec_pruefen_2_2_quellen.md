# Quellen Schritt 2 (5 ok, 0 schlecht)


### `role-split/kette/spec_pruefen.py` def pruefe (Zeilen 194–226) – um die Prüfung zu erweitern

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

### `role-split/kette/spec_pruefen.py` def _abschnitte (Zeilen 56–63) – um Befunde zu sammeln

```python
56| def _abschnitte(text: str, befunde: list[str]) -> None:
57|     """A2.1: Pflichtabschnitte pruefen."""
58|     for titel in PFLICHT:
59|         muster = rf"^##\s+{re.escape(titel)}"
60|         if not re.search(muster, text, re.M | re.I):
61|             befunde.append(f'Abschnitt „## {titel}“ fehlt')
62|         elif not kette.abschnitt(text, titel).strip():
63|             befunde.append(f'Abschnitt „## {titel}“ ist leer')
```

### `role-split/kette/automatik.py` def groesse (Zeilen 18–35) – zur Größenermittlung

```python
18| def groesse(spec_text: str) -> dict:
19|     """Groessenpruefung der Spec.
20| 
21|     dateien: Eintraege aus kette._schreibbereich (keiner -> 0).
22|     anforderungen: Anzahl der Ueberschriften ### <Buchstabe(n)><Zahl>:
23|                    **nur** im Abschnitt ``## Anforderungen``.
24|     tests: Anzahl kette.tests_finden.
25|     """
26|     dateien = len(kette._schreibbereich(spec_text)) if kette._schreibbereich(spec_text) is not None else 0
27|     anforderungen = len(
28|         re.findall(
29|             r"^###\s+[A-Za-z]+\d+:\s",
30|             kette.abschnitt(spec_text, "Anforderungen"),
31|             re.M,
32|         )
33|     )
34|     tests = len(kette.tests_finden(spec_text))
35|     return {"dateien": dateien, "anforderungen": anforderungen, "tests": tests}
```

### `role-split/kette/kette.py` def urteil (Zeilen 169–237) – um das Urteil aus den Befunden zu leiten

```python
169| def urteil(pfad: Path, anhaengen: bool = False) -> int:
170|     if not pfad.is_file():
171|         print(f"Nicht gefunden: {pfad}"); return 2
172|     text = pfad.read_text(encoding="utf-8")
173|     m = re.search(r"\b(PASS|NACHBESSERN|FAIL)\b", abschnitt(text, "Ergebnis"))
174|     modell = m.group(1) if m else None
175|     hinweise, korrekturen = [], []
176| 
177|     offen = []
178|     for z in tabelle(abschnitt(text, "Anforderungen")):
179|         status = (spalte(z, "befund", "status") or "").lower()
180|         if "teilweise" in status or re.search(r"\bnicht\b", status):
181|             offen.append(f"{spalte(z, 'nr') or '?'}: {status}")
182| 
183|     befunde = tabelle(abschnitt(text, "Befunde"))
184|     hoch = []
185|     kriterien_da = befunde and any(spalte(befunde[0], k) is not None
186|                                    for k in ("datenverlust", "unbemerkt", "harte"))
187|     if befunde and not kriterien_da:
188|         hinweise.append("Altes Format: Befunde ohne Spalten Datenverlust/Unbemerkt/Harte Vorgabe "
189|                         "-- Schwere wird nur uebernommen, nicht geprueft.")
190|     for z in befunde:
191|         nr = spalte(z, "#") or "?"
192|         schwere = (spalte(z, "schwere") or "").lower()
193|         if not schwere.strip(" -"):
194|             continue  # leere Vorlagenzeile
195|         gruende = [k for k, n in (("Datenverlust", "datenverlust"), ("Unbemerkt", "unbemerkt"),
196|                                   ("Harte Vorgabe", "harte")) if ja(spalte(z, n))]
197|         if gruende and "hoch" not in schwere:
198|             korrekturen.append(f"Befund {nr}: als '{schwere}' eingestuft, aber ja bei "
199|                                f"{', '.join(gruende)} -> hoch")
200|             hoch.append(nr)
201|         elif "hoch" in schwere:
202|             hoch.append(nr)
203| 
204|     regel = "NACHBESSERN" if (hoch or offen) else "PASS"
205|     # Die Regel verschaerft nur: ein strengeres Modellurteil bleibt stehen.
206|     rang = {"PASS": 0, "NACHBESSERN": 1, "FAIL": 2}
207|     mech = max(regel, modell or "PASS", key=rang.get)
208| 
209|     zeilen = [f"Modell-Urteil:       {modell or 'nicht gefunden'}",
210|               f"Regel-Urteil:        {regel}",
211|               f"Es gilt:             {mech}"]
212|     if hoch:
213|         zeilen.append(f"  Befunde hoch: {', '.join(hoch)}")
214|     if offen:
215|         zeilen.append(f"  Anforderungen offen: {'; '.join(offen)}")
216|     zeilen += [f"  Korrektur: {k}" for k in korrekturen]
217|     zeilen += [f"  Hinweis: {h}" for h in hinweise]
218|     if modell and rang[regel] > rang[modell]:
219|         zeilen.append(f"  WIDERSPRUCH: Modell sagt {modell}, die Regel verlangt {regel}.")
220|     elif modell and rang[regel] < rang[modell]:
221|         zeilen.append(f"  Modell strenger als die Regel -- Begruendung im Verdikt lesen.")
222|     print("\n".join(zeilen))
223| 
224|     if anhaengen:
225|         marke = "## Mechanisches Urteil (kette.py)"
226|         if marke in text:
227|             print("(Abschnitt existiert schon, nicht erneut angehaengt)")
228|         else:
229|             stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
230|             pfad.write_text(text.rstrip("\n") + f"\n\n{marke}\n\n_{stamp}_\n\n```\n"
231|                             + "\n".join(zeilen) + "\n```\n", encoding="utf-8")
232|             print(f"Angehaengt an {pfad.name}")
233|     if modell is None and not befunde:
234|         return 2
235|     return 0 if mech == "PASS" else 1
236| 
237| # ---------------------------------------------------------------- abgleich
```

### `docs/projekt_management/_vorlage_spec.md` (Zeilen 1–101) – um die Spezifikation der Spec-Prüfung zu verstehen

```markdown
  1| # Spec: <kurztitel>
  2| 
  3| - **Datum:** <JJJJ-MM-TT>
  4| - **Modell:** <Modellname aus dem System-Prompt>
  5| - **Betroffene Dateien:** <nur Dateien, die du gelesen hast>
  6| - **Änderungsstellen:** <Zahl der Stellen im Code, die die Umsetzung ändert; ab etwa 10 teilen (R55, R59)>
  7| 
  8| ## Ziel
  9| 
 10| <1–3 Sätze>
 11| 
 12| ## Nicht-Ziele
 13| 
 14| - <…>
 15| 
 16| ## Schreibbereich
 17| 
 18| <!-- Dateien/Ordner, die die Umsetzung ändern darf, z. B. role-split/kette/ oder einzelne Pfade. Ordner mit „/" am Ende. -->
 19| Pflicht für `kette.py umsetzung-auto` (ohne diesen Abschnitt: Exit 2). Eine Zeile je Eintrag, Pfad in Backticks, relativ
 20| zum Repo. `tests/test_<kurztitel>.py` und der Handover sind immer erlaubt; Spec, Anforderung, Quellen und Vorlagen nie.
 21| 
 22| - `pfad/datei.py`
 23| - `pfad/ordner/`
 24| 
 25| ## Vorgabe-Tests
 26| 
 27| <!-- Optional (ab K11a). Nur wenn die Tests VOR der Umsetzung geschrieben werden (R48); sonst Abschnitt löschen. -->
 28| Mit diesem Abschnitt ist `tests/test_<kurztitel>.py` Vorgabe: Sie wird mit der Spec committet, vor dem Erstlauf von
 29| `kette.py tests-pruefen <kurztitel>` geprüft (je Test-ID eine Methode, Skript lädt, jeder Test rot vorab) und darf von der
 30| Umsetzung nicht geändert werden. Tests für bestehendes Verhalten tragen `(Bestand)` im Titel und müssen vorab grün sein (R49).
 31| 
 32| - `tests/test_<kurztitel>.py`
 33| 
 34| ## Außenwirkung und Sperre
 35| 
 36| - **Was kann die Aufgabe außerhalb des Repos auslösen?** <Mail, Netzwerk, echte Daten/DB, Schlüsselbund, launchd … oder „nichts">
 37| - **Technische Sperre für Tests:** <z. B. Variable, die echten Versand erst erlaubt; temporäres Datenverzeichnis. Eine Regel im Prompt reicht nicht.>
 38| 
 39| ## Einstiegspunkte
 40| 
 41| Welche geänderten Dateien werden **wie** gestartet (Pipeline, launchd, von Hand, als Modul importiert)?
 42| Für jeden Einstiegspunkt gibt es einen Test, der ihn so startet wie im Betrieb (ohne Außenwirkung, z. B.
 43| `runpy.run_path(…, run_name="kein_main")` für Imports, Ersatzskripte für Pipelines).
 44| Anlass 18.10.: Ein relativer Import ließ den Scout bei jedem Lauf abstürzen; alle Funktionstests waren grün.
 45| 
 46| | Datei | Wie gestartet | Test |
 47| |---|---|---|
 48| | `pfad/skript.py` | `python3 pfad/skript.py` aus `run_x.sh` | T… |
 49| 
 50| ## Quellen
 51| 
 52| Jede Konstante, jedes Dateiformat, jede Schnittstelle oder Option, die die Umsetzung braucht, als Fundstelle im Repo –
 53| **nichts aus dem Gedächtnis**. Eine Zeile je Quelle, Pfad in Backticks, dann `Zeilen a–b` oder `def Name` / `class Name`
 54| (ohne Angabe: ganze Datei, max. 400 Zeilen), dann Zweck. `kette.py quellen <kurztitel>` holt die Auszüge danach
 55| maschinell und wörtlich nach `quellen_<JJJJMMTT>_<kurztitel>.md`. Was nicht im Repo steht (externe Doku, Format
 56| eines Fremdprogramms), kommt unter „Offene Fragen" – Hawe legt die Quelle dann als Datei ins Repo.
 57| 
 58| - `pfad/datei.py` def funktion – wofür gebraucht
 59| - `pfad/datei.py` Zeilen 10–40 – wofür gebraucht
 60| 
 61| ## Anforderungen
 62| 
 63| ### A1: <Titel>
 64| - **Anforderung:** <prüfbar formuliert>
 65| - **Stelle:** <Datei, Funktion>
 66| - **Akzeptanz:** <beobachtbares Ergebnis>
 67| 
 68| ## Fehlerpfade
 69| 
 70| Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").
 71| 
 72| | Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
 73| |---|---|---|---|---|
 74| | A1 | Gegenstelle antwortet nicht oder schweigt (Netz, Server, Router) | | | T… |
 75| | A1 | Eingabe leer oder ungültig (Variable, Datei, Argument) | | | |
 76| | A1 | Ziel existiert schon (Datei, Eintrag) — wird etwas überschrieben? | | | |
 77| | A1 | Schalter kombiniert (z. B. Trockenlauf + anderer Modus) | | | |
 78| | A1 | Lauf ohne Testschalter / gegen echte Daten | | | |
 79| | A1 | Absturz mitten im Lauf | | | |
 80| 
 81| ## Testplan
 82| 
 83| Alle Tests werden als `tests/test_<kurztitel>.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.
 84| Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.
 85| 
 86| ### T1: <Titel>
 87| - **Prüft:** A1, Fehlerpfad „…"
 88| - **Aufbau:** <Testserver, temporäres Verzeichnis, Umgebungsvariablen>
 89| - **Erwartung:** <prüfbare Bedingung: Exit-Code, Datei existiert, Dauer ≥ x s …>
 90| - **Warum misst der Test das Richtige?** <ein Satz: woran würde der Test scheitern, wenn die Anforderung NICHT erfüllt ist?>
 91| - **Gegenprobe:** <welche Datei bzw. welche Codezeile muss im alten Zustand sein, damit dieser Test rot wird? „keine" = Test prüft Bestehendes, dann begründen>
 92| 
 93| <!-- Test für bestehendes Verhalten mit Vorgabe-Tests: „### T2: <Titel> (Bestand)“ – muss vorab grün sein. -->
 94| 
 95| ## Offene Fragen
 96| 
 97| - <… oder „Keine">
 98| 
 99| ## Abweichende Meinung
100| 
101| - <… oder „Keine">
```
