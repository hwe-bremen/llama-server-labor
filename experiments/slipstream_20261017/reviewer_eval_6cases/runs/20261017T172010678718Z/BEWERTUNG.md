# Qwen als Code-Reviewer: sechs kleine Fälle

## Ergebnis und Empfehlung

Die sechs API-Anfragen haben jeweils Text bis zum vereinbarten Limit geliefert. **Alle sechs Antworten sind unvollständig**: jeweils exakt 1.024 Ausgabetokens, `finish_reason=length`, anschließend reguläres SSE-`[DONE]`. Das ist ein Ausgabelimit, kein Engine-Absturz. Kein vollständig abgeschlossener Review liegt vor.

Im tatsächlich vorhandenen Text sind die primären Fehler der Fälle01,02 und04 mit richtiger Kausalkette erklärt. Fall03 nähert sich der verlorenen Invalidierung an, beendet die Erklärung aber nicht. Bei den korrekten Gegenbeispielen werden korrekte Mechanismen anerkannt, zugleich entsteht erheblicher spekulativer Prüfaufwand. Daraus folgt weder eine Gesamtnote noch eine allgemeine Qualitätsaussage.

**Zuerst Antwortdisziplin und ausreichenden Ausgaberaum prüfen, danach einen eng begrenzten echten Projektfall.** Noch kein großer Repository-Review: Schon kleine Fälle benötigen rund vier Minuten und bleiben abgeschnitten. Ein größerer Eingabekontext ist durch diesen Lauf nicht als nötig belegt; die tatsächlichen Prompts haben399–760Tokens. Auch ein Modellwechsel lässt sich daraus noch nicht begründen.

Ein späterer, getrennt versionierter Versuch sollte eine knappe Befundstruktur und eine Umfangsvorgabe verwenden, mit ausreichendem technischem Ausgabelimit als Reserve. Das erhöht gegebenenfalls die Laufzeit; bei unverändert rund5Tokens/s würden weitere1.024Tokens grob weitere3–4Minuten Decode benötigen, keine Messung eines solchen Folgeversuchs. Die alte Rubrik, Prompts und Antworten bleiben unverändert. Eine Wiederholung wäre eine weitere Entwicklungsrunde auf bekannten Aufgaben, keine unabhängige Bestätigung. In dieser Auswertung wurde kein neuer Modelllauf gestartet.

## Durchführung und belastbare Grenzen

Lauf: `20261017T172010678718Z`, Nutzer-Terminal, 17.10.2026, ungefähr19:20–19:46Uhr Europe/Berlin. Identische bewährte Engine, verifiziertes Qwen3.6-35B-A3B-UD-Q4_K_XL-GGUF extern, aktive PGRN intern. Expertencache2GiB, Reserve8GiB, Batch/UBatch32, MTP4, Temp0/Seed42, ein Slot. Kontext4096 statt früher512, kein Kontextverschieben, Thinking im Request ausgeschaltet; kein separater Reasoning-Text in den Antworten. Das verhindert keine Selbstkorrekturen im sichtbaren Text.

Alle26 eingefrorenen Dateien stimmen weiterhin mit FROZEN.json überein. Alle sechs gespeicherten Nachrichtenpaare stimmen exakt mit den eingefrorenen Prompts überein. Musterlösung/Rubrik/Verifikationstests wurden nicht übertragen, keine Werkzeuge angeboten. Je Fall frische System-/User-Nachrichten, keine Historie; native Cache-Prompttokens jeweils0. Reihenfolge01–06, Expertencache innerhalb desselben Prozesses warm. Keine Modellantwort als Befehl ausgeführt. Bewertung ausschließlich anhand gelieferten Codes/Vertrags und vorhandenen Textes, nicht anhand erdachter Fortsetzungen.

## Einzelfälle

| Fall | Bewertung des vorhandenen Fragments | TTFT s | Gesamt s | Decode Tokens/s |
|---|---|---:|---:|---:|
| case01 | Primärer Fehler im vorhandenen Fragment gefunden; Review unvollständig | 36.9 | 240.0 | 5.04 |
| case02 | Primärer Fehler im vorhandenen Fragment gefunden; Review unvollständig | 26.7 | 236.3 | 4.89 |
| case03 | Im vorhandenen Fragment teilweise erkannt; Review unvollständig | 29.9 | 228.9 | 5.15 |
| case04 | Primärer Fehler im vorhandenen Fragment gefunden; Review unvollständig | 33.6 | 244.3 | 4.86 |
| case05 | Im Fragment kein aufrechterhaltener konkreter Fehler; Gegenbeispielprüfung unvollständig | 24.3 | 234.3 | 4.87 |
| case06 | Im Fragment korrektes Verhalten erkannt; Gegenbeispielprüfung unvollständig | 45.8 | 238.2 | 5.32 |

### case01

**Primärer Fehler im vorhandenen Fragment gefunden; Review unvollständig.** Cache-Key ohne tenant_id, A/B-Ablauf und private Datenweitergabe ausdrücklich richtig erklärt. Anfangszusammenfassung behauptet fälschlich keine Fehler, später ausdrücklich korrigiert.

Ursache: richtig; Ort: richtig. Unbegrenztes Caching jeder neuen Frage ist ein zusätzlich plausibles Kapazitätsrisiko; Memory Leak ist dafür unpräzise. Keine erfundene zweite Codeursache nötig.

Umgang mit Vermutungen: anfangs widersprüchlich, später als konkreter Fehler korrigiert.

### case02

**Primärer Fehler im vorhandenen Fragment gefunden; Review unvollständig.** CancelledError erbt nicht von Exception; release wird übersprungen, spätere Requests blockieren. Position14–21 umfasst relevante Kette.

Ursache: richtig; Ort: richtig. Anfangs als bloßes Designrisiko verharmlost, im Fazit als konkreter Bug erkannt; Race Condition ist für diesen Cleanup-Fehler eine unpräzise Bezeichnung. Nebenbemerkung zu BaseException/SystemExit/KeyboardInterrupt missverständlich, keine weitere eigenständige Fehlerursache.

Umgang mit Vermutungen: anfangs widersprüchlich, Fazit konkreter Fehler.

### case03

**Im vorhandenen Fragment teilweise erkannt; Review unvollständig.** Load außerhalb Lock, konkurrierendes Publish und Invalidierung werden angesprochen; kein sauber abgeschlossener Ablauf alter Snapshot -> invalidate -> verspätetes Publish -> dauerhaft alter Cache.

Ursache: teilweise; Ort: richtig. Behauptung eines Verstoßes gegen Store-Zugriff außerhalb Lock wird ausdrücklich zurückgenommen. Aussage Code löscht Cache erst nach load ist falsch: invalidate wartet nicht auf load. Es fehlt eine eindeutige abgeschlossene Kausalkette, nicht nachgewiesen ist ein generelles Übersehen.

Umgang mit Vermutungen: wechselnde Bewertung, keine abgeschlossene Auflösung.

### case04

**Primärer Fehler im vorhandenen Fragment gefunden; Review unvollständig.** BEGIN IMMEDIATE hält globale Schreibsperre über await generate; zweite Session läuft nach50ms in database is locked.

Ursache: richtig; Ort: richtig. Atomicity-Verletzung ist kein belegter weiterer Fehler: Rollback erfüllt gerade den gelieferten Vertrag; Text relativiert eigene Überschrift. Initialisierungs-Race mit mehreren Instanzen/Threads fällt außerhalb der expliziten einen Instanz/einen Eventloop; kein belastbarer Befund für diesen Fall.

Umgang mit Vermutungen: bedingt formuliert, aber irreführende Fehlerüberschriften.

### case05

**Im Fragment kein aufrechterhaltener konkreter Fehler; Gegenbeispielprüfung unvollständig.** async with gibt Semaphore bei Cancellation frei. Das Modell bestätigt diese Semantik und den garantierten CancelledError-Durchlauf später selbst.

Ursache: korrekte async-with-Freigabe letztlich anerkannt; Ort: richtig. Anfänglicher Alarm signifikantes Designrisiko/Deadlocks unbelegt unter geliefertem Vertrag. Szenario verschluckter Cancellation widerspricht ausdrücklicher Voraussetzung und wird im Text letztlich zurückgenommen. Zweiter Befund zu nicht-abbrechbaren Operationen nur angeschnitten. Kein vorbehaltlos bestandener Kontrollfall, aber auch nicht als bestätigte falsche Bugbehauptung zählen.

Umgang mit Vermutungen: Vermutungen kenntlich, teilweise vertraglich ausgeschlossen und zurückgenommen.

### case06

**Im Fragment korrektes Verhalten erkannt; Gegenbeispielprüfung unvollständig.** Kein logischer Fehler behauptet; Mandantenschlüssel und Epoch-Abgleich werden als korrekt anerkannt.

Ursache: weitgehend richtig; Ort: weitgehend richtig. Ungültige tenant-ID ist ausdrücklich außerhalb Vorbedingungen; als bedingtes Risiko markiert, kein Fehlalarm zu aktueller Korrektheit. Wahl KeyError vs ValueError ist API-Designhinweis. Detailfehler: epoch wird angeblich vor dem Lock gelesen; tatsächlich innerhalb des Locks. Kein vollständiger Fehlalarmfreiheitsnachweis wegen Abbruch.

Umgang mit Vermutungen: bedingtes Risiko ausdrücklich kenntlich.

### Belegstellen und Gegenprüfung

- **01:** Das Modell schreibt „Dies führt zur Auslieferung von Daten des falschen Mandanten“ und zeigt A/B mit identischer Frage. `retrieval.py:9–12` enthält ausschließlich den Frageschlüssel. Der private Test reproduziert A-private für B. Der zusätzliche Hinweis auf unbegrenzte Cache-Einträge ist nachvollziehbar, weil auch leere Antworten je beliebiger Frage gespeichert werden.
- **02:** „Der except Exception: Block ... fängt CancelledError nicht“ und „alle weiteren Anfragen blockieren dauerhaft“ treffen den Fehler in `provider.py:15–21`. Der private Test zeigt den gesperrten Slot nach Cancel. Der Kommentar zur BaseException-Hierarchie im weiteren Text ist teilweise unsauber formuliert; die zentrale Erklärung bleibt richtig.
- **03:** „Der Code löscht den Cache-Eintrag erst, wenn load fertig ist“ ist falsch: `invalidate` sperrt nur kurz den Dictzugriff und kann während des Loads laufen. Die Antwort zitiert zwar den entscheidenden Snapshot-Vertrag, bricht aber während des Codeblocks zur Invalidierung ab. Der private Test belegt das tatsächliche alte Publish nach invalidate. Nur teilweise erkannt im sichtbaren Fragment, kein sicherer negativer Schluss über eine hypothetische vollständige Antwort.
- **04:** Der Timeout-/Lock-Befund nennt `chat.py:17–21` und ist durch den vorhandenen SQLite-Test mit zweiter Session belegt. „Verletzung der Atomicity-Anforderung“ wird im eigenen Text relativiert: kein halbes Paar bei Rollback erfüllt exakt den Vertrag. Die später behauptete parallele Initialisierung mehrerer Instanzen ist im gelieferten einen ChatJournal nicht vorhanden. Kein zusätzlicher nachgewiesener Bug aus diesen Abschnitten.
- **05:** Erst „signifikantes Designrisiko ... Deadlocks“, später „Also: Kein nachgewiesener Fehler“. `async with self._slots` gibt beim ausdrücklich garantierten CancelledError-Durchlauf frei; privater Cancel-/Exception-Test bestätigt das. Die Rücknahme zählt: keine aufrechterhaltene konkrete Bugbehauptung aus dem ersten Abschnitt, aber unnötiger Alarm und irrelevante Bedingungswechsel. Der angeschnittene zweite Befund bleibt unbewertbar.
- **06:** „kein Fehler im aktuellen Betriebsmodus“ zum ungültigen Mandanten ist richtig eingegrenzt; die API weist diese IDs vorab ab. Die Epoch-Begründung erkennt korrekt das Nicht-Publizieren alter Loads nach invalidate. „epoch vor dem Lock-Halten ... gelesen“ ist dagegen ein Detailfehler: `cache.py:20–21` liegt innerhalb des Locks. Der private Kontrolltest bestätigt Isolation, Invalidierung und Kapazitätsgrenze. Kein belastbarer aktueller Bug im vorhandenen Text; wegen Abbruch kein vollständiger Kontrollfall-Pass.

Die sechs privaten Tests wurden vor Modellantworten ausgeführt und gespeichert; die ersten vier reproduzieren bewusst den Fehlerzustand, die letzten beiden prüfen korrekte Abläufe. Das ist keine repräsentative Testabdeckung aller möglichen Eingaben. Neue Codeänderungen oder nachträglich angepasste Bewertungskriterien gibt es nicht.

## Laufzeit, Speicher und Abschluss

Median Antwortdauer237,24s, Spannweite228,91–244,29s; TTFT24,26–45,83s. Native Decode4,86–5,32Tokens/s, Median4,96. Die vorab festgelegte Orientierung180–360s ordnet die Zeit eher asynchron ein. Da sämtliche Antworten unvollständig sind, ist die Laufzeit eines brauchbaren abgeschlossenen Reviews damit noch nicht nachgewiesen. Sechs Anfragen zusammen23min42s, Laden bis /health126,65s, Gesamtlauf ungefähr25min49s. Lange, wiederholende Erläuterungen und Selbstkorrekturen verbrauchen einen wesentlichen Teil des Ausgaberaums.

Peak beobachtetes Prozess-RSS7,84GiB (8.218.272KiB), mehr als die früheren kurzen512-Kontext-Versuche. RSS ist nicht der gesamte Unified-Memory-Verbrauch. Swapout-Zähler blieb bei13.490.826, keine zusätzlichen Swapouts während aller Samples; vorhandener belegter Swap sank6682->6538MiB. Native Experten-Cache-Misses sind positiv, kein reiner Test ohne Expertenstreaming.

`report.json` meldet `inference_passed=false`, weil der Client die sechs abgeschnittenen Antworten absichtlich als unvollständig verworfen hat (`API-Anfrage fehlgeschlagen`). Die Meldung beweist keinen Prozess- oder Modellladefehler: Alle sechs Streams hatten DONE, Usage und1.024generierteTokens. Engine-Exit0, Labor vor/nachher gestoppt, Port8083frei. Bei der lesenden Nachprüfung ebenfalls keine relevanten Listener. Kein Labor automatisch gestartet und keine bestehenden Dienste gestoppt.

Die Ausgabe „Router vollständig entladen ... False“ ist im Modus `lab_stopped` kein zusätzlicher Fehler: Es gab keinen laufenden Router und daher keine Router-Entladeprüfung. `Entladeaufruf ... []` ist in diesem Modus erwartbar.

## Einordnung und Rohdaten

Aufgabenkonstruktion, Musterlösung und Bewertung stammen vom selben Assistenten; die Unabhängigkeit ist begrenzt. Nur sechs handgefertigte Fälle, je ein Lauf, bekannte Reihenfolge, keine Vergleichsmodelle. Keine Aussage über Haiku, Modelle oberhalb48GB oder allgemeine Reviewerqualität. Einzelne brauchbare Funde ersetzen keine menschliche Prüfung, und wegen der abgeschnittenen Kontrollantworten ist eine Fehlalarmquote nicht belastbar.

Rohdaten bleiben unverändert: responses.json, case01–case06-request.json, -stream.jsonl, -answer.md, engine.log, client.log, memory.jsonl und report.json. DURCHFUEHRUNG.md ist der ursprüngliche technische Zwischenstand; die fachliche Auswertung steht hier und maschinenlesbar in BEWERTUNG.json. FROZEN.json und private/RUBRIK.md bleiben unverändert.
