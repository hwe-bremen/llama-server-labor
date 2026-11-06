# K12c-Messung – Schlüssel (vor der Messung geschrieben, 06.11.2026)

Vergleichsmaßstab für die Spec-Entwürfe des lokalen Modells. Geschrieben von Claude **vor** dem ersten Messlauf aus
den Specs der drei Ketten (`git_schutz` 7f95f7d, `spec_pruefen` 031d296, `lauf_spec_pruefen` 2b63547) und den
Entscheidungen Hawes. Commit vor dem Messlauf, damit die Reihenfolge nachweisbar ist. Die Messpunkte (Ketten,
Antworten statt Live-Rückfragen, keine Zweitbewertung vorab) hat Hawe am 06.11. Claude überlassen.

## Ablauf je Lauf (siehe messung.py)

1. **Schritt 1 (Modell):** Anforderung + Antworten + Projektkontext vom Stand vor der Spec → Rückfragen (nur
   Auftraggeber-Entscheidungen), Annahmen, Quellen-Vorschlag.
2. **Schritt 2 (Skript):** Quellen wörtlich vom selben Stand holen (`git show`), nicht auflösbare zählen.
3. **Schritt 3 (Modell):** Spec-Entwurf nach der Vorlage, ohne Testcode.
4. **Schritt 4 (Skript):** `spec_pruefen.pruefe` am Entwurf; Quellen-Abschnitt des Entwurfs erneut auflösen.

## Maßstab

**Mechanisch ok** (Skript, von Hawe nachprüfbar in `uebersicht.md`):
- `spec_pruefen.pruefe`: 0 Befunde – ausgenommen „Offene Fragen nicht geklärt“ (vor den Antworten ein zulässiger Zustand);
- jede Quelle im Entwurf auflösbar (kein FEHLT/ZU LANG/UNKLAR/VERWEIGERT; PRÜFEN zählt als nicht aufgelöst).

**Inhaltlich ok** (Claude, gegen diesen Schlüssel):
- jede **Kern-A**-Vorgabe (steht in Aufgabe/Antworten) eingehalten – eine Verletzung = nicht ok;
- jede **Kern-T**-Entscheidung richtig getroffen **oder** als Offene Frage gestellt; höchstens **eine** falsch;
- keine erfundenen Pfade, Funktionen, Konstanten oder Befehle (gegen den Stand vor der Spec);
- je Anforderung eine Einbaustelle, die es im Stand gibt.

**Trägt**, wenn in mindestens 2 von 3 Ketten mindestens 2 von 3 Wiederholungen mechanisch **und** inhaltlich ok sind.
Knapp (genau 2 von 3 Ketten, oder Claude im Zweifel) → Zweitbewertung durch frische Instanz.

Schritt 1 wird zusätzlich ausgewertet wie K12b: Rückfragen je Kategorie (K Kern / B schon beantwortet /
U Umsetzungsdetail statt Auftraggeber-Entscheidung / S sonstige berechtigte). Ziel: wenige Fragen, keine B, wenig U.

## git_schutz (Stand 7f95f7d^)

Kern-A (in Aufgabe/Antworten):
- GA1 Nur melden (Befund, Exit 1), nichts zurücksetzen/abbrechen.
- GA2 Umfang `config`, `hooks/`, `info/` – nicht ganz `.git/`.
- GA3 Kein Schutz von `~/.gitconfig`.
- GA4 Auch Nacharbeit-Läufe.

Kern-T (Modell entscheidet):
- GT1 Einbau in `umsetzung_auto` in `role-split/kette/kette.py` (Schnappschuss vor dem Opencode-Lauf, Vergleich danach); Schreibbereich `kette.py`.
- GT2 Erkennen per Vorher/Nachher-Vergleich (Inhalt/Prüfsumme je Datei, `hooks/` rekursiv) statt Pre-Commit-Hook oder Laufzeitsperre – ein Hook wäre selbst änderbar. Grenze „zurückgenommene Änderung bleibt unerkannt“ genannt (Nicht-Ziel/Abweichende Meinung) – fehlt sie, kein Fehler.
- GT3 Git-Verzeichnis nicht fest als `ROOT/.git` ohne Gedanken an Worktrees: `git rev-parse --git-common-dir` (oder `--git-dir`) bzw. Offene Frage. Fest `ROOT/.git` = falsch.
- GT4 Befund fließt in den bestehenden Befund-/Exit-Mechanismus von `umsetzung_auto` (Protokoll, Exit 1), keine neue Exit-Bedeutung.
Neben (kein Muss): kaputte `.git/config` → kein Absturz; Symlinks/Ausführbar-Bit in `hooks/`; Vorgabe-Tests mit Temp-Repo.
Fehler: Pre-Commit-Hook als Lösung; blockieren/zurücksetzen; `~/.gitconfig` einbezogen; Änderung an `automatik.py` oder MCP ohne Grund.

## spec_pruefen (Stand 031d296^)

Kern-A (alle in der Aufgabe bzw. Antworten): nur wörtliche Platzhalter der Vorlage; `Prüft:` mit Unterpunkten
und Klammerzusätzen; Offene Fragen ≠ „Keine“ → Befund Exit 1; Größe samt Änderungsstellen gegen R59 nur Hinweis
Exit 0; Stelle je Anforderung, Prüft je Test, Schreibbereich, Form der Quellen; „Änderungsstellen“ wird
Pflichtzeile der Vorlage; Trockenlauf an `git_schutz`/`alle_tests` ohne Fehlalarme; `lauf` erst später; alte Specs
bekommen den Befund. (SA1–SA6)

Kern-T:
- ST1 Zuschnitt: eigenes Modul (z. B. `role-split/kette/spec_pruefen.py`), in `kette.py` nur Befehl/Verteiler. Alles in `kette.py` = falsch (R59/R55-Zuschnitt), außer es wird begründet und die Änderungsstellen bleiben ≤ ~9.
- ST2 Wiederverwendung vorhandener Bausteine statt Neubau: mindestens zwei von `automatik.groesse`, `kette.abschnitt`, `kette.tests_finden`/`TEST_ID`, `kette.datei_suchen`, `kette.quelle_lesen`, `kette._schreibbereich`, `PAKET_NIE`.
- ST3 Platzhalter in HTML-Kommentaren der Vorlage lösen keinen Befund aus (Kommentare vorher entfernen) – oder Offene Frage.
- ST4 Exit 2 für ungültigen Kurztitel / fehlende Spec; Exit 0/1 wie Aufgabe; liest nur, schreibt nichts.
- ST5 Die Vorlage `_vorlage_spec.md` bekommt die Zeile – Änderung in Schreibbereich oder ausdrücklich „mit der Spec durch Claude“; nicht vergessen.
Neben: Spec-Suche im Ablage-Ordner (`datei_suchen`); Trockenlauf-Test über die Befehlszeile; Befunde vor Hinweisen.
Fehler: allgemeine Prüfung auf spitze Klammern; Größe als Befund; Spec als YAML/JSON; Modellaufruf.

## lauf_spec_pruefen (Stand 2b63547^ = ee2bf4d)

Kern-A (Aufgabe): Befunde halten vor der Umsetzung an; Größe nur noch Hinweis (Halt 2/6/8 entfällt); kein
Sonderweg/Schalter für alte Specs. (LA1–LA3)

Kern-T:
- LT1 Halt-Exit unterscheidbar von Exit 1 (= Umsetzungs-/Review-Befunde) – z. B. 3 wie der bisherige Halt vor dem Start; Exit 1 für den Halt = falsch (außer als Offene Frage).
- LT2 Reihenfolge: nach den bestehenden Prüfungen (Kurztitel, Spec-Commit, Spec-Datei, Vorgabe-Tests), vor `umsetzung_auto`.
- LT3 Exit 2 von `spec_pruefen` (Datei/Format) behandelt – durchreichen oder eigener Halt, nicht ignoriert.
- LT4 `groesse` bleibt (wird von `spec_pruefen` benutzt); nur die Konstanten/der Halt fallen weg. `groesse` löschen = falsch.
- LT5 Zirkelimport (`spec_pruefen` importiert `automatik`): Import im Funktionsrumpf oder ausdrücklich bedacht – oder Offene Frage. Import am Dateianfang ohne Gedanken = falsch.
- LT6 Schreibbereich nur `role-split/kette/automatik.py`; der Bestand-Test `tests/test_lauf_status.py` (T3 prüft den alten Größen-Halt) wird als betroffen erkannt (anpassen vor dem Lauf / Hinweis) – fehlt es, zählt es als die eine zulässige falsche Kern-T.
Neben: Ausgabe von `spec-pruefen` unverändert durchreichen; Trockenlauf an alten Specs; MCP zeigt Exit nur an.
Fehler: Schalter zum Umgehen; Hinweise halten an; `spec_pruefen.py` oder `kette.py` im Schreibbereich ohne Grund.
