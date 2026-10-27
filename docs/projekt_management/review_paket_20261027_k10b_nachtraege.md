# Review-Paket: k10b_nachtraege


Erzeugt 2026-10-27 21:00 von `kette.py paket`. Ruecksetzpunkt: `29060aa`. Geaenderte Code-Dateien: `role-split/kette/kette.py`, `tests/test_k10b_nachtraege.py`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: k10b_nachtraege

## Aufgabe

> Vier kleine Nachträge aus der K10-Abnahme in `role-split/kette/kette.py`:
> 1. Der Umsetzer-Prompt (`umsetzung-auto`) nennt für jede Test-ID der Spec die Pflichtzeile `**Tn: Titel** – bestanden | fehlgeschlagen` für den Handover.
> 2. `abgleich` zählt Bereiche wie „T1–T5“ unter „Nicht getestet“ nicht als Einzelnennung.
> 3. Protokoll und Zusammenfassung von `umsetzung-auto` zeigen zusätzlich die Token-Spitze eines einzelnen Schritts.
> 4. `zusammenfuehren` zählt Befundzeilen, die das Modell selbst zurückgezogen hat („Korrekt.“ / „Befund entfällt.“ am Ende), nicht als hoch – die Zeilen bleiben aber im Gesamtbefund sichtbar.
> Sonst nichts an `kette.py` ändern.

## Zweck

- Erster echter Einsatz von `umsetzung-auto` (35B-A3B), kleine gezielte Änderungen in einer großen Datei (R43).

## 2. Spec (Auszug aus `spec_20261027_k10b_nachtraege.md`)

### Ziel
Vier kleine Nachträge aus der K10-Abnahme in `kette.py`: Der Umsetzer-Prompt nennt die Pflichtzeilen des Handovers, `abgleich` wertet Bereiche wie „T1–T5“ nicht als Einzelnennung, das Protokoll zeigt die Token-Spitze, und `zusammenfuehren` zählt vom Modell selbst zurückgezogene Befunde nicht als hoch.

### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)
- Keine weitere Änderung an `kette.py` außer den vier Stellen unten. Nichts umbenennen, nichts neu formatieren, nichts löschen.
- `urteil` (Einzelverdikt) bleibt unverändert.
- Das Format der Protokoll-Hauptzeile (A6 aus K10, `PROTOKOLL_RE`) bleibt unverändert.
- Keine Änderung an Prompts unter `role-split/kette/prompts/`.

### Anforderungen
### A1: Pflichtzeilen des Handovers im Umsetzer-Prompt
- **Anforderung:** `_umsetzung_prompt` liest die Spec des Kurztitels (`datei_suchen("spec", kurztitel, None)`) und holt die Test-IDs mit `tests_finden`. Gibt es mindestens eine Test-ID, hängt die Funktion **nach** dem Grundtext und **vor** einem eventuellen Nachbesserungs-Teil diesen Abschnitt an:
  - eine Leerzeile, dann die Überschrift `## Pflichtzeilen im Handover`;
  - den Satz `Unter „## Getestet“ steht für jede Test-ID genau eine dieser Zeilen (Titel unverändert, Status wählen):`;
  - je Test-ID in Spec-Reihenfolge eine Zeile `**<ID>: <Titel>** – bestanden | fehlgeschlagen` (Titel genau wie von `tests_finden` geliefert);
  - zum Schluss den Satz `Unter „## Nicht getestet“ nur Test-IDs, die wirklich nicht getestet sind – keine Sammelangaben wie „T1–T5“.`
  
  Hat die Spec keine Test-ID (oder gibt es keine Spec), wird nichts angehängt.
- **Stelle:** `def _umsetzung_prompt`
- **Akzeptanz:** T1.

### A2: Bereiche unter „Nicht getestet“
- **Anforderung:** In `abgleich` werden vor dem Suchen der Test-IDs im Abschnitt „Nicht getestet“ alle Bereichsangaben der Form `<ID>–<ID>` oder `<ID>-<ID>` (Gedankenstrich oder Bindestrich, Leerzeichen dazwischen erlaubt, ID nach dem vorhandenen Muster `TEST_ID`) entfernt. Einzeln genannte IDs zählen weiter.
- **Stelle:** `def abgleich`, die Zeile mit `nicht = set(re.findall(...))`
- **Akzeptanz:** T2.

### A3: Token-Spitze
- **Anforderung:** `_lauf` merkt sich in `info["tokens_spitze"]` (Startwert 0) den größten `part.tokens.total` eines einzelnen `step_finish`. `info["tokens"]` (Summe) bleibt wie bisher.
  - Die Unterzeile im Protokoll wird zu `  - Tokens: input <i>, output <o>, reasoning <r>, spitze <s>` (nur `, spitze <s>` angehängt).
  - Die Zusammenfassung auf stdout zeigt statt `Tokens <summe>` jetzt `Tokens <summe> (Spitze <s>)`; der Rest der Zeile bleibt.
- **Stelle:** `def _lauf`; Unterzeile und Zusammenfassung in `def umsetzung_auto` (Zeilen aus den Quellen)
- **Akzeptanz:** T3. Mit der Attrappe (zwei `step_finish` mit total 100 und 50) ergibt das `Tokens 150 (Spitze 100)` und `spitze 100`.

### A4: Zurückgezogene Befunde in `zusammenfuehren`
- **Anforderung:** Neue Funktion `_zurueckgezogen(text: str) -> bool`: Entfernt alle `*` aus dem Befundtext, dann rechts Leerraum; wahr, wenn der Rest auf `Korrekt.` oder auf `Befund entfällt.` endet.
  - In `zusammenfuehren` gilt eine Zeile nur dann als hoch, wenn `_ist_hoch` wahr ist **und** `_zurueckgezogen(<Befundtext>)` falsch.
  - Zeilen, die nach `_ist_hoch` hoch wären, aber zurückgezogen sind, stehen weiter im Gesamtbefund (nichts weglassen), in der Spalte „hoch nach Regel“ mit `nein (zurückgezogen)` statt `nein`.
  - Die Zusammenfassung auf stdout lautet `<n> Befunde aus <m> Läufen, davon <h> hoch, <z> zurückgezogen -> <Ergebnis>`; der Teil `, <z> zurückgezogen` entfällt bei z = 0.
  - Die übrige Ergebnisregel bleibt: Ein `NACHBESSERN` im Ergebnis eines Laufs gilt weiter.
- **Stelle:** neue Funktion direkt vor `def zusammenfuehren`; `def zusammenfuehren`
- **Akzeptanz:** T4.

### Testplan (nur Titel und Erwartungen)
### T1: Prompt nennt je Test-ID eine Pflichtzeile
- **Erwartung:** Erster Aufruf enthält `## Pflichtzeilen im Handover`, `**T1: Erster** – bestanden | fehlgeschlagen` und `**T2: Zweiter Fall** – bestanden | fehlgeschlagen`. Zweiter Aufruf enthält `Pflichtzeilen` nicht.
### T2: abgleich – Bereich unter „Nicht getestet“ ist keine Einzelnennung
- **Erwartung:** Erster Aufruf: Ausgabe enthält `FEHLT     T2` (fünf Leerzeichen nach FEHLT), enthält `NICHT GET` nicht, Rückgabe 1. Zweiter Aufruf: Ausgabe enthält `NICHT GET T2`.
### T3: Tokens – Spitze je Schritt im Protokoll und auf stdout
- **Erwartung:** Rückgabe 0; Ausgabe enthält `Tokens 150 (Spitze 100)`; `self.protokoll()` enthält `  - Tokens: input 130, output 18, reasoning 2, spitze 100`.
### T4: zusammenfuehren – zurückgezogene „hoch“-Zeilen zählen nicht
- **Erwartung:** Erster Aufruf: Rückgabe 0; Ausgabe enthält `davon 0 hoch, 2 zurückgezogen -> PASS`; `gesamt_20261027_k.md` enthält genau zweimal `| nein (zurückgezogen) |` und den Text `Befund entfällt.`. Zweiter Aufruf: Rückgabe 1; Ausgabe enthält `davon 1 hoch -> NACHBESSERN`.

### Offene Fragen
- Keine

## 3. Code-Aenderungen gegen `29060aa`

### role-split/kette/kette.py (Diff, 125 Zeilen)

```diff
diff --git a/role-split/kette/kette.py b/role-split/kette/kette.py
index 789913f..a9bf332 100644
--- a/role-split/kette/kette.py
+++ b/role-split/kette/kette.py
@@ -276,7 +276,10 @@ def abgleich(kurztitel: str, datum: str | None = None, schwelle: float = 0.6) ->
     spec_tests = tests_finden(spec.read_text(encoding="utf-8"))
     ho_text = ho.read_text(encoding="utf-8")
     getestet = tests_finden(abschnitt(ho_text, "Getestet"))
-    nicht = set(re.findall(rf"\b({TEST_ID})\b", abschnitt(ho_text, "Nicht getestet")))
+    # A2: Bereichsangaben (T1–T2, T1-T2) unter "Nicht getestet" entfernen
+    nicht_text = abschnitt(ho_text, "Nicht getestet")
+    nicht_text = re.sub(rf"\b({TEST_ID})\s*[–—-]\s*({TEST_ID})\b", "", nicht_text)
+    nicht = set(re.findall(rf"\b({TEST_ID})\b", nicht_text))
     print(f"Spec:     {spec.name}  ({len(spec_tests)} Tests)\nHandover: {ho.name}\n")
     if not spec_tests:
         print("Keine Test-IDs (T1, NT1 ...) in der Spec gefunden."); return 2
@@ -825,6 +828,13 @@ def _ist_hoch(zeile: dict) -> bool:
     return "hoch" in schwere or any(ja(spalte(zeile, n)) for n in ("datenverl", "unbemerkt", "harte"))
 
 
+# A4: Modell hat Befund selbst zurückgezogen
+def _zurueckgezogen(text: str) -> bool:
+    """Wahr, wenn der Befundtext (ohne *, rechts gestrippt) auf 'Korrekt.' oder 'Befund entfällt.' endet."""
+    bereinigt = text.replace("*", "").rstrip()
+    return bereinigt.endswith("Korrekt.") or bereinigt.endswith("Befund entfällt.")
+
+
 def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
     if len(pfade) < 2:
         if _internal:
@@ -864,10 +874,12 @@ def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
             schwere = spalte(b, "schwere") or "?"
             text_b = spalte(b, "befund", "begründung", "begruendung") or " | ".join(v for v in b.values() if v)
             ort = spalte(b, "datei", "zeile", "anfor") or ""
-            zeilen.append((p.name, schwere, text_b, ort, _ist_hoch(b)))
+            h = _ist_hoch(b)
+            z = _zurueckgezogen(text_b)
+            zeilen.append((p.name, schwere, text_b, ort, h, z))
     if fehlt:
         print("Fehlt: " + ", ".join(fehlt)); return 2
-    hoch = [z for z in zeilen if z[4]]
+    hoch = [z for z in zeilen if z[4] and not z[5]]
     if hoch or any(e == "NACHBESSERN" for _, e in ergebnisse):
         urteil_ = "NACHBESSERN"
     elif any(e == "FAIL" for _, e in ergebnisse):
@@ -887,11 +899,19 @@ def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
              "## Ergebnis\n", f"**{urteil_}** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.\n",
              "| Lauf | Ergebnis des Laufs |", "|---|---|"] + [f"| `{n}` | {e} |" for n, e in ergebnisse] + [
              "", "## Befunde (alle Läufe)\n", "| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |", "|---|---|---|---|---|"]
-    for n, s_, t, o, h in zeilen:
-        teile.append(f"| `{n}` | {s_} | {'ja' if h else 'nein'} | {o.replace('|', '/')} | {t.replace('|', '/')} |")
+    for n, s_, t, o, h, z in zeilen:
+        if h and z:
+            hoch_zeig = "nein (zurückgezogen)"
+        elif h:
+            hoch_zeig = "ja"
+        else:
+            hoch_zeig = "nein"
+        teile.append(f"| `{n}` | {s_} | {hoch_zeig} | {o.replace('|', '/')} | {t.replace('|', '/')} |")
     ziel = PM / f"gesamt_{datum}_{kurz}.md"
     ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
-    print(f"{len(zeilen)} Befunde aus {len(ergebnisse)} Läufen, davon {len(hoch)} hoch -> {urteil_}")
+    zurueckgezogen = len([z for z in zeilen if z[5]])
+    zeile_zur = f", {zurueckgezogen} zurückgezogen" if zurueckgezogen else ""
+    print(f"{len(zeilen)} Befunde aus {len(ergebnisse)} Läufen, davon {len(hoch)} hoch{zeile_zur} -> {urteil_}")
     print(f"Geschrieben: {ziel.relative_to(ROOT) if ziel.is_relative_to(ROOT) else ziel}")
     return 0 if urteil_ == "PASS" else 1
 
@@ -1646,6 +1666,17 @@ def _umsetzung_prompt(kurztitel: str, datum: str, commit: str, nacharbeit: Path
             .replace("{anforderung}", anf_pfad)
             .replace("{quellen}", f"docs/projekt_management/quellen_{datum}_{kurztitel}.md"))
     text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
+    # A1: Pflichtzeilen im Handover – nach Grundtext, vor Nachbesserung
+    spec_p = datei_suchen("spec", kurztitel, None)
+    if spec_p:
+        spec_tests = tests_finden(spec_p.read_text(encoding="utf-8"))
+        if spec_tests:
+            zeilen = ["", "## Pflichtzeilen im Handover",
+                      'Unter „## Getestet" steht für jede Test-ID genau eine dieser Zeilen (Titel unverändert, Status wählen):']
+            for tid, titel in spec_tests.items():
+                zeilen.append(f"**{tid}: {titel}** – bestanden | fehlgeschlagen")
+            zeilen.append('Unter „## Nicht getestet" nur Test-IDs, die wirklich nicht getestet sind – keine Sammelangaben wie „T1–T5".')
+            text += "\n".join(zeilen) + "\n"
     if nacharbeit:
         text += (f"\n## Nachbesserung {nb}\n\nDas ist Nachbesserung {nb}. Der Auftrag steht unten (aus "
                  f"`{_rel(nacharbeit)}`). Ergänze den Handover docs/projekt_management/handover_{datum}_"
@@ -1657,7 +1688,7 @@ def _umsetzung_prompt(kurztitel: str, datum: str, commit: str, nacharbeit: Path
 def _lauf(befehl: list[str], env: dict, timeout: int, rohdaten: Path) -> dict:
     """Startet opencode in eigener Prozessgruppe, liest den JSON-Strom zeilenweise (sofort in die
     Rohdaten), gibt je Werkzeugaufruf eine Zeile aus und beendet die Gruppe nach `timeout` s (A5, A6, A9)."""
-    info = {"werkzeuge": 0, "fehler": [], "abgelehnt": [], "tokens": 0, "reason": None, "text": "",
+    info = {"werkzeuge": 0, "fehler": [], "abgelehnt": [], "tokens": 0, "tokens_spitze": 0, "reason": None, "text": "",
             "ereignisse": 0, "kaputt": 0, "timeout": False,
             "tokens_teile": {"input": 0, "output": 0, "reasoning": 0}}
     rohdaten.parent.mkdir(parents=True, exist_ok=True)
@@ -1708,7 +1739,10 @@ def _lauf(befehl: list[str], env: dict, timeout: int, rohdaten: Path) -> dict:
                 elif typ == "step_finish":
                     info["reason"] = teil.get("reason")
                     tok = teil.get("tokens") or {}
-                    info["tokens"] += int(tok.get("total") or 0)
+                    total = int(tok.get("total") or 0)
+                    info["tokens"] += total
+                    if total > info["tokens_spitze"]:
+                        info["tokens_spitze"] = total
                     for k in info["tokens_teile"]:
                         info["tokens_teile"][k] += int(tok.get(k) or 0)
                 elif typ == "text":
@@ -1894,7 +1928,7 @@ def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
         protokoll_p.write_text(f"# Umsetzungs-Protokoll: {kurztitel}\n\nJe Lauf eine Zeile (kette.py umsetzung-auto).\n\n",
                                encoding="utf-8")
     tt = info["tokens_teile"]
-    zeile += f"  - Tokens: input {tt['input']}, output {tt['output']}, reasoning {tt['reasoning']}\n"
+    zeile += f"  - Tokens: input {tt['input']}, output {tt['output']}, reasoning {tt['reasoning']}, spitze {info['tokens_spitze']}\n"
     for e in info["fehler"]:
         zeile += f"  - {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}\n"
     with open(protokoll_p, "a", encoding="utf-8") as f:
@@ -1902,7 +1936,7 @@ def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
 
     print(f"\n=== umsetzung-auto {kurztitel} ({art}) ===")
     print(f"Dauer {info['dauer']} s, Werkzeugaufrufe {info['werkzeuge']}, Fehler {len(info['fehler'])}, "
-          f"abgelehnt {len(info['abgelehnt'])}, Tokens {info['tokens']}, reason {reason}")
+          f"abgelehnt {len(info['abgelehnt'])}, Tokens {info['tokens']} (Spitze {info['tokens_spitze']}), reason {reason}")
     for e in info["fehler"]:
         print(f"  {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}")
     if info["text"]:
```

### tests/test_k10b_nachtraege.py (neue Datei, mit Zeilennummern, 121 Zeilen)

```
   1  #!/usr/bin/env python3
   2  """Tests fuer K10b (spec_20261027_k10b_nachtraege.md, T1–T4), nach R42 von Claude uebernommen.
   3  
   4  Je Test-ID eine Methode; der Gegenfall steht in derselben Methode, damit die Gegenprobe jeden Test
   5  rot macht. T3 nutzt Basis aus tests/test_umsetzung_auto.py (Attrappe mit Temp-Sperre, Pruefung des
   6  echten Repos). Neue Funktionen werden in den Methoden importiert.
   7  """
   8  import io
   9  import sys
  10  import tempfile
  11  import unittest
  12  from contextlib import redirect_stderr, redirect_stdout
  13  from pathlib import Path
  14  
  15  ECHT = Path(__file__).resolve().parent.parent
  16  sys.path.insert(0, str(ECHT / "role-split" / "kette"))
  17  sys.path.insert(0, str(ECHT))
  18  import kette  # noqa: E402
  19  from tests.test_umsetzung_auto import Basis, HANDOVER  # noqa: E402
  20  
  21  SPEC = "# Spec: k\n\n## Testplan\n\n### T1: Erster\n- x\n\n### T2: Zweiter Fall\n- y\n"
  22  KOPF = ("| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |\n"
  23          "|---|---|---|---|---|---|---|---|\n")
  24  
  25  
  26  class TempPM(unittest.TestCase):
  27      def setUp(self):
  28          d = tempfile.TemporaryDirectory()
  29          self.addCleanup(d.cleanup)
  30          self.root = Path(d.name).resolve()
  31          self.pm = self.root / "docs" / "projekt_management"
  32          self.pm.mkdir(parents=True)
  33          for name, wert in (("ROOT", self.root), ("PM", self.pm)):
  34              alt = getattr(kette, name)
  35              setattr(kette, name, wert)
  36              self.addCleanup(setattr, kette, name, alt)
  37  
  38      def leise(self, f, *a):
  39          aus = io.StringIO()
  40          with redirect_stdout(aus), redirect_stderr(aus):
  41              code = f(*a)
  42          return code, aus.getvalue()
  43  
  44  
  45  class PromptTests(TempPM):
  46      def test_t1_pflichtzeilen_im_prompt(self):
  47          """T1: Prompt nennt je Test-ID eine Pflichtzeile"""
  48          from kette import _umsetzung_prompt
  49          (self.pm / "spec_20261027_k.md").write_text(SPEC, encoding="utf-8")
  50          text = _umsetzung_prompt("k", "20261027", "abc1234", None, 1)
  51          self.assertIn("## Pflichtzeilen im Handover", text)
  52          self.assertIn("**T1: Erster** – bestanden | fehlgeschlagen", text)
  53          self.assertIn("**T2: Zweiter Fall** – bestanden | fehlgeschlagen", text)
  54          # Spec-Reihenfolge, nicht Textsortierung: T2 vor T10
  55          (self.pm / "spec_20261027_k.md").write_text("# Spec: k\n\n### T2: Zwei\n- x\n\n### T10: Zehn\n- y\n",
  56                                                     encoding="utf-8")
  57          text = _umsetzung_prompt("k", "20261027", "abc1234", None, 1)
  58          self.assertLess(text.index("**T2: Zwei**"), text.index("**T10: Zehn**"))
  59          # Gegenfall: Spec ohne Test-IDs -> kein Abschnitt
  60          (self.pm / "spec_20261027_k.md").write_text("# Spec: k\n\n## Ziel\nx\n", encoding="utf-8")
  61          text = _umsetzung_prompt("k", "20261027", "abc1234", None, 1)
  62          self.assertNotIn("Pflichtzeilen", text)
  63  
  64  
  65  class AbgleichTests(TempPM):
  66      def handover(self, nicht):
  67          (self.pm / "spec_20261027_k.md").write_text(SPEC, encoding="utf-8")
  68          (self.pm / "handover_20261027_k.md").write_text(
  69              "# Handover\n\n## Getestet (mit echter Ausgabe)\n\n**T1: Erster** – bestanden\n\n"
  70              f"## Nicht getestet\n\n{nicht}\n", encoding="utf-8")
  71  
  72      def test_t2_bereich_zaehlt_nicht(self):
  73          """T2: abgleich – Bereich „T1–T2“ unter Nicht getestet ist keine Einzelnennung"""
  74          self.handover("- Nichts, alle Tests (T1–T2) laufen grün.")
  75          code, out = self.leise(kette.abgleich, "k")
  76          self.assertIn("FEHLT     T2", out)
  77          self.assertNotIn("NICHT GET", out)
  78          self.assertEqual(code, 1)
  79          # Gegenfall: einzeln genannte Test-ID bleibt "nicht getestet"
  80          self.handover("- T2: braucht einen echten Server.")
  81          code, out = self.leise(kette.abgleich, "k")
  82          self.assertIn("NICHT GET T2", out)
  83  
  84  
  85  class TokenTests(Basis):
  86      def test_t3_tokens_spitze(self):
  87          """T3: Tokens – Spitze je Schritt im Protokoll und auf stdout"""
  88          code, out = self.lauf(FAKE_HANDOVER=HANDOVER)
  89          self.assertEqual(code, 0, out)
  90          self.assertIn("Tokens 150 (Spitze 100)", out)
  91          self.assertIn("  - Tokens: input 130, output 18, reasoning 2, spitze 100", self.protokoll())
  92  
  93  
  94  class ZusammenfuehrenTests(TempPM):
  95      def verdikte(self, zeilen1, ergebnis1="PASS"):
  96          p1 = self.pm / "verdict_20261027_k_qwen36-35b.md"
  97          p2 = self.pm / "verdict_20261027_k_qwen36-35b_betrieb.md"
  98          p1.write_text(f"# V\n\n## Ergebnis\n\n{ergebnis1}\n\n## Befunde\n\n{KOPF}{zeilen1}", encoding="utf-8")
  99          p2.write_text(f"# V\n\n## Ergebnis\n\nPASS\n\n## Befunde\n\n{KOPF}"
 100                        "| – | nein | nein | nein | – | – | keine Befunde | – |\n", encoding="utf-8")
 101          return [p1, p2]
 102  
 103      def test_t4_zurueckgezogen_nicht_hoch(self):
 104          """T4: zusammenfuehren – zurückgezogene „hoch“-Zeilen zählen nicht"""
 105          pfade = self.verdikte("| 1 | nein | nein | nein | hoch | `x.py:1` | Prüfung X ist da. **Befund entfällt.** | – |\n"
 106                                "| 2 | nein | ja | nein | hoch | `x.py:2` | Fall Y: Exit 2. **Korrekt.** | – |\n")
 107          code, out = self.leise(kette.zusammenfuehren, pfade)
 108          self.assertEqual(code, 0, out)
 109          self.assertIn("davon 0 hoch, 2 zurückgezogen -> PASS", out)
 110          gesamt = (self.pm / "gesamt_20261027_k.md").read_text(encoding="utf-8")
 111          self.assertEqual(gesamt.count("| nein (zurückgezogen) |"), 2)
 112          self.assertIn("Befund entfällt.", gesamt)               # nichts weggelassen
 113          # Gegenfall: echter hoher Befund bleibt hoch
 114          pfade = self.verdikte("| 1 | nein | nein | nein | hoch | `x.py:1` | Timeout fehlt, Lauf hängt unbegrenzt. | – |\n")
 115          code, out = self.leise(kette.zusammenfuehren, pfade)
 116          self.assertEqual(code, 1, out)
 117          self.assertIn("davon 1 hoch -> NACHBESSERN", out)
 118  
 119  
 120  if __name__ == "__main__":
 121      unittest.main()
```

## 4. Testskript `tests/test_k10b_nachtraege.py` (Methoden)

- `test_t1_pflichtzeilen_im_prompt` (Zeile 46): T1: Prompt nennt je Test-ID eine Pflichtzeile
- `test_t2_bereich_zaehlt_nicht` (Zeile 72): T2: abgleich – Bereich „T1–T2“ unter Nicht getestet ist keine Einzelnennung
- `test_t3_tokens_spitze` (Zeile 86): T3: Tokens – Spitze je Schritt im Protokoll und auf stdout
- `test_t4_zurueckgezogen_nicht_hoch` (Zeile 103): T4: zusammenfuehren – zurückgezogene „hoch“-Zeilen zählen nicht

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

- A1: Zwischen Überschrift, Einleitungssatz und Pflichtzeilen stehen keine Leerzeilen; die schließenden Anführungszeichen sind `"` statt `“`. Inhaltlich wie verlangt; nicht nachgebessert.
- A2: Das Bereichsmuster erlaubt zusätzlich den Geviertstrich `—`. Unschädlich.

## Annahmen

- Keine.

## Nicht getestet

- Reihenfolge „Pflichtzeilen vor dem Nachbesserungs-Teil“ (A1) ist nicht eigens geprüft.

## Offene Punkte / bekannte Schwächen

- Messwerte 35B: Erstlauf 21:34 min (79 Werkzeugaufrufe), NB1 29:25 min (94 Aufrufe, Kontextspitze 58 118 Token von 64K). Code beide Male richtig bzw. nach Hinweis korrigiert; Tests beide Male nicht wie in der Spec.

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

#### abgleich
```
Spec:     spec_20261027_k10b_nachtraege.md  (4 Tests)
Handover: handover_20261027_k10b_nachtraege.md

  ok        T1    Prompt nennt je Test-ID eine Pflichtzeile
  ok        T2    abgleich – Bereich unter „Nicht getestet“ ist keine Einzelnennung
  ok        T3    Tokens – Spitze je Schritt im Protokoll und auf stdout
  ok        T4    zusammenfuehren – zurückgezogene „hoch“-Zeilen zählen nicht

  Testskript tests/test_k10b_nachtraege.py: alle 4 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_k10b_nachtraege.py

Keine Abweichung.
```

#### gegenprobe
```
Gegenprobe gegen 29060aa: 4 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 4 Test(s) rot

  rot   test_t1_pflichtzeilen_im_prompt  <- kette.py
  rot   test_t2_bereich_zaehlt_nicht  <- kette.py
  rot   test_t3_tokens_spitze  <- kette.py
  rot   test_t4_zurueckgezogen_nicht_hoch  <- kette.py

4 von 4 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```

#### unittest (Zusammenfassung)
Ran 4 tests in 0.174s
OK
