# Runbook: die Kette (Stand 25.10.2026)

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
| D Review | Qwen3.6-35B-A3B (Web-UI, neuer Chat) | `verdict_…` | 15–25 min |
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
   **Immer als letzten Satz anhängen** (Kontext schonen, siehe Kasten unten):
   ```
   Lies keine großen Dateien ganz. Erst search_files (liefert Zeilennummern), dann read_file mit start_line/end_line. Sag vorher, was du lesen willst und warum.
   ```
2. Das Modell liest Code, nimmt Stellung, stellt Rückfragen. **Einfach im Chat antworten** – jede Antwort
   wird samt Frage an die Anforderung angehängt. Entscheidungen hier treffen, nicht später.
3. Wenn alles geklärt ist: **Kontextanzeige ansehen.**
   - unter ~50 %: im selben Chat **„Spec schreiben"**.
   - ab ~50 %: **Phase teilen** (Kasten unten) – die Spec in einem frischen Chat schreiben lassen.

> **Kasten: Kontext schonen in Phase A** (eingeführt 25.10. nach K8-Spec, Kontext voll)
> Warum: In der Web-UI bleibt jedes Werkzeugergebnis im Kontext. `read_file` ohne Bereich liest die *ganze* Datei
> (z. B. `kette.py` ≈ 12 000 Token). Rückfragen-Runde + Lesen + Spec-Text passen dann nicht in 64K.
> Seit 25.10. kann `read_file` Ausschnitte: `start_line`/`end_line` (wirkt nach Lab-Neustart); bei Dateien > 300 Zeilen
> hängt es ohne Bereich einen Hinweis an.
> 1. **Gezielt lesen:** Satz oben an die Aufgabe hängen; liest das Modell trotzdem große Dateien ganz → Stopp, „nur search_files + read_file mit Zeilenbereich".
> 2. **Phase teilen:** Deine Antworten stehen schon in der Anforderung (der Proxy hängt sie an). Neuer Chat, Qwen3.8, Reasoning aus:
>    ```
>    @review Spec schreiben für <kurztitel>: Lies docs/projekt_management/anforderung_<datum>_<kurztitel>.md – dort stehen Aufgabe, alle Rückfragen und meine Antworten. Keine neuen Rückfragen außer bei echtem Widerspruch. Lies Code nur gezielt: search_files, dann read_file mit start_line/end_line. Schreib die Spec abschnittsweise: write_file für den Kopf, danach append_file je Abschnitt.
>    ```
>    (Noch wenig erprobt – greift die Rolle nicht, Claude fragen.)
> 3. **Abschnittsweise schreiben:** Korrekturen an der Spec mit `replace_in_file`, nie die ganze Spec neu schreiben lassen.
> 4. **Mehr Kontext (131K + KV-Cache q8_0)** erst, wenn 1–3 nicht reichen – kostet Speicher und Tempo, vorher messen.
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
2. Prompt holen – baut dabei automatisch das **Review-Paket** `review_paket_<datum>_<kurztitel>.md`
   (Anforderung, Spec-Auszug, Code-Diff, Testliste, Handover-Abweichungen, Kurzfassung der Prüfung – eine Datei
   statt sechs) und zeigt dessen Größe:
   ```bash
   python3 role-split/kette/kette.py prompt review <kurztitel>
   ```
   Steht dort `WARNUNG: Paket > 80000 Zeichen`: Claude fragen, ob das Review in Teilen laufen soll.
3. **Lauf 1 (Anforderung):** Browser **neuer Chat**, Modell **Qwen3.6-35B-A3B**, Reasoning **aus**, Prompt einfügen,
   abschicken. Der Prompt enthält die sechs Pflichtfragen und verlangt ein knappes Verdikt, das **abschnittsweise**
   gespeichert wird (`write_file`, dann `append_file`).
4. **Lauf 2 (Betrieb, anderer Blickwinkel):** neuer Chat, gleiches Modell, Prompt holen mit
   ```bash
   python3 role-split/kette/kette.py prompt review2 <kurztitel>
   ```
   Lauf 2 sucht gezielt, was Lauf 1 typischerweise übersieht: Test-Attrappen statt echter Abhängigkeiten (LLM, Netz,
   Postfach), Eingaben, die bei jedem Lauf erneut scheitern, Widersprüche zwischen Sätzen der Anforderung, ersten echten
   Einsatz. Er liest Lauf 1 nicht. (Einführung 23.10. nach K6: beide Läufe zusammen fanden alle hohen Befunde.)
5. **Kontextanzeige beobachten.** Ab **80 %** die Notbremse schicken (Abschnitt 5).
6. **Zusammenführen – mechanisch, kein dritter Modell-Lauf:**
   ```bash
   python3 role-split/kette/kette.py zusammenfuehren docs/projekt_management/verdict_<…>.md docs/projekt_management/verdict_<…>_betrieb.md
   ```
   Schreibt `gesamt_<datum>_<kurztitel>.md` mit allen Befunden beider Läufe; ein hoher Befund in irgendeinem Lauf
   (oder „ja" bei Datenverlust/Unbemerkt/Harte Vorgabe) ergibt NACHBESSERN.

**Fertig, wenn:** `gesamt_…`-Datei existiert (oder ein Kurzverdikt im Chat steht).

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

## Phase G – Learnings (nach dem Commit, 10 min)

Ziel: Das Wissen aus der Kette geht nicht verloren und wirkt in der nächsten Kette mit.
Ort: `docs/learnings/` (Aufbau und Form: `docs/learnings/README.md`).

1. Projekt-Chat: **„Kette <kurztitel> committet, bitte Learnings entwerfen."**
   Claude schreibt `docs/learnings/kette_<kurztitel>.md` (was durchrutschte, Fehlerklasse, gefunden durch, Regel)
   und schlägt neue oder geänderte Regeln für `LERNREGELN.md` vor.
2. **Du gibst frei** (oder streichst). Faustregel: Neue Regel nur für wiederkehrende oder teure Fehler;
   `LERNREGELN.md` bleibt unter ~100 Zeilen – lieber eine alte Regel schärfen als eine neue anhängen.
3. Committen:
   ```bash
   git add docs/learnings/ && git commit -m "Learnings <kurztitel>"
   ```

Hinweis: Proben, die bekannte Defekte als Prüfstein nutzen, sperren `docs/learnings` per `MCP_DENY` – sonst liest der Reviewer die Lösung.
(Ab K8 geplant: `kette.py prompt` gibt `LERNREGELN.md` automatisch in Spec- und Review-Prompts mit.)

---

## 5. Notbremsen und Störungen

**Notbremse Kontext Spec (ab 80 %)** – in denselben Chat, rettet den Stand:
```
Stopp, Kontext fast voll. Nichts mehr lesen. Speichere jetzt deinen Stand nach
docs/projekt_management/spec_<datum>_<kurztitel>.md: erst write_file mit Kopf und den Abschnitten, die fertig sind,
dann je weiterer Abschnitt append_file. Unfertiges als „OFFEN: …" markieren.
```
Danach weiter mit **Phase teilen** (Kasten in Phase A): neuer Chat liest Anforderung + diese Spec-Datei und ergänzt nur die offenen Abschnitte.
Antwortet der Chat gar nicht mehr: deine Antworten auf die Rückfragen stehen trotzdem in der Anforderung → direkt Phase teilen.

**Notbremse Kontext Review (ab 80 %)** – in denselben Chat:
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
| Spec-Chat: Kontext voll, bevor die Spec steht | ganze Dateien gelesen, lange Rückfragen-Runde | Notbremse Spec, dann Phase teilen (Phase A, Kasten) |
| `error: the following arguments are required: kurztitel` | Kurztitel fehlt (leere Variable) | Kurztitel ausschreiben |
| `zsh: no such file or directory` | `<…>` mit eingetippt | Platzhalter ersetzen |
| `pruefen`: „Kein Commit 'Spec …' gefunden" | Commit-Nachricht anders | `git log --oneline -10`, dann `--commit <hash>` |
| OpenCode „Cannot connect to API" | Eval-Lauf, Provider zeigt auf 8091 | Provider „M4 direkt (8080)" |
| Web-UI: keine Datei-Tools | MCP-Eintrag fehlt / alter Chat | `+` → MCP servers → `http://127.0.0.1:8787/mcp`, Proxy-Toggle an; Seite neu laden, neuer Chat |
| `502 Upstream nicht erreichbar` direkt nach Start | Gedächtnis-Proxy startet noch | 30 s warten, neu laden |
| Modell schreibt endlos dieselbe Datei | Schleife | Esc, Stand notieren, neuer Anlauf |
| Leere `verdict_…md` und daneben `…_2.md` | MCP-Verdiktschutz | `_2` ist das echte Verdikt; seit `append_file` sollte das nicht mehr nötig sein |
| Modell meldet „ist eine Vorgabe der Kette … nie geschrieben" | will Vorlage/Anforderung/Quellen ändern | richtig so – im Chat sagen, es soll die Spec bzw. das Verdikt ändern |
| Modell kennt `append_file` nicht | MCP-Server läuft noch mit altem Stand | Lab neu starten, in der Web-UI MCP-Eintrag aus/an, Seite neu laden, neuer Chat |
| `git status` zeigt `_vorlage_*.md` geändert | Modell hat Vorlage überschrieben | `git restore docs/projekt_management/_vorlage_*.md` |
| Speicher voll / Modell lädt nicht | zwei große Modelle / Qwen3-Next parallel | Lab beenden, `sudo purge`, neu starten |
| Montag 08:00 | Scout-Lauf braucht den Router | keine Langläufe über Montagmorgen |

---

## 6. Spickzettel (eine Kette komplett)

```bash
cd ~/PycharmProjects/llama-server && source .venv/bin/activate && git status --short
# A  start_rollen | neuer Chat | Qwen3.8, Reasoning aus
#    "@review Neue Aufgabe <kurztitel>: … Lies keine großen Dateien ganz …"  →  Rückfragen beantworten
#    →  Kontext < 50 %: "Spec schreiben" | sonst neuer Chat: "@review Spec schreiben für <kurztitel>: …"  →  Spec-Checkliste
python3 role-split/kette/kette.py quellen <kurztitel>
git add docs/projekt_management/*_<kurztitel>.md && git commit -m "Spec <kurztitel>"
# B
python3 role-split/kette/kette.py prompt umsetzung <kurztitel>     # → opencode, Qwen3.6, Agent umsetzung
# C
python3 role-split/kette/kette.py pruefen <kurztitel>
# D  Ctrl+C, start_eval | Qwen3.6-35B-A3B, Reasoning aus | Lauf 1: prompt review | Lauf 2 (neuer Chat): prompt review2
python3 role-split/kette/kette.py prompt review <kurztitel>
python3 role-split/kette/kette.py zusammenfuehren docs/projekt_management/verdict_<…>.md docs/projekt_management/verdict_<…>_betrieb.md
# E  Projekt-Chat: "Kette <kurztitel> fertig, bitte gegenprüfen."
# F  Freigabe → git add -A && git commit -m "Kette <kurztitel>: …"
#    Nachbessern → Claude-Prompt in OpenCode → zurück zu C → E
# G  Projekt-Chat: "Kette <kurztitel> committet, bitte Learnings entwerfen." → freigeben → git commit "Learnings <kurztitel>"
```

---

## 7. Notizen je Kette und Stand

Notiere je Kette (Claude übernimmt das in die Projektdokumente, wenn du es im Chat nennst):
Start/Ende je Phase, Modelle, deine Eingriffe, welche Befunde das Review fand und welche erst die Gegenprüfung.

**Ziel (entschieden 22.10.):** Die Kette soll ohne externe Prüfung verlässlich werden.
**Schwelle:** 3 Ketten in Folge, in denen kein kritischer Fehler am lokalen Review vorbei bis vor den Commit rutscht.
**Stand:** 0/3 (K4, K5 verfehlt). Seit 22.10. im Review: Review-Paket statt vieler Dateien, abschnittsweises Speichern
(`append_file`), sechs Pflichtfragen (erzwungen oder nur verlangt? leerer/abweichender Fall? markiert, aber nie gezeigt?
läuft die Absicherung selbst ins Leere? widersprüchliche Anweisungen? stimmt jeder Satz der Anforderung?). **Ab K6 wird neu gezählt;** nach 3 Ketten ohne 3/3 gilt
„lokal bauen, extern prüfen" als Ergebnis.
Details: Projektdokument `standort-kette.md`.
