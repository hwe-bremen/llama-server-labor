# Kette git_schutz (01.11.2026)
Aufgabe: `umsetzung-auto` meldet laut (Befund, Exit 1), wenn der Umsetzer `config`, `hooks/` oder `info/` im Git-Verzeichnis ändert; kein Absturz mehr bei kaputter `.git/config`.
Ergebnis: bestanden. Tests und Referenz von Claude, Code vom 35B im Erstlauf ohne Nacharbeit und ohne Patch, gleichwertig zur Referenz; komplett aus der Chat-UI (`kette_lauf`, `kette_status`, `kette_commit`). Spec `7f95f7d`, Commit `76f6c5a`.

## Anlass
27.10. (K10-Lauf): Der Umsetzer setzte `user.name=Test` in `.git/config` des echten Repos; ~40 Commits liefen als „Test“, entdeckt erst 29.10. über `kette_commit`. Die Schreibbereich-Prüfung beruht auf `git status` – und das zeigt `.git/` nie.

## Messung
| Schritt | Modell | Dauer | Ergebnis |
|---|---|---|---|
| Spec, Vorgabe-Tests, Referenz | Claude | – | 1 Datei / 4 Anforderungen / 8 Tests; vorab 8/8 rot; Referenz 8/8 grün; Mutanten 24/24 (auch fremde Arten: zurücksetzen, ganzes `.git/`, Präfix `hooks_alt`, `--git-dir`, Schnappschuss zu spät) |
| Erstlauf `umsetzung-auto` | 35B | 9:32 | Exit 0, 9 Änderungsstellen, 38 Werkzeugaufrufe, Kontextspitze 57,6K von 64K; ein abgelehnter `grep` mit absolutem Pfad |
| `review-auto` | 35B | – | NACHBESSERN / PASS – der einzige „hohe“ Befund widerlegte sich im eigenen Text |
| `alle_tests` am Repo | – | ~40 s | 27 Dateien, 26 ok, 1 rot (Altlast `scout_kw`) |

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| `.git/config` vom Umsetzer geändert, Schreibbereich-Prüfung blind (27.10.) | Sicherung läuft ins Leere (Prüfung sieht nur, was `git status` zeigt) | Hawe, zwei Tage später über Commit-Autor |
| Bei kaputter `.git/config` Traceback in `umsetzung_auto` (`_git(...)` mit `check=True`), keine Protokollzeile | lautester Fall wird stillster | Claude (Code lesen vor der Spec) |
| Gesamturteil NACHBESSERN aus einem Befund, der „kein echter Fehler“ sagt | falscher Befund (R54/R56) | Claude (Befundtext gelesen) |
| Schnappschuss nach `git status` statt als erste Anweisung | Spec-Abweichung ohne Wirkung (`git status` schreibt nicht in `config`/`hooks`/`info`) | Claude (Diff) – hingenommen |

## Regeln daraus
- R59 (vorläufig) → LERNREGELN.md
- R60 → LERNREGELN.md
- Umgesetzt in `role-split/kette/kette.py`: `GIT_SCHUTZ`, `_git_verzeichnis`, `_git_schutz`, Befund + Protokoll-Unterzeile + Zeile `Git-Schutz: …` in `umsetzung_auto`

## Sonst bemerkenswert
- Erste Kette, in der der 35B ohne Nacharbeit und ohne Patch durch Claude gleichwertig zur Referenz lieferte. Vergleich: K13a ~20 Stellen → zwei Läufe à ~25 min + Rest Claude; hier 9 Stellen → 9:32.
- Dieser Lauf selbst war noch ungeschützt (alte `kette.py`, R50) – `.git/` danach von Hand geprüft: sauber.
- Bewusst offen (Spec „Abweichende Meinung“): `git config --global` (`~/.gitconfig`) und Änderungen, die der Umsetzer vor Laufende selbst zurücknimmt. Kandidat: opencode-Regel, die `git config` für den Umsetzer verbietet.
- Kette ohne K-Nummer; Bedienung aus der Chat-UI brauchte eine Rückfrage („wie rufe ich `kette_lauf` auf?“) – Kurzanleitung gehört in die Übergabe.
