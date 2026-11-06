# Review-Paket: lauf_spec_pruefen


Erzeugt 2026-11-06 16:35 von `kette.py paket`. Ruecksetzpunkt: `2b63547`. Geaenderte Code-Dateien: `role-split/kette/automatik.py`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: lauf_spec_pruefen

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> K12a2: lauf nutzt spec-pruefen statt groesse. Befunde halten vor der Umsetzung an, Groesse nur noch Hinweis, kein Sonderweg fuer alte Specs.

## Antworten auf Rueckfragen

## 2. Spec (Auszug aus `spec_20261106_lauf_spec_pruefen.md`)

### Ziel
K12a2: `kette.py lauf <kt>` prüft die Spec vor der Umsetzung mit `spec-pruefen` (K12a) statt mit der eigenen Größenprüfung 2/6/8. Befunde halten den Lauf vor der Umsetzung an (Exit 3); die Größe hält nicht mehr an, sie erscheint nur noch als R59-Hinweis aus `spec-pruefen`. Entscheidung 05./06.11.: HALT bei Befunden, kein harter Größen-Halt, kein Sonderweg für alte Specs.

### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)
- **`tests/test_lauf_spec_pruefen.py` und `tests/test_lauf_status.py` sind Vorgabe und werden nicht geändert – keine Zeile.**
- Keine Änderung an `role-split/kette/spec_pruefen.py`, `role-split/kette/kette.py`, den MCP-Werkzeugen, dem RUNBOOK oder den Vorlagen.
- `groesse` bleibt unverändert (Name, Signatur, Rumpf) – `spec_pruefen._groesse` ruft sie auf.
- In `automatik.py` nur die vier genannten Stellen; `stand`, `status` und der Rest von `lauf` bleiben, wie sie sind.
- Kein Schalter, der die Spec-Prüfung umgeht; keine Ausnahme für alte Specs.
- Alle bestehenden Tests bleiben grün (`python3 scripts/alle_tests.py`; Altlast `test_scout_kw_doppelversand.py` bleibt rot).

### Anforderungen
### A1: lauf ruft spec-pruefen vor der Umsetzung
- **Anforderung:** In `lauf` ersetzt dieser Block den bisherigen Größenblock (von `g = groesse(spec_text)` bis einschließlich `return 3`), also **nach** den Prüfungen Kurztitel, Spec-Commit, Spec-Datei und Vorgabe-Tests (die bleiben unverändert und liefern weiter Exit 2) und **vor** `print(f"Umsetzer: {UMSETZER_VORSCHLAG}")`:
  1. `import spec_pruefen` **im Funktionsrumpf** (nicht am Dateianfang: `spec_pruefen` importiert `automatik`, und `kette.py spec-pruefen` lädt `spec_pruefen` zuerst).
  2. `exit_spec = spec_pruefen.spec_pruefen(kurztitel)` – über das Modul aufrufen, nicht `pruefe`; die Ausgabe ist damit genau die des Einzelbefehls.
  3. `exit_spec == 1` → `print("HALT – Spec-Prüfung mit Befunden: Spec nachbessern, neu committen, dann lauf erneut.")` und `return 3`; kein `status`, keine Zeile `HALT – Entscheidung Hawe.`.
  4. Sonst `exit_spec != 0` → `return exit_spec` ohne weitere Ausgabe.
  5. Sonst (Exit 0, auch mit Hinweisen) weiter wie bisher mit `Umsetzer: 35B`.
- **Stelle:** `role-split/kette/automatik.py`, `lauf`, anstelle des Größenblocks.
- **Akzeptanz:** T1, T3, T4, T5, T6.

### A2: Größen-Halt entfällt
- **Anforderung:** Die Konstanten `GROESSE_DATEIEN`, `GROESSE_ANFORDERUNGEN`, `GROESSE_TESTS` werden gelöscht; `UMSETZER_VORSCHLAG = "35B"` bleibt. `lauf` gibt keine eigene Größenzeile mehr aus und hält bei keiner Größe an. `groesse` bleibt unverändert. Docstrings: Modul-Docstring nennt K12a2 und dass `groesse` nur noch zählt (für `spec_pruefen`); `lauf`-Docstring `Kette: spec-pruefen -> umsetzung-auto -> review-auto -> status -> HALT.`
- **Stelle:** `role-split/kette/automatik.py`, Modul-Docstring, Konstanten am Dateianfang, Docstring von `lauf`.
- **Akzeptanz:** T2, T5.

### Testplan (nur Titel und Erwartungen)
### T1: Befunde halten vor der Umsetzung
- **Erwartung:** je Exit 3, keine Umsetzung; Ausgabe mit `Spec-Prüfung k: …`, dem jeweiligen Befund und `HALT – Spec-Prüfung mit Befunden`; weder `Umsetzer:` noch `HALT – Entscheidung Hawe.`.
### T2: Größe nur noch Hinweis
- **Erwartung:** Exit 0, Umsetzung und Review laufen; vier Hinweise `Größe über R59 (vorläufig): …`; kein „teilen“.
### T3: Ausgabe wie der Einzelbefehl
- **Erwartung:** `lauf`-Ausgabe beginnt mit genau der Ausgabe des Einzelbefehls, direkt danach `Umsetzer: 35B`; keine Zeile `Schwellen 2/6/8`; Exit 0 bzw. Exit 1 bei roter Umsetzung (wie bisher).
### T4: Vorbedingungen und Exit 2
- **Erwartung:** ohne Vorgabe-Tests Exit 2 und keine Spec-Prüfung in der Ausgabe; Attrappe mit Kurztitel `k` aufgerufen; Exit 2 → `lauf` Exit 2 ohne Umsetzung und ohne `HALT – Entscheidung Hawe.`; Exit 1 → Exit 3.
### T5: Standardwerte und echter Aufruf
- **Erwartung:** keine Konstanten `GROESSE_*`; `groesse` zählt wie bisher; `UMSETZER_VORSCHLAG` `35B`; `spec_pruefen.R59` unverändert; `lauf` Exit 3 mit HALT-Zeile, `spec-pruefen` Exit 1, beide ohne Traceback.
### T6: Trockenlauf am echten Bestand
- **Erwartung:** `git_schutz` Exit 3 mit genau dem Befund „Änderungsstellen“, keine Umsetzung; `spec_pruefen` Exit 0, „Keine Befunde“, Umsetzung und Review je einmal; Arbeitsstand unverändert.

### Offene Fragen
- Keine

## 3. Code-Aenderungen gegen `2b63547`

### role-split/kette/automatik.py (Diff, 61 Zeilen)

```diff
diff --git a/role-split/kette/automatik.py b/role-split/kette/automatik.py
index 6fdbea6..6ca5f33 100644
--- a/role-split/kette/automatik.py
+++ b/role-split/kette/automatik.py
@@ -1,6 +1,7 @@
-"""Automatik: groesse, stand, status, lauf – K11b.
+"""Automatik: groesse, stand, status, lauf – K11b, K12a2.
 
 Importiert kette (nicht umgekehrt), damit kette.py klein bleibt (R43).
+groesse zaehlt nur noch (fuer spec_pruefen), haelt nicht mehr an.
 """
 import re
 import subprocess
@@ -9,9 +10,6 @@ from pathlib import Path
 
 import kette
 
-GROESSE_DATEIEN = 2
-GROESSE_ANFORDERUNGEN = 6
-GROESSE_TESTS = 8
 UMSETZER_VORSCHLAG = "35B"
 
 
@@ -135,7 +133,7 @@ def status(kurztitel: str) -> int:
 
 
 def lauf(kurztitel: str) -> int:
-    """Kette: Groesse -> umsetzung-auto -> review-auto -> status -> HALT."""
+    """Kette: spec-pruefen -> umsetzung-auto -> review-auto -> status -> HALT."""
     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
         print(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).", file=sys.stderr)
         return 2
@@ -158,22 +156,13 @@ def lauf(kurztitel: str) -> int:
         )
         return 2
 
-    g = groesse(spec_text)
-    print(
-        f"Größe: {g['dateien']} Datei(en), {g['anforderungen']} Anforderungen, "
-        f"{g['tests']} Tests (Schwellen 2/6/8, vorläufig)"
-    )
-
-    if (
-        g["dateien"] > GROESSE_DATEIEN
-        or g["anforderungen"] > GROESSE_ANFORDERUNGEN
-        or g["tests"] > GROESSE_TESTS
-    ):
-        print(
-            "HALT – zu groß für den lokalen Umsetzer: Spec teilen oder "
-            "Claude übernimmt (R43)."
-        )
+    import spec_pruefen
+    exit_spec = spec_pruefen.spec_pruefen(kurztitel)
+    if exit_spec == 1:
+        print("HALT – Spec-Prüfung mit Befunden: Spec nachbessern, neu committen, dann lauf erneut.")
         return 3
+    if exit_spec != 0:
+        return exit_spec
 
     print(f"Umsetzer: {UMSETZER_VORSCHLAG}")
     exit_umsetzung = kette.umsetzung_auto(kurztitel)
```

## 4. Testskript `tests/test_lauf_spec_pruefen.py` (Methoden)

- `test_t1_befunde_halten_vor_der_umsetzung` (Zeile 102): T1: lauf – Befunde aus spec-pruefen halten mit Exit 3 vor der Umsetzung
- `test_t2_groesse_nur_hinweis` (Zeile 120): T2: lauf – Größe über den alten Schwellen und über R59 hält nicht mehr an
- `test_t3_ausgabe_wie_einzelbefehl` (Zeile 136): T3: lauf – gültige Spec: Ausgabe wie spec-pruefen, danach Umsetzung und Review
- `test_t4_vorbedingungen_und_exit_2` (Zeile 154): T4: lauf – Vorbedingungen vor der Spec-Prüfung, Exit 2 der Spec-Prüfung durchgereicht
- `test_t5_standardwerte_und_echter_aufruf` (Zeile 179): T5: Standardwerte – alte Schwellen weg, groesse bleibt, lauf und spec-pruefen über kette.main in frischem Prozess
- `test_t6_trockenlauf_echter_bestand` (Zeile 212): T6: Trockenlauf am echten Bestand – alte Spec hält, saubere Spec läuft, nichts geschrieben

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

- Keine. Alle 4 Änderungsstellen aus der Spec (Modul-Docstring, Konstanten, Docstring `lauf`, Größenblock) wurden exakt umgesetzt.
- Die Vorgabe-Tests `tests/test_lauf_spec_pruefen.py` wurden nicht geändert (wie gefordert).

## Annahmen

- Keine.

## Nicht getestet

- Nichts. Alle 6 Tests laufen grün.

## Offene Punkte / bekannte Schwächen

- Keine.

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

#### abgleich
```
Spec:     spec_20261106_lauf_spec_pruefen.md  (6 Tests)
Handover: handover_20261106_lauf_spec_pruefen.md

  ok        T1    Befunde halten vor der Umsetzung
  ok        T2    Größe nur noch Hinweis
  ok        T3    Ausgabe wie der Einzelbefehl
  ok        T4    Vorbedingungen und Exit 2
  ok        T5    Standardwerte und echter Aufruf
  ok        T6    Trockenlauf am echten Bestand

  Testskript tests/test_lauf_spec_pruefen.py: alle 6 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_lauf_spec_pruefen.py

Keine Abweichung.
```

#### gegenprobe
```
Gegenprobe gegen 2b63547: 6 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/automatik.py: 6 Test(s) rot

  rot   test_t1_befunde_halten_vor_der_umsetzung  <- automatik.py
  rot   test_t2_groesse_nur_hinweis  <- automatik.py
  rot   test_t3_ausgabe_wie_einzelbefehl  <- automatik.py
  rot   test_t4_vorbedingungen_und_exit_2  <- automatik.py
  rot   test_t5_standardwerte_und_echter_aufruf  <- automatik.py
  rot   test_t6_trockenlauf_echter_bestand  <- automatik.py

6 von 6 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```

#### unittest (Zusammenfassung)
Ran 6 tests in 0.432s
OK
