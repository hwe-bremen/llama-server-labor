# Kette 4 scout_bericht_ueberschreiben (18./19.10.2026)
Aufgabe: Zweiter Scout-Lauf in einer Woche überschreibt den Bericht, Einträge gehen verloren.
Ergebnis: nicht bestanden – der Kerndefekt entstand **in der Spec** und wurde von Umsetzung und drei Reviewern bestätigt.

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| Spec: Versandmerker **vor** dem Versand reservieren, als „bekanntes Restrisiko" erklärt → nach SMTP-Fehler kommt die Mail nie an | Spec widerspricht Anforderung („genau einmal") | Claude; danach Review mit Originalanforderung |
| Nachtrag-Mail schickt die ganze Datei erneut | Spec-Lücke | Claude |
| Test T3 schrieb das Fehlverhalten als Erwartung fest | Test validiert Fehler | Review mit Originalanforderung |
| Präfix-Prüfung trifft Alt-Zeilen (Migrationswoche) | Altbestand nicht bedacht | Review Qwen3.8 |
| Reviewer überschrieb `_vorlage_verdict.md` | fehlender Schreibschutz | Claude |

## Regeln daraus
- R01 Restrisiken als Fehlerpfad durchspielen · R15 Review gegen Anforderung (umgesetzt: `anforderung_*.md`, Proxy-Mitschrift)
- Schreibschutz für Vorlagen (umgesetzt im MCP-Server: `_vorlage_*`, `anforderung_*`, `quellen_*`)

## Sonst bemerkenswert
- Dasselbe Qwen3.6, das die Spec-Entscheidung tags zuvor befürwortete, fand den Fehler, sobald es Hawes Originalanforderung bekam: Der Hebel lag im Auftrag, nicht im Modell.
- Qwen3-Coder-Next 80B (Slipstream) als Reviewer hier nicht besser: mehr Befunde, viel Füllmaterial, eine Erfindung.
