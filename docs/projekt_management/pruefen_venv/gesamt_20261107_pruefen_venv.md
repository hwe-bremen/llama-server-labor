# Gesamtbefund: pruefen_venv

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-11-07 14:20). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**PASS** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261107_pruefen_venv_qwen36-35b.md` | PASS |
| `verdict_20261107_pruefen_venv_qwen36-35b_betrieb.md` | PASS |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261107_pruefen_venv_qwen36-35b.md` | niedrig | nein | `kette.py:400` | Symlink-Verhalten |
| `verdict_20261107_pruefen_venv_qwen36-35b_betrieb.md` | niedrig | nein | `kette.py:400` | `os.path.relpath` kann bei Symlinks zu `ROOT` irrefuehrend sein, falls `ROOT` selbst ein Link ist. Da `s` vorab geloesst wird, ist dies in der Praxis meist unkritisch, aber theoretisch moeglich. |
