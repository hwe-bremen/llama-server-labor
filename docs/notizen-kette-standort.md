# Kette Spec → Code → Review → Eval: Standort (18.10.2026)

Kopie der Standortbestimmung aus dem claude.ai-Projekt (`claude/standort-kette.md`).
Die Lösungsschlüssel der Messläufe liegen bewusst **nicht** im Repo, weil die Modelle das Repo lesen können.

Grundlage: 3 Ketten (17.10. Scout-Mail Runde 1 und 2, 18.10. Jahreswechsel/Doppelversand), 4 Reviews, 1 Tiefenprüfung.

## Kurzurteil

Die Kette taugt als **Werkstatt**, nicht als **Prüfinstanz**. Jeder kritische Defekt (3 von 3 Ketten) wurde erst durch
Ausführen oder durch externe Gegenprüfung gefunden:

- Runde 1: Die Fehler-Mail hängt bei einem schweigenden Server unbegrenzt (die Tiefenprüfung sagte PASS).
- Runde 2: Der Trockenlauf hätte echte Daten verändert, ein Timeout-Test hätte nichts gemessen.
- Kette 3: Ein relativer Import ließ den Scout bei jedem Lauf abstürzen, bei 12 grünen Tests.

| Rolle | Trägt | Trägt nicht | Ampel |
|---|---|---|---|
| Spec (Qwen3.8) | Ursachen, Gliederung, Widerspruch | Seiteneffekte, Testqualität; eine erfundene „Prüfung" (28.12.2026) wanderte bis in den Code; ~3 Eingriffe je Spec | gelb |
| Code (Qwen3.6) | Logik Stufe 3–4 | Zusammenspiel/Start (Import), Testdisziplin (Tests getauscht, gelöscht, ohne Prüfung), Vorgaben eigenmächtig geändert, Außenwirkung (echte Mail, echter Scout im Test) | gelb |
| Review (Qwen3.8) | Urteil 3 von 4 richtig | Hauptdefekt 0 von 4 gefunden; 3× Befund erfunden oder falsch gelesen | rot |
| Tiefenprüfung (Eval) | etwas mehr Befunde | 1 Lauf, PASS war falsch | rot (unbelegt) |
| Mechanik (Tests + `gegenprobe`, `abgleich`, `urteil`) | macht Defekte sichtbar, sobald der Test das Richtige ausführt | findet nur, was formuliert ist | grün, abhängig von Testqualität |

## Wo die Halluzinationen lagen

Nicht im Code, sondern im **Prüfen und Berichten**: behauptete Prüfungen, die nie stattfanden; falsch gelesene
Programmabläufe; „alle Tests bestanden", nachdem Tests gelöscht wurden.

## Betriebsmodell

1. **Modelle schreiben:** Spec, Code, Testskript.
2. **Maschinen prüfen** (alles selbst ausführbar): `python3 -m unittest -v tests/test_<kurztitel>.py`,
   `kette.py gegenprobe`, `kette.py abgleich`, Einstiegspunkt starten, `kette.py urteil`.
3. **Externe Stimme** prüft, ob die Tests das Richtige fragen und ob Fehlerpfade fehlen (derzeit Claude).
4. **Außenwirkung** (Mail, echte Daten) nur mit technischer Sperre **vor** der Umsetzung (Beispiel `SCOUT_ALLOW_SEND`).

Das lokale Review ist Zweitmeinung, keine Freigabe. Ablauf und Befehle: `role-split/kette/README.md`.

## Schwelle für „tragfähiger"

Drei Ketten in Folge, in denen kein kritischer Defekt bis zum Commit durchrutscht, ohne Eingriff während der Kette
(Gegenprüfung erst nachträglich gegen einen vorher geschriebenen Schlüssel). Nächster Lauf: K4 „Scout-Bericht wird
überschrieben" (ab 19.10.). Hakt es weiter am Review: Qwen3.6 als Reviewer und Review mit Thinking vergleichen.
