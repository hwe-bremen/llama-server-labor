# Review-Paket: git_schutz


Erzeugt 2026-11-01 20:16 von `kette.py paket`. Ruecksetzpunkt: `7f95f7d`. Geaenderte Code-Dateien: `role-split/kette/kette.py`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: git_schutz

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Der Umsetzer darf .git/config und .git/hooks/ nicht unbemerkt ändern können. Anlass: Am 27.10. setzte der 35B user.name=Test in .git/config, die Schreibbereich-Prüfung sah es nicht.

## Antworten auf Rueckfragen

## 2. Spec (Auszug aus `spec_20261101_git_schutz.md`)

### Ziel
`umsetzung-auto` merkt, wenn der Umsetzer im Git-Verzeichnis `config`, `hooks/` oder `info/` ändert, und meldet das laut (Befund, Exit 1). Anlass 27.10. (K10-Lauf): Der Umsetzer setzte `user.name=Test` in `.git/config`; ~40 Commits liefen danach als „Test“. Die Schreibbereich-Prüfung sah es nicht, weil sie auf `git status` beruht und `git status` das Git-Verzeichnis nie zeigt. Zusätzlich: Macht der Umsetzer `.git/config` unlesbar, stürzt `umsetzung_auto` heute mit Traceback ab (`_git("rev-parse", "HEAD")` mit `check=True`) – ohne Protokollzeile. Das wird zu einem Befund.

### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)
- **`tests/test_git_schutz.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- **Nichts zurücksetzen.** Wie bei Selbst-Commit und Schreibbereich: nur melden, Hawe entscheidet.
- Keine Änderung an `role-split/kette/testdata/opencode_fake.py` (die Vorgabe-Tests bringen einen eigenen Wrapper mit), an `automatik.py`, an den MCP-Werkzeugen oder an der Prompt-Vorlage.
- Kein Schutz der globalen Git-Konfiguration (`~/.gitconfig`) und keine Änderung der Umgebungsvariablen des Umsetzer-Prozesses (siehe „Abweichende Meinung“).
- Alle bestehenden Tests bleiben grün, besonders `tests/test_umsetzung_auto.py` (33 Tests).

### Anforderungen
### A1: Git-Verzeichnis bestimmen
- **Anforderung:** Konstante `GIT_SCHUTZ = ("config", "hooks", "info")` direkt hinter `ABGELEHNT_TEXTE`. Funktion `_git_verzeichnis() -> Path | None`: `subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--git-common-dir"], capture_output=True, text=True)`; Exit ≠ 0 oder leere Ausgabe → `None`. Sonst den Pfad absolut machen (relativ → `ROOT / pfad`) und `.resolve()` zurückgeben. `ROOT` wird zur Aufrufzeit gelesen. Im verknüpften Worktree ist das das `.git` des Hauptrepos (dort liegen `config` und `hooks/`).
- **Stelle:** `role-split/kette/kette.py`, neue Funktion direkt vor `PROTOKOLL_RE`.
- **Akzeptanz:** T7, T8.

### A2: Schnappschuss der geschützten Teile
- **Anforderung:** `_git_schutz(gitdir: Path) -> dict[str, str]`. Für jeden Namen aus `GIT_SCHUTZ`: Ist `gitdir/<name>` ein Symlink oder eine Datei → ein Eintrag unter `<name>`. Ist es ein Ordner → rekursiv (`os.walk`, Symlinks nicht verfolgen) je Datei **und je Symlink** (auch Symlink auf Ordner oder ins Leere) ein Eintrag; Ordner selbst sind keine Einträge. Fehlt es → kein Eintrag. Schlüssel = Pfad relativ zu `gitdir` in POSIX-Form (`config`, `hooks/pre-commit`, `hooks/tief/unten/hook`). Wert:
  - Symlink → `link:` + `os.readlink(p)`
  - Datei → sha256 (hex) des Inhalts, bei gesetztem Ausführbar-Bit (`st_mode & 0o111`) mit Anhang `:x`
  - `OSError` beim Lesen → `<unlesbar>`
  Nur exakte Namen: `hooks_alt/` oder `description` gehören nicht dazu. Die Funktion schreibt nichts.
- **Stelle:** neue Funktion (ggf. mit kleiner Hilfsfunktion für einen Eintrag) direkt hinter `_git_verzeichnis`.
- **Akzeptanz:** T3, T4, T5, T8.

### A3: Einbau in `umsetzung_auto`
- **Anforderung:**
  1. Vor dem Start, unmittelbar vor `head_vor = …` (Abschnitt „A7 Schnappschuss VOR dem Start“): `gitdir = _git_verzeichnis()`; `None` → `nein("Git-Verzeichnis nicht gefunden (git rev-parse --git-common-dir) – kein Lauf.")` (Exit 2, opencode startet nicht). Sonst `schutz_vor = _git_schutz(gitdir)`.
  2. **Sofort nach `_lauf`**, als erste Anweisung von „A7 Schnappschuss SOFORT nach dem Lauf“: `schutz = _in_diesem_lauf(schutz_vor, _git_schutz(gitdir))` – mit dem **vorher** bestimmten `gitdir` (nicht neu bestimmen; bei kaputter `config` ginge das nicht).
  3. Gilt für Erstlauf und Nacharbeit gleich.
  4. Befund direkt nach dem Selbst-Commit-Befund (a), wenn `schutz` nicht leer ist – genau dieser Text, Einträge in der Reihenfolge von `schutz` (sortiert):
     ```
     Git-Schutz verletzt – .git/ in diesem Lauf geändert (nichts zurückgesetzt):
       .git/<rel> (<neu|weg|geaendert>)
     ```
     Der Befund ändert nichts am Ablauf: (c)/(d) laufen wie bisher (wenn git benutzbar ist, A4), Exit wird 1, weil ein Befund vorliegt.
  5. Protokoll: Nach den bisherigen Unterzeilen (Tokens, Fehler) je Eintrag aus `schutz` eine Unterzeile `  - git-schutz: .git/<rel> (<art>)`. Die Laufzeile selbst bleibt unverändert (`_protokoll`/`automatik` lesen sie).
  6. Schlussausgabe: direkt nach der Zeile `In diesem Lauf geändert: …` die Zeile `Git-Schutz: unverändert` bzw. `Git-Schutz: geändert (<Anzahl Einträge>)`.
- **Stelle:** `def umsetzung_auto`
- **Akzeptanz:** T1–T5, T7.

### A4: git nach dem Lauf nicht benutzbar – kein Absturz
- **Anforderung:** `head_nach` nicht mehr über `_git(...)` (wirft), sondern `subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)`; Exit ≠ 0 → `head_nach = None`. Dann statt des Selbst-Commit-Befunds der Befund `git nach dem Lauf nicht benutzbar (git rev-parse HEAD: <erste Zeile von stderr, sonst ?>) – (c)/(d) übersprungen.`; kein Selbst-Commit-Befund. (c)/(d) laufen nur, wenn der Lauf abgeschlossen **und** `head_nach` nicht `None` ist; sonst die bestehende Ausgabe `(c) übersprungen (…)` / `(d) übersprungen (…)` mit dem Grund `Lauf nicht abgeschlossen` bzw. `git nicht benutzbar`. Protokollzeile wird trotzdem geschrieben (`rot: –, pruefen: –`).
- **Stelle:** `def umsetzung_auto`, Abschnitte A7 nach dem Lauf, (a), (c)/(d).
- **Akzeptanz:** T6.

### Testplan (nur Titel und Erwartungen)
### T1: Unverändertes Git-Verzeichnis – Lauf OK, Zeile „Git-Schutz: unverändert“
- **Erwartung:** Exit 0, Zeile `Git-Schutz: unverändert`, kein Befund, keine `git-schutz:`-Unterzeile, `pruefen` einmal.
### T2: git config user.name Test (Fall vom 27.10.) – lauter Befund, Exit 1, nichts zurückgesetzt
- **Erwartung:** Exit 1, Befund mit `  .git/config (geaendert)`, `Git-Schutz: geändert (1)`, Protokoll `art: erst, Exit: 1` plus Unterzeile, `user.name` ist weiter `Test`, `pruefen` lief, kein Schreibbereich-Befund.
### T3: hooks/ – neuer Hook, nur ausführbar gemacht, Symlink, gelöscht
- **Erwartung:** genau vier Einträge, sortiert, mit `neu`/`geaendert`/`neu`/`weg`; vier Unterzeilen im Protokoll.
### T4: info/ und Unterordner – auch im Nacharbeit-Lauf
- **Erwartung:** beide Einträge, `Git-Schutz: geändert (2)` (Ordner zählen nicht), `art: nb1, Exit: 1`.
### T5: Änderungen in .git/ außerhalb von config/hooks/info – kein Git-Schutz-Befund
- **Erwartung:** erster Lauf Exit 0, `unverändert`; zweiter Lauf nur Selbst-Commit-Befund, `unverändert`.
### T6: config kaputt – kein Absturz, Befund, Protokollzeile, (c)/(d) übersprungen
- **Erwartung:** keine Ausnahme, Exit 1, Git-Schutz-Befund für `config`, Befund `git nach dem Lauf nicht benutzbar (git rev-parse HEAD: …`, `(c) übersprungen (git nicht benutzbar)`, `pruefen` nicht aufgerufen, kein Selbst-Commit-Befund, Protokoll mit `rot: –, pruefen: –, art: erst, Exit: 1`.
### T7: Git-Verzeichnis – Worktree nutzt das des Hauptrepos; nicht bestimmbar → Exit 2, kein Start
- **Erwartung:** zweimal `<temp>/.git` (aufgelöst), einmal `None`; Lauf Exit 2, Meldung mit „Git-Verzeichnis“, opencode nicht gestartet.
### T8: Standardwerte im echten Pfad – GIT_SCHUTZ, echtes Git-Verzeichnis, nur lesend
- **Erwartung:** `("config", "hooks", "info")`; Pfad = `git rev-parse --path-format=absolute --git-common-dir`; `config` als 64-stelliger Hash, nur Schlüssel `config`, `hooks/…`, `info/…`; zweiter Aufruf gleich.

### Offene Fragen
- Keine

## 3. Code-Aenderungen gegen `7f95f7d`

### role-split/kette/kette.py (Diff, 159 Zeilen)

```diff
diff --git a/role-split/kette/kette.py b/role-split/kette/kette.py
index f7914e2..fb347d0 100644
--- a/role-split/kette/kette.py
+++ b/role-split/kette/kette.py
@@ -1624,6 +1624,7 @@ UMSETZUNG_BASH_MS_STANDARD = 300000        # ms, Einzelbefehl, wertet OpenCode s
 KETTEN_PRAEFIXE = ("pruefung", "umsetzung", "review_paket", "verdict", "gesamt", "nacharbeit")
 VORGABE_PRAEFIXE = ("spec_", "anforderung_", "quellen_", "_vorlage_")
 ABGELEHNT_TEXTE = ("rejected permission", "rule which prevents")
+GIT_SCHUTZ = ("config", "hooks", "info")
 
 
 def _schreibbereich(spec_text: str) -> list[str] | None:
@@ -1722,6 +1723,60 @@ def _in_diesem_lauf(vor: dict[str, str], nach: dict[str, str]) -> dict[str, str]
     return raus
 
 
+def _git_verzeichnis() -> Path | None:
+    """Git-Verzeichnis (common-dir) bestimmen; None wenn nicht moeglich."""
+    try:
+        out = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--git-common-dir"],
+                             capture_output=True, text=True)
+    except OSError:
+        return None
+    if out.returncode != 0 or not out.stdout.strip():
+        return None
+    pfad = out.stdout.strip()
+    if not os.path.isabs(pfad):
+        pfad = str(ROOT / pfad)
+    return Path(pfad).resolve()
+
+
+def _git_schutz(gitdir: Path) -> dict[str, str]:
+    """Schnappschuss der geschuetzten Teile: {rel: hash|x|link:...|<unlesbar>}."""
+    raus = {}
+    for name in GIT_SCHUTZ:
+        p = gitdir / name
+        if p.is_symlink():
+            raus[name] = "link:" + os.readlink(p)
+        elif p.is_file():
+            try:
+                h = hashlib.sha256(p.read_bytes()).hexdigest()
+                if p.stat().st_mode & 0o111:
+                    h += ":x"
+                raus[name] = h
+            except OSError:
+                raus[name] = "<unlesbar>"
+        elif p.is_dir():
+            for dirpath, dirnames, filenames in os.walk(p, followlinks=False):
+                dp = Path(dirpath)
+                for fn in filenames:
+                    fp = dp / fn
+                    rel = fp.relative_to(gitdir).as_posix()
+                    if fp.is_symlink():
+                        raus[rel] = "link:" + os.readlink(fp)
+                    else:
+                        try:
+                            h = hashlib.sha256(fp.read_bytes()).hexdigest()
+                            if fp.stat().st_mode & 0o111:
+                                h += ":x"
+                            raus[rel] = h
+                        except OSError:
+                            raus[rel] = "<unlesbar>"
+                for dn in dirnames:
+                    dpp = dp / dn
+                    if dpp.is_symlink():
+                        rel = dpp.relative_to(gitdir).as_posix()
+                        raus[rel] = "link:" + os.readlink(dpp)
+    return raus
+
+
 PROTOKOLL_RE = re.compile(r"rot: (?P<rot>[^,]+), pruefen: (?P<pruefen>[^,]+), art: (?P<art>erst|nb\d+)")
 
 
@@ -2015,6 +2070,10 @@ def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
         return nein("KETTE_UMSETZUNG_TIMEOUT / OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS muessen ganze Zahlen sein.")
 
     # A7 Schnappschuss VOR dem Start
+    gitdir = _git_verzeichnis()
+    if gitdir is None:
+        return nein("Git-Verzeichnis nicht gefunden (git rev-parse --git-common-dir) – kein Lauf.", 2)
+    schutz_vor = _git_schutz(gitdir)
     head_vor = _git("rev-parse", "HEAD").strip()
     stand_vor = _stand()
     if stand_vor is None:
@@ -2029,7 +2088,11 @@ def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
 
     # A7 Schnappschuss SOFORT nach dem Lauf, bevor kette.py selbst etwas schreibt
     stand_nach = _stand() or {}
-    head_nach = _git("rev-parse", "HEAD").strip()
+    head_nach_result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
+                                      capture_output=True, text=True)
+    head_nach = head_nach_result.stdout.strip() if head_nach_result.returncode == 0 else None
+    schutz_nach = _git_schutz(gitdir)
+    schutz_aenderung = _in_diesem_lauf(schutz_vor, schutz_nach)
     aenderungen = _in_diesem_lauf(stand_vor, stand_nach)
     abgeschlossen = not info["timeout"] and info["reason"] == "stop"
     befunde = []
@@ -2045,8 +2108,16 @@ def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
     elif info["reason"] != "stop":
         befunde.append(f"Lauf nicht abgeschlossen (reason: {info['reason']}).")
     # (a) immer
-    if head_vor != head_nach:
+    if head_nach is not None and head_vor != head_nach:
         befunde.append(f"Selbst-Commit: HEAD {head_vor[:7]} -> {head_nach[:7]} (nichts zurückgesetzt).")
+    # git-schutz befund
+    if schutz_aenderung:
+        befunde.append("Git-Schutz verletzt – .git/ in diesem Lauf geändert (nichts zurückgesetzt):\n"
+                        + "\n".join(f"  .git/{k} ({v})" for k, v in sorted(schutz_aenderung.items())))
+    # git nach dem Lauf nicht benutzbar
+    if head_nach is None:
+        stderr_text = head_nach_result.stderr.strip().splitlines()[0] if head_nach_result.stderr.strip() else "?"
+        befunde.append(f"git nach dem Lauf nicht benutzbar (git rev-parse HEAD: {stderr_text}) – (c)/(d) übersprungen.")
     # (b) immer
     if vorgabe and testdatei in aenderungen:
         befunde.append(f"Vorgabe-Tests in diesem Lauf geändert: {testdatei} ({aenderungen[testdatei]}) – "
@@ -2056,9 +2127,9 @@ def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
     if verstoesse:
         befunde.append("Schreibbereich verletzt (nichts zurückgesetzt):\n"
                        + "\n".join(f"  {d} ({a})" for d, a in verstoesse))
-    # (c) und (d) nur bei abgeschlossenem Lauf
+    # (c) und (d) nur bei abgeschlossenem Lauf und git benutzbar
     rot, pruefen_code = "–", "–"
-    if abgeschlossen:
+    if abgeschlossen and head_nach is not None:
         if handover_rel not in aenderungen or not (ROOT / handover_rel).is_file():
             befunde.append(f"Handover {handover_rel} in diesem Lauf nicht geschrieben.")
         elif nach_p and not re.search(rf"^## Nachbesserung {nb}\b",
@@ -2070,7 +2141,10 @@ def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
         if code != 0:
             befunde.append(f"pruefen: Exit {code}.")
     else:
-        print("(c) übersprungen (Lauf nicht abgeschlossen)\n(d) übersprungen (Lauf nicht abgeschlossen)")
+        if head_nach is None:
+            print("(c) übersprungen (git nicht benutzbar)\n(d) übersprungen (git nicht benutzbar)")
+        else:
+            print("(c) übersprungen (Lauf nicht abgeschlossen)\n(d) übersprungen (Lauf nicht abgeschlossen)")
 
     exit_code = 1 if befunde else 0
     reason = "timeout" if info["timeout"] else (info["reason"] or "–")
@@ -2085,6 +2159,8 @@ def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
     zeile += f"  - Tokens: input {tt['input']}, output {tt['output']}, reasoning {tt['reasoning']}, spitze {info['tokens_spitze']}\n"
     for e in info["fehler"]:
         zeile += f"  - {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}\n"
+    for k in sorted(schutz_aenderung):
+        zeile += f"  - git-schutz: .git/{k} ({schutz_aenderung[k]})\n"
     with open(protokoll_p, "a", encoding="utf-8") as f:
         f.write(zeile)
 
@@ -2096,6 +2172,10 @@ def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
     if info["text"]:
         print(f"Schlusstext: {info['text'][:300]}")
     print(f"In diesem Lauf geändert: {', '.join(aenderungen) or 'nichts'}")
+    if schutz_aenderung:
+        print(f"Git-Schutz: geändert ({len(schutz_aenderung)})")
+    else:
+        print("Git-Schutz: unverändert")
     for b in befunde:
         print(f"!!! {b}")
     print(f"Rohdaten: {_rel(rohdaten)}\nProtokoll: {_rel(protokoll_p)}")
```

## 4. Testskript `tests/test_git_schutz.py` (Methoden)

- `test_t1_unveraendertes_git_verzeichnis_lauf_ok` (Zeile 157): T1: Unverändertes Git-Verzeichnis – Lauf OK, Zeile „Git-Schutz: unverändert“
- `test_t2_git_config_user_name_test_fall_vom_27_10` (Zeile 167): T2: git config user.name Test (Fall vom 27.10.) – lauter Befund, Exit 1, nichts zurückgesetzt
- `test_t3_hooks_neu_ausfuehrbar_symlink_geloescht` (Zeile 180): T3: hooks/ – neuer Hook, nur ausführbar gemacht, Symlink, gelöscht
- `test_t4_info_exclude_und_unterordner_auch_in_der_nacharbeit` (Zeile 200): T4: info/ und Unterordner – auch im Nacharbeit-Lauf
- `test_t5_aenderungen_ausserhalb_der_geschuetzten_teile_kein_befund` (Zeile 215): T5: Änderungen in .git/ außerhalb von config/hooks/info – kein Git-Schutz-Befund
- `test_t6_config_unlesbar_kein_absturz` (Zeile 229): T6: config kaputt – kein Absturz, Befund, Protokollzeile, (c)/(d) übersprungen
- `test_t7_git_verzeichnis_worktree_und_fehlt` (Zeile 244): T7: Git-Verzeichnis – Worktree nutzt das des Hauptrepos; nicht bestimmbar → Exit 2, kein Start
- `test_t8_standardwerte_im_echten_pfad` (Zeile 261): T8: Standardwerte im echten Pfad – GIT_SCHUTZ, echtes Git-Verzeichnis, nur lesend

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

- Keine. Alle Anforderungen A1–A4 wurden wie spezifiziert umgesetzt.
- Die Spec nennt als Einbaustelle für A3.1 „unmittelbar vor `head_vor = …`". Die Umsetzung fügt `gitdir = _git_verzeichnis()` und `schutz_vor = _git_schutz(gitdir)` exakt davor ein – wie verlangt.
- Die Spec fordert für A4, dass `head_nach` nicht mehr über `_git()` geht. Die Umsetzung verwendet `subprocess.run` mit `check=False` und prüft `returncode == 0`.

## Annahmen

- Keine eigenen Annahmen getroffen. Konstanten, Formate und Schnittstellen ausschließlich aus Spec, Quellen und bestehendem Code übernommen.

## Nicht getestet

- Nichts. Alle 8 Tests (T1–T8) bestanden.

## Offene Punkte / bekannte Schwächen

- Vorher/Nachher-Vergleich erkennt keine Änderung, die der Umsetzer vor Laufende selbst zurücknimmt (bewusst offen, siehe Spec „Abweichende Meinung").
- Globale Git-Konfiguration (`~/.gitconfig`) wird nicht geschützt (bewusst nicht im Auftrag).

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

#### abgleich
```
Spec:     spec_20261101_git_schutz.md  (8 Tests)
Handover: handover_20261101_git_schutz.md

  ok        T1    Unverändertes Git-Verzeichnis – Lauf OK, Zeile „Git-Schutz: unverändert“
  ok        T2    git config user.name Test (Fall vom 27.10.) – lauter Befund, Exit 1, nichts zurückgesetzt
  ok        T3    hooks/ – neuer Hook, nur ausführbar gemacht, Symlink, gelöscht
  ok        T4    info/ und Unterordner – auch im Nacharbeit-Lauf
  ok        T5    Änderungen in .git/ außerhalb von config/hooks/info – kein Git-Schutz-Befund
  ok        T6    config kaputt – kein Absturz, Befund, Protokollzeile, (c)/(d) übersprungen
  ok        T7    Git-Verzeichnis – Worktree nutzt das des Hauptrepos; nicht bestimmbar → Exit 2, kein Start
  ok        T8    Standardwerte im echten Pfad – GIT_SCHUTZ, echtes Git-Verzeichnis, nur lesend

  Testskript tests/test_git_schutz.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_git_schutz.py

Keine Abweichung.
```

#### gegenprobe
```
Gegenprobe gegen 7f95f7d: 8 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 8 Test(s) rot

  rot   test_t1_unveraendertes_git_verzeichnis_lauf_ok  <- kette.py
  rot   test_t2_git_config_user_name_test_fall_vom_27_10  <- kette.py
  rot   test_t3_hooks_neu_ausfuehrbar_symlink_geloescht  <- kette.py
  rot   test_t4_info_exclude_und_unterordner_auch_in_der_nacharbeit  <- kette.py
  rot   test_t5_aenderungen_ausserhalb_der_geschuetzten_teile_kein_befund  <- kette.py
  rot   test_t6_config_unlesbar_kein_absturz  <- kette.py
  rot   test_t7_git_verzeichnis_worktree_und_fehlt  <- kette.py
  rot   test_t8_standardwerte_im_echten_pfad  <- kette.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```

#### unittest (Zusammenfassung)
Ran 8 tests in 1.499s
OK
