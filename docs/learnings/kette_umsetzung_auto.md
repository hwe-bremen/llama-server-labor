# Kette 10 umsetzung_auto (27.10.2026)
Aufgabe: `kette.py umsetzung-auto <kurztitel> [--nacharbeit <datei>]` – Umsetzung und Nacharbeit über `opencode run --format json` ohne TUI (Agent `umsetzung_nacht`), danach mechanisch prüfen: Selbst-Commit, Schreibbereich (`## Schreibbereich` in der Spec), Handover, `pruefen`; Protokoll und Halt-Regel.
Ergebnis: bestanden (`ca85c5c`), aber nicht durch das lokale Modell: Der 35B-Lauf wurde verworfen, Claude baute. Gegenprüfung durch frische Instanz: NACHBESSERN → NB1 → PASS. Abnahme an einer Mini-Spec mit beiden Modellen (`claude/k10-abnahme-vergleich.md` im Projekt).

## Messung
| Schritt | Modell | Dauer | Ergebnis |
|---|---|---|---|
| Spec Runde 1 | Qwen3.8 | – | brauchbar |
| Spec Korrekturen Runde 2 | Qwen3.8 | länger als Runde 1, Kontext voll, zweiter Chat nötig | unfertig → Claude präzisierte direkt |
| Umsetzung | 35B-A3B (OpenCode, TUI) | ~1 h bis Abbruch | `main()` gelöscht, Tests committet (3 leere Selbst-Commits), `pruefen` NameError → verworfen, `git reset --soft 3700da7` |
| Umsetzung | Claude | < 1 Tag inkl. NB1 | 33 Tests, Gegenprobe 32/32 |
| `review-auto` | 35B-A3B | 144 s + 73 s | formal NACHBESSERN; 26/27 „hoch" vom Modell selbst zurückgezogen („Korrekt."), Paket 89k > 80k |
| Gegenprüfung | frische Claude-Instanz | – | 3 Pflicht- + 4 niedrige Befunde, alle berechtigt; nach NB1 PASS + 1 niedriger Nachtrag |
| Abnahme Mini-Spec | 35B-A3B / 27B | 3:21 / 14:15 | beide Code korrekt; 27B Handover formal sauber, 35B nicht |

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| Umsetzer las `kette.py` (~1 900 Zeilen) ganz, Kontext erschöpft, `main()` beim Umbau verloren | Aufgabe zu groß für den Umsetzer | `pruefen` (NameError) |
| Tests des Umsetzers committeten ins echte Repo | Test mit Außenwirkung | Hawe (`git show --stat`) |
| Nacharbeitsnummer aus dem Protokoll statt aus dem Handover | Spec still umgedeutet | Gegenprüfung (M1) |
| Spec-Erwartung von T13 durch schwächere Prüfung ersetzt, im Handover als „Verstärkung" beschrieben | Test ersetzt statt gebaut | Gegenprüfung (M3) |
| Attrappe prüfte nur den Arbeitsordner, nicht die Schreibziele (`../`) | Sperre mit Lücke | Gegenprüfung (N1) |
| Ausbruchs-Test hätte in der Gegenprobe mit der alten Attrappe wirklich hinausgeschrieben | Test mit Außenwirkung über die Gegenprobe | Claude (eigener Mutationslauf) |
| Protokoll-Unterzeilen mit fremdem Befehlstext konnten die Halt-Regel täuschen | ungeankerter Marker (R22) | Gegenprüfung nach NB1 |
| Mini-Spec mit Schreibbereich unter `experiments/` → Gegenprobe blind | Werkzeuggrenze (`PAKET_NIE`) nicht beachtet | Abnahme |

## Regeln daraus
- R43 Aufgabengröße für lokale Umsetzer.
- R44 Spec-Korrekturen ab Runde 2 direkt.
- R45 Attrappen sperren sich selbst; Tests prüfen das echte Repo.
- R46 OpenCode ohne TUI: Sperren in der Agent-Datei, Erfolg nur aus dem JSON.
- R47 Schreibbereich nicht unter Pfaden, die die Kette ausblendet.
- R22 bestätigt (Protokoll-Unterzeilen), R39 wirkt weiter nur halb (K10b: mechanisch).

## Sonst bemerkenswert
- OpenCode 1.19.3: Exit immer 0; `ask` ohne TUI = Ablehnung und stummes Ende (`reason: tool-calls`); `deny` = Fehlermeldung, Modell arbeitet weiter; Regelreihenfolge Default → `OPENCODE_PERMISSION` → Agent, letzte passende gewinnt.
- deny greift im echten Lauf (abgelehnt: `mkdir`, Befehle mit `;`/`||`); `git commit` hat in der Abnahme kein Modell versucht.
- Tokens im Protokoll sind die Summe der Schritt-Totals (vermutlich je Schritt der ganze Kontext) – kein Verbrauchsmaß.
- Ein Modell, das den Code einer Kette nicht geschrieben hat, darf ihn gegenprüfen; dieselbe Gegenprüfer-Instanz kann ihre eigene Nachbesserung bestätigen.
