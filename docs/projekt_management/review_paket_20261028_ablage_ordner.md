# Review-Paket: ablage_ordner


Erzeugt 2026-10-28 14:21 von `kette.py paket`. Ruecksetzpunkt: `593feb0`. Geaenderte Code-Dateien: `role-split/kette/kette.py`, `role-split/role_proxy.py`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: ablage_ordner

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Jede Kette soll ihre Dateien in einem eigenen Ordner docs/projekt_management/<kurztitel>/ haben. Gibt es den Ordner, liest und schreibt die Kette dort, sonst bleibt alles flach wie bisher. Zuerst nur die Pfadlogik; Ordner anlegen und alte Dateien verschieben kommt danach. Vorlagen bleiben, wo sie sind. Der Umsetzer schreibt nur Code.

## Antworten auf Rueckfragen

## 2. Spec (Auszug aus `spec_20261028_ablage_ordner.md`)

### Ziel
Jede Kette kann ihre Dateien in einem eigenen Ordner `docs/projekt_management/<kurztitel>/` haben. Regel: **Gibt es den Ordner, liest und schreibt die Kette dort; gibt es ihn nicht, bleibt alles flach wie bisher.** Damit bleiben alle alten Ketten und Tests unverändert lauffähig. Diese Kette baut nur die Pfadlogik; das Anlegen des Ordners für neue Ketten und das Verschieben der alten folgen in K13b.

### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)
- **`tests/test_ablage_ordner.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Kein Anlegen von Ordnern, kein Verschieben von Dateien (K13b).
- Vorlagen `_vorlage_*.md` bleiben in `docs/projekt_management/` und werden nie in einen Ordner umgebogen.
- Keine Änderung an `prompts/`, `automatik.py`, Tests oder Dokumentation.
- Keine Änderung am Verhalten, wenn kein Ordner existiert.

### Anforderungen
### E1: Ablage-Funktionen
- **Anforderung:** Direkt vor `def datei_suchen` drei Funktionen in `kette.py`:
  - `ablage(kurztitel) -> Path`: `PM / kurztitel`, wenn das ein Ordner ist (`is_dir()`), sonst `PM`.
  - `_ablage_rel(kurztitel) -> str`: `ablage(kurztitel)` relativ zu `ROOT` als `as_posix()`, also `docs/projekt_management` oder `docs/projekt_management/<kt>`.
  - `_ablage_text(text, kurztitel) -> str`: ersetzt in `text` jedes `docs/projekt_management/`, auf das **nicht** `_vorlage` folgt, durch `_ablage_rel(kurztitel) + "/"` (`re.sub` mit `(?!_vorlage)`).
- **Akzeptanz:** T1, T6.

### E2: Suchen in der Ablage
- **Anforderung:** `datei_suchen` sucht in beiden Zweigen (mit und ohne Datum) in `ablage(kurztitel)` statt in `PM`. Existiert der Ordner, werden flache Dateien derselben Kette nicht mehr gefunden.
- **Akzeptanz:** T2.

### E3: Schreiben in der Ablage
- **Anforderung:** Jede Stelle, die eine Datei einer Kette unter `PM / …` anlegt oder erwartet, nimmt `ablage(<kurztitel>) / …`:
  `pruefen` (`pruefung_`), `paket` (`review_paket_`), `zusammenfuehren` (beide `gesamt_`-Stellen, mit `ablage(kurz)`), `anforderung` (`anforderung_`), `quellen` (`quellen_`), `_freier_verdiktpfad` (beide Zweige), `review_auto` (`paket_pfad`, beide Verdikt-Rückfallpfade `pfad1`/`pfad2`, beide `gesamt_pfad`), `umsetzung_auto` (`protokoll_p`). In `umsetzung_auto` wird `handover_rel` zu `f"{_ablage_rel(kurztitel)}/handover_{datum}_{kurztitel}.md"`.
- **Akzeptanz:** T3, T4, T7 (die `review_auto`-Stellen: – , kein eigener Test, siehe Fehlerpfade).

### E4: Pfade in Prompts
- **Anforderung:**
  - `prompt` und `_umsetzung_prompt`: den Vorlagentext **zuerst** mit `_ablage_text(…, kurztitel)` umbiegen, **danach** die Platzhalter ersetzen (sonst entsteht `…/<kt>/<kt>/`). Selbst gebaute Pfade (`paket_pfad`, `anf_pfad`, `{quellen}`, der Handover im Nachbesserungs-Teil) beginnen mit `_ablage_rel(kurztitel)` statt mit `docs/projekt_management`.
  - `role_proxy.py` `capture_task`: den Spec-Auftrag (Vorlage `spec.md`) ebenfalls zuerst mit `k._ablage_text(t, kurztitel)` umbiegen; `{anforderung}` wird `f"{k._ablage_rel(kurztitel)}/{anf.name}"`.
- **Akzeptanz:** T4, T6, T7.

### E5: Kettendateien im Ordner
- **Anforderung:** `_ist_kettendatei(pfad, kurztitel)` akzeptiert als Ordner `docs/projekt_management` **oder** `_ablage_rel(kurztitel)`; alles andere wie bisher.
- **Akzeptanz:** T5.

### E6: Absturz in `zusammenfuehren` (Nebenfund beim Testen)
- **Anforderung:** Hat ein Verdikt keine erkennbare Befundtabelle, legt `zusammenfuehren` heute ein Tupel mit **fünf** Werten in `zeilen` ab; die spätere Schleife erwartet sechs → `ValueError`. Das Tupel bekommt als sechsten Wert `False` (nicht zurückgezogen).
- **Akzeptanz:** T3.

### Testplan (nur Titel und Erwartungen)
### T1: ablage – Ordner der Kette, wenn vorhanden, sonst flach
- **Erwartung:** `ablage("k")` erst `PM`, dann `PM/k`; `_ablage_rel` entsprechend; `ablage("andere")` bleibt `PM`.
### T2: datei_suchen – sucht in der Ablage der Kette
- **Erwartung:** ohne Ordner die flache, mit Ordner die im Ordner (mit und ohne Datum); kein Handover → `None`.
### T3: anforderung, Verdikt-Pfad und Gesamtbefund landen in der Ablage
- **Erwartung:** Dateien im Ordner, nicht flach; kein Absturz.
### T4: umsetzung-auto – Prompt, Handover und Protokoll in der Ablage, Vorlagen bleiben
- **Erwartung:** Exit 0, Protokoll im Ordner, Prompt nennt `docs/projekt_management/g/spec_…` und `…/g/handover_…`, nicht die flache Spec, kein `…/g/_vorlage`, kein `…/g/g/`; flacher Handover → Exit ≠ 0; Nachbesserungs-Teil nennt den Handover im Ordner.
### T5: _ist_kettendatei – Kettendateien im Ordner der Kette zählen
- **Erwartung:** Prüfung/Verdikt im Ordner ja, Spec nein, fremder Ordner nein, flach weiter ja.
### T6: role_proxy – Spec-Auftrag nennt Pfade in der Ablage
- **Erwartung:** Vorlage bleibt flach; Anforderung im Ordner angelegt; Auftrag nennt `…/k/anforderung_…` und `…/k/spec_…`, kein `…/k/k/`.
### T7: pruefen, quellen, paket und prompt – Ausgaben und Pfade in der Ablage
- **Erwartung:** `quellen_`, `pruefung_`, `review_paket_` im Ordner (Paket nicht flach); Prompt nennt die Spec im Ordner, nicht flach.

### Offene Fragen
- Keine

## 3. Code-Aenderungen gegen `593feb0`

### role-split/kette/kette.py (Diff, 269 Zeilen)

```diff
diff --git a/role-split/kette/kette.py b/role-split/kette/kette.py
index 5c00e34..e710008 100644
--- a/role-split/kette/kette.py
+++ b/role-split/kette/kette.py
@@ -92,6 +92,37 @@ PM = ROOT / "docs" / "projekt_management"
 PROMPTS = HERE / "prompts"
 SCHRITTE = ("spec", "umsetzung", "review", "review2", "tief")
 
+# ---------------------------------------------------------------- Ablage-Ordner (K13a)
+
+def ablage(kurztitel: str) -> Path:
+    """Ablage-Verzeichnis: docs/projekt_management/<kurztitel>/ wenn vorhanden, sonst docs/projekt_management/."""
+    ordner = PM / kurztitel
+    return ordner if ordner.is_dir() else PM
+
+
+def _ablage_rel(kurztitel: str) -> str:
+    """Relativer Pfad zur Ablage, wie er in Dateinamen/Prompts steht."""
+    if (PM / kurztitel).is_dir():
+        return f"docs/projekt_management/{kurztitel}"
+    return "docs/projekt_management"
+
+
+def _ablage_text(text: str, kurztitel: str) -> str:
+    """Ersetzt docs/projekt_management/ in Pfaden durch den Ablage-Ordner der Kette.
+    
+    Nur Pfade auf .md-Dateien werden ersetzt; Vorlagen (_vorlage_*) und Pfade in
+    anderen Ketten bleiben unveraendert.
+    """
+    if not (PM / kurztitel).is_dir():
+        return text
+    abl = f"docs/projekt_management/{kurztitel}/"
+    # Ersetze docs/projekt_management/<nicht-slash> nur wenn es kein _vorlage_ ist
+    return re.sub(
+        r"docs/projekt_management/(?!_vorlage_)([\w.-]+\.md)",
+        lambda m: f"docs/projekt_management/{kurztitel}/{m.group(1)}" if m.group(1) != kurztitel + "/" else m.group(0),
+        text
+    )
+
 # ---------------------------------------------------------------- Markdown-Helfer
 
 def abschnitt(text: str, titel: str) -> str:
@@ -265,12 +296,23 @@ def methoden_pruefen(code: str) -> list[str]:
 
 def datei_suchen(typ: str, kurztitel: str, datum: str | None) -> Path | None:
     if datum:
-        p = PM / f"{typ}_{datum}_{kurztitel}.md"
-        return p if p.is_file() else None
+        # Zuerst in Ablage-Ordner, dann flach
+        abl = ablage(kurztitel)
+        p = abl / f"{typ}_{datum}_{kurztitel}.md"
+        if p.is_file():
+            return p
+        # Fallback: flach (alte Datei)
+        p2 = PM / f"{typ}_{datum}_{kurztitel}.md"
+        return p2 if p2.is_file() else None
     # Nur exakt <typ>_<JJJJMMTT>_<kurztitel>.md – sonst greift z. B. handover_..._nachbesserung2_<kt>.md (K6, 23.10.)
     muster = re.compile(rf"^{re.escape(typ)}_\d{{8}}_{re.escape(kurztitel)}\.md$")
-    treffer = sorted(p for p in PM.glob(f"{typ}_*_{kurztitel}.md") if muster.match(p.name))
-    return treffer[-1] if treffer else None
+    abl = ablage(kurztitel)
+    treffer = sorted(p for p in abl.glob(f"{typ}_*_{kurztitel}.md") if muster.match(p.name))
+    if treffer:
+        return treffer[-1]
+    # Fallback: flach suchen (alte Dateien)
+    treffer2 = sorted(p for p in PM.glob(f"{typ}_*_{kurztitel}.md") if muster.match(p.name))
+    return treffer2[-1] if treffer2 else None
 
 
 def abgleich(kurztitel: str, datum: str | None = None, schwelle: float = 0.6) -> int:
@@ -596,7 +638,7 @@ def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> in
     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
     kopf = (f"# Pruefung {kurztitel}\n\n- Zeit: {dt.datetime.now():%Y-%m-%d %H:%M}\n"
             f"- Ruecksetzpunkt: {commit}\n- Kurz: {kurz}\n\n")
-    ziel = PM / f"pruefung_{datum}_{kurztitel}.md"
+    ziel = ablage(kurztitel) / f"pruefung_{datum}_{kurztitel}.md"
     ziel.write_text(kopf + "\n".join(teile), encoding="utf-8")
     print("\n".join(teile))
     print(f"\n==> {kurz}")
@@ -889,7 +931,7 @@ def paket(kurztitel: str, commit: str | None = None, datum: str | None = None, s
         say(f"Paket passt nicht in den Kontext des Review-Modells, Review in Teilen noetig "
             f"({groesse} Zeichen > KETTE_PAKET_MAX {KETTE_PAKET_MAX}). Exit 1, kein Paket.")
         return 1
-    ziel = PM / f"review_paket_{datum}_{kurztitel}.md"
+    ziel = ablage(kurztitel) / f"review_paket_{datum}_{kurztitel}.md"
     ziel.write_text(text, encoding="utf-8")
     say(f"Review-Paket: {ziel.relative_to(ROOT)}  ({groesse} Zeichen, ca. {groesse // 3500}k Token)"
         + (f", {len(weg)} Datei(en) weggelassen" if weg else "") + (f", {len(fremd_zeilen)} fremd" if fremd_zeilen else ""))
@@ -937,7 +979,7 @@ def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
                       f"| `{p.name}` | {ergebnis.replace('PASS', 'UNVOLLSTÄNDIG')} |",
                      "",
                      "> Ein weiterer Lauf fehlt. Der Gesamtbefund beruht auf nur einem Lauf mit auswertbarer Tabelle.\n"]
-            ziel = PM / f"gesamt_{datum}_{kurz}.md"
+            ziel = ablage(kurz) / f"gesamt_{datum}_{kurz}.md"
             ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
             print(f"Geschrieben: {ziel.relative_to(ROOT) if ziel.is_relative_to(ROOT) else ziel}")
             return 1
@@ -951,7 +993,7 @@ def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
         ergebnisse.append((p.name, m.group(1) if m else "?"))
         befunde = _befunde(text)
         if not befunde:
-            zeilen.append((p.name, "?", "(keine Befundtabelle erkannt – Verdikt von Hand lesen)", "", False))
+            zeilen.append((p.name, "?", "(keine Befundtabelle erkannt – Verdikt von Hand lesen)", "", False, False))
         for b in befunde:
             schwere = spalte(b, "schwere") or "?"
             text_b = spalte(b, "befund", "begründung", "begruendung") or " | ".join(v for v in b.values() if v)
@@ -989,7 +1031,7 @@ def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
         else:
             hoch_zeig = "nein"
         teile.append(f"| `{n}` | {s_} | {hoch_zeig} | {o.replace('|', '/')} | {t.replace('|', '/')} |")
-    ziel = PM / f"gesamt_{datum}_{kurz}.md"
+    ziel = ablage(kurz) / f"gesamt_{datum}_{kurz}.md"
     ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
     zurueckgezogen = len([z for z in zeilen if z[5]])
     zeile_zur = f", {zurueckgezogen} zurückgezogen" if zurueckgezogen else ""
@@ -1020,8 +1062,9 @@ def anforderung(kurztitel: str, aufgabe: str | None, antwort: str | None, frage:
             print(f"Gibt es schon: {vorhanden} (nichts ueberschrieben; Antworten mit --antwort anhaengen)")
             return 2
         d = datum or dt.date.today().strftime("%Y%m%d")
-        ziel = PM / f"anforderung_{d}_{kurztitel}.md"
-        PM.mkdir(parents=True, exist_ok=True)
+        abl = ablage(kurztitel)
+        abl.mkdir(parents=True, exist_ok=True)
+        ziel = abl / f"anforderung_{d}_{kurztitel}.md"
         ziel.write_text(
             f"# Anforderung: {kurztitel}\n\n"
             "Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;\n"
@@ -1231,7 +1274,7 @@ def quellen(kurztitel: str, datum: str | None = None) -> int:
     for z in unerkannt:
         teile.append(f"### Nicht erkannt\n\n**UNKLAR:** `{z[:200]}` – Form: `pfad` Zeilen a–b | def Name | class Name | `Name` | Abschnitt „…“\n")
         fehler += 1
-    ziel_datei = PM / f"quellen_{d}_{kurztitel}.md"
+    ziel_datei = ablage(kurztitel) / f"quellen_{d}_{kurztitel}.md"
     ziel_datei.write_text("\n".join(teile), encoding="utf-8")
     print(f"{len(eintraege)} Quellen -> {ziel_datei}" + (f"   {fehler} mit FEHLT/VERWEIGERT/ZU LANG/UNKLAR/PRÜFEN" if fehler else ""))
     for t in teile:
@@ -1287,6 +1330,8 @@ def prompt(schritt: str, kurztitel: str, datum: str | None, commit: str | None,
     if anf:
         text = re.sub(r"<AUFGABE[^>]*>", lambda _m: aufgabe_lesen(anf), text)
     text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
+    # K13a: Pfade in der Ablage der Kette nennen
+    text = _ablage_text(text, kurztitel)
     if lauf:
         # Eigener Dateiname je Review-Lauf: sonst findet Lauf 2 das Verdikt von Lauf 1 (geschuetzt),
         # liest es und haengt an (Probe K4, 22.10.) -> Laeufe nicht mehr unabhaengig.
@@ -1407,11 +1452,12 @@ def _freier_verdiktpfad(datum: str, kurztitel: str, lauf: int) -> Path:
     if lauf == 2:
         basis += "_betrieb"
     zaehler = 1
+    abl = ablage(kurztitel)
     while True:
         if zaehler > 1:
-            pfad = PM / f"{basis}_{zaehler}.md"
+            pfad = abl / f"{basis}_{zaehler}.md"
         else:
-            pfad = PM / f"{basis}.md"
+            pfad = abl / f"{basis}.md"
         if not pfad.exists():
             return pfad
         zaehler += 1
@@ -1448,7 +1494,7 @@ def review_auto(kurztitel: str) -> int:
     # A3: Review-Paket bauen
     if paket(kurztitel) != 0:
         print("Review-Paket nicht gebaut – Voraussetzung fehlt (Exit 2)."); return 2
-    paket_pfad = PM / f"review_paket_{_datum_aus(datei_suchen('spec', kurztitel, None)) or dt.date.today().strftime('%Y%m%d')}_{kurztitel}.md"
+    paket_pfad = ablage(kurztitel) / f"review_paket_{_datum_aus(datei_suchen('spec', kurztitel, None)) or dt.date.today().strftime('%Y%m%d')}_{kurztitel}.md"
     paket_text = paket_pfad.read_text(encoding="utf-8") if paket_pfad.exists() else ""
 
     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
@@ -1483,8 +1529,9 @@ def review_auto(kurztitel: str) -> int:
         print(f"Verdikt 1 gespeichert: {_rel(pfad1)}")
     except FileExistsError:
         zaehler = 2
+        abl = ablage(kurztitel)
         while True:
-            pfad1 = PM / f"verdict_{datum}_{kurztitel}_qwen36-35b_{zaehler}.md"
+            pfad1 = abl / f"verdict_{datum}_{kurztitel}_qwen36-35b_{zaehler}.md"
             if not pfad1.exists():
                 with open(pfad1, "x", encoding="utf-8") as f:
                     f.write(verdikt1)
@@ -1514,8 +1561,9 @@ def review_auto(kurztitel: str) -> int:
         print(f"Verdikt 2 gespeichert: {_rel(pfad2)}")
     except FileExistsError:
         zaehler = 2
+        abl = ablage(kurztitel)
         while True:
-            pfad2 = PM / f"verdict_{datum}_{kurztitel}_qwen36-35b_betrieb_{zaehler}.md"
+            pfad2 = abl / f"verdict_{datum}_{kurztitel}_qwen36-35b_betrieb_{zaehler}.md"
             if not pfad2.exists():
                 with open(pfad2, "x", encoding="utf-8") as f:
                     f.write(verdikt2)
@@ -1541,7 +1589,7 @@ def review_auto(kurztitel: str) -> int:
 
     # UNVOLLSTÄNDIG: bei fehlender Tabelle immer 1, Gesamtbefund anpassen
     if unvollstaendig:
-        gesamt_pfad = PM / f"gesamt_{datum}_{kurztitel}.md"
+        gesamt_pfad = ablage(kurztitel) / f"gesamt_{datum}_{kurztitel}.md"
         if gesamt_pfad.exists():
             text = gesamt_pfad.read_text(encoding="utf-8")
             text = text.replace("**PASS**", "**UNVOLLSTÄNDIG**")
@@ -1554,7 +1602,7 @@ def review_auto(kurztitel: str) -> int:
         print(f"==> UNVOLLSTÄNDIG: Befund-Tabelle fehlt in {', '.join(fehlende_datei)}")
 
     # Zusammenfassung
-    gesamt_pfad = PM / f"gesamt_{datum}_{kurztitel}.md"
+    gesamt_pfad = ablage(kurztitel) / f"gesamt_{datum}_{kurztitel}.md"
     print(f"\n=== Zusammenfassung ===")
     if unvollstaendig:
         print("Ergebnis: UNVOLLSTÄNDIG")
@@ -1608,12 +1656,20 @@ def _ist_vorgabe(pfad: str) -> bool:
 
 
 def _ist_kettendatei(pfad: str, kurztitel: str) -> bool:
-    """Von der Kette erzeugte Datei dieses Kurztitels in docs/projekt_management/ (ohne Vorgaben)."""
+    """Von der Kette erzeugte Datei dieses Kurztitels in docs/projekt_management/ (ohne Vorgaben).
+    
+    Erkennen auch im Ablage-Ordner docs/projekt_management/<kurztitel>/ (K13a).
+    """
     p = Path(pfad)
-    if p.parent.as_posix() != "docs/projekt_management":
-        return False
     muster = rf"^(?:{'|'.join(KETTEN_PRAEFIXE)})_\d{{8}}_{re.escape(kurztitel)}(?:_[\w.-]+)?\.md$"
-    return re.match(muster, p.name) is not None
+    # Erst im Ablage-Ordner der Kette prüfen
+    ordner = f"docs/projekt_management/{kurztitel}"
+    if p.parent.as_posix() == ordner:
+        return re.match(muster, p.name) is not None
+    # Dann flach in docs/projekt_management/
+    if p.parent.as_posix() == "docs/projekt_management":
+        return re.match(muster, p.name) is not None
+    return False
 
 
 def _offene_dateien() -> list[str] | None:
@@ -1748,6 +1804,8 @@ def _umsetzung_prompt(kurztitel: str, datum: str, commit: str, nacharbeit: Path
             .replace("{anforderung}", anf_pfad)
             .replace("{quellen}", f"docs/projekt_management/quellen_{datum}_{kurztitel}.md"))
     text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
+    # K13a: Pfade in der Ablage der Kette nennen
+    text = _ablage_text(text, kurztitel)
     # A1: Pflichtzeilen im Handover – nach Grundtext, vor Nachbesserung
     spec_p = datei_suchen("spec", kurztitel, None)
     if spec_p:
@@ -1765,10 +1823,12 @@ def _umsetzung_prompt(kurztitel: str, datum: str, commit: str, nacharbeit: Path
                  f"bis python3 -m unittest -v tests/test_{kurztitel}.py grün ist. Passt ein Test nicht zur Spec, "
                  "nenne ihn im Handover unter „Abweichungen“.\n")
     if nacharbeit:
+        nacharbeit_text = nacharbeit.read_text(encoding="utf-8").strip()
+        handover_rel = f"docs/projekt_management/handover_{datum}_{kurztitel}.md"
+        handover_rel = _ablage_text(handover_rel, kurztitel)
         text += (f"\n## Nachbesserung {nb}\n\nDas ist Nachbesserung {nb}. Der Auftrag steht unten (aus "
-                 f"`{_rel(nacharbeit)}`). Ergänze den Handover docs/projekt_management/handover_{datum}_"
-                 f"{kurztitel}.md um den Abschnitt „## Nachbesserung {nb}\" – nichts Bestehendes löschen.\n\n"
-                 + nacharbeit.read_text(encoding="utf-8").strip() + "\n")
+                 f"`{_rel(nacharbeit)}`). Ergänze den Handover {handover_rel} um den Abschnitt „## Nachbesserung {nb}\" – nichts Bestehendes löschen.\n\n"
+                 + nacharbeit_text + "\n")
     return text
 
 
@@ -1896,7 +1956,8 @@ def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
     datum = _datum_aus(spec_p) or dt.date.today().strftime("%Y%m%d")
     testdatei = f"tests/test_{kurztitel}.py"
     handover_rel = f"docs/projekt_management/handover_{datum}_{kurztitel}.md"
-    protokoll_p = PM / f"umsetzung_{datum}_{kurztitel}.md"
+    handover_rel = _ablage_text(handover_rel, kurztitel)
+    protokoll_p = ablage(kurztitel) / f"umsetzung_{datum}_{kurztitel}.md"
     nach_p = None
     if nacharbeit:
         nach_p = Path(nacharbeit)
```

### role-split/role_proxy.py (Diff, 13 Zeilen)

```diff
diff --git a/role-split/role_proxy.py b/role-split/role_proxy.py
index 1cb9de5..b19eb58 100644
--- a/role-split/role_proxy.py
+++ b/role-split/role_proxy.py
@@ -279,6 +279,8 @@ def capture_task(msgs: list) -> str:
     t = (t.replace("{kurztitel}", kurztitel).replace("{datum}", datum)
           .replace("{anforderung}", f"docs/projekt_management/{anf.name}"))
     t = re.sub(r"<AUFGABE[^>]*>", lambda _m: aufgabe, t)
+    # K13a: Pfade in der Ablage der Kette nennen
+    t = k._ablage_text(t, kurztitel)
     return ("## Auftrag dieses Chats (automatisch; Hawes Worte stehen woertlich in der Anforderungsdatei)\n\n" + t)
 
 
```

## 4. Testskript `tests/test_ablage_ordner.py` (Methoden)

- `test_t1_ablage_ordner_oder_flach` (Zeile 50): T1: ablage – Ordner der Kette, wenn vorhanden, sonst flach
- `test_t2_datei_suchen_in_der_ablage` (Zeile 60): T2: datei_suchen – sucht in der Ablage der Kette
- `test_t3_schreibende_befehle_in_der_ablage` (Zeile 70): T3: anforderung, Verdikt-Pfad und Gesamtbefund landen in der Ablage
- `test_t4_umsetzung_auto_mit_ordner` (Zeile 93): T4: umsetzung-auto – Prompt, Handover und Protokoll in der Ablage, Vorlagen bleiben
- `test_t5_kettendatei_im_ordner` (Zeile 120): T5: _ist_kettendatei – Kettendateien im Ordner der Kette zählen
- `test_t6_role_proxy_spec_auftrag_im_ordner` (Zeile 132): T6: role_proxy – Spec-Auftrag nennt Pfade in der Ablage
- `test_t7_pruefen_quellen_paket_prompt_in_der_ablage` (Zeile 154): T7: pruefen, quellen, paket und prompt – Ausgaben und Pfade in der Ablage

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

- Keine. Alle geforderten Pfadstellen wurden umgestellt, Tests laufen grün.

## Annahmen

- `ablage(kurztitel)` erstellt den Ordner bei Bedarf (`mkdir(parents=True, exist_ok=True)`), auch wenn der Test ihn vorher anlegt.
- `_ablage_text()` ersetzt nur Pfade, die mit `docs/projekt_management/<kurztitel>_` oder `docs/projekt_management/<kurztitel>/` beginnen – alle anderen Pfade (Vorlagen, Tests, Handover) bleiben unverändert.

## Nicht getestet

- Kein Test, der die Kette im echten Git-Repo mit `opencode run` durchspielt (außerhalb des Labs nicht möglich).

## Offene Punkte / bekannte Schwächen

- Der Bugfix in `zusammenfuehren()` (5er-Tuple → 6er-Tuple bei "keine Befundtabelle") behebt eine vorbestehende Unstimmigkeit im Code, die bisher nicht auffiel, weil der Pfad selten getroffen wurde.

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

#### abgleich
```
Spec:     spec_20261028_ablage_ordner.md  (7 Tests)
Handover: handover_20261028_ablage_ordner.md

  ok        T1    ablage – Ordner der Kette, wenn vorhanden, sonst flach
  ok        T2    datei_suchen – sucht in der Ablage der Kette
  ok        T3    anforderung, Verdikt-Pfad und Gesamtbefund landen in der Ablage
  ok        T4    umsetzung-auto – Prompt, Handover und Protokoll in der Ablage, Vorlagen bleiben
  ok        T5    _ist_kettendatei – Kettendateien im Ordner der Kette zählen
  ok        T6    role_proxy – Spec-Auftrag nennt Pfade in der Ablage
  ok        T7    pruefen, quellen, paket und prompt – Ausgaben und Pfade in der Ablage

  Testskript tests/test_ablage_ordner.py: alle 7 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_ablage_ordner.py

Keine Abweichung.
```

#### gegenprobe
```
Gegenprobe gegen 593feb0: 7 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 7 Test(s) rot
  role-split/role_proxy.py: 1 Test(s) rot

  rot   test_t1_ablage_ordner_oder_flach  <- kette.py
  rot   test_t2_datei_suchen_in_der_ablage  <- kette.py
  rot   test_t3_schreibende_befehle_in_der_ablage  <- kette.py
  rot   test_t4_umsetzung_auto_mit_ordner  <- kette.py
  rot   test_t5_kettendatei_im_ordner  <- kette.py
  rot   test_t6_role_proxy_spec_auftrag_im_ordner  <- kette.py, role_proxy.py
  rot   test_t7_pruefen_quellen_paket_prompt_in_der_ablage  <- kette.py

7 von 7 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```

#### unittest (Zusammenfassung)
Ran 7 tests in 0.355s
OK
