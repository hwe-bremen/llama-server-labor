# Learnings der Kette

Gedächtnis der Kette: Was haben wir aus jeder Kette gelernt, und welche Regel folgt daraus?
Gedacht für lokale Modelle (Spec, Umsetzung, Review) **und** für Claude als Gegenprüfer.
Abgeschlossene Ketten wandern später ins Archiv (`docs/projekt_management/archiv/`), dieser Ordner bleibt.

## Aufbau
- **`LERNREGELN.md`** – verdichtete Regeln, höchstens ~100 Zeilen, jede mit Datum und Quelle.
  Wird (nach K8) von `kette.py prompt` automatisch in Spec- und Review-Prompts mitgegeben.
  Neue Regel nur, wenn sie eine *wiederkehrende* oder *teure* Fehlerklasse verhindert. Veraltete Regeln streichen, nicht sammeln.
- **`kette_<kurztitel>.md`** – je Kette eine Seite: Was ist passiert, welche Fehlerklasse, welche Regel, wo umgesetzt.

## Form einer Ketten-Seite
```
# Kette <Nr> <kurztitel> (<Datum>)
Aufgabe: ein Satz.
Ergebnis: bestanden / nicht bestanden – warum, ein Satz.
## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
## Regeln daraus
- Regel → in LERNREGELN.md als Rnn / umgesetzt in <Datei/Prompt/Werkzeug>
## Sonst bemerkenswert
```

## Ablauf (RUNBOOK Phase G)
Nach dem Commit einer Kette entwirft der Gegenprüfer (derzeit Claude) die Ketten-Seite und schlägt neue Regeln vor.
Hawe gibt frei. Keine Lösungsdetails, die als Prüfstein für spätere Proben dienen sollen, ohne Hinweis
(Proben sperren diesen Ordner per `MCP_DENY`).

Erstbefüllung 25.10.2026 durch Claude aus den Projekt-Auswertungen der Ketten R1/R2 (17.10.) bis K7 (24.10.).
