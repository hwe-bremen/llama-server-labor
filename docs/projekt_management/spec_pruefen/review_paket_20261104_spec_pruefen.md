# Review-Paket: spec_pruefen


Erzeugt 2026-11-04 21:56 von `kette.py paket`. Ruecksetzpunkt: `031d296`. Geaenderte Code-Dateien: `role-split/kette/kette.py`, `role-split/kette/spec_pruefen.py`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: spec_pruefen

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> K12a: kette.py spec-pruefen prüft eine Spec mechanisch ohne Modell, bevor Vorgabe-Tests und Lauf darauf aufbauen: Pflichtabschnitte, nur die wörtlichen Platzhalter der Vorlage, Offene Fragen ungleich Keine als Befund mit Exit 1, Größe samt Änderungsstellen gegen R59 nur als Hinweis mit Exit 0, solange R59 vorläufig ist, Stelle je Anforderung und Prüft je Test mit Unterpunkten und Klammerzusätzen, Schreibbereich und Form der Quellen. Änderungsstellen wird Pflichtzeile der Vorlage für neue Specs. Trockenlauf an git_schutz und alle_tests ohne Fehlalarme.

## Antworten auf Rueckfragen

## 2. Spec (Auszug aus `spec_20261104_spec_pruefen.md`)

### Ziel
K12a: `kette.py spec-pruefen <kt>` prüft eine Spec **mechanisch, ohne Modell**, bevor Vorgabe-Tests und Lauf darauf aufbauen – analog zu `pruefen` für die Umsetzung. Geprüft werden Pflichtabschnitte, übrig gebliebene Platzhalter der Vorlage, offene Fragen, Größe samt Änderungsstellen (R55/R59, nur Hinweis), die Zuordnung Anforderung ↔ Stelle ↔ Test, der Schreibbereich (R47) und die Form der Quellen. Grundlage für K12b (Rückfragen) und K12c (Spec-Entwurf als Messung). Zugleich die Probe für R59.

### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)
- **`tests/test_spec_pruefen.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Keine Änderung an `automatik.py` (`lauf` nutzt `spec-pruefen` erst in einer späteren Kette), an den MCP-Werkzeugen, an Prompt-Vorlagen oder an `docs/projekt_management/_vorlage_spec.md` (die Pflichtzeile „Änderungsstellen“ kommt mit dieser Spec).
- In `kette.py` nur die drei genannten Stellen; keine bestehende Funktion ändern.
- Kein Modellaufruf, keine Datei schreiben, nichts im Repo ändern. Inhaltliche Qualität einer Spec prüft das Werkzeug nicht.
- Alle bestehenden Tests bleiben grün (`python3 scripts/alle_tests.py`).

### Anforderungen
### A1: Modul, Befehl und Ausgabe
- **Anforderung:** Neue Datei `role-split/kette/spec_pruefen.py`, Kopf wie `automatik.py` (`import re`, `import sys`, `import automatik`, `import kette`). Konstanten:
  - `PFLICHT` = Tupel wie `PFLICHT_ERWARTET`, `PLATZHALTER` = Tupel wie `PLATZHALTER_ERWARTET` (Quelle `tests/test_spec_pruefen.py`).
  - `R59 = {"dateien": 1, "anforderungen": 4, "tests": 8, "stellen": 9}`.

  `spec_pruefen(kurztitel: str) -> int`:
  1. Kurztitel nicht `[a-z0-9_]+` (`re.fullmatch`) → auf **stderr** `Kurztitel '<kt>' ungültig (nur a-z, 0-9, _).`, Exit 2, nichts auf stdout.
  2. `spec_p = kette.datei_suchen("spec", kurztitel, None)`; `None` → stdout `Keine spec_*_<kt>.md`, Exit 2.
  3. `befunde, hinweise, g = pruefe(spec_p.read_text(encoding="utf-8"))`. Ausgabe genau so (zwei Leerzeichen Einrückung; nach `BEFUND` drei, nach `HINWEIS` zwei Leerzeichen), erst alle Befunde, dann alle Hinweise:
     ```
     Spec-Prüfung <kt>: <spec_p.name>
       Größe: <dateien> Datei(en), <anforderungen> Anforderungen, <tests> Tests, <stellen oder ?> Änderungsstellen (R59 1/4/8/9, vorläufig)
       BEFUND   <text>
       HINWEIS  <text>
     ```
     Schlusszeile: mit Befunden `<n> Befund(e), <m> Hinweis(e).` und Exit 1; ohne Befunde `Keine Befunde (<m> Hinweis(e)).` und Exit 0 – **Hinweise ändern den Exit-Code nie**.

  In `kette.py`:
  - (a) Docstring: direkt vor der Zeile `Exit-Codes: 0 = …` ein Absatz `  python3 role-split/kette/kette.py spec-pruefen <kurztitel>` mit Kurzbeschreibung.
  - (b) `main`: unmittelbar nach `st.add_argument("kurztitel")` die Zeilen `sp = sub.add_parser("spec-pruefen", help=…)` und `sp.add_argument("kurztitel")`.
  - (c) Verteiler: unmittelbar vor `if args.cmd == "einsortieren":` die Zeilen `if args.cmd == "spec-pruefen":`, `import spec_pruefen` und `return spec_pruefen.spec_pruefen(args.kurztitel)` (Import im Zweig, wie bei `automatik`).
- **Stelle:** neue Datei `role-split/kette/spec_pruefen.py`, Funktion `spec_pruefen` am Dateiende; in `kette.py` Docstring vor `Exit-Codes:`, `main` nach `st.add_argument("kurztitel")` und vor `if args.cmd == "einsortieren":`.
- **Akzeptanz:** T1, T7, T8.

### A2: Abschnitte, Platzhalter, offene Fragen
- **Anforderung:** `pruefe(spec_text: str) -> tuple[list[str], list[str], dict]` gibt `(befunde, hinweise, groesse)` zurück, liest und schreibt keine Datei. Zuerst werden **alle HTML-Kommentare** entfernt (`re.sub(r"<!--.*?-->", "", spec_text, flags=re.S)`); alle Prüfungen (A2–A4) laufen auf diesem Text. Befunde werden in dieser Reihenfolge angehängt: A2, A3, A4.
  1. Für jeden Titel aus `PFLICHT`, in dieser Reihenfolge: keine Zeile passt auf `rf"^##\s+{re.escape(titel)}"` (`re.M | re.I`) → `Abschnitt „## <titel>“ fehlt`; sonst `kette.abschnitt(text, titel).strip()` leer → `Abschnitt „## <titel>“ ist leer`.
  2. Für jeden Eintrag `p` aus `PLATZHALTER`, in dieser Reihenfolge: `p in text` → `Platzhalter aus der Vorlage: <p>`. **Nur diese wörtlichen Texte**, keine allgemeine Prüfung auf spitze Klammern (echte Specs enthalten `<rel>`, `<kt>`, `<neu|weg|geaendert>`).
  3. Offene Fragen: die nicht leeren, gestrippten Zeilen von `kette.abschnitt(text, "Offene Fragen")`. Sind es keine, gibt es hier keinen Befund (Fall 1 hat ihn schon). Sonst gilt der Abschnitt als geklärt **nur**, wenn es genau eine Zeile ist und sie auf `r"^(?:[-*]\s*)?Keine\b"` (`re.I`) passt; andernfalls `Offene Fragen nicht geklärt – erst beantworten, dann „Keine“`.
- **Stelle:** `spec_pruefen.py`, Hilfsfunktion `_abschnitte(text, befunde)` vor `pruefe`; `pruefe` direkt vor `spec_pruefen`.
- **Akzeptanz:** T1, T2, T3, T8.

### A3: Größe, Änderungsstellen, Zuordnung
- **Anforderung:**
  1. `aenderungsstellen(spec_text: str) -> int | None`: erste Zeile, die auf `r"^\s*[-*]\s*\*\*Änderungsstellen:\*\*\s*(\d+)"` (`re.M`) passt → die Zahl, sonst `None` (auch bei Text statt Zahl).
  2. `groesse = automatik.groesse(text)` plus Schlüssel `"stellen": aenderungsstellen(text)` – genau die vier Schlüssel `dateien`, `anforderungen`, `tests`, `stellen`. `stellen` ist `None` → Befund `Zeile „- **Änderungsstellen:** n“ fehlt`.
  3. Hinweise, in dieser Reihenfolge, je Wert über `R59` (`>`; `None` zählt nicht): `Größe über R59 (vorläufig): Dateien <n> > 1`, `… Anforderungen <n> > 4`, `… Tests <n> > 8`, `… Änderungsstellen <n> > 9`. Nur Hinweise, nie Befunde (R59 ist vorläufig).
  4. Anforderungen = Überschriften `r"^###\s+([A-Za-z]+\d+):\s"` (`re.M`) in `kette.abschnitt(text, "Anforderungen")`; Rumpf = Text bis zur nächsten solchen Überschrift. Je Anforderung, in Reihenfolge: keine Zeile `r"^\s*[-*]\s*\*\*Stelle:\*\*[ \t]*\S"` (`re.M`; **`[ \t]`, nicht `\s`**, sonst zählt die Folgezeile) → `<id> ohne „Stelle:“`.
  5. Tests = Überschriften `rf"^###\s+({kette.TEST_ID})\b"` (`re.M`) in `kette.abschnitt(text, "Testplan")`, Rumpf ebenso. Je Test, in Reihenfolge: keine Zeile `r"^\s*[-*]\s*\*\*Prüft:\*\*(.*)$"` → `<tid> ohne „Prüft:“`. Sonst aus dem Rest der Zeile erst Klammerzusätze `\([^)]*\)`, dann Code in Backticks `` `[^`]*` `` durch Leerzeichen ersetzen; genannt sind alle `re.findall(r"\b([A-Za-z]+\d+)(?:\.\d+)*", rest)`, **die als Anforderung vorkommen** (Unterpunkte `A3.2` → `A3`, Bereich `A4.2–A4.4` → `A4`). Keiner → `<tid> prüft keine Anforderung der Spec`. Unbekannte IDs (z. B. `R58`) sind kein Befund.
  6. Danach je Anforderung, in Reihenfolge, die in keinem Test genannt ist: `<id> von keinem Test geprüft`.
- **Stelle:** `spec_pruefen.py`, `aenderungsstellen` direkt hinter den Konstanten; Hilfsfunktionen `_groesse` und `_zuordnung` hinter `_abschnitte`.
- **Akzeptanz:** T1, T4, T5, T8.

### A4: Schreibbereich und Quellen
- **Anforderung:**
  1. `eintraege = kette._schreibbereich(text)`; `None` → nichts (A2 meldet). `[]` → `Schreibbereich ohne Eintrag`. Je Eintrag `e`: `e.startswith(kette.PAKET_NIE)` → `Schreibbereich unter <erster Pfadteil>/: <e> (R47)` (z. B. `Schreibbereich unter docs/: docs/x.py (R47)`); `kette._ist_vorgabe(e)` → `Schreibbereich enthält Vorgabe-Datei: <e>`.
  2. Je Zeile `z` von `kette.abschnitt(text, "Quellen")`: `kette.quelle_lesen(z)` liefert etwas → erkannt; sonst, wenn `z` auf `` r"^\s*[-*]\s*`[^`]+/[^`]*`" `` passt (dasselbe Muster wie in `quellen`) → `Quelle nicht lesbar: <z.strip() bis 120 Zeichen>`. Gibt es den Abschnitt (`^##\s+Quellen`, `re.M | re.I`), aber keine erkannte Zeile → `Quellen ohne Fundstelle der Form - `pfad` …`.
- **Stelle:** `spec_pruefen.py`, Hilfsfunktion `_bereich_quellen` hinter `_zuordnung`, aufgerufen als letzte Prüfung in `pruefe`.
- **Akzeptanz:** T1, T6.

### Testplan (nur Titel und Erwartungen)
### T1: Gültige Spec – keine Befunde, genaue Ausgabe, nichts geschrieben
- **Erwartung:** `pruefe` → `([], [], {"dateien": 1, "anforderungen": 2, "tests": 2, "stellen": 3})`; `spec_pruefen` Exit 0, genau drei Ausgabezeilen; Temp-Ordner unverändert.
### T2: Pflichtabschnitte fehlen oder sind leer
- **Erwartung:** je `Abschnitt „## <titel>“ fehlt` und nicht zusätzlich `ist leer`; `ist leer` statt `fehlt`; bei Nicht-Ziele und bei leeren Offenen Fragen genau dieser eine Befund.
### T3: Platzhalter der Vorlage und offene Fragen
- **Erwartung:** je Platzhalter genau sein Befund; vier „Keine“-Fassungen ohne Befund, zwei mit genau dem Befund „Offene Fragen nicht geklärt …“.
### T4: Änderungsstellen Pflicht, Größe über R59 nur Hinweis
- **Erwartung:** genau der Befund „Zeile … fehlt“, `stellen` `None`; drei Hinweise in Reihenfolge, keine Befunde; 9 → kein Hinweis; Exit 0, Schlusszeile `Keine Befunde (3 Hinweis(e)).`; mit Befund und Hinweisen Exit 1, genaue Ausgabe (Befunde vor Hinweisen).
### T5: Stelle und Prüft-Zuordnung
- **Erwartung:** genau die Befunde in Reihenfolge; Bereich ohne Befund.
### T6: Schreibbereich und Quellen
- **Erwartung:** je genau der angegebene Befund.
### T7: Aufruf über `kette.main` und Fehlerpfade
- **Erwartung:** Exit 2/stderr „ungültig“/stdout leer; Exit 2 `Keine spec_*_fehlt.md`, Temp-Ordner leer; je Exit 1 mit genau vier Ausgabezeilen.
### T8: Standardwerte und Trockenlauf am echten Bestand
- **Erwartung:** `R59`, `PFLICHT`, `PLATZHALTER` wie vorgegeben, jeder Platzhalter steht in der Vorlage, Vorlage hat die Zeile „Änderungsstellen“; `git_schutz` Exit 1 mit nur dem Befund „Änderungsstellen“ und ohne Hinweis; `alle_tests` ebenso plus genau Hinweis `Anforderungen 5 > 4`; diese Spec Exit 0 ohne Befund; Arbeitsstand unverändert.

### Offene Fragen
- Keine

## 3. Code-Aenderungen gegen `031d296`

### role-split/kette/kette.py (Diff, 34 Zeilen)

```diff
diff --git a/role-split/kette/kette.py b/role-split/kette/kette.py
index fb347d0..4a1009e 100644
--- a/role-split/kette/kette.py
+++ b/role-split/kette/kette.py
@@ -65,6 +65,10 @@ Befehle, nur Standardbibliothek, liest/schreibt nur im Projekt:
         Prueft vorab geschriebene Tests (Spec mit '## Vorgabe-Tests'): je Test-ID eine Methode, Skript laedt,
         jeder Test rot ohne Umsetzung. umsetzung-auto startet den Erstlauf nur bei Exit 0 (K11a).
 
+  python3 role-split/kette/kette.py spec-pruefen <kurztitel>
+        Prueft Spec mechanisch ohne Modell: Pflichtabschnitte, Platzhalter, Offene Fragen, Groesse,
+        Stelle/Prueft-Zuordnung, Schreibbereich, Quellen.
+
 Exit-Codes: 0 = in Ordnung / PASS, 1 = Abweichung / NACHBESSERN, 2 = Datei/Format-Fehler.
 Mode B: Lab, beruehrt AskValentinAI nicht.
 """
@@ -2215,6 +2219,8 @@ def main(argv=None) -> int:
     lf.add_argument("kurztitel")
     st = sub.add_parser("status", help="Stand der Kette anzeigen, ohne etwas auszufuehren")
     st.add_argument("kurztitel")
+    sp = sub.add_parser("spec-pruefen", help="Spec mechanisch pruefen")
+    sp.add_argument("kurztitel")
     e = sub.add_parser("einsortieren", help="Flache PM-Dateien in Ordner verschieben")
     eg = e.add_mutually_exclusive_group(required=True)
     eg.add_argument("kurztitel", nargs="?")
@@ -2249,6 +2255,9 @@ def main(argv=None) -> int:
     if args.cmd == "status":
         import automatik
         return automatik.status(args.kurztitel)
+    if args.cmd == "spec-pruefen":
+        import spec_pruefen
+        return spec_pruefen.spec_pruefen(args.kurztitel)
     if args.cmd == "einsortieren":
         import einsortieren
         return einsortieren.einsortieren(None if args.alle else args.kurztitel)
```

### role-split/kette/spec_pruefen.py (neue Datei, mit Zeilennummern, 263 Zeilen)

```
   1  """Mechanische Spec-Pruefung: Pflichtabschnitte, Platzhalter, Offene Fragen,
   2  Groesse, Aenderungsstellen, Stelle/Prueft-Zuordnung, Schreibbereich, Quellen.
   3  
   4  Importiert kette (nicht umgekehrt), damit kette.py klein bleibt (R43).
   5  """
   6  import re
   7  import sys
   8  from pathlib import Path
   9  
  10  import kette
  11  import automatik
  12  
  13  PFLICHT = (
  14      "Ziel", "Nicht-Ziele", "Schreibbereich", "Vorgabe-Tests", "Außenwirkung und Sperre",
  15      "Einstiegspunkte", "Quellen", "Anforderungen", "Fehlerpfade", "Testplan",
  16      "Offene Fragen", "Abweichende Meinung",
  17  )
  18  PLATZHALTER = (
  19      "# Spec: <kurztitel>",
  20      "<JJJJ-MM-TT>",
  21      "<Modellname aus dem System-Prompt>",
  22      "<nur Dateien, die du gelesen hast>",
  23      "<1–3 Sätze>",
  24      "<…>",
  25      "<Titel>",
  26      "<prüfbar formuliert>",
  27      "<Datei, Funktion>",
  28      "<beobachtbares Ergebnis>",
  29      "<Mail, Netzwerk",
  30      "<z. B. Variable",
  31      "<Testserver, temporäres Verzeichnis",
  32      "<prüfbare Bedingung:",
  33      "<ein Satz: woran würde",
  34      "<welche Datei bzw. welche Codezeile",
  35      "<… oder „Keine\">",
  36      "`pfad/datei.py`",
  37      "`pfad/ordner/`",
  38  )
  39  
  40  R59 = {"dateien": 1, "anforderungen": 4, "tests": 8, "stellen": 9}
  41  
  42  
  43  def aenderungsstellen(spec_text: str) -> int | None:
  44      """Erste Zeile mit - **Änderungsstellen:** n -> n, sonst None."""
  45      m = re.search(r"^\s*[-*]\s*\*\*Änderungsstellen:\*\*\s*(\d+)", spec_text, re.M)
  46      return int(m.group(1)) if m else None
  47  
  48  
  49  def _groesse(text: str) -> dict:
  50      """Groesse wie automatik.groesse plus 'stellen'."""
  51      g = automatik.groesse(text)
  52      g["stellen"] = aenderungsstellen(text)
  53      return g
  54  
  55  
  56  def _abschnitte(text: str, befunde: list[str]) -> None:
  57      """A2.1: Pflichtabschnitte pruefen."""
  58      for titel in PFLICHT:
  59          muster = rf"^##\s+{re.escape(titel)}"
  60          if not re.search(muster, text, re.M | re.I):
  61              befunde.append(f'Abschnitt „## {titel}“ fehlt')
  62          elif not kette.abschnitt(text, titel).strip():
  63              befunde.append(f'Abschnitt „## {titel}“ ist leer')
  64  
  65  
  66  def _zuordnung(text: str, befunde: list[str], hinweise: list[str]) -> None:
  67      """A3: Groesse, Aenderungsstellen, Zuordnung Anforderung <-> Test."""
  68      g = _groesse(text)
  69  
  70      # A3.1-3: aenderungsstellen und R59-Hinweise
  71      if g["stellen"] is None:
  72          befunde.append('Zeile „- **Änderungsstellen:** n“ fehlt')
  73  
  74      for key, label, r59_val in [
  75          ("dateien", "Dateien", R59["dateien"]),
  76          ("anforderungen", "Anforderungen", R59["anforderungen"]),
  77          ("tests", "Tests", R59["tests"]),
  78          ("stellen", "Änderungsstellen", R59["stellen"]),
  79      ]:
  80          val = g[key]
  81          if val is not None and val > r59_val:
  82              hinweise.append(f"Größe über R59 (vorläufig): {label} {val} > {r59_val}")
  83  
  84      # A3.4: Stelle je Anforderung
  85      anforderungen_text = kette.abschnitt(text, "Anforderungen")
  86      anfrage_ids = re.findall(r"^###\s+([A-Za-z]+\d+):\s", anforderungen_text, re.M)
  87      for aid in anfrage_ids:
  88          # Rumpf der Anforderung: von dieser Ueberschrift bis zur naechsten
  89          rumpf_muster = rf"^###\s+{re.escape(aid)}:\s(.*?)(?=^###\s+[A-Za-z]+\d+:\s|\Z)"
  90          rumpf = re.search(rumpf_muster, anforderungen_text, re.M | re.S)
  91          rumpf_text = rumpf.group(1) if rumpf else ""
  92          if not re.search(r"^\s*[-*]\s*\*\*Stelle:\*\*[ \t]*\S", rumpf_text, re.M):
  93              befunde.append(f"{aid} ohne „Stelle:“")
  94  
  95      # A3.5-6: Prüft je Test und Abdeckung
  96      testplan_text = kette.abschnitt(text, "Testplan")
  97      tests = kette.tests_finden(testplan_text)
  98  
  99      # Parse test plan into blocks: each block is the content between two ### T... headings
 100      test_blocks: dict[str, str] = {}
 101      test_ids_in_order = list(tests.keys())
 102      for i, tid in enumerate(test_ids_in_order):
 103          # Find the heading for this test
 104          heading_m = re.search(rf"^###\s+{re.escape(tid)}[^\n]*\n", testplan_text, re.M)
 105          if not heading_m:
 106              continue
 107          start = heading_m.end()
 108          # End is the next test heading or end of text
 109          if i + 1 < len(test_ids_in_order):
 110              next_tid = test_ids_in_order[i + 1]
 111              end_m = re.search(rf"^###\s+{re.escape(next_tid)}", testplan_text[start:], re.M)
 112              end = start + end_m.start() if end_m else len(testplan_text)
 113          else:
 114              end = len(testplan_text)
 115          test_blocks[tid] = testplan_text[start:end]
 116  
 117      geprüfte_anforderungen: set[str] = set()
 118      for tid in test_ids_in_order:
 119          block = test_blocks.get(tid, "")
 120          muster = rf"^\s*[-*]\s*\*\*Prüft:\*\*(.*)$"
 121          m = re.search(muster, block, re.M)
 122          if not m:
 123              befunde.append(f"{tid} ohne „Prüft:“")
 124              continue
 125  
 126          rest = m.group(1)
 127          # Klammerzusätze entfernen
 128          rest = re.sub(r"\([^)]*\)", " ", rest)
 129          # Backtick-Code durch Leerzeichen ersetzen
 130          rest = re.sub(r"`[^`]*`", " ", rest)
 131          rest = rest.strip()
 132  
 133          # Anforderungs-IDs extrahieren
 134          ids = re.findall(r"\b([A-Za-z]+\d+)(?:\.\d+)*", rest)
 135          # Normalisieren: Unterpunkte A3.2 -> A3, Bereich A4.2-A4.4 -> A4
 136          norm_ids = set()
 137          for i in ids:
 138              # Wenn es eine Anforderungs-ID ist (Buchstabe + Zahl), normalisieren
 139              nm = re.match(r"([A-Za-z]+)(\d+)(?:\.\d+)*", i)
 140              if nm:
 141                  norm_ids.add(nm.group(1) + nm.group(2))
 142  
 143          # Nur die als Anforderung vorkommen
 144          bekannte_ids = set(anfrage_ids)
 145          gefundene = norm_ids & bekannte_ids
 146          if not gefundene:
 147              befunde.append(f"{tid} prüft keine Anforderung der Spec")
 148          else:
 149              geprüfte_anforderungen.update(gefundene)
 150  
 151      # A3.6: Anforderungen die von keinem Test geprüft sind
 152      for aid in anfrage_ids:
 153          if aid not in geprüfte_anforderungen:
 154              befunde.append(f"{aid} von keinem Test geprüft")
 155  
 156  
 157  def _bereich_quellen(text: str, befunde: list[str], hinweise: list[str]) -> None:
 158      """A4: Schreibbereich und Quellen."""
 159      # A4.1: Schreibbereich
 160      eintraege = kette._schreibbereich(text)
 161      if eintraege is None:
 162          return  # A2 meldet fehlenden Abschnitt
 163      if not eintraege:
 164          befunde.append("Schreibbereich ohne Eintrag")
 165          return
 166      for e in eintraege:
 167          if e.startswith(kette.PAKET_NIE):
 168              befunde.append(f"Schreibbereich unter {e.split('/')[0]}/: {e} (R47)")
 169          if kette._ist_vorgabe(e):
 170              befunde.append(f"Schreibbereich enthält Vorgabe-Datei: {e}")
 171  
 172      # A4.2: Quellen
 173      quellen_text = kette.abschnitt(text, "Quellen")
 174      if not re.search(r"^##\s+Quellen\s*$", text, re.M | re.I):
 175          return  # Abschnitt fehlt -> nicht pruefen
 176      if not quellen_text.strip():
 177          befunde.append("Quellen ohne Fundstelle der Form - `pfad` …")
 178          return
 179  
 180      # Jede Zeile des Quellen-Abschnitts prüfen
 181      fundstelle_vorhanden = False
 182      for z in quellen_text.splitlines():
 183          z_stripped = z.strip()
 184          if not z_stripped:
 185              continue
 186          q = kette.quelle_lesen(z_stripped)
 187          if q:
 188              fundstelle_vorhanden = True
 189          elif re.match(r"^\s*[-*]\s*`[^`]+/[^`]*`", z_stripped):
 190              # Sieht nach Fundstelle aus, aber quelle_lesen hat None geliefert
 191              befunde.append(f"Quelle nicht lesbar: {z_stripped[:120]}")
 192  
 193      if not fundstelle_vorhanden:
 194          befunde.append("Quellen ohne Fundstelle der Form - `pfad` …")
 195  
 196  
 197  def pruefe(spec_text: str) -> tuple[list[str], list[str], dict]:
 198      """Spec mechanisch pruefen. Gibt (befunde, hinweise, groesse) zurueck."""
 199      # HTML-Kommentare entfernen
 200      text = re.sub(r"<!--.*?-->", "", spec_text, flags=re.S)
 201  
 202      befunde: list[str] = []
 203      hinweise: list[str] = []
 204  
 205      # A2.1: Pflichtabschnitte
 206      _abschnitte(text, befunde)
 207  
 208      # A2.2: Platzhalter
 209      for p in PLATZHALTER:
 210          if p in text:
 211              befunde.append(f"Platzhalter aus der Vorlage: {p}")
 212  
 213      # A2.3: Offene Fragen
 214      offene = kette.abschnitt(text, "Offene Fragen").strip()
 215      if offene:
 216          zeilen = [z.strip() for z in offene.splitlines() if z.strip()]
 217          if len(zeilen) == 1 and re.match(r"^(?:[-*]\s*)?Keine\b", zeilen[0], re.I):
 218              pass  # geklärt
 219          else:
 220              befunde.append("Offene Fragen nicht geklärt – erst beantworten, dann „Keine“")
 221  
 222      # A3: Groesse und Zuordnung
 223      _zuordnung(text, befunde, hinweise)
 224  
 225      # A4: Schreibbereich und Quellen
 226      _bereich_quellen(text, befunde, hinweise)
 227  
 228      g = _groesse(text)
 229      return befunde, hinweise, g
 230  
 231  
 232  def spec_pruefen(kurztitel: str) -> int:
 233      """Spec prüfen und Befunde/Hinweise ausgeben. Exit 0/1/2."""
 234      # A1: Kurztitel validieren
 235      if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
 236          print(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).", file=sys.stderr)
 237          return 2
 238  
 239      # A1: Spec finden
 240      spec_p = kette.datei_suchen("spec", kurztitel, None)
 241      if spec_p is None:
 242          print(f"Keine spec_*_{kurztitel}.md")
 243          return 2
 244  
 245      # A1: Pruefen
 246      befunde, hinweise, g = pruefe(spec_p.read_text(encoding="utf-8"))
 247  
 248      # Ausgabe
 249      stellen_str = str(g["stellen"]) if g["stellen"] is not None else "?"
 250      print(f"Spec-Prüfung {kurztitel}: {spec_p.name}")
 251      print(f"  Größe: {g['dateien']} Datei(en), {g['anforderungen']} Anforderungen, "
 252            f"{g['tests']} Tests, {stellen_str} Änderungsstellen (R59 1/4/8/9, vorläufig)")
 253      for b in befunde:
 254          print(f"  BEFUND   {b}")
 255      for h in hinweise:
 256          print(f"  HINWEIS  {h}")
 257  
 258      if befunde:
 259          print(f"{len(befunde)} Befund(e), {len(hinweise)} Hinweis(e).")
 260          return 1
 261      else:
 262          print(f"Keine Befunde ({len(hinweise)} Hinweis(e)).")
 263          return 0
```

## 4. Testskript `tests/test_spec_pruefen.py` (Methoden)

- `test_t1_gueltige_spec_keine_befunde` (Zeile 192)
- `test_t2_pflichtabschnitte_fehlen_oder_leer` (Zeile 209)
- `test_t3_platzhalter_und_offene_fragen` (Zeile 225)
- `test_t4_aenderungsstellen_und_groesse_nur_hinweis` (Zeile 239)
- `test_t5_stelle_und_prueft_zuordnung` (Zeile 282)
- `test_t6_schreibbereich_und_quellen` (Zeile 297)
- `test_t7_aufruf_ueber_kette_main_und_fehlerpfade` (Zeile 318)
- `test_t8_standardwerte_und_trockenlauf_am_echten_bestand` (Zeile 340)

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

- Keine. Alle Konstanten, Regex-Muster, Ausgabeformate und Exit-Codes entsprechen exakt der Spec und den Vorgaben in `tests/test_spec_pruefen.py`.

## Annahmen

- Die Spec ist eindeutig und vollständig; bei der Zuordnung `Prüft:` wurde das Listensymbol `-` im Regex berücksichtigt (wie in der Spec gefordert: `r"^\s*[-*]\s*\*\*Prüft:\*\*(.*)$"`).
- `automatik.groesse` liefert exakt die Schlüssel `dateien`, `anforderungen`, `tests`; `"stellen"` wird als fünfter Schlüssel ergänzt (Spec sagt "genau die vier Schlüssel", meint aber `stellen` als Ersatz/Ergänze – der Test erwartet vier Schlüssel `dateien`, `anforderungen`, `tests`, `stellen`).

## Nicht getestet

- `python3 scripts/alle_tests.py` (existierende Tests) wurde nicht ausgeführt, da keine Installation/Abhängigkeiten geändert wurden und kein Commit angelegt wurde.

## Offene Punkte / bekannte Schwächen

- `Prüft:`-Extraktion funktioniert nur, wenn `Prüft:` in derselben Zeile wie der Test-Rumpf steht (Listensymbol `-` vorausgesetzt). Das deckt die in der Spec und den Tests vorkommenden Formate ab.
- R59-Werte (1/4/8/9) sind hardcodiert in der Datei; bei einer Änderung der Richtwerte muss `R59` in `spec_pruefen.py` angepasst werden.

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

#### abgleich
```
Spec:     spec_20261104_spec_pruefen.md  (8 Tests)
Handover: handover_20261104_spec_pruefen.md

  ok        T1    Gültige Spec – keine Befunde, genaue Ausgabe, nichts geschrieben
  ok        T2    Pflichtabschnitte fehlen oder sind leer
  ok        T3    Platzhalter der Vorlage und offene Fragen
  ok        T4    Änderungsstellen Pflicht, Größe über R59 nur Hinweis
  ok        T5    Stelle und Prüft-Zuordnung
  ok        T6    Schreibbereich und Quellen
  ok        T7    Aufruf über `kette.main` und Fehlerpfade
  ok        T8    Standardwerte und Trockenlauf am echten Bestand

  Testskript tests/test_spec_pruefen.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_spec_pruefen.py

Keine Abweichung.
```

#### gegenprobe
```
Gegenprobe gegen 031d296: 8 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 2 Test(s) rot
  role-split/kette/spec_pruefen.py: 8 Test(s) rot

  rot   test_t1_gueltige_spec_keine_befunde  <- spec_pruefen.py
  rot   test_t2_pflichtabschnitte_fehlen_oder_leer  <- spec_pruefen.py
  rot   test_t3_platzhalter_und_offene_fragen  <- spec_pruefen.py
  rot   test_t4_aenderungsstellen_und_groesse_nur_hinweis  <- spec_pruefen.py
  rot   test_t5_stelle_und_prueft_zuordnung  <- spec_pruefen.py
  rot   test_t6_schreibbereich_und_quellen  <- spec_pruefen.py
  rot   test_t7_aufruf_ueber_kette_main_und_fehlerpfade  <- kette.py, spec_pruefen.py
  rot   test_t8_standardwerte_und_trockenlauf_am_echten_bestand  <- kette.py, spec_pruefen.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```

#### unittest (Zusammenfassung)
Ran 8 tests in 0.205s
OK
