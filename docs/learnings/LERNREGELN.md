# Lernregeln der Kette (Stand 28.10.2026, nach K11a2)

Verdichtet aus 10 Ketten. Format: **Rnn** Regel – *Warum (Quelle)*. Höchstens ~100 Zeilen; neue Regel nur für wiederkehrende oder teure Fehler.
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

## Automatik (K8)
- **R34** Ein Review über die API ohne Werkzeuge sieht **nur das Paket**: Fehlt dort der Code, urteilt das Modell über Spec und Übergabe – und glaubt der Übergabe. Paket vor jedem automatischen Review auf „Geänderte Code-Dateien: keine" prüfen. – *K8: echter Lauf meldete A4/A5 fälschlich als fehlend.*
- **R35** Werkzeuge der Kette dürfen den Ordner, den eine Kette ändert, nicht ausblenden (auch nicht `role-split/` und `tests/`). – *K8: `paket`/`gegenprobe` blind für `kette.py` selbst.* (behoben K9)
- **R36** Tests mit Servern, Threads oder Netz immer mit Zeitlimit starten (`timeout 120 …`); ein hängender Test sieht aus wie langsames Arbeiten. `server.shutdown()` nur bei `serve_forever()`, sonst `server_close()`. – *K8.*
- **R37** Automatische Prompts aus den bewährten Hand-Prompts ableiten (Pflichtfragen mit Erläuterung, Verdikt-Vorlage wörtlich), nicht neu und kürzer schreiben; Rollen-Trigger wie `@review` wirken nur über den Proxy. – *K8.*

## Automatik (K9)
- **R38** API-Aufrufe übernehmen das Sampling des Servers (`config/models.ini`); keine feste Temperatur im Aufruf. Bricht eine Antwort mit `finish_reason=length` ab, erst den Text auf eine Schleife prüfen, dann das Limit erhöhen. – *K9: Temperatur 0,1 statt 0,6 → 35B wiederholte sich bis 16 000 Token; mit Server-Werten 1 200–1 900 Token.*
- **R39** In die Befund-Tabelle gehören nur echte Mängel; ohne Mangel genau die Leerzeile `| – | nein | nein | nein | – | – | keine Befunde | – |`. Ein „hoch" aus dem automatischen Review wird gegengeprüft, bevor nachgebessert wird. – *K9: Bestätigung mit „Unbemerkt: ja" ergab NACHBESSERN; derselbe 35B am selben Paket einmal PASS, einmal 2× unbegründet „hoch".*
- **R40** Wer die Arbeit eines Umsetzers zurücksetzt, korrigiert auch dessen Handover (oder markiert ihn als ungültig) – der neueste Handover geht ins Review-Paket. – *K9 T10: falscher K7-NB3-Handover („Datei existiert nicht") ließ das Review A4/A5 anzweifeln.*
- **R41** Paket für eine abgeschlossene Kette nur bei sauberem Arbeitsstand bauen: Nicht committete und unversionierte Dateien zählen immer zur Kette, für die das Paket gebaut wird. – *K9: K7-Paket mit uncommitteter K9-Arbeit 175 161 Zeichen → Exit 1.*
- **R42** Umsetzer läuft zwei Nachbesserungen ohne Fortschritt oder deutet die Spec um, damit Tests grün werden ⇒ Gegenprüfer übernimmt, Dauer wird gemessen. Selbst-Commits des Umsetzers trotz „Kein Commit" melden. – *K9: 27B NB1+NB2 je ~4,5 h, `role-split/`-Sonderregel, Selbst-Commit `1b2e74c`.*

## Automatik (K10)
- **R43** Lokale Umsetzer nach Aufgabengröße einsetzen: eine Datei, ~100 Zeilen, wenige Tests schafft der 35B in Minuten; ein Umbau von Hunderten Zeilen in einer großen Datei plus Dutzende Tests nicht → teilen oder übernehmen. – *K10: 35B scheiterte an ~460 Zeilen in `kette.py` + 33 Tests (`main()` gelöscht); dieselbe Kette als Mini-Spec: 35B 3:21, 27B 14:15, beide korrekt.*
- **R44** Spec-Korrekturen ab der zweiten Runde schreibt die externe Stimme direkt in die Spec (als „präzisiert" markiert), statt sie dem lokalen Modell zurückzugeben. – *K10: Korrekturrunde dauerte länger als die Spec selbst, Kontext voll, zweiter Chat nötig.*
- **R45** Attrappen für Fremdprogramme sperren sich selbst (Arbeitsordner **und** jedes Schreibziel im Temp-Ordner), und jeder Test prüft am Ende, dass HEAD, Status und Prüfsummen des echten Repos unverändert sind. Auch an die Gegenprobe denken: Dort läuft der Test gegen die **alte** Attrappe. – *K10: Tests des Umsetzers committeten ins echte Repo; Ausbruchs-Test hätte mit alter Attrappe hinausgeschrieben.*
- **R46** OpenCode ohne TUI: Verbote als `deny` in die Agent-Datei (Umgebungsvariablen überstimmen Agent-Regeln nicht, `ask` beendet den Lauf stumm); Erfolg nur aus dem JSON-Strom (`reason: stop`), nie aus dem Exit-Code. – *K10 Probe P1–P6.*
- **R47** Schreibbereich einer Spec nie unter Pfaden, die Paket und Gegenprobe ausblenden (`PAKET_NIE`: `docs/`, `experiments/`). – *K10 Abnahme: Mini-Spec unter `experiments/` → „Keine geaenderten Code-Dateien", Exit 1 trotz korrektem Code.*

## Automatik (K11a/K11a2)
- **R48** Tests vor der Umsetzung schreiben (Claude), in der Spec als `## Vorgabe-Tests` markieren und vor dem Start mit `kette.py tests-pruefen` prüfen; der lokale Umsetzer schreibt nur Code. Ohne ausdrückliches Verbot im Prompt schreibt der 35B Vorgabe-Tests passend zu seinem Code um. – *K11a: Tests überschrieben, 1/8 gegen die echten Vorgabe-Tests; K11a2 mit Prompt-Abschnitt: Testdatei unverändert, Code gleichwertig zur Referenz in 12:28.*
- **R49** „Rot vorab“ schließt Tests für bestehendes Verhalten aus: solche Tests mit `(Bestand)` im Titel kennzeichnen (müssen vorab grün sein) oder in eine Methode legen, die wegen eines neuen Teils rot ist. – *K11a2: Befunde 1, 4, 5 der Gegenprüfung waren sonst nicht als Vorgabe-Tests schreibbar.*
- **R50** Ein neuer Schutzmechanismus der Kette greift erst ab der nächsten Kette: Den Lauf, der ihn baut, nicht als Messung werten – Mechanismus von Claude einbauen, an der nächsten kleinen Kette messen. Nach jedem Lauf **alle** Testdateien laufen lassen, nicht nur die der Kette. – *K11a: alter Prompt verlangte noch „Tests schreibst du“; Regression 22/37 sah `pruefen` nicht.*
- **R51** Eigene Vorgabe-Tests per Mutation gegenprüfen: je Anforderung die tragende Zeile im Referenzcode entfernen – mindestens ein Test muss rot werden; jede Zeile der Fehlerpfad-Tabelle braucht einen Test oder „–“ mit Grund. – *K11a: frische Instanz fand zwei Lücken in Claudes Tests (T5, T7), beide per Mutation bestätigt.*
