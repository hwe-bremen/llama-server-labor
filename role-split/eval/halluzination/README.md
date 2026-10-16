# Halluzinations-Probe

Kurzer Vortest, bevor ein neues Modell ernsthaft genutzt oder ins Review-Eval geht: Wie
ehrlich ist es bei Lücken? Das Skript schickt 11 feste Fragen direkt an den Router (8080),
**ohne Tools und ohne Web-UI**, je einmal ohne Systemprompt und einmal mit der Rolle `research`.

| Typ | Fragen | Richtiges Verhalten |
|---|---|---|
| erfunden | E1–E4: Modell, Flag, Python-Funktion, Paper, die es nicht gibt | „kenne ich nicht“ |
| texttreue | T1–T2: Frage zu einem mitgegebenen Text, die der Text nicht beantwortet | „steht nicht drin“ |
| wissen | W1–W4: feste Fakten (Port, Quantisierung, GGUF, Jahr) | richtige Antwort |
| kontrolle | T3: aus dem Text beantwortbar | richtige Antwort (prüft, dass es nicht alles ablehnt) |

Die Lösungen stehen in `fragen.json`. Das ist hier unbedenklich, weil das Modell ohne Tools
nichts im Repo lesen kann.

## Aufruf

Lab läuft (für Vergleiche `start_eval.command`, damit nur ein Modell im Speicher ist):

```bash
python3 role-split/eval/halluzination/probe.py --alle                 # alle Modelle aus dem Router
python3 role-split/eval/halluzination/probe.py --modelle "unsloth/Qwen3.8-27B-GGUF:Q4_K_XL"
python3 role-split/eval/halluzination/probe.py --alle --kein-denken   # Thinking aus, deutlich schneller
python3 role-split/eval/halluzination/probe.py --alle --nur ohne      # nur ohne Rolle
python3 role-split/eval/halluzination/probe.py --trocken --alle       # nur anzeigen
python3 role-split/eval/halluzination/test_probe.py                   # Selbsttest ohne Modell
```

Ergebnis: `ergebnisse/<JJJJMMTT_HHMM>_uebersicht.md` (Tabelle + alle Antworten) und je Modell
eine `.jsonl` mit Rohdaten. Beides darf ins Git, es sind synthetische Fragen.

## Dauer (Schätzung, nicht gemessen)

22 Anfragen je Modell. Ohne Thinking bei kurzen Antworten wenige Minuten. Mit Thinking
hängt es am Modell: Qwen3.8 denkt lang (~9 Token/s), dort eher 30–60 Minuten. Für einen
schnellen Vortest `--kein-denken`; für die ehrliche Messung mit Preset laufen lassen.
Erstes Laden eines Modells kommt dazu (Download vorher, siehe `../README.md`).

## Lesen der Übersicht

- `✓?` / `✗?` ist nur eine **Vorsortierung** über Stichworte und typische Formulierungen
  („nicht bekannt", „steht nicht im Text" …). Ein Modell, das „bin nicht sicher, aber so geht's: …"
  schreibt, landet fälschlich bei `✓?`. Das Urteil fällt beim Lesen der Antworten.
- Wichtigste Spalten: **Erfundenes abgelehnt** und **Texttreue**. Wissen/Kontrolle zeigen nur,
  dass das Modell nicht einfach alles verweigert.
- Vergleich `ohne` vs. `research`: zeigt, ob unsere Rollen-Regeln („nichts erfinden",
  belegt/Wissensstand/Vermutung) Halluzinationen tatsächlich senken.

## Grenzen

Die Probe misst eine **Neigung**, kein Schutzniveau. Ein Modell, das hier gut abschneidet,
kann im Alltag trotzdem erfinden. Schutz im Alltag: Belege verlangen (Datei/URL), unbelegte
Details als ungeprüft behandeln, bei Wichtigem eine zweite Stimme.

Fragen nur ergänzen, nicht still ändern; bei Änderungen `version` in `fragen.json` hochzählen,
sonst sind alte Läufe nicht vergleichbar. Erfundene Begriffe zuletzt per Websuche geprüft: 16.10.2026.

Mode B: Lab, berührt AskValentinAI nicht.
