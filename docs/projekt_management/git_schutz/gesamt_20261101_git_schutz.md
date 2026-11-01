# Gesamtbefund: git_schutz

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-11-01 20:18). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**NACHBESSERN** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261101_git_schutz_qwen36-35b.md` | NACHBESSERN |
| `verdict_20261101_git_schutz_qwen36-35b_betrieb.md` | PASS |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261101_git_schutz_qwen36-35b.md` | hoch | ja | `kette.py:2091-2100` | Bei kaputter Git-Konfiguration wird ein Befund erzeugt, aber der Exit-Code ist 1. Die Spec sagt: „Exit wird 1, weil ein Befund vorliegt." Das ist korrekt. Allerdings ist die Fehlermeldung „git nach dem Lauf nicht benutzbar" nur dann relevant, wenn der Lauf *durchgelaufen* ist. Wenn `gitdir` nicht gefunden wird (A3.1), wird Exit 2 gesetzt und der Lauf bricht ab. Das ist korrekt. Der Befund bei A4 bezieht sich auf den Fall, dass der Lauf durchgelaufen ist, aber `git rev-parse HEAD` danach fehlschlaegt. Hier wird Exit 1 gesetzt. Das ist korrekt laut Spec. Ein echter Fehler ist nicht erkennbar, außer dass die Fehlermeldung bei `head_nach` den stderr des *letzten* Befehls nutzt, was korrekt ist. |
| `verdict_20261101_git_schutz_qwen36-35b_betrieb.md` | niedrig | nein | `kette.py:1750` | Symlink-Verfolgung in `os.walk` ist korrekt deaktiviert (`followlinks=False`), aber die manuelle Prüfung von `dirnames` auf Symlinks (`dpp.is_symlink()`) ist redundant, da `os.walk` mit `followlinks=False` keine Symlinks auf Verzeichnisse als `dirnames` liefert, wenn sie nicht explizit aufgelöst werden sollen – hier wird aber der Symlink selbst erfasst, was korrekt ist. Allerdings: Wenn ein Symlink auf ein Verzeichnis zeigt, wird er in `dirnames` gelistet? Nein, `os.walk` listet Symlinks auf Verzeichnisse in `dirnames`, wenn `followlinks=False`? Tatsächlich listet `os.walk` Symlinks auf Verzeichnisse in `dirnames`, aber `followlinks=False` verhindert das Rekursiv-Eintreten. Die manuelle Prüfung `if dpp.is_symlink()` fängt also Symlinks auf Verzeichnisse ab, die nicht betreten werden. Das ist korrekt und gewünscht. |
