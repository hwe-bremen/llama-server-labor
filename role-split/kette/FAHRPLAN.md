# Fahrplan: eine Kette Schritt für Schritt (Stand 20.10.2026)

Alle Befehle aus der Projektwurzel `~/PycharmProjects/llama-server`, mit aktivierter `.venv`.
`K=<kurztitel>` steht für den Kurztitel der Aufgabe (nur Kleinbuchstaben, Ziffern, `_`), z. B. `scout_feeds_pruefen`.
Spitze Klammern `<…>` im Fahrplan sind Platzhalter – **nie** so ins Terminal tippen (zsh liest `<` als Umleitung).

```sh
cd ~/PycharmProjects/llama-server && source .venv/bin/activate
K=scout_feeds_pruefen          # eigenen Kurztitel einsetzen
```

Notiere je Schritt: Start- und Endzeit, Modell, deine Eingriffe (Antworten, Freigaben, Korrekturen).

---

## Schritt 1 – Aufgabe im Chat geben, Spec entsteht (Web-UI, ca. 30–60 min)

1. Lab starten: `bash start_rollen.command` → Browser `http://127.0.0.1:8092`, **neuer Chat**, Modell **Qwen3.8**, Reasoning **aus**.
2. Aufgabe einfach hinschreiben – Kurztitel nach „Neue Aufgabe", dann Doppelpunkt:
   ```
   @review Neue Aufgabe scout_feeds_pruefen: Die GitHub-Feeds im Scout liefern seit Wochen nichts mehr. Ich will wissen warum und dass ein Ausfall künftig auffällt.
   ```
   Der Rollen-Proxy schreibt deinen Text **wörtlich** nach `docs/projekt_management/anforderung_<datum>_scout_feeds_pruefen.md`
   (verbindliche Vorgabe für alle Schritte) und gibt dem Modell die Spec-Anweisungen automatisch mit.
3. Das Modell diskutiert und stellt höchstens eine Rückfrage. **Einfach im Chat antworten** – jede deiner Antworten
   wird mit der Frage davor wörtlich an die Anforderung angehängt. Kommandos wie „Spec schreiben" nicht.
4. Wenn die Diskussion steht: im Chat **„Spec schreiben"**.
5. Kontrolle (optional): `cat docs/projekt_management/anforderung_*_$K.md`

Ohne Web-UI (Ausnahme): `python3 role-split/kette/kette.py anforderung $K --aufgabe "…"` und `… prompt spec $K` wie bisher.

6. **Spec lesen** (`docs/projekt_management/spec_<datum>_$K.md`), Checkliste:
   - [ ] „Außenwirkung und Sperre": Kann die Aufgabe Mails, Netz, echte Daten oder den Schlüsselbund berühren? Ist eine **technische Sperre** genannt (z. B. `SCOUT_ALLOW_SEND`)? Fehlt sie → im Chat nachfordern, **vor** der Umsetzung einbauen.
   - [ ] „Offene Fragen": Stehen dort Einschränkungen gegenüber deiner Anforderung (Verlust, Doppelversand, „Restrisiko")? → Im selben Chat entscheiden (wird mitgeschrieben) und die Spec anpassen lassen.
   - [ ] Jeder Test hat ID, prüfbare Erwartung und keine Außenwirkung.
7. Spec committen und **Rücksetzpunkt notieren**:
   ```sh
   git add docs/projekt_management/spec_*_$K.md docs/projekt_management/anforderung_*_$K.md
   git commit -m "Spec $K"
   R=$(git rev-parse --short HEAD); echo "Rücksetzpunkt: $R"
   ```
   `$R` brauchst du in Schritt 2, 3 und 4. Steht es nicht mehr im Terminal: `git log --oneline -3`.

---

## Schritt 2 – Umsetzung (OpenCode, ca. 1 h mit Qwen3.6)

1. Prompt holen:
   ```sh
   python3 role-split/kette/kette.py prompt umsetzung $K --commit $R
   ```
2. OpenCode starten (`opencode`), Modell **Qwen3.6** (Provider „M4 mit Gedaechtnis" oder „direkt"), Agent **„umsetzung"** (Tab), Prompt einfügen.
3. **Nicht nachhelfen.** Freigaben für Shell-Befehle nur geben, wenn sie keine Außenwirkung haben; im Zweifel ablehnen.
4. Fertig, wenn das Handover `docs/projekt_management/handover_<datum>_$K.md` geschrieben ist. **Nicht committen.**

---

## Schritt 2b – Mechanische Prüfungen (Terminal, 5 min)

```sh
python3 role-split/kette/kette.py abgleich $K
python3 -m unittest -v tests/test_$K.py
python3 role-split/kette/kette.py gegenprobe $K --commit $R
```

Lesen:
- `abgleich`: „Keine Abweichung" = jeder Spec-Test hat Titel und Methode. **Prüft nur Titel**, nicht ob der Test das Richtige misst.
- `unittest`: alles grün? Rot → Befund für die Nachbesserung.
- `gegenprobe`: `rot` = Test misst die Änderung (gut). `GRUEN` = Test wird auch mit altem Code grün → prüft Bestehendes oder **nichts**. Jeden GRUEN-Test im Review ansprechen lassen.

---

## Schritt 3 – Review (Web-UI, ca. 30 min mit Qwen3.6)

1. Lab für vergleichbare Reviews: Lab beenden (Strg+C), `bash start_eval.command` (ohne Gedächtnis, `git_log` aus) → `http://127.0.0.1:8092`, eingebaute Tools aus.
2. Prompt holen:
   ```sh
   python3 role-split/kette/kette.py prompt review $K --commit $R
   ```
3. **Neuer Chat**, Modell **Qwen3.6** (im Prozess-Test der beste Reviewer), einfügen, abschicken.
4. Urteil mechanisch prüfen – Dateinamen aus der UI übernehmen (Kürzel z. B. `qwen36-27b`, evtl. mit `_2`):
   ```sh
   ls docs/projekt_management/verdict_*_${K}_*.md
   python3 role-split/kette/kette.py urteil docs/projekt_management/verdict_<datum>_${K}_qwen36-27b.md --anhaengen
   ```
   „Es gilt: …" ist das maßgebliche Urteil (die Regel hebt zu niedrig eingestufte Befunde an).
5. Optional zweiter Reviewer: neuer Chat, **Qwen3.8**, Reasoning **aus** (mit Reasoning lief der Kontext in Kette 4 voll).

---

## Schritt 4 – Tiefenprüfung (optional)

Nur für Eval-Zwecke oder kritische Änderungen. Wie Schritt 3 mit `prompt tief $K --commit $R`.

---

## Schritt 5 – Externe Gegenprüfung (vor dem Commit)

Das lokale Review ist Zweitmeinung, keine Freigabe. In allen bisherigen Ketten fand erst Ausführen oder die externe Stimme den kritischen Defekt.
Claude im Projekt-Chat: „Kette $K fertig, bitte gegenprüfen" – mit Rücksetzpunkt `$R`. Claude liest Anforderung, Spec, Diff, Tests und Verdikt.

---

## Schritt 6 – Entscheidung

**PASS** (und Gegenprüfung ohne hohen Befund):
```sh
git add -A && git status --short      # prüfen: nur Dateien dieser Aufgabe?
git commit -m "Kette $K: Umsetzung + Handover + Verdikt"
```

**NACHBESSERN:**
1. Befundliste aus Verdikt/Gegenprüfung an OpenCode, Agent „umsetzung", z. B.:
   „Nachbesserung zu docs/projekt_management/handover_<datum>_$K.md. Befunde: 1) … 2) … Nur ergänzen, keine bestehenden Tests löschen oder umbauen. Handover um Abschnitt ‚Nachbesserung' ergänzen."
2. Danach **erneut Schritt 2b** (abgleich, unittest, gegenprobe) und ein **neues Review** (neuer Chat).
3. Erst dann Schritt 6 PASS.

**FAIL:** nichts committen; Umsetzung verwerfen (`git restore . && git clean -n` → prüfen → `git clean -fd`), Spec überarbeiten, ab Schritt 1.

---

## Stolpersteine (gesammelt)

| Problem | Abhilfe |
|---|---|
| `zsh: no such file or directory: kürzel` | `<…>` ist Platzhalter, echten Namen einsetzen. |
| Prompt nennt falsches Datum oder falschen Commit | `--datum` / `--commit $R` angeben; `prompt` warnt, wenn es HEAD nimmt. |
| Verdikt als leere Datei + `_2` | Bekannter Effekt des MCP-Verdiktschutzes; `_2` ist das echte Verdikt, leere Datei löschen. |
| Reviewer hat `_vorlage_*.md` geändert | `git restore docs/projekt_management/_vorlage_verdict.md` vor dem Commit; `git status` zeigt es. |
| Chat bleibt hängen, „Context 100 %" | Neuer Chat; Reasoning aus; Verdikt ggf. „im Chat ausgeben" lassen. |
| Modell wiederholt endlos denselben Schritt | Abbrechen (Esc), Stand notieren, ggf. neuer Anlauf. |
| Lab und Qwen3-Next gleichzeitig | Geht nicht (Speicher). Vor Qwen3-Next Lab beenden, ggf. `sudo purge`. |
| Montag 8:00 läuft der Scout | Vorher Lab-Router laufen lassen bzw. keine Langläufe über Montagmorgen. |

## Kurzfassung (Spickzettel)

```sh
K=<kurztitel>
bash start_rollen.command                                   # Spec: Qwen3.8, Reasoning aus
# Web-UI: "@review Neue Aufgabe <kurztitel>: …" – Antworten im Chat werden mitgeschrieben – "Spec schreiben"
git add docs/projekt_management/*_$K.md && git commit -m "Spec $K" && R=$(git rev-parse --short HEAD)
python3 role-split/kette/kette.py prompt umsetzung $K --commit $R            # OpenCode, Qwen3.6, Agent umsetzung
python3 role-split/kette/kette.py abgleich $K
python3 -m unittest -v tests/test_$K.py
python3 role-split/kette/kette.py gegenprobe $K --commit $R
bash start_eval.command                                     # Review: Qwen3.6, neuer Chat
python3 role-split/kette/kette.py prompt review $K --commit $R
python3 role-split/kette/kette.py urteil docs/projekt_management/verdict_….md --anhaengen
# externe Gegenprüfung (Claude) → PASS: commit | NACHBESSERN: Befunde an OpenCode, 2b + Review wiederholen
```
