<!-- Schritt 4 (Eval), start_eval, Modell vorher laden, MCP aus/an + Seite neu laden, NEUER Chat. -->
@review Tiefenprüfung (zweite, unabhängige Prüfung) der Umsetzung zu docs/projekt_management/spec_{datum}_{kurztitel}.md.
Verbindliche Vorgabe ist {anforderung}; die Spec kann falsch sein. Prüf zuerst ihre Designentscheidungen und „akzeptierten Restrisiken" gegen die Anforderung.
Lies Spec, Handover docs/projekt_management/handover_{datum}_{kurztitel}.md, den Diff gegen {commit}, den Code vollständig und tests/test_{kurztitel}.py.
Lies KEINE vorhandenen Verdikte zu diesem Thema.
Spiele jeden Fehlerpfad aus der Fehlerpfad-Tabelle der Spec selbst im Code nach und suche Fälle, die in der Tabelle fehlen.
Beantworte zusätzlich für jede Anforderung die vier Pflichtfragen aus dem Review-Prompt (erzwungen oder nur verlangt? leerer/abweichender Fall? markiert, aber nie gezeigt? läuft die Absicherung selbst ins Leere?). Überblick vorab: {paket}.
Befundtabelle genau nach _vorlage_verdict.md, mit den Spalten Datenverlust / Unbemerkt / Harte Vorgabe (ja/nein).
Speichern in Abschnitten: erst write_file (Kopf, Ergebnis, Befunde), dann je weiterer Abschnitt append_file.
Verdikt nach docs/projekt_management/verdict_{datum}_{kurztitel}_tief_<modellkürzel>.md
