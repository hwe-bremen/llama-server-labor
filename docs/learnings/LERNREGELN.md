# Lernregeln der Kette (Stand 25.10.2026)

Verdichtet aus 7 Ketten. Format: **Rnn** Regel – *Warum (Quelle)*. Höchstens ~100 Zeilen; neue Regel nur für wiederkehrende oder teure Fehler.
Details je Kette: `kette_<kurztitel>.md`.

## Spec
- **R01** Jede Designentscheidung und jedes „akzeptierte Restrisiko" gegen Hawes Originalanforderung als Fehlerpfad durchspielen: Was passiert beim nächsten Lauf konkret? – *K4: Spec führte „Merker vor Versand" ein, Mail kam nach SMTP-Fehler nie an.*
- **R02** Keine Werte, Zeilennummern oder „geprüften" Fakten aus dem Gedächtnis. Was nicht im Repo steht, kommt unter „Offene Fragen". – *K3: erfundene ISO-Woche wanderte über Spec bis in den Docstring; R1: erfundene Zeilennummern.*
- **R03** Ein Modell ohne Rechenwerkzeug rechnet nicht im Kopf (Datum, Kalender, Größen): Werte im Test berechnen lassen. – *K3: Schleife beim „Nachrechnen".*
- **R04** Außenwirkung (Mail, Netz, Schlüsselbund, echte Daten, Docker) braucht eine **technische** Sperre für Tests, nicht nur einen Satz. – *R2: echter Gmail-Versand im Test; K7: Test las den echten Schlüsselbund-Dienst.*
- **R05** Eine Prüfung, die den Normalbetrieb verbietet, ist ein Fehler: Sicherheitsprüfungen nur für den Ausnahmefall (z. B. unverschlüsselt nur mit Schalter **und** localhost). – *K7 A5: „Nicht-localhost → Exit 1" hätte den Echtbetrieb blockiert.*
- **R06** Ein echtes Modell lässt sich nicht zum Scheitern zwingen: Fehlerpfade des Modells deterministisch per Attrappe testen, im echten Lauf nur „kein Hänger, Eintrag vorhanden". – *K7 Giftmails 09/10.*

## Umsetzung
- **R07** Nur die im Auftrag genannten Dateien ändern; Nachbesserungen additiv, nie „komplett neu schreiben". – *K3: Tests beim Neuschreiben gelöscht; K7 NB3: Testdatei außerhalb des Auftrags ersetzt.*
- **R08** Übergabe nur mit tatsächlich in dieser Sitzung erzeugter Ausgabe; „Abweichungen: Keine" ist eine Behauptung, die geprüft wird. – *R2, K7 NB3: falsche Angaben in der Übergabe.*
- **R09** Vorgaben im Prompt nicht still ändern (Namen, Parameter, Testfälle). – *K3: `kein_main` → `__main__`, echter Scout lief im Test.*

## Tests
- **R10** Ein Test zählt erst, wenn er mit dem alten Code rot wird (Gegenprobe). GRUEN-Tests einzeln begründen. – *K3, K4: Tests verglichen eine Funktion mit sich selbst.*
- **R11** Den echten Einstiegspunkt mindestens einmal ausführen (Skript starten, nicht nur Funktionen importieren). – *K3: relativer Import ließ den Scout bei jedem Lauf abstürzen, 12 Tests grün.*
- **R12** Den Erfolgsfall testen, nicht nur Fehler gegen tote Ports. – *K3, K4.*
- **R13** Testdaten, Erwartungen und Spec müssen zueinander passen (gleiche IDs, gleiche Fälle). – *K7: Mails und `erwartungen.json` beschrieben zwei verschiedene Sätze; niemand merkte es.*
- **R14** Mock-Tests beweisen nichts über die echte Umgebung. Wo es eine Außenwelt gibt, ist ein **echter Lauf** Pflichtphase (Testserver, echtes Modell). – *K7: Docker-Port vor Dienst, Umlaute in smtplib, `unknown-8bit` – alles für 31 Mock-Tests unsichtbar.*

## Review
- **R15** Prüfen gegen die **Anforderung**, nicht nur gegen die Spec. – *K4: alle Reviewer bestätigten den Spec-Fehler; mit Originalanforderung fand dasselbe Modell ihn.*
- **R16** Schwere mechanisch: ja bei Datenverlust / Unbemerkt / Harte Vorgabe ⇒ hoch (`kette.py urteil`, `zusammenfuehren`). Modelle gewichten zu niedrig. – *R1, R2, K3.*
- **R17** Zwei unabhängige Läufe (Anforderung + Betrieb), mechanisch vereinigt. – *R1 Schritt 3+4, K6.*
- **R18** Pflichtfragen je Anforderung: erzwungen oder nur verlangt? Leerer/abweichender Fall? Markiert, aber nie gezeigt? Läuft die Absicherung ins Leere? Widersprüchliche Anweisungen? Satz für Satz nach Normal-/Wiederholungs-/Fehlerlauf? – *K4–K6, Fehlerklasse „verlangt, aber nicht abgesichert".*
- **R19** Zusätzlich fragen: Was fasst jeder Aufruf außerhalb des Repos an, mit welchen Werten, wenn niemand etwas setzt? Läuft Aufräumen bei **jedem** Ausstieg? – *K7: beide Review-Läufe verfehlten echten Schlüsselbund-Dienst und `trap ERR`.* (noch nicht im Prompt)

## Robustheit (wiederkehrende Fehlerklasse „Sicherung läuft ins Leere")
- **R20** Fehler melden reicht nicht: Teilerfolg ⇒ Exit ≠ 0. – *K7: Einlieferung meldete 15 Fehler, Exit 0.*
- **R21** Eine Eingabe darf nie den ganzen Lauf blockieren; dauerhafte Fehler sichtbar markieren, vorübergehende wiederholen. – *K6 Giftmail; K7: eine Mail mit unkodiertem Betreff stoppte alles.*
- **R22** Absicherungen an exakten Markern, nicht an losen Textvergleichen oder Überschriften. – *K5: `"## Fazit" in …` + exakte Ersetzung → Nachträge still verloren; K6: Marker-Prüfung nur auf Datum.*
- **R23** Optionale Prüf-Schalter, die nie übergeben werden, prüfen nichts: Pflicht machen. – *K7: Byte-Identität per optionalem `--first-run-plan`.*

## Technik-Fallen (gemessen)
- **R24** Blankes `except:` fängt auch `SystemExit` – immer `except OSError`/konkrete Klasse. – *K7 Warteschleife meldete nie „bereit".*
- **R25** Docker Desktop nimmt Port-Verbindungen an, bevor der Dienst läuft: Bereitschaft am Protokoll-Gruß prüfen (`* OK`, `220`). – *K7.*
- **R26** `smtplib.sendmail` mit `str` scheitert an Umlauten: Rohbytes senden. Header-Zeichensatz `unknown-8bit` abfangen. – *K7.*
- **R27** Netzaufrufe immer mit Timeout. – *R1: SMTP ohne Timeout, Fehler-Mail hing unbegrenzt.*
- **R28** Qwen3.x per API: `chat_template_kwargs.enable_thinking=false`, Code-Zäune vor JSON entfernen. – *K6.*
- **R29** Python hinter einer Pipe (`| tee`) puffert: `PYTHONUNBUFFERED=1` für Live-Fortschritt. – *K7.*

## Kontext und Ablauf
- **R30** Lokaler Kontext (64K) ist die harte Grenze: gezielt lesen (`search_files`, dann `read_file` mit Zeilenbereich), ein Paket je Phase statt vieler Dateien, abschnittsweise schreiben (`append_file`/`replace_in_file`). – *K4, K5, K6, K8.*
- **R31** Phase teilen: Rückfragen-Runde und Spec-Schreiben in getrennten, frischen Chats; Zustand liegt in Dateien. – *K8.*
- **R32** Rücksetzpunkt vor jeder agentischen Änderung committen. – *K7 NB2 ohne Rücksetzpunkt.*
- **R33** Erst die Datei auf der Platte prüfen, dann urteilen – Ansichten können veraltet sein. – *K7: Claude las einen alten Stand und warf dem Umsetzer zu Unrecht Erfindung vor.*
