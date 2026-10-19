# Qwen3-Coder-Next 80B als Umsetzer in OpenCode (19.10.2026, Claude)

Aufgabe: Kette 4 (`scout_bericht_ueberschreiben`) mit der **korrigierten** Spec, Worktree `../llama-server-k4next` auf `818aa5d`.
Server: Slipstream-PGRN, Cache 18 GiB, Kontext 65536. Lauf ca. 11:06–18:31 (~7,5 h). Vergleich: Qwen3.6 brauchte am 18.10. ~1 h (andere, fehlerhafte Spec).

## Zeitprofil (Server-Log, Stand ~17:30, 58 Anfragen)
- Prompt einlesen gesamt 188 min für 264.000 Token, davon 12 Anfragen > 8.000 Token = 143 min (fast vollständiges Neueinlesen).
- Generieren 77 min für 34.000 Token (7–8 Token/s), Cache-Treffer 82 %.
- Vermutung: Hybridmodell (rekurrente Schichten) kann den Prompt-Cache nur an Checkpoints wiederverwenden; ändert OpenCode frühere Teile der Unterhaltung, wird alles neu eingelesen. Nicht geprüft.

## Verhalten (von Claude mit Mocks geprüft)
| Fall | Ergebnis |
|---|---|
| D1: SMTP-Fehler, nächster Lauf | ✓ Exit 1, kein Merker; nächster Lauf sendet nach |
| D2: Nachtrag-Mail | ✓ nur der Nachtrag, Betreff „– Nachtrag" |
| Alt-Zeile `KEY DATUM` | ✓ zählt als lauf_nr 1, Nachtrag einmal, dann Ruhe |
| „## Nachtrag KW" im Text | ✓ zählt nicht (Trennstelle mit `---`) |
| Zwei offene Nachträge | ✗ pro Lauf nur **ein** Abschnitt; der zweite wartet auf einen weiteren Lauf derselben Woche (sonst nie gesendet); Betreff „– 2 Nachträge", obwohl nur einer im Inhalt |
| Nachtrag-Überschrift in der Mail | ✗ Trennstelle wird beim Zerlegen entfernt → Mail beginnt mit „43_2026 (…)" statt „## Nachtrag KW43_2026 (…)" (aus dem Code gelesen) |

## Code und Tests
- `llm_scout.py`: Anhängen direkt in `main()`, kein `save_report()` (Spec/T8 verlangen es) → Abweichung nicht im Handover.
- Eigene Tests 9/9 grün, aber: T1/T9 schreiben die Datei im Test selbst (messen den Scout-Code nicht); T3 prüft nur „kein Merker", nicht das erfolgreiche Nachsenden; T7 ruft nur `send_scout_email.py` auf (Pipeline nie gestartet, im Test-Kommentar selbst eingeräumt); kein Test für den Erfolgsfall.
- Claudes 13 Referenztests gegen diesen Code: 8 ok; T1/T9/T8 scheitern an fehlendem `save_report`, T3/T12 an einer internen Hilfsfunktion der Referenz (Verhalten separat geprüft: ✓).
- Positiv: Widerspruch zwischen altem T3-Text und Spec-Nachtrag erkannt und richtig aufgelöst (Nachtrag gilt), offen im Handover benannt. Keine Außenwirkung.

## Einordnung
Kernlogik richtig, Testqualität und Spec-Treue schwächer als nötig, ~7× so lange wie Qwen3.6. Als Umsetzer in OpenCode mit dieser Engine derzeit nicht alltagstauglich; Engpass ist das wiederholte Neueinlesen, nicht das Modell.
