# Quellen Schritt 2 (4 ok, 0 schlecht)


### `role-split/kette/kette.py` def _schreibbereich (Zeilen 1629–1638) – wie der Schreibbereich aktuell geprüft wird

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
```

### `role-split/kette/kette.py` def _ist_vorgabe (Zeilen 1646–1649) – um sicherzustellen, dass die neuen Prüfungen nicht gegen die Vorgabe-Tests verstoßen

```python
1646| def _ist_vorgabe(pfad: str) -> bool:
1647|     """Spec, Anforderung, Quellen, Vorlagen der Kette – darf die Umsetzung nie aendern."""
1648|     name = Path(pfad).name
1649|     return name.endswith(".md") and name.startswith(VORGABE_PRAEFIXE)
```

### `role-split/kette/kette.py` def gegenprobe (Zeilen 432–489) – wie die Gegenprobe funktioniert (wichtig für die Test-Strategie)

```python
432| def gegenprobe(kurztitel: str, commit: str, timeout: int = 300) -> int:
433|     """Setzt jede seit <commit> geaenderte Code-Datei einzeln voruebergehend auf den alten Stand
434|     zurueck und laesst das Testskript laufen. Ein Test, der dabei nie rot wird, prueft keine der
435|     Aenderungen. Danach wird jeweils der aktuelle Stand wiederhergestellt (Pruefsumme)."""
436|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
437|     if not skript.is_file():
438|         print(f"Kein Testskript {skript.relative_to(ROOT)}"); return 2
439|     try:
440|         kette, _fremd = _aenderungen(commit, kurztitel)
441|     except subprocess.CalledProcessError as e:
442|         print(f"git-Fehler: {e.stderr.strip()}"); return 2
443|     # A5: dieselbe Auswahl wie paket – nur zur Kette gehoerige Code-Dateien, auch role-split/kette/
444|     dateien = sorted(d for d in kette
445|                      if d.endswith((".py", ".sh", ".command")) and not d.startswith("tests/"))
446|     if not dateien:
447|         print(f"Keine geaenderten Code-Dateien seit {commit}."); return 2
448| 
449|     vorher = tests_laufen(skript, timeout)
450|     if not vorher or any(v not in ("ok", "skipped") for v in vorher.values()):
451|         print(f"Abbruch: Das Testskript laeuft auf dem aktuellen Stand nicht gruen ({vorher}). Erst reparieren.")
452|         return 2
453|     print(f"Gegenprobe gegen {commit}: {len(vorher)} Tests, je Datei einzeln zurueckgesetzt\n")
454|     bestand = _bestand_ids(kurztitel)
455|     rot_durch: dict[str, list[str]] = {t: [] for t in vorher}
456|     laden_scheitert: list[str] = []
457|     for d in dateien:
458|         nachher = _zuruecksetzen_und_testen(skript, d, commit, timeout)
459|         if nachher is None:
460|             print(f"  {d}: Zeitueberschreitung"); continue
461|         if set(nachher) - set(vorher):            # Laden gescheitert
462|             print(f"  {d}: ohne die neue Fassung laedt das Testskript gar nicht -- alle Tests rot, aber ohne Einzelaussage")
463|             laden_scheitert.append(Path(d).name)
464|             continue
465|         rote = [t for t, v in nachher.items() if v in ("FAIL", "ERROR")]
466|         for t in rote:
467|             rot_durch[t].append(d)
468|         print(f"  {d}: {len(rote)} Test(s) rot")
469|     print()
470|     bestand_re = re.compile(rf"test_({'|'.join(bestand)})(_|$)", re.I)
471|     gruen = [t for t, ds in rot_durch.items() if not ds and not bestand_re.match(t)]
472|     for t in sorted(rot_durch):
473|         if rot_durch[t]:
474|             print(f"  rot   {t}  <- {', '.join(Path(x).name for x in rot_durch[t])}")
475|         elif bestand_re.match(t) and not rot_durch[t]:
476|             print(f"  BESTAND {t}  (prueft laut Spec bewusst Bestehendes)")
477|         elif laden_scheitert:
478|             print(f"  LADEN {t}  (rot nur, weil das Skript ohne {', '.join(laden_scheitert)} nicht laedt -- schwacher Beleg)")
479|         else:
480|             print(f"  GRUEN {t}  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)")
481|     print(f"\n{len(vorher) - len(gruen)} von {len(vorher)} Tests werden durch eine einzelne alte Datei rot"
482|           + (f", {len(gruen)} nur ueber das Laden" if laden_scheitert else "") + ". Aktueller Stand ist wiederhergestellt.")
483|     if gruen:
484|         print("GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) "
485|               "oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, "
486|               "dann wird die Gegenprobe je Test aussagekraeftig.")
487|     return 0 if not gruen else 1
488| 
489| # ---------------------------------------------------------------- tests-pruefen (K11a)
```

### `docs/projekt_management/_vorlage_spec.md` (Zeilen 1–100) – Struktur der Spec

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
 15| ## Schreibbereich
 16| 
 17| <!-- Dateien/Ordner, die die Umsetzung ändern darf, z. B. role-split/kette/ oder einzelne Pfade. Ordner mit „/" am Ende. -->
 18| Pflicht für `kette.py umsetzung-auto` (ohne diesen Abschnitt: Exit 2). Eine Zeile je Eintrag, Pfad in Backticks, relativ
 19| zum Repo. `tests/test_<kurztitel>.py` und der Handover sind immer erlaubt; Spec, Anforderung, Quellen und Vorlagen nie.
 20| 
 21| - `pfad/datei.py`
 22| - `pfad/ordner/`
 23| 
 24| ## Vorgabe-Tests
 25| 
 26| <!-- Optional (ab K11a). Nur wenn die Tests VOR der Umsetzung geschrieben werden (R48); sonst Abschnitt löschen. -->
 27| Mit diesem Abschnitt ist `tests/test_<kurztitel>.py` Vorgabe: Sie wird mit der Spec committet, vor dem Erstlauf von
 28| `kette.py tests-pruefen <kurztitel>` geprüft (je Test-ID eine Methode, Skript lädt, jeder Test rot vorab) und darf von der
 29| Umsetzung nicht geändert werden. Tests für bestehendes Verhalten tragen `(Bestand)` im Titel und müssen vorab grün sein (R49).
 30| 
 31| - `tests/test_<kurztitel>.py`
 32| 
 33| ## Außenwirkung und Sperre
 34| 
 35| - **Was kann die Aufgabe außerhalb des Repos auslösen?** <Mail, Netzwerk, echte Daten/DB, Schlüsselbund, launchd … oder „nichts">
 36| - **Technische Sperre für Tests:** <z. B. Variable, die echten Versand erst erlaubt; temporäres Datenverzeichnis. Eine Regel im Prompt reicht nicht.>
 37| 
 38| ## Einstiegspunkte
 39| 
 40| Welche geänderten Dateien werden **wie** gestartet (Pipeline, launchd, von Hand, als Modul importiert)?
 41| Für jeden Einstiegspunkt gibt es einen Test, der ihn so startet wie im Betrieb (ohne Außenwirkung, z. B.
 42| `runpy.run_path(…, run_name="kein_main")` für Imports, Ersatzskripte für Pipelines).
 43| Anlass 18.10.: Ein relativer Import ließ den Scout bei jedem Lauf abstürzen; alle Funktionstests waren grün.
 44| 
 45| | Datei | Wie gestartet | Test |
 46| |---|---|---|
 47| | `pfad/skript.py` | `python3 pfad/skript.py` aus `run_x.sh` | T… |
 48| 
 49| ## Quellen
 50| 
 51| Jede Konstante, jedes Dateiformat, jede Schnittstelle oder Option, die die Umsetzung braucht, als Fundstelle im Repo –
 52| **nichts aus dem Gedächtnis**. Eine Zeile je Quelle, Pfad in Backticks, dann `Zeilen a–b` oder `def Name` / `class Name`
 53| (ohne Angabe: ganze Datei, max. 400 Zeilen), dann Zweck. `kette.py quellen <kurztitel>` holt die Auszüge danach
 54| maschinell und wörtlich nach `quellen_<JJJJMMTT>_<kurztitel>.md`. Was nicht im Repo steht (externe Doku, Format
 55| eines Fremdprogramms), kommt unter „Offene Fragen" – Hawe legt die Quelle dann als Datei ins Repo.
 56| 
 57| - `pfad/datei.py` def funktion – wofür gebraucht
 58| - `pfad/datei.py` Zeilen 10–40 – wofür gebraucht
 59| 
 60| ## Anforderungen
 61| 
 62| ### A1: <Titel>
 63| - **Anforderung:** <prüfbar formuliert>
 64| - **Stelle:** <Datei, Funktion>
 65| - **Akzeptanz:** <beobachtbares Ergebnis>
 66| 
 67| ## Fehlerpfade
 68| 
 69| Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").
 70| 
 71| | Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
 72| |---|---|---|---|---|
 73| | A1 | Gegenstelle antwortet nicht oder schweigt (Netz, Server, Router) | | | T… |
 74| | A1 | Eingabe leer oder ungültig (Variable, Datei, Argument) | | | |
 75| | A1 | Ziel existiert schon (Datei, Eintrag) — wird etwas überschrieben? | | | |
 76| | A1 | Schalter kombiniert (z. B. Trockenlauf + anderer Modus) | | | |
 77| | A1 | Lauf ohne Testschalter / gegen echte Daten | | | |
 78| | A1 | Absturz mitten im Lauf | | | |
 79| 
 80| ## Testplan
 81| 
 82| Alle Tests werden als `tests/test_<kurztitel>.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.
 83| Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.
 84| 
 85| ### T1: <Titel>
 86| - **Prüft:** A1, Fehlerpfad „…"
 87| - **Aufbau:** <Testserver, temporäres Verzeichnis, Umgebungsvariablen>
 88| - **Erwartung:** <prüfbare Bedingung: Exit-Code, Datei existiert, Dauer ≥ x s …>
 89| - **Warum misst der Test das Richtige?** <ein Satz: woran würde der Test scheitern, wenn die Anforderung NICHT erfüllt ist?>
 90| - **Gegenprobe:** <welche Datei bzw. welche Codezeile muss im alten Zustand sein, damit dieser Test rot wird? „keine" = Test prüft Bestehendes, dann begründen>
 91| 
 92| <!-- Test für bestehendes Verhalten mit Vorgabe-Tests: „### T2: <Titel> (Bestand)“ – muss vorab grün sein. -->
 93| 
 94| ## Offene Fragen
 95| 
 96| - <… oder „Keine">
 97| 
 98| ## Abweichende Meinung
 99| 
100| - <… oder „Keine">
```
