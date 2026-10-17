# Handover: <kurztitel>

- **Spec:** `docs/projekt_management/spec_<JJJJMMTT>_<kurztitel>.md`
- **Datum:** <JJJJ-MM-TT>
- **Modell / Werkzeug:** <z. B. Qwen3.6 27B in OpenCode, Agent „umsetzung">
- **Rücksetzpunkt:** <Commit-Hash vor der Umsetzung>

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| 1 | erfüllt / teilweise / nicht | `datei.py`, Funktion `xy` |

## Geänderte und neue Dateien

- `pfad/datei.py` – neu / geändert – ein Satz, was sich geändert hat

## Abweichungen von der Spec

- <Was anders gemacht wurde und warum. „Keine", wenn keine.>

## Annahmen

- <Was nicht in der Spec stand und selbst entschieden wurde.>

## Getestet (mit echter Ausgabe)

Testtitel **exakt wie in der Spec** (`kette.py abgleich` vergleicht sie). Ein Test, der anders gebaut wurde, gehört zusätzlich unter „Abweichungen".

**T1: <Titel wie in der Spec>** – bestanden / fehlgeschlagen

```
$ python3 -m unittest -v tests/test_<kurztitel>.py
<echte Ausgabe>
```

## Außenwirkung

- <„Keine Befehle mit Außenwirkung ausgeführt." — oder genau, was passiert ist (Versand, Netz, echte Daten).>

## Hawe muss ausführen

- <Befehle mit Außenwirkung, die bewusst nicht ausgeführt wurden. „Nichts", wenn nichts.>

## Nicht getestet

- <Was nicht geprüft werden konnte und warum.>

## Offene Punkte / bekannte Schwächen

- <…>
