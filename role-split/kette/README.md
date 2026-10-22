# Kette: Spec → Umsetzung → Review (→ Tiefenprüfung)

Werkzeug und Vorlagen, damit die Kette weniger am Urteil der Modelle hängt und
mehr an Dingen, die Hawe selbst prüfen kann. Anlass: Live-Test 17.10.
(siehe Projekt-Doku `claude/kette-email-runde2.md`): Der Code war gut, aber Befunde
wurden zu niedrig eingestuft, Tests haben nichts gemessen oder wurden ausgetauscht,
und ein Test hat echt gesendet.

## Ablauf

**Gebrauchsanweisung mit allen Befehlen, Entscheidungsregeln und Notbremsen: [RUNBOOK.md](RUNBOOK.md)**

| Schritt | Wo | Prompt holen |
|---|---|---|
| 1 Aufgabe + Spec | Web-UI, `start_rollen`, neuer Chat | `@review Neue Aufgabe <kurztitel>: <Text>` – der Rollen-Proxy schreibt Aufgabe und deine Antworten wörtlich nach `anforderung_<datum>_<kurztitel>.md` und gibt die Spec-Anweisungen mit; ohne Web-UI: `kette.py anforderung …` + `prompt spec …` |
| – | Spec lesen; Außenwirkung? → **Sperre vor der Umsetzung** einbauen; `git commit` | |
| 2 Umsetzung | OpenCode, Agent „umsetzung" | `… prompt umsetzung <kurztitel> --commit <rücksetzpunkt>` (ohne `--commit`: HEAD, mit Warnung) |
| – | **Prüfen:** `… abgleich <kurztitel>`, `python3 -m unittest -v tests/test_<kurztitel>.py` und `… gegenprobe <kurztitel> --commit <rücksetzpunkt>` | |
| 3 Review | Web-UI, neuer Chat | `… prompt review <kurztitel>` |
| – | **Prüfen:** `… urteil docs/projekt_management/verdict_….md --anhaengen` | |
| 4 Tiefenprüfung (optional, Eval) | `start_eval`, Modell laden, MCP aus/an, neuer Chat | `… prompt tief <kurztitel>` |

`prompt` kopiert den Text am Mac gleich in die Zwischenablage (pbcopy).

`prompt` nimmt ohne `--datum` das Datum der vorhandenen Spec (nicht „heute“). Review und Tiefenprüfung prüfen zuerst die Spec gegen die Anforderung, dann Code und Tests gegen die Anforderung (seit 20.10.: In Kette 4 bestätigten alle Reviewer eine falsche Spec; mit der Anforderung im Auftrag fanden Qwen3.6 und Qwen3.8 den Defekt).

## Was die Prüfbefehle tun

- **`abgleich`**: Vergleicht die Test-IDs (T1, NT1 …) der Spec mit dem Handover:
  fehlt, unter „Nicht getestet", **anders** (Titel passt nicht, Hinweis auf Austausch)
  oder extra. Prüft, ob `tests/test_<kurztitel>.py` je Test eine Methode `test_<id>` hat.
  Auf das Handover vom 17.10. angewandt, meldet es den ausgetauschten Test NT9.
- **`abgleich`** prüft zusätzlich jede Testmethode: **ohne assert/fail** (kann nicht rot werden) oder **doppelt** (gleicher Rumpf wie eine andere). Beides war am 18.10. in T9.
- **`gegenprobe`**: Setzt jede seit dem Rücksetzpunkt geänderte Code-Datei **einzeln** auf den alten Stand zurück, lässt das Testskript laufen und stellt danach wieder her (Prüfsumme, eigener Bytecode-Cache). Je Test: `rot ← datei` (prüft die Änderung), `GRUEN` (prüft Bestehendes oder nichts), `LADEN` (rot nur, weil das Testskript ohne die neue Datei gar nicht lädt, schwacher Beleg). Achtung: verändert die Dateien für Sekunden; nicht laufen lassen, während launchd oder ein Agent arbeitet.
- **`urteil`**: Ein Befund mit „ja" bei Datenverlust / Unbemerkt / Harte Vorgabe ist
  „hoch". Ein offener Befund „hoch" oder eine Anforderung „teilweise/nicht" ergibt
  NACHBESSERN. Die Regel **verschärft nur**: Ein strengeres Modellurteil bleibt stehen.
  Verdikte im alten Format (ohne die drei Spalten) werden nur übernommen, nicht geprüft.

## Was das nicht ersetzt

Die Regeln prüfen Form und Einstufung, nicht, ob ein Befund **fehlt** oder eine Anforderung
die richtige ist. Dafür bleibt eine zweite Stimme nötig (Tiefenprüfung, frische Instanz,
Claude). Ein Modell kann auch bei den drei Fragen falsch „nein" sagen. Dann hilft nur
Nachlesen.

## Mitgebaut (17.10.)

- `docs/projekt_management/_vorlage_spec.md`: neu, mit Außenwirkung/Sperre, Fehlerpfad-Tabelle, Testplan mit IDs.
- `_vorlage_handover.md`: Testtitel exakt, unittest-Ausgabe, Abschnitte Außenwirkung und „Hawe muss ausführen".
- `_vorlage_verdict.md`: Befundtabelle mit den drei ja/nein-Spalten.
- `role-split/roles/review.md`: Spec nach Vorlage; Schwere über die drei Fragen, „vorbestehend" senkt nicht.
- `.opencode/agents/umsetzung.md`: Tests als Skript, kein Austausch, keine Außenwirkung, auch nicht nach Freigabe.
- MCP-Server: `verdict_*.md` wird nie überschrieben oder gelöscht (wirkt nach MCP-Neustart).

Selbsttest: `python3 role-split/kette/test_kette.py`

Mode B: Lab, berührt AskValentinAI nicht.
