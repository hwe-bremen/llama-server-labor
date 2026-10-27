# Anforderung: umsetzung_auto

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Die Umsetzung soll ohne TUI laufen, damit ich nicht mehr Prompts kopieren und Befehle freigeben muss.
> 1. Neuer Befehl `kette.py umsetzung-auto <kurztitel>`: startet `opencode run --format json` mit Agent `umsetzung_nacht` und Modell aus `KETTE_UMSETZUNG_MODEL` (Vorgabe `llamacpp/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL`). Prompt wie `prompt umsetzung`, aber ohne Ausgabe/Zwischenablage. Jeder Lauf ist eine neue Sitzung (kein `--continue`).
> 2. Vor dem Start prüfen, sonst Exit 2 ohne Lauf: Commit „Spec <kurztitel>" existiert; die Spec hat einen Abschnitt `## Schreibbereich` (Dateien/Ordner, die die Umsetzung ändern darf); Arbeitsstand sauber (erster Lauf) bzw. nur Änderungen im Schreibbereich (Nacharbeit); `opencode` ist installiert; das Modell beginnt mit `llamacpp/`.
> 3. `umsetzung_nacht` verbietet zusätzlich ausdrücklich (deny): `git commit`, `reset`, `checkout`, `restore`, `clean`, `stash`, `push`, `rm`, `mv`. Kein `ask` im Agenten.
> 4. Zeitlimits: ganzer Lauf `KETTE_UMSETZUNG_TIMEOUT` (Vorgabe 7200 s), danach OpenCode samt Unterprozessen beenden, Exit 1; Einzelbefehl über `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS` (Vorgabe 300000).
> 5. Ausgewertet wird nur das JSON, nie der Exit-Code von OpenCode: Dauer, Werkzeugaufrufe, fehlgeschlagene und abgelehnte Befehle (mit Wortlaut), Tokens, letzter `reason`, Schlusstext. Ohne `reason: stop` am Ende gilt der Lauf als „nicht abgeschlossen" (Exit 1). Rohdaten nach `role-split/results/`, je Lauf eine Protokollzeile in `docs/projekt_management/umsetzung_<datum>_<kurztitel>.md`.
> 6. Danach mechanisch: (a) HEAD unverändert, sonst lauter Fehler „Selbst-Commit"; (b) jede in diesem Lauf geänderte oder neue Datei liegt im Schreibbereich, ist `tests/test_<kurztitel>.py` oder der Handover der Kette – Spec, Anforderung, Quellen und Vorlagen nie; bei Verstoß Liste, Exit 1, nichts zurücksetzen (entscheide ich); (c) Handover wurde in diesem Lauf geschrieben oder ergänzt; (d) `pruefen`.
> 7. Nacharbeit: `kette.py umsetzung-auto <kurztitel> --nacharbeit <datei.md>` – Auftrag aus der Datei, Handover wird unter „## Nachbesserung n" ergänzt. Zwei Nachbesserungen in Folge ohne Fortschritt (rote Tests nicht weniger, `pruefen` nicht besser) ⇒ keine weitere starten, Exit 1, „Übergabe an Hawe".
> 8. Während des Laufs: je Werkzeugaufruf eine kurze Zeile, dazu jede Minute ein Lebenszeichen.
> 9. Exit 0 nur, wenn der Lauf abgeschlossen ist, kein Verstoß vorliegt und `pruefen` 0 meldet. RUNBOOK Phase B und die Spec-Vorlage (`## Schreibbereich`) werden ergänzt.
> 10. Der Prompt von `umsetzung-auto` verweist auf `docs/learnings/LERNREGELN.md`, Abschnitte „Umsetzung" und „Tests", als Pflichtlektüre vor der ersten Änderung.
> Tests nutzen eine Attrappe statt `opencode` (Pfad über `KETTE_OPENCODE`), nie ein echtes Modell. Bestehende Tests bleiben grün, Code läuft unter Python 3.10. Abnahme: echter Lauf mit dem 35B an einer Mini-Spec, die Claude schreibt; Dauer wird gemessen.
> Lies NUR zwei Dateien: diese Anforderung und docs/projekt_management/spec_paket_20261027_umsetzung_auto.md. Weitere Stellen nur, wenn wirklich etwas fehlt: search_files, dann read_file mit start_line/end_line, höchstens drei Mal.

## Antworten auf Rueckfragen

**2026-10-27 09:56** — Frage (Hawe): Dann läuft alles ohne Gedächtnis?

> Verstehe ich, kein Gedächtnis! Nimm Punkt 10 auf!
> (Von Claude nach Hawes Zustimmung am 27.10. 09:59 eingetragen: neue Sitzung je Lauf und kein Gedächtnis-Proxy sind gewollt; Zustand liegt in Dateien, Kettenwissen kommt über Punkt 10.)
**2026-10-27 10:08** — Frage: Globale ~/.config/opencode/AGENTS.md verlangt Erklärung vor Architekturänderungen und englische Bezeichner – Widerspruch zum Automatikbetrieb?

> Ja. Die globale AGENTS.md bleibt unverändert. Zu Punkt 3: umsetzung_nacht sagt ausdrücklich, dass er Vorrang vor allgemeinen Kommunikationsregeln hat: nicht vorab erklären oder auf Freigabe warten, sondern umsetzen und Begründungen ins Handover schreiben; Bezeichner wie in Spec und bestehendem Code (in diesem Repo deutsch).

