# Kette 8 kette_review_auto (25.10.2026)
Aufgabe: Review-Phase automatisieren – `kette.py review-auto <kurztitel>`: pruefen → Paket → zwei Review-Läufe per Router-API → zusammenfuehren → Zusammenfassung.
Ergebnis: mechanisch fertig (15/15 Tests, echter Lauf: 2 Läufe in < 2 min statt 2×15–25 min). **Inhaltlich blind**, weil das Paket keinen Code enthält → K9. Betriebsmodell seit heute Hybrid, Schwelle nicht mehr gezählt.

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| Spec A2: Abbruch bei jedem `pruefen`-Exit ≠ 0 (auch nur Abgleich-Abweichung) → Befehl hätte nie ein Review gestartet | Spec widerspricht Anforderung („Unit-Tests rot") | Claude (Spec-Gegenprüfung vor Commit) |
| Verlangter echter Lauf fehlte in der Spec | Anforderung fallen gelassen | Claude (Spec-Gegenprüfung) |
| Spec-Chat zweimal Kontext voll (ganze Dateien gelesen) | Kontext | Hawe; Lösung Phase teilen + Spec-Paket + `read_file` mit Zeilenbereich |
| `paket` und `gegenprobe` blenden `role-split/` (und `paket` auch `tests/`) aus → K8 prüfte sich ohne Code; echter Lauf auf K7 meldete A4/A5 fälschlich „nicht umgesetzt" | Werkzeug blendet den eigenen Ordner aus | Claude (K8); **echter Lauf** (K7-Fall) |
| Scheitert Lauf 1, lief trotzdem Lauf 2 | Fehler gemeldet, nicht gestoppt | Claude (beide Review-Läufe verfehlt) |
| API-Prompts fest im Code, ohne Pflichtfragen-Erläuterung, ohne Tabellenspalten, mit `@review` (wirkt nur über den Proxy) → automatisches Review still schwächer als das manuelle | verlangt, aber nicht abgesichert | Claude (Review verfehlt) |
| Timeout über `subprocess.TimeoutExpired` abgefangen – `urllib` wirft das nie | falscher Fehlertyp | **Review (beide Läufe)** |
| Ein-Lauf-Gesamtbefund nicht geschrieben; Test T8 schrieb danach das falsche Verhalten fest | Test validiert Fehler | Review + Claude |
| Test-Aufräumen `srv.shutdown()` bei `handle_request()` blockierte ewig → OpenCode „hing" | Test ohne Zeitlimit | Claude |
| Umsetzer änderte bestehendes `zusammenfuehren` (Exit 2 → 1) | Arbeit außerhalb des Auftrags | Claude (alter Test rot) |

## Regeln daraus
- R34 Paket = einzige Sicht des Reviewers · R35 Werkzeuge blenden den eigenen Ordner nicht aus · R36 Tests mit Server/Netz mit Zeitlimit · R37 API-Prompts aus den Hand-Prompts ableiten (siehe LERNREGELN)
- Bestätigt: R14 (echter Lauf fand den wichtigsten Fehler), R01/R15 (Spec gegen Anforderung, vor dem Commit gegengeprüft), R30/R31 (Kontext)

## Sonst bemerkenswert
- **Qwen3.6-35B-A3B als Umsetzer:** Code ~1 h nach Start (vorher 1 h nur Lesen bis zur Verdichtung, Ursache: zu viel Lesestoff im Auftrag); 3 Nacharbeitsrunden; spec-treu, schnell; einmal außerhalb des Auftrags; Übergabe mit Formfehlern (Tests in einer Zeile). Ähnlich dem 27B – kein klarer Vor- oder Nachteil auf dieser Aufgabe.
- **35B-A3B als Reviewer (von Hand, 2 Läufe, ~8 min):** fand die Laufzeitfehler (Timeout, Ein-Lauf-Fall), nicht die Qualitätslücke der Prompts.
- Neu am Rand: Rolle `@idee` (Phase 0), `docs/learnings/`, Spec-Paket als Prototyp für Stufe 3, `opencode run` für Stufe 2 bestätigt (Doku).
