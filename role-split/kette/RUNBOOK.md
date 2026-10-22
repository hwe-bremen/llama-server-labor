# Runbook: die Kette (Stand 22.10.2026)

Gebrauchsanweisung für eine Aufgabe von der Idee bis zum Commit. **Das ist die einzige maßgebliche Anleitung**;
`FAHRPLAN.md` verweist hierher, `docs/KURZANLEITUNG.md` ist der Spickzettel fürs ganze Lab.

---

## 0. Worum es geht – in einer Minute

Du beschreibst eine Aufgabe im Chat. Danach arbeiten nacheinander:

| Phase | Wer | Was entsteht | Dauer (ca.) |
|---|---|---|---|
| A Aufgabe + Spec | **Du** + Qwen3.8 (Web-UI) | `anforderung_…`, `spec_…`, `quellen_…` | 30–60 min |
| B Umsetzung | Qwen3.6 in OpenCode | Code, Tests, `handover_…` | 30–60 min |
| C Prüfen | **Maschine** (`kette.py pruefen`) | `pruefung_…` | 2 min |
| D Review | Qwen3.6 (Web-UI, neuer Chat) | `verdict_…` | 15–30 min |
| E Gegenprüfung | Claude (Projekt-Chat) | Befunde oder Freigabe | 5–15 min |
| F Entscheidung | **Du** | Commit, Nachbesserung oder Verwerfen | 2 min |

Alle Dateien liegen in `docs/projekt_management/` und tragen Datum und Kurztitel im Namen,
z. B. `spec_20261021_search_results_verbessern.md`.

**Drei Grundsätze**
1. Was du willst, steht **wörtlich** in der Anforderung – alles wird daran gemessen, nicht an der Spec.
2. Maschinen prüfen vor Modellen: Tests, Gegenprobe, Abgleich laufen immer, bevor ein Modell urteilt.
3. Kein Commit ohne externe Gegenprüfung. Das lokale Review ist derzeit Zweitmeinung (Stand: 0 von 3, siehe Abschnitt 7).

---

## 1. Vor jeder Kette (2 min)

**Kurztitel wählen:** nur Kleinbuchstaben, Ziffern, `_`, sprechend. Beispiel: `scout_feeds_pruefen`.
Du schreibst ihn in allen Befehlen **ausgeschrieben** hin – keine Variablen wie `$K`.
In diesem Runbook steht dafür `<kurztitel>`: spitze Klammern nie mit eintippen.

**Fenster 2** (Fenster 1 gehört dem Lab):
```bash
cd ~/PycharmProjects/llama-server && source .venv/bin/activate
git status --short          # muss leer sein – sonst erst committen oder klären
```

---

## Phase A – Aufgabe und Spec

**Lab:** Fenster 1 `bash start_rollen.command`, warten bis die `.ts.net`-URL erscheint.
**Browser:** `http://127.0.0.1:8092` (oder iPad-URL), **neuer Chat**, Modell **Qwen3.8**, Reasoning **aus**.

1. Aufgabe schreiben – genau diese Form:
   ```
   @review Neue Aufgabe <kurztitel>: <was du willst, in deinen Worten>
   ```
   Der Rollen-Proxy legt `anforderung_<datum>_<kurztitel>.md` mit deinem Text an.
2. Das Modell liest Code, nimmt Stellung, stellt Rückfragen. **Einfach im Chat antworten** – jede Antwort
   wird samt Frage an die Anforderung angehängt. Entscheidungen hier treffen, nicht später.
3. Wenn alles geklärt ist: **„Spec schreiben"**.
4. **Spec lesen** – diese vier Punkte prüfst du selbst:
   - [ ] **Außenwirkung:** Kann die Aufgabe Mails senden, ins Netz gehen, echte Daten oder den Schlüsselbund berühren?
         Dann muss eine **technische Sperre für Tests** genannt sein. Fehlt sie → im Chat nachfordern.
   - [ ] **Offene Fragen / Restrisiken:** Weicht die Spec irgendwo von deiner Anforderung ab? → Im Chat entscheiden.
   - [ ] **Tests:** Jeder Test hat eine ID (T1, T2 …) und eine prüfbare Erwartung.
   - [ ] **Quellen:** Für Konstanten, Formate, Schnittstellen steht eine Fundstelle (Datei + Zeilen oder `def`), kein Wert „aus dem Kopf".
5. Quellen holen (Fenster 2):
   ```bash
   python3 role-split/kette/kette.py quellen <kurztitel>
   ```
   Meldet es `FEHLT`, `ZU LANG`, `VERWEIGERT` oder `UNKLAR`: im Spec-Chat korrigieren lassen, Befehl wiederholen.
6. Committen – **die Nachricht muss genau so lauten**, daran findet `pruefen` später den Rücksetzpunkt:
   ```bash
   git add docs/projekt_management/*_<kurztitel>.md && git commit -m "Spec <kurztitel>"
   ```

**Fertig, wenn:** Commit „Spec <kurztitel>" existiert (`git log --oneline -3`).

---

## Phase B – Umsetzung (OpenCode)

1. Prompt holen (landet automatisch in der Zwischenablage):
   ```bash
   python3 role-split/kette/kette.py prompt umsetzung <kurztitel>
   ```
2. `opencode` im Projektordner starten, Modell **Qwen3.6**, mit **Tab** Agent **`umsetzung`** wählen, Prompt einfügen.
   Provider: Läuft `start_rollen` → beliebig. Läuft `start_eval` → **„M4 direkt (8080)"** (sonst „Cannot connect").
3. **Nicht nachhelfen.** Shell-Freigaben nur ohne Außenwirkung (Tests, Syntax-Checks, `git status/diff`), im Zweifel ablehnen.
   `umsetzung_nacht` nur, wenn du bewusst nicht dabei bist.
4. **Nicht committen.**

**Fertig, wenn:** OpenCode meldet, `handover_<datum>_<kurztitel>.md` ist geschrieben.

---

## Phase C – Maschinelle Prüfung (ein Befehl)

```bash
python3 role-split/kette/kette.py pruefen <kurztitel>
```

Das macht nacheinander **abgleich** (Spec-Tests vs. Handover/Testskript), **unittest** und **gegenprobe**
(jede geänderte Datei einzeln auf den alten Stand zurück – wird ein Test dann rot, misst er die Änderung).
Die ganze Ausgabe steht danach in `pruefung_<datum>_<kurztitel>.md`.

**Lesen – nur die letzte Zeile:**

| Kurzzeile | Bedeutung | Weiter mit |
|---|---|---|
| `unittest: Abweichung` | Tests rot | direkt **F → Nachbessern** (kein Review nötig) |
| `gegenprobe: Abweichung` | mind. ein Test `GRUEN` (bleibt mit altem Code grün) | normal: im Review/Gegenprüfung ansehen lassen; Bestandstests sind ok |
| `abgleich: Abweichung` | Test fehlt, umbenannt (`ANDERS`) oder ohne Methode | im Review/Gegenprüfung ansehen lassen |
| `… FEHLER` | Werkzeug konnte nicht laufen (Datei fehlt, kein Spec-Commit) | Meldung lesen; Rücksetzpunkt fehlt → `pruefen <kurztitel> --commit <hash>` |

Achtung: `gegenprobe` verändert Dateien für Sekunden – nicht laufen lassen, während OpenCode arbeitet.

---

## Phase D – Review (lokales Modell)

1. Lab umschalten: Fenster 1 **Ctrl+C**, dann `bash start_eval.command` (ohne Gedächtnis, fairer Vergleich).
2. Prompt holen:
   ```bash
   python3 role-split/kette/kette.py prompt review <kurztitel>
   ```
3. Browser **neuer Chat**, Modell **Qwen3.6**, Reasoning **aus**, Prompt einfügen. Ans Ende schreiben:
   `Ergebnisse der maschinellen Prüfung: docs/projekt_management/pruefung_<datum>_<kurztitel>.md`
4. **Kontextanzeige beobachten.** Ab **80 %** sofort die Notbremse schicken (Abschnitt 5) – sonst geht beim
   Speichern alles verloren.
5. Urteil mechanisch nachrechnen (Dateinamen aus dem Chat übernehmen):
   ```bash
   python3 role-split/kette/kette.py urteil docs/projekt_management/verdict_<…>.md --anhaengen
   ```

**Fertig, wenn:** Verdikt-Datei existiert (oder das Kurzverdikt im Chat steht).

---

## Phase E – Externe Gegenprüfung (Claude)

Im Projekt-Chat „LLM-Lokal-Labor":
```
Kette <kurztitel> fertig, bitte gegenprüfen.
```
Mehr nicht – Claude liest Anforderung, Spec, Code, Tests, Prüfung und Verdikt selbst (MCP).
Hat das Review nur im Chat geantwortet: die Antwort mit hineinkopieren, Claude legt die Datei an.

**Ergebnis:** Freigabe, oder Befunde mit einem fertigen Nachbesserungs-Prompt für OpenCode.

---

## Phase F – Entscheidung

| Lage | Entscheidung | Was du tust |
|---|---|---|
| Review PASS **und** Gegenprüfung ohne hohen Befund | **Commit** | `git status --short` ansehen (nur Dateien dieser Aufgabe?), dann `git add -A && git commit -m "Kette <kurztitel>: <kurz was>"` |
| Ein hoher Befund – egal, was das Review sagt | **Nachbessern** | Prompt von Claude in OpenCode (`umsetzung`, Qwen3.6), danach wieder **Phase C**, dann **E**. Neues Review (D) nur bei größeren Änderungen. |
| Grundsätzlich falscher Ansatz / Spec falsch | **Verwerfen** | `git restore .` und `git clean -n` (zeigt, was gelöscht würde) → prüfen → `git clean -fd`; zurück zu **A** |

**Regeln, die immer gelten**
- Korrekturen macht **OpenCode**, nicht der Gegenprüfer (sonst prüft er seinen eigenen Code).
- Scheitert OpenCode **zweimal an derselben Stelle**, übernimmt Claude – und eine frische Instanz prüft.
- Hat die Aufgabe Außenwirkung: Sperre **vor** der Umsetzung, kein Test darf echt senden.
- Vor jeder Umsetzung ist der Stand committet (Spec-Commit = Rollback-Punkt).

---

## 5. Notbremsen und Störungen

**Notbremse Kontext (Review oder Spec ab 80 %)** – in denselben Chat:
```
Stopp, Kontext fast voll. KEIN Tool-Aufruf, nichts speichern, nichts lesen.
Antworte nur im Chat, maximal 15 Zeilen:
Zeile 1: Ergebnis: PASS / NACHBESSERN / FAIL – ein Satz Begründung
Dann je Befund eine Zeile: # | Schwere | Datei:Zeile | Befund (ein Satz)
Letzte Zeile: Nicht geprüft: Stichworte
```
Die Antwort an Claude geben (Phase E).

| Symptom | Ursache | Abhilfe |
|---|---|---|
| „Failed to parse tool call arguments … missing closing quote" | Kontext voll beim Speichern | neuer Chat, Reasoning aus; beim Review Notbremse |
| `error: the following arguments are required: kurztitel` | Kurztitel fehlt (leere Variable) | Kurztitel ausschreiben |
| `zsh: no such file or directory` | `<…>` mit eingetippt | Platzhalter ersetzen |
| `pruefen`: „Kein Commit 'Spec …' gefunden" | Commit-Nachricht anders | `git log --oneline -10`, dann `--commit <hash>` |
| OpenCode „Cannot connect to API" | Eval-Lauf, Provider zeigt auf 8091 | Provider „M4 direkt (8080)" |
| Web-UI: keine Datei-Tools | MCP-Eintrag fehlt / alter Chat | `+` → MCP servers → `http://127.0.0.1:8787/mcp`, Proxy-Toggle an; Seite neu laden, neuer Chat |
| `502 Upstream nicht erreichbar` direkt nach Start | Gedächtnis-Proxy startet noch | 30 s warten, neu laden |
| Modell schreibt endlos dieselbe Datei | Schleife | Esc, Stand notieren, neuer Anlauf |
| Leere `verdict_…md` und daneben `…_2.md` | MCP-Verdiktschutz | `_2` ist das echte Verdikt |
| `git status` zeigt `_vorlage_*.md` geändert | Modell hat Vorlage überschrieben | `git restore docs/projekt_management/_vorlage_*.md` |
| Speicher voll / Modell lädt nicht | zwei große Modelle / Qwen3-Next parallel | Lab beenden, `sudo purge`, neu starten |
| Montag 08:00 | Scout-Lauf braucht den Router | keine Langläufe über Montagmorgen |

---

## 6. Spickzettel (eine Kette komplett)

```bash
cd ~/PycharmProjects/llama-server && source .venv/bin/activate && git status --short
# A  start_rollen | neuer Chat | Qwen3.8, Reasoning aus
#    "@review Neue Aufgabe <kurztitel>: …"  →  Rückfragen beantworten  →  "Spec schreiben"  →  Spec-Checkliste
python3 role-split/kette/kette.py quellen <kurztitel>
git add docs/projekt_management/*_<kurztitel>.md && git commit -m "Spec <kurztitel>"
# B
python3 role-split/kette/kette.py prompt umsetzung <kurztitel>     # → opencode, Qwen3.6, Agent umsetzung
# C
python3 role-split/kette/kette.py pruefen <kurztitel>
# D  Ctrl+C, start_eval | neuer Chat | Qwen3.6, Reasoning aus | ab 80 % Notbremse
python3 role-split/kette/kette.py prompt review <kurztitel>
python3 role-split/kette/kette.py urteil docs/projekt_management/verdict_<…>.md --anhaengen
# E  Projekt-Chat: "Kette <kurztitel> fertig, bitte gegenprüfen."
# F  Freigabe → git add -A && git commit -m "Kette <kurztitel>: …"
#    Nachbessern → Claude-Prompt in OpenCode → zurück zu C → E
```

---

## 7. Notizen je Kette und Stand

Notiere je Kette (Claude übernimmt das in die Projektdokumente, wenn du es im Chat nennst):
Start/Ende je Phase, Modelle, deine Eingriffe, welche Befunde das Review fand und welche erst die Gegenprüfung.

**Ziel (entschieden 22.10.):** Die Kette soll ohne externe Prüfung verlässlich werden.
**Schwelle:** 3 Ketten in Folge, in denen kein kritischer Fehler am lokalen Review vorbei bis vor den Commit rutscht.
**Stand:** 0/3 (K4, K5 verfehlt). Nächste Verbesserungen am Review: ein Review-Paket statt vieler Dateien,
abschnittsweises Speichern, Pflichtfragen („nur im Prompt verlangt oder im Code erzwungen?", „leerer/abweichender Fall?",
„kann die Absicherung selbst ins Leere laufen?"). Danach wird neu gezählt; nach 3 weiteren Ketten ohne 3/3 gilt
„lokal bauen, extern prüfen" als Ergebnis.
Details: Projektdokument `standort-kette.md`.
