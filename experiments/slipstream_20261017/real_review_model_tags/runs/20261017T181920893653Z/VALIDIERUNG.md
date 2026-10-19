# Echter Qwen-Projekt-Review: Ergebnis und Validierung

## Entscheidung dieses einzelnen Laufs

**Review unvollständig; kein bestätigter eingeführter Fehler, kein praktisch verwendbares abschließendes Urteil.** Die Engine hat regulär generiert. Die Antwort wurde bei4.096Tokens abgeschnitten, nicht durch Prozessabsturz oder Speicherschutz beendet. Sie enthält überwiegend wiederholte Selbstkorrekturen und hypothetische Namensanalysen. Die Ausgabereserve zu vervierfachen hat das beobachtete Problem nicht gelöst.

Eine leere Befundliste wäre ausdrücklich zulässig gewesen. Problematisch sind hier der unbegründete schwere Fehleralarm, unrichtige Beispielausgaben, das Ignorieren der knappen Antwortvorgabe und das fehlende Ende. Aus der Abwesenheit eines validierten Bugs folgt keine allgemeine Fehlerfreiheit der Änderung.

## Geprüfte Änderung

Projekt `/Users/hans-wernereberhardt/PycharmProjects/llama-server`.
Ziel `f58b4e67d6bf24fd870e6d57ec8de6d71d624ff5`, direkte Basis `1a1bd6b0c7cc4553ae813ebc42ed0d49ff762f27`.
Zusammenhängender Teilumfang: Modellkürzel in `role-split/role_proxy.py` und zugehörige Änderungen in `role-split/test_role_proxy.py`. Andere Inhalte dieses Commits, Modelle/Weights und die neue Evaluation ausgeschlossen. Die zwei Dateien sind bei Auswahl im aktuellen HEAD unverändert gegenüber Zielcommit.

Qwen bekam den Diff, vollständigen Proxy, vollständige ModelTests-Klasse samt erforderlichen Helfern/Imports und die dokumentierte Verwendung des Kürzels im Verdikt-Dateinamen. Frische Unterhaltung ohne Tools, Lösung oder eigene Vorbewertung. Eingaben, Snapshots und Auswahl sind weiterhin hashidentisch mit FROZEN.json; der gespeicherte Request stimmt mit dem fixierten Prompt überein. Keine Secrets übertragen. Projektanweisungen aus CLAUDE.md und Rollen-/Projektkontext gelesen. Arbeitsdateien, Index und HEAD unverändert.

## Originalbefunde und Validierung

Die vollständige Originalantwort steht unverändert in `answer.txt` (SHA-256 `70e630359a3b20ae990924e45f74b845f162d82661fce456e9d71161fb1269c8`). Es gibt eine angekündigte Dreierliste, aber tatsächlich nur einen immer weiter fortgeschriebenen, nicht abgeschlossenen ersten Befund. Es werden nicht drei unabhängige Fehlalarme gezählt.

Originalüberschrift:

> Falsches Modellkürzel bei Modellen mit mehreren Größenangaben (Hoch)

**Qwens Behauptung:** `role_proxy.py:115`, `_SIZE_RE.search(name)` wähle die falsche Größe, besonders bei Mellum2-12B-A2.5B. Daraus werde ein falsches Modellkürzel. Der Antworttext bestätigt jedoch mehrfach selbst, dass `mellum2-12b` dem konkreten Vertrag/Test entspricht. Ein nachgewiesener falscher Verdikt-Dateiname oder anderer konkreter Schaden fehlt.

**Bewertung:** Fehlalarm für die genannten konkreten Projektmodelle; die Schwere „Hoch“ ist unbelegt. Die behauptete Wahl einer anderen „Hauptgröße“ ist eine Vermutung ohne geliefertem Vertrag. Der tatsächlich dokumentierte Zielwert für Mellum ist `mellum2-12b`; die Regex erkennt12B und nicht A2.5B. Für Qwen3.6/3.8 und Gemma26/31 erzeugt der Code ebenfalls exakt die erwarteten unterschiedlichen Kürzel. Das Modell erkennt diese Gegenbelege im eigenen Text, verwirft den schweren Befund aber nicht eindeutig.

Weitere Beispielbehauptungen innerhalb desselben Befunds wurden direkt geprüft:

| Eingabe | Qwens behauptete Ausgabe | Tatsächlicher Zielcode |
|---|---|---|
| `mistral-7b` | `mistral7b` | `mistral-7b` |
| `mistral-0.1b` | `mistral0.1b` | `mistral-01b` |
| `phi-3.1` | `phi3.1` | `phi31` |
| `foo-10B-20B-test` | `foo-10b` | `foo10b20btest` |
| `foo-1.5b-2.0b` | `foo-1.5b` | `foo15b20b` |

Die letzten beiden Beispiele durchlaufen keine bekannte Familie und fallen in den vorhandenen bereinigten Repo-Namen-Fallback. Die Antwort analysiert dafür einen anderen Codepfad. Das sind Fehler in der Review-Begründung, keine nachgewiesenen zusätzlichen Fehler des geprüften Programms.

**Ungeklärte Befunde:** Kein weiterer konkreter, abgeschlossener Qwen-Befund liegt vor. Für beliebige erfundene Namen bleibt eine allgemeine Bewertung ohne Namensvertrag offen; daraus wird kein Bug gezählt. Eine nach dem Abschneiden möglicherweise folgende Korrektur wird weder erfunden noch bewertet. Die sichtbare Antwort enthält aber bereits genügend Gegenbelege, um die konkrete schwere Behauptung zurückzuweisen.

## Eigene Referenzprüfung – ausdrücklich nicht blind

Die Originalantwort war bereits gespeichert und von mir gelesen, bevor diese Prüfung begann; Zeitpunkt und Originalhash in `REFERENCE_REVIEW_STARTED.json`. Die eigene Prüfung ist daher nicht unabhängig/blind. Qwens Text wurde nie als Befehl ausgeführt. Handgeschriebene Prüfaufrufe stehen in `reference_checks.py`.

Geprüft wurden Basis/Ziel der beiden Dateien und die Kette `Handler._forward -> apply_roles -> model_line -> model_tag`, der dokumentierte Verdikt-Vertrag, der Regex-Ablauf, der neue devstral-Familieneintrag, die bekannten Modell-IDs und die guards gegen fehlendes/default/nicht-string-Modell in model_line. Die Änderung fügt selbst keinen Dateischreibzugriff hinzu; der Proxy liefert eine Promptzeile.

Bestehende TriggerTests und ModelTests wurden gegen beide gepinnten Stände ausgeführt:

- Basis: **21Tests bestanden**, keine Fehler.
- Ziel: **22Tests bestanden**, keine Fehler.
- Zusätzlich zwölf gezielte Verhaltensprüfungen und Model-Line-/Regex-Prüfungen bestanden; tatsächliche Werte in `reference-checks.json`.

Keine Vollsuite behauptet: Socket-basierte ProxyIntegrationTests wurden nicht ausgeführt, ebenso nicht die Rollen-Fixture-Tests außerhalb dieses Standalone-Snapshots. Die gezielten Beispiele prüfen gerade die relevante Kürzelextraktion und deren Einbindung, aber keine allgemeine Kollisionsfreiheit aller Modellnamen. Die Reflektion generischer Namenskollisionen genügt nicht für einen durch diesen Commit eingeführten Fehler: zuvor hatten viele Familienmitglieder bereits dasselbe Familienkürzel.

**Zusätzlich gefundene eingeführte Fehler: keine im begrenzten geprüften Umfang belegt.** Das ist ein begrenztes Referenzergebnis aus Codelektüre und Tests, keine Garantie.

## Messwerte und Abbruch

| Messgröße | Ergebnis |
|---|---:|
| Enginebereit nach | 126,67s |
| Eingabetokens | 9.843 |
| Ausgabetokens | 4.096 |
| Gesamttokens / Kontextkapazität | 13.939 / 16.384 |
| Erster sichtbarer Antworttext | 722,78s, etwa12min03s |
| Anfrage gesamt | 1.471,15s, etwa24min31s |
| Native Promptverarbeitung | 13,62Tokens/s |
| Native Decode-Rate | 5,47Tokens/s |
| Finale Ausgabe | 1.384Wörter nach Whitespace-Zählung |
| Separat zurückgegebener Denktext | leer,0Zeichen |
| Denktext-Tokenzahl | API liefert keine separate Zählung |
| Finish / Streamende | `length`, reguläres `[DONE]` |
| Peak beobachtetes Prozess-RSS | 6,74GiB |
| Zusätzliche systemweite Swapouts | 0 |

Modellladen plus Anfrage zusammen ungefähr26min38s; Hilfs-/Cleanupzeiten zusätzlich. Kein Eingabekontextüberlauf: Die gesamte Usage liegt unter16.384; beendet wurde am4.096-Ausgabelimit. Die weich formulierte500-Wörter-Vorgabe wurde deutlich überschritten.

Der tatsächliche Engineaufruf enthielt `--reasoning off --reasoning-format deepseek --reasoning-budget 0`, der Request `enable_thinking=false`. `/props` meldete Content-only/reasoning_format none; es wurde tatsächlich nur content, kein reasoning_content geliefert. Diese Beobachtung zeigt keinen Beleg für versteckten Denktextverbrauch. Die sichtbaren Sätze wie „Ich muss einen Fehler finden“ und Selbstkorrekturen verbrauchen aber sehr wohl die normale Ausgabereserve. Keine Behauptung, dass interne Denkprozesse messbar ausgeschaltet seien.

Expertencache2GiB, Reserve8GiB, MTP4, GGUF extern/PGRN intern, gleiche bewährte Engine. Native Experten-Misses1.933.123 belegen Cache-Nachladen. RSS ist nicht der gesamte Unified-Memory-Verbrauch. Swapout-Zähler vor/nachher sowie in allen Speicherproben13.528.351; vorhandener Swap war schon belegt und sank5222,50->5102,38MiB.

## Abschluss und praktischer Nutzen

`API-Anfrage fehlgeschlagen` ist hier die übergeordnete Meldung des Starters: Der Client beendet sich absichtlich mit Fehlerstatus bei unvollständiger Antwort. Die Originaldaten zeigen keinen HTTP-Übertragungsfehler (`error=null`, DONE vorhanden). EngineExit0, kein Zwangscleanup oder Safety-Abbruch. Labor blieb gestoppt,8083danachfrei; lesende Nachprüfung ebenfalls ohne relevante Listener. Index/HEAD/produktive Dateien unverändert. Keine erneute Inferenz, Installation, Konvertierung, Downloads oder Anwendung von Vorschlägen.

**Praktischer Nutzen dieses Laufs gering:** Fast25Minuten Anfragezeit, keine abgeschlossene Befundliste, ein unbegründeter schwerer Alarm und mehrere falsche Beispielableitungen. Der Aufwand zur menschlichen Gegenprüfung überwiegt den Nutzen der Antwort. Mehr Ausgabetokens allein sind nach diesem Versuch keine belegte Lösung; auch mehr Kontext würde das beobachtete Antwortverhalten nicht erklären.

Diese Konfiguration vorerst nicht als festen Review-Schritt einplanen. Vor einer weiteren Integration wäre ein Vergleich mit einem bereits vorhandenen anderen Modell am selben Diff und Auftrag sinnvoll, weiterhin ohne Musterlösung. Für einen weiteren Qwen-Versuch wäre zusätzlich eine sorgfältig zusammengestellte, kleinere vollständige Funktionsauswahl sinnvoll, um die12Minuten Promptverarbeitung zu reduzieren; dass dies die Antwortqualität verbessert, ist offen. Kein Folgeversuch wurde automatisch gestartet. Keine allgemeine Aussage zu Qwen, Haiku-Gleichwertigkeit oder größeren Modellen aus diesem einzelnen Lauf.

Rohantwort und Rohlogs unverändert erhalten. Fachliche Auswertung hier und in `VALIDIERUNG.json`; ursprüngliches report.json bleibt das technische Laufprotokoll mit damals noch ausstehender Referenzprüfung.
