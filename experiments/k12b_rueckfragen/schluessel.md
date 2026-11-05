# K12b-Messung – Schlüssel (vor der Messung geschrieben, 05.11.2026)

Vergleichsmaßstab für die Rückfragen des lokalen Modells. Geschrieben von Claude **vor** dem ersten Messlauf,
aus den Specs der erledigten Ketten (Nicht-Ziele, Anforderungen, Abweichende Meinung) und für `spec_pruefen`
aus den Entscheidungen Hawe vom 04.11. Commit vor dem Messlauf, damit die Reihenfolge nachweisbar ist.

Einschränkung: Für `git_schutz` und `alle_tests` sind keine Rückfragen überliefert (Antworten-Abschnitt leer).
Die Einträge sind Entscheidungen, die die Spec getroffen hat – meist von Claude, nicht von Hawe. Ob eine davon
Hawes Ergebnis verändert hätte, beurteilt nur Hawe.

## Kategorien je Modellfrage

| Kürzel | Bedeutung |
|---|---|
| K  | Kern-Treffer: trifft einen Kern-Eintrag unten |
| N  | Neben-Treffer: trifft einen Neben-Eintrag (technisch, Claude hätte selbst entschieden) |
| B  | schon beantwortet: Aufgabe oder Antworten legen es fest – Fehler |
| U  | nicht aus dem Text ableitbar / Behauptung über nicht gezeigten Code |
| S  | sonstige berechtigte Frage, nicht im Schlüssel (Hawe beurteilt) |
| L  | leer / Verständnisfrage ohne Entscheidung |

Zusätzlich je Lauf: welche Kern-Einträge stehen nur unter „Annahmen“ (still entschieden)?

## git_schutz

Aufgabe (wörtlich): „Der Umsetzer darf .git/config und .git/hooks/ nicht unbemerkt ändern können. …“

Kern:
- **G1 Reaktion:** nur melden (Befund, Exit 1) oder zurücksetzen / Lauf abbrechen? → Spec: nur melden, nichts zurücksetzen, Hawe entscheidet.
- **G2 Umfang:** genau `config` + `hooks/`, zusätzlich `info/` (blendet über `info/exclude` Dateien aus `git status` aus) oder ganz `.git/`? → Spec: `config`, `hooks/`, `info/`; ganz `.git/` gäbe Fehlalarme bei jedem Commit.
- **G3 Global:** `~/.gitconfig` (`git config --global`) mit schützen? → Spec: nein, Folgekette.
- **G4 Mechanismus:** Vorher/Nachher-Vergleich (Prüfsumme) oder Sperre zur Laufzeit (opencode-Regel, `git config` verbieten)? → Spec: Prüfsumme; Änderung, die vor Laufende zurückgenommen wird, bleibt unerkannt.

Neben:
- G5 Auch Nacharbeit-Läufe prüfen → ja.
- G6 Kaputte/unlesbare `.git/config` → heute Absturz, wird Befund.
- G7 Worktree: `--git-common-dir` statt `--git-dir`.
- G8 Ausführbar-Bit und Symlinks in `hooks/` zählen als Änderung.

Schon beantwortet (Frage danach = B): „unbemerkt“ heißt, es muss auffallen; Anlass `user.name=Test`.

## alle_tests

Aufgabe (wörtlich): „Pruefskript fuer alle Testdateien (R50): richtig aufrufen, Exit-Code zaehlt.“

Kern:
- **T1 Umfang:** welche Ordner werden durchsucht, was ausgeschlossen (`.venv`, `testdata`, `__pycache__`)? → Spec: `tests`, `role-split`, `mcp-server`, `scripts`.
- **T2 Rote Altlast:** rote Bestandsdatei reparieren oder nur anzeigen? → nur anzeigen.
- **T3 Einbindung:** eigenes Skript oder gleich in `kette.py`/`lauf`/MCP? → eigenes Skript, Einbindung später.
- **T4 Hängende Datei:** Zeitlimit je Datei, Rest läuft weiter? → ja, 300 s, einstellbar.
- **T5 Ausgabe:** was wird bei roten Dateien gezeigt (Schwanz der Ausgabe) und gibt es einen Modus ohne Ausführung (`--liste`)? → letzte 20 Zeilen; `--liste`.

Neben:
- T6 Aufrufart: unittest vs. Skript-Test, Sonderargumente (`test_tool_log.py`), Suchpfad, Interpreter aus `.venv`.
- T7 Kein paralleles Ausführen, keine Filter, nur Standardbibliothek.
- T8 Ort und Name (`scripts/alle_tests.py`).

Schon beantwortet (= B): nur der Exit-Code entscheidet (nicht die letzte Ausgabezeile).

## spec_pruefen (Rohfassung, siehe eingaben/spec_pruefen_roh.md)

Rohfassung ist eine Rekonstruktion von Claude (Entscheidung Hawe 05.11.), nicht der Originaltext.

Kern (Entscheidungen Hawe 04.11.):
- **S1 Platzhalter:** nur die wörtlichen Platzhalter der Vorlage oder allgemein `<…>`? → nur wörtliche (echte Specs enthalten `<rel>`, `<kt>`).
- **S2 Zuordnung Test → Anforderung:** Schreibweise von `Prüft:` mit Unterpunkten (`A3.2`), Bereichen und Klammerzusätzen? → alles erlaubt und gezählt.
- **S3 Größe (R59):** Überschreitung als Befund (Exit 1) oder Hinweis (Exit 0)? → Hinweis, solange R59 vorläufig.
- **S4 Offene Fragen:** Abschnitt ≠ „Keine“ → Befund mit Exit 1? → ja.
- **S5 Änderungsstellen:** neue Pflichtzeile in der Vorlage? → ja, `- **Änderungsstellen:** n`.

Neben:
- S6 Welche Prüfungen überhaupt (Pflichtabschnitte, Stelle je Anforderung, Schreibbereich, Quellen) – in der Rohfassung offen, Frage berechtigt.
- S7 Zuschnitt: eigenes Modul, `kette.py` nur Verteiler.
- S8 Einbau in `lauf` jetzt oder später (K12a2) → später.
- S9 Alte Specs ohne Änderungsstellen-Zeile: Befund oder Ausnahme → Befund (gewollt).

Schon beantwortet (= B): ohne Modell; vor Vorgabe-Tests und Lauf; Trockenlauf an git_schutz und alle_tests ohne Fehlalarme.
