# Gesamtbefund: ablage_ordner

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-10-28 14:23). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**NACHBESSERN** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261028_ablage_ordner_qwen36-35b.md` | NACHBESSERN |
| `verdict_20261028_ablage_ordner_qwen36-35b_betrieb.md` | PASS |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261028_ablage_ordner_qwen36-35b.md` | hoch | ja | `kette.py:115-123` | **Falsche Pfadersetzung in `_ablage_text`**: Der Regex `r"docs/projekt_management/(?!_vorlage_)([\w.-]+\.md)"` ersetzt *alle* `.md`-Dateien im `docs/projekt_management/`-Verzeichnis, die nicht `_vorlage_` heissen, durch den Pfad der *aktuellen* Kette. Wenn also Kette A eine Datei `spec.md` hat und Kette B laeuft, wird `docs/projekt_management/spec.md` in `docs/projekt_management/b/spec.md` umgeschrieben, obwohl `spec.md` zu A gehoert. Dies fuehrt dazu, dass Prompts von Kette B falsche Pfade zu Dateien von Kette A enthalten. |
| `verdict_20261028_ablage_ordner_qwen36-35b.md` | mittel | ja | `kette.py:965-966` | **Fehlende Ordner-Erzeugung in `anforderung`**: `abl.mkdir(...)` wird aufgerufen, aber wenn `ablage(kurztitel)` einen Pfad zurueckgibt, der noch nicht existiert (was ja der Fall ist, wenn der Ordner neu angelegt werden soll), muss sichergestellt sein, dass `mkdir` erfolgreich ist. Da `ablage()` selbst keinen Ordner anlegt (nur prüft), und `anforderung()` erst dann `mkdir` aufruft, ist dies korrekt. ABER: In `zusammenfuehren` und anderen Stellen wird `ablage()` verwendet, ohne vorher `mkdir` aufgerufen zu haben. Wenn der Ordner noch nicht existiert, schlagen Schreiboperationen fehl. Die Spec sagt: „Zuerst nur die Pfadlogik; Ordner anlegen ... kommt danach." Dies wird hier jedoch teilweise ignoriert, da `anforderung` den Ordner anlegt, `pruefen` aber nicht. |
| `verdict_20261028_ablage_ordner_qwen36-35b.md` | niedrig | ja | `tests/test_ablage_ordner.py:100-110` | **Test deckt Fehler in `_ablage_text` nicht ab**: Der Test `test_t4_umsetzung_auto_mit_ordner` prueft nur, dass Pfade der *aktuellen* Kette korrekt ersetzt werden. Er testet nicht, ob Pfade *fremder* Ketten oder *flacher* Dateien korrekt ignoriert werden. Daher wird der Fehler in Befund #1 vom Test nicht erkannt. |
| `verdict_20261028_ablage_ordner_qwen36-35b_betrieb.md` | niedrig | nein | `kette.py:109` | `_ablage_rel` hartcodiert |
| `verdict_20261028_ablage_ordner_qwen36-35b_betrieb.md` | hoch | ja | `kette.py:109, 123` | Falscher Pfadname |
| `verdict_20261028_ablage_ordner_qwen36-35b_betrieb.md` | hoch | ja | `kette.py:109, 123, 1664` | Pfadname hartcodiert |
| `verdict_20261028_ablage_ordner_qwen36-35b_betrieb.md` | Schwere | nein | Datei:Zeile | Befund |
| `verdict_20261028_ablage_ordner_qwen36-35b_betrieb.md` | hoch | ja | `kette.py:109, 123, 1664` | Falscher Pfadname |
