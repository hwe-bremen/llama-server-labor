# Review-Paket: lauf_status


Erzeugt 2026-10-28 12:54 von `kette.py paket`. Ruecksetzpunkt: `c9469ed`. Geaenderte Code-Dateien: `role-split/kette/automatik.py`, `role-split/kette/kette.py`, `tests/test_lauf_status.py`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: lauf_status

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Ein Befehl kette.py lauf <kt> führt die Kette ab committeter Spec mit Vorgabe-Tests bis zum Halt an meiner Entscheidung: Größenprüfung mit Umsetzer-Vorschlag, umsetzung-auto, review-auto, dann Status mit nächstem Schritt. kette.py status <kt> zeigt den Stand aus den vorhandenen Dateien. Ablauf im neuen Modul automatik.py. Der Umsetzer schreibt nur Code.

## Antworten auf Rueckfragen

## 2. Spec (Auszug aus `spec_20261028_lauf_status.md`)

### Ziel
Ein Befehl `kette.py lauf <kurztitel>` führt die Kette ab fertiger, committeter Spec mit Vorgabe-Tests bis zum Halt an Hawes Entscheidung: Größenprüfung mit Umsetzer-Vorschlag → `umsetzung-auto` → `review-auto` → Status mit nächstem Schritt. `kette.py status <kurztitel>` zeigt den Stand der Kette aus den vorhandenen Dateien, ohne etwas auszuführen. Der Ablauf liegt im neuen Modul `automatik.py`, damit `kette.py` klein bleibt (R43).

### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)
- **`tests/test_lauf_status.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Keine Nacharbeit aus `lauf` heraus (der Nacharbeitsauftrag kommt von Claude; `umsetzung-auto --nacharbeit` bleibt der Weg).
- Keine eigene Zustandsdatei: `status` leitet alles aus Spec, Protokoll `umsetzung_*`, Gesamtbefund `gesamt_*` und `git status` ab.
- Keine Rückfragen im Lauf (kein `input()`), keine weiteren Schalter.
- In `kette.py` nichts außer C5 ändern; `umsetzung_auto`, `review_auto` usw. bleiben unverändert.
- Kein Lauf aller Testdateien (R50) im Werkzeug – `status` nennt ihn als Schritt vor dem Commit.

### Anforderungen
### C1: Größenprüfung
- **Anforderung:** In `automatik.py` Konstanten `GROESSE_DATEIEN = 2`, `GROESSE_ANFORDERUNGEN = 6`, `GROESSE_TESTS = 8` (vorläufig) und `UMSETZER_VORSCHLAG = "35B"`. Funktion `groesse(spec_text) -> dict` mit `dateien` (Einträge aus `kette._schreibbereich`, keiner → 0), `anforderungen` (Überschriften `### <Buchstabe(n)><Zahl>:` **nur im Abschnitt `## Anforderungen`**) und `tests` (Anzahl `kette.tests_finden`). Zu groß ist eine Spec, wenn **ein** Wert seine Schwelle **überschreitet** (an der Schwelle nicht).
- **Stelle:** `automatik.py`
- **Akzeptanz:** T3.

### C2: `lauf(kurztitel) -> int`
- **Anforderung:** in dieser Reihenfolge:
  1. Kurztitel nicht `[a-z0-9_]+` → Exit 2. Keine Spec oder kein Commit „Spec <kt>“ (`kette.spec_commit`) → Meldung, die `Spec <kt>` nennt, Exit 2. Spec ohne `## Vorgabe-Tests` → Meldung mit `Vorgabe-Tests` und Hinweis auf R48, Exit 2. In diesen Fällen wird nichts gestartet.
  2. Zeile `Größe: <d> Datei(en), <a> Anforderungen, <t> Tests (Schwellen 2/6/8, vorläufig)`. Zu groß → Zeile `HALT – zu groß für den lokalen Umsetzer: Spec teilen oder Claude übernimmt (R43).`, Exit 3, nichts gestartet.
  3. Zeile `Umsetzer: 35B`; dann `kette.umsetzung_auto(kurztitel)` (genau ein Argument). Nur bei Exit 0 danach `kette.review_auto(kurztitel)`.
  4. Leerzeile, Ausgabe von `status(kurztitel)` (C3/C4), dann Zeile `HALT – Entscheidung Hawe.`
  5. Rückgabe: 0, wenn Umsetzung und Review 0 waren; 2, wenn der zuletzt gelaufene Schritt 2 lieferte; sonst 1.
- **Stelle:** `automatik.py`
- **Akzeptanz:** T1, T2, T3, T4, T5, T6.

### C3: Stand aus Dateien
- **Anforderung:** Funktion `stand(kurztitel) -> dict` mit:
  - `spec` (Pfad oder `None`, `kette.datei_suchen("spec", kt, None)`), `spec_commit` (`kette.spec_commit` oder `None`), `vorgabe` (bool),
  - `laeufe`: Liste `(art, exit)` aus `PM/umsetzung_<spec-datum>_<kt>.md`, **nur Zeilen, die mit `- **` beginnen**, je Treffer von `art: (erst|nb\d+), Exit: (\d+)` (Unterzeilen mit fremdem Text zählen nicht),
  - `review`: `PASS` / `NACHBESSERN` / `UNVOLLSTÄNDIG` aus der ersten Zeile `**<WERT>**` in `kette.datei_suchen("gesamt", kt, None)`, sonst `None`,
  - `offen`: Pfade aus `git -C <ROOT> status --porcelain`.
- **Stelle:** `automatik.py`
- **Akzeptanz:** T7.

### C4: `status(kurztitel) -> int` und nächster Schritt
- **Anforderung:** Kurztitel ungültig → Exit 2. Ausgabe (Einrückung zwei Leerzeichen, Werte ab Spalte 17 wie gezeigt):
  ```
  Status <kt>
    Spec:          <dateiname oder fehlt>
    Spec-Commit:   <hash oder fehlt>
    Vorgabe-Tests: <ja|nein>
    Umsetzung:     <"erst Exit 1, nb1 Exit 0" oder keiner>
    Review:        <PASS|NACHBESSERN|UNVOLLSTÄNDIG oder keins>
    Offen:         <n> Datei(en)
  Nächster Schritt: <text>
  ```
  Nächster Schritt, erste zutreffende Regel:
  1. keine Spec → Text mit „Spec fehlt“;
  2. kein Spec-Commit → `Spec committen: git commit -m "Spec <kt>"`;
  3. keine Läufe → `kette.py lauf <kt>`;
  4. letzter Lauf Exit ≠ 0 → Text, der „Nacharbeit“ und „Übernahme durch Claude“ nennt;
  5. kein Review → `kette.py review-auto <kt>`;
  6. Review nicht `PASS` → Text mit dem Review-Wert und „gegenprüfen“;
  7. offene Dateien → Text mit „alle Testdateien laufen lassen (R50), dann committen“;
  8. sonst → `Abgeschlossen – nichts offen.`
  Rückgabe 0, wenn eine Spec existiert, sonst 2.
- **Stelle:** `automatik.py`
- **Akzeptanz:** T7.

### C5: Befehle in `kette.py`
- **Anforderung:** Subparser `lauf` und `status`, je mit `kurztitel`. In `main`: bei `lauf`/`status` `import automatik` **in der Verzweigung** (nicht am Dateianfang, sonst Kreisimport) und Rückgabe von `automatik.lauf(kt)` bzw. `automatik.status(kt)`.
- **Stelle:** `def main`
- **Akzeptanz:** T8.

### Testplan (nur Titel und Erwartungen)
### T1: lauf – ohne Commit „Spec <kt>“ kein Start
- **Erwartung:** Exit 2, Ausgabe enthält `Spec k`, keine Attrappe aufgerufen; ungültiger Kurztitel Exit 2.
### T2: lauf – ohne Abschnitt Vorgabe-Tests kein Start
- **Erwartung:** Exit 2, Ausgabe enthält `Vorgabe-Tests`, keine Attrappe aufgerufen.
### T3: lauf – Größenprüfung hält bei Überschreitung, an der Schwelle läuft es
- **Erwartung:** dreimal Exit 3 (erste Ausgabe enthält `9 Tests` und `teilen`, keine Attrappe aufgerufen); an der Schwelle Exit 0 und `2 Datei(en), 6 Anforderungen, 8 Tests`.
### T4: lauf – Umsetzung und Review grün, Halt an Hawes Entscheidung
- **Erwartung:** Exit 0; Aufrufe genau `umsetzung_auto("k")` (ohne Nacharbeit), dann `review_auto("k")`; Ausgabe enthält `Umsetzer: 35B`, `Nächster Schritt:` und `HALT – Entscheidung Hawe.`
### T5: lauf – Umsetzung nicht in Ordnung, kein Review
- **Erwartung:** Exit 1, nur der Umsetzungsaufruf, HALT-Zeile; mit Exit 2 der Umsetzung Exit 2.
### T6: lauf – Review nicht PASS ergibt Exit 1
- **Erwartung:** Exit 1, Aufrufe Umsetzung dann Review.
### T7: status – Stand und nächster Schritt aus den Dateien
- **Erwartung:** Exit 2 und `Spec:          fehlt`; dann Exit 0, `Vorgabe-Tests: ja`, `Nächster Schritt: kette.py lauf k`; `Umsetzung:     erst Exit 1`, kein `nb9`, Schritt nennt „Nacharbeit“; `Nächster Schritt: kette.py review-auto k`; `Review:        NACHBESSERN` und „gegenprüfen“; Schritt nennt „committen“; zuletzt „Abgeschlossen“. Keine Attrappe aufgerufen.
### T8: main – lauf und status über kette.py
- **Erwartung:** Rückgaben 3 und 0, Attrappen mit `k` aufgerufen.

### Offene Fragen
- Keine

## 3. Code-Aenderungen gegen `c9469ed`

### role-split/kette/automatik.py (neue Datei, mit Zeilennummern, 190 Zeilen)

```
   1  """Automatik: groesse, stand, status, lauf – K11b.
   2  
   3  Importiert kette (nicht umgekehrt), damit kette.py klein bleibt (R43).
   4  """
   5  import re
   6  import subprocess
   7  import sys
   8  from pathlib import Path
   9  
  10  import kette
  11  
  12  GROESSE_DATEIEN = 2
  13  GROESSE_ANFORDERUNGEN = 6
  14  GROESSE_TESTS = 8
  15  UMSETZER_VORSCHLAG = "35B"
  16  
  17  
  18  def groesse(spec_text: str) -> dict:
  19      """Groessenpruefung der Spec.
  20  
  21      dateien: Eintraege aus kette._schreibbereich (keiner -> 0).
  22      anforderungen: Anzahl der Ueberschriften ### <Buchstabe(n)><Zahl>:
  23                     **nur** im Abschnitt ``## Anforderungen``.
  24      tests: Anzahl kette.tests_finden.
  25      """
  26      dateien = len(kette._schreibbereich(spec_text)) if kette._schreibbereich(spec_text) is not None else 0
  27      anforderungen = len(
  28          re.findall(
  29              r"^###\s+[A-Za-z]+\d+:\s",
  30              kette.abschnitt(spec_text, "Anforderungen"),
  31              re.M,
  32          )
  33      )
  34      tests = len(kette.tests_finden(spec_text))
  35      return {"dateien": dateien, "anforderungen": anforderungen, "tests": tests}
  36  
  37  
  38  def stand(kurztitel: str) -> dict:
  39      """Stand der Kette aus den vorhandenen Dateien."""
  40      spec_p = kette.datei_suchen("spec", kurztitel, None)
  41      spec_commit = kette.spec_commit(kurztitel)
  42      spec_text = spec_p.read_text(encoding="utf-8") if spec_p else ""
  43      vorgabe = kette._vorgabe_tests(spec_text)
  44  
  45      # Laeufe aus Protokoll
  46      protokoll_p = kette.datei_suchen("umsetzung", kurztitel, None)
  47      laeufe = []
  48      if protokoll_p:
  49          text = protokoll_p.read_text(encoding="utf-8")
  50          muster = re.compile(r"art:\s*(erst|nb\d+),\s*Exit:\s*(\d+)")
  51          for z in text.splitlines():
  52              if not z.lstrip().startswith("- **"):
  53                  continue
  54              m = muster.search(z)
  55              if m:
  56                  laeufe.append((m.group(1), int(m.group(2))))
  57  
  58      # Review aus Gesamtbefund
  59      review = None
  60      gesamt_p = kette.datei_suchen("gesamt", kurztitel, None)
  61      if gesamt_p:
  62          text = gesamt_p.read_text(encoding="utf-8")
  63          for z in text.splitlines():
  64              if "**" in z:
  65                  for wert in ("PASS", "NACHBESSERN", "UNVOLLSTÄNDIG"):
  66                      if f"**{wert}**" in z:
  67                          review = wert
  68                          break
  69                  if review:
  70                      break
  71  
  72      # Offene Dateien
  73      offen_list = []
  74      r = subprocess.run(
  75          ["git", "-C", str(kette.ROOT), "status", "--porcelain"],
  76          capture_output=True, text=True,
  77      )
  78      if r.returncode == 0:
  79          offen_list = [line.strip() for line in r.stdout.splitlines() if line.strip()]
  80  
  81      return {
  82          "spec": str(spec_p) if spec_p else None,
  83          "spec_commit": spec_commit,
  84          "vorgabe": vorgabe,
  85          "laeufe": laeufe,
  86          "review": review,
  87          "offen": offen_list,
  88      }
  89  
  90  
  91  def status(kurztitel: str) -> int:
  92      """Status ausgeben und naechsten Schritt bestimmen."""
  93      if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
  94          print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _).", file=sys.stderr)
  95          return 2
  96  
  97      s = stand(kurztitel)
  98  
  99      # Naechster Schritt, erste zutreffende Regel
 100      if not s["spec"]:
 101          next_text = "Spec fehlt."
 102      elif not s["spec_commit"]:
 103          next_text = f'Spec committen: git commit -m "Spec {kurztitel}"'
 104      elif not s["laeufe"]:
 105          next_text = f"kette.py lauf {kurztitel}"
 106      elif s["laeufe"][-1][1] != 0:
 107          next_text = (
 108              "Nacharbeit notwendig – Umsetzer aufgerufen und nicht in Ordnung, "
 109              "dann Übernahme durch Claude."
 110          )
 111      elif not s["review"]:
 112          next_text = f"kette.py review-auto {kurztitel}"
 113      elif s["review"] != "PASS":
 114          next_text = f"Review {s['review']} – gegenprüfen."
 115      elif s["offen"]:
 116          next_text = "Alle Testdateien laufen lassen (R50), dann committen."
 117      else:
 118          next_text = "Abgeschlossen – nichts offen."
 119  
 120      # Ausgabe
 121      print(f"Status {kurztitel}")
 122      print(f"  Spec:          {Path(s['spec']).name if s['spec'] else 'fehlt'}")
 123      print(f"  Spec-Commit:   {s['spec_commit'] or 'fehlt'}")
 124      print(f"  Vorgabe-Tests: {'ja' if s['vorgabe'] else 'nein'}")
 125      if s["laeufe"]:
 126          lauf_text = ", ".join(f"{a} Exit {e}" for a, e in s["laeufe"])
 127      else:
 128          lauf_text = "keiner"
 129      print(f"  Umsetzung:     {lauf_text}")
 130      print(f"  Review:        {s['review'] or 'keins'}")
 131      print(f"  Offen:         {len(s['offen'])} Datei(en)")
 132      print(f"Nächster Schritt: {next_text}")
 133  
 134      return 0 if s["spec"] else 2
 135  
 136  
 137  def lauf(kurztitel: str) -> int:
 138      """Kette: Groesse -> umsetzung-auto -> review-auto -> status -> HALT."""
 139      if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
 140          print(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).", file=sys.stderr)
 141          return 2
 142  
 143      commit = kette.spec_commit(kurztitel)
 144      if not commit:
 145          print(f'Kein Commit "Spec {kurztitel}" gefunden – erst die Spec committen.')
 146          return 2
 147  
 148      spec_p = kette.datei_suchen("spec", kurztitel, None)
 149      if not spec_p:
 150          print(f"Keine Spec spec_<datum>_{kurztitel}.md gefunden.")
 151          return 2
 152  
 153      spec_text = spec_p.read_text(encoding="utf-8")
 154      if not kette._vorgabe_tests(spec_text):
 155          print(
 156              "Spec hat keinen Abschnitt '## Vorgabe-Tests'. "
 157              "Vorgabe-Tests vorab schreiben (R48), sonst kein Start."
 158          )
 159          return 2
 160  
 161      g = groesse(spec_text)
 162      print(
 163          f"Größe: {g['dateien']} Datei(en), {g['anforderungen']} Anforderungen, "
 164          f"{g['tests']} Tests (Schwellen 2/6/8, vorläufig)"
 165      )
 166  
 167      if (
 168          g["dateien"] > GROESSE_DATEIEN
 169          or g["anforderungen"] > GROESSE_ANFORDERUNGEN
 170          or g["tests"] > GROESSE_TESTS
 171      ):
 172          print(
 173              "HALT – zu groß für den lokalen Umsetzer: Spec teilen oder "
 174              "Claude übernimmt (R43)."
 175          )
 176          return 3
 177  
 178      print(f"Umsetzer: {UMSETZER_VORSCHLAG}")
 179      exit_umsetzung = kette.umsetzung_auto(kurztitel)
 180      exit_code = exit_umsetzung
 181  
 182      if exit_umsetzung == 0:
 183          exit_review = kette.review_auto(kurztitel)
 184          exit_code = exit_review
 185  
 186      print()
 187      status(kurztitel)
 188      print("HALT – Entscheidung Hawe.")
 189  
 190      return exit_code
```

### role-split/kette/kette.py (Diff, 28 Zeilen)

```diff
diff --git a/role-split/kette/kette.py b/role-split/kette/kette.py
index 19326a9..5c00e34 100644
--- a/role-split/kette/kette.py
+++ b/role-split/kette/kette.py
@@ -2076,6 +2076,10 @@ def main(argv=None) -> int:
     ua.add_argument("kurztitel"); ua.add_argument("--nacharbeit", help="Datei mit dem Nachbesserungs-Auftrag")
     tp = sub.add_parser("tests-pruefen", help="Vorgabe-Tests pruefen: Abdeckung, laedt, rot vorab")
     tp.add_argument("kurztitel"); tp.add_argument("--timeout", type=int, default=300)
+    lf = sub.add_parser("lauf", help="Kette: Groesse -> umsetzung-auto -> review-auto -> status")
+    lf.add_argument("kurztitel")
+    st = sub.add_parser("status", help="Stand der Kette anzeigen, ohne etwas auszufuehren")
+    st.add_argument("kurztitel")
     args = ap.parse_args(argv)
     if args.cmd == "zusammenfuehren":
         return zusammenfuehren([Path(v) if Path(v).is_absolute() or Path(v).exists() else PM / Path(v).name
@@ -2100,6 +2104,12 @@ def main(argv=None) -> int:
         return prompt(args.schritt, args.kurztitel, args.datum, args.commit, args.lauf)
     if args.cmd == "abgleich":
         return abgleich(args.kurztitel, args.datum)
+    if args.cmd == "lauf":
+        import automatik
+        return automatik.lauf(args.kurztitel)
+    if args.cmd == "status":
+        import automatik
+        return automatik.status(args.kurztitel)
     pfad = Path(args.verdikt)
     if not pfad.is_absolute() and not pfad.exists():
         pfad = PM / pfad.name
```

### tests/test_lauf_status.py (Diff, 24 Zeilen)
> **nicht in der Uebergabe genannt** – moeglicherweise ausserhalb des Auftrags

```diff
diff --git a/tests/test_lauf_status.py b/tests/test_lauf_status.py
index 570643e..0b4ebd7 100644
--- a/tests/test_lauf_status.py
+++ b/tests/test_lauf_status.py
@@ -172,6 +172,7 @@ class Status(Temp):
         self.assertEqual(code, 0, out)
         self.assertIn("Vorgabe-Tests: ja", out)
         self.assertIn("Nächster Schritt: kette.py lauf k", out)
+        self.assertIn(f"Spec:          spec_{DATUM}_k.md\n", out)      # Dateiname, kein Pfad (C4; Nacharbeit 1)
         self.protokoll(("erst", 1))
         code, out = self.rufen(automatik.status, "k")
         self.assertIn("Umsetzung:     erst Exit 1", out)
@@ -184,6 +185,11 @@ class Status(Temp):
         code, out = self.rufen(automatik.status, "k")
         self.assertIn("Review:        NACHBESSERN", out)
         self.assertIn("gegenprüfen", out)
+        (self.pm / f"gesamt_{DATUM}_k.md").write_text("# Gesamtbefund: k\n\n> Hinweis\n\n**UNVOLLSTÄNDIG** – Regel\n",
+                                                encoding="utf-8")
+        code, out = self.rufen(automatik.status, "k")
+        self.assertIn("Review:        UNVOLLSTÄNDIG", out)          # Wert wie in gesamt_* (C3; Nacharbeit 1)
+        self.assertIn("gegenprüfen", out.split("Nächster Schritt:")[1])
         (self.pm / f"gesamt_{DATUM}_k.md").write_text("# Gesamtbefund: k\n\n**PASS** – Regel\n", encoding="utf-8")
         code, out = self.rufen(automatik.status, "k")
         self.assertIn("committen", out.split("Nächster Schritt:")[1])
```

## 4. Testskript `tests/test_lauf_status.py` (Methoden)

- `test_t1_lauf_ohne_spec_commit` (Zeile 81): T1: lauf – ohne Commit „Spec <kt>“ kein Start
- `test_t2_lauf_ohne_vorgabe_tests` (Zeile 92): T2: lauf – ohne Abschnitt Vorgabe-Tests kein Start
- `test_t3_lauf_zu_gross` (Zeile 101): T3: lauf – Größenprüfung hält bei Überschreitung, an der Schwelle läuft es
- `test_t4_lauf_ok_bis_halt` (Zeile 122): T4: lauf – Umsetzung und Review grün, Halt an Hawes Entscheidung
- `test_t5_lauf_umsetzung_rot` (Zeile 133): T5: lauf – Umsetzung nicht in Ordnung, kein Review
- `test_t6_lauf_review_nicht_pass` (Zeile 146): T6: lauf – Review nicht PASS ergibt Exit 1
- `test_t7_status_naechster_schritt` (Zeile 164): T7: status – Stand und nächster Schritt aus den Dateien
- `test_t8_main_lauf_und_status` (Zeile 205): T8: main – lauf und status über kette.py

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

- Keine. Alle Anforderungen der Spec umgesetzt.

## Annahmen

- Keine.

## Nicht getestet

- Nichts.

## Offene Punkte / bekannte Schwächen

- Keine.

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

#### abgleich
```
Spec:     spec_20261028_lauf_status.md  (8 Tests)
Handover: handover_20261028_lauf_status.md

  ok        T1    lauf – ohne Commit „Spec <kt>“ kein Start
  ok        T2    lauf – ohne Abschnitt Vorgabe-Tests kein Start
  ok        T3    lauf – Größenprüfung hält bei Überschreitung, an der Schwelle läuft es
  ok        T4    lauf – Umsetzung und Review grün, Halt an Hawes Entscheidung
  ok        T5    lauf – Umsetzung nicht in Ordnung, kein Review
  ok        T6    lauf – Review nicht PASS ergibt Exit 1
  ok        T7    status – Stand und nächster Schritt aus den Dateien
  ok        T8    main – lauf und status über kette.py

  Testskript tests/test_lauf_status.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_lauf_status.py

Keine Abweichung.
```

#### gegenprobe
```
Gegenprobe gegen c9469ed: 8 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/automatik.py: 8 Test(s) rot
  role-split/kette/kette.py: 1 Test(s) rot

  rot   test_t1_lauf_ohne_spec_commit  <- automatik.py
  rot   test_t2_lauf_ohne_vorgabe_tests  <- automatik.py
  rot   test_t3_lauf_zu_gross  <- automatik.py
  rot   test_t4_lauf_ok_bis_halt  <- automatik.py
  rot   test_t5_lauf_umsetzung_rot  <- automatik.py
  rot   test_t6_lauf_review_nicht_pass  <- automatik.py
  rot   test_t7_status_naechster_schritt  <- automatik.py
  rot   test_t8_main_lauf_und_status  <- automatik.py, kette.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```

#### unittest (Zusammenfassung)
Ran 8 tests in 0.501s
OK
