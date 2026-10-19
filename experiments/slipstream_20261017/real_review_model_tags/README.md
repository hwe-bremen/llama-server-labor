# Echter Projekt-Review: Modellkürzel im Rollen-Proxy

Status: vorbereitet, noch keine Modellantwort. Keine eigene Referenzprüfung vorweggenommen.

## Auswahl und unveränderlicher Kontext

Zielcommit `f58b4e67d6bf24fd870e6d57ec8de6d71d624ff5`, direkte Basis
`1a1bd6b0c7cc4553ae813ebc42ed0d49ff762f27`.
Review nur der zusammenhängenden Modellkürzel-Änderung in
`role-split/role_proxy.py` und `role-split/test_role_proxy.py`.
Diese Dateien sind im aktuellen HEAD unverändert gegenüber dem Zielcommit.
Weitere Commit-Inhalte (neue Modelle und eingefrorene Scout-Evaluation) sind
explizit ausgeschlossen. Kein Review der gesamten Repository-Historie.

Übertragen werden Diff, vollständiger Proxy, vollständige Klasse ModelTests samt
benötigten Imports/Helfern sowie die dokumentierte Dateinamenkonvention als
Quellmaterial. Originalzeilen bleiben erkennbar. Keine Musterlösung, keine
Vorbewertung, keine bisherigen Reviewerbefunde. Keine .env, Laufzeitsecrets oder
Zugangsdaten. Nur explizite Nachrichtenpaare, keine Tools/Repositoryzugriff.

Geltende AGENTS.md wurden im Projekt und seinen Elternpfaden gesucht; keine
gefunden. CLAUDE.md, README und Rollenbeschreibung wurden gelesen; insbesondere
keine produktiven Kunden-/AskValentin-Daten und ausschließlich lokaler Modellzugriff.
Keine vorhandenen Arbeitsdateien geändert, kein Git-Checkout/Reset/Commit/Staging.
Alle neuen Dateien dieses Schritts ausschließlich in diesem Experimentordner.
Snapshots/Diff/Prompt/Settings/SELECTION sind in FROZEN.json gehasht.

## Engine und Ausgabe

Bewährtes v0.3.4-Bundle, llama-server10116/852e7daa1, gleicher SHA-256 wie bisher.
Aktuelle --help/--version erfolgreich ohne Modell in logs/ gespeichert.
`--reasoning off`, `--reasoning-budget 0` und `--reasoning-format deepseek`
stehen in der tatsächlichen Hilfe: Thinking aus, Budget0, getrennte Extraktion,
falls trotzdem Thought-Tags vorkommen. Das garantiert keine knappe finale Antwort.
`--verbosity` steuert laut Hilfe Logmeldungen und wird nicht als Antwortmodus verwendet.

Im vorigen Sechs-Fälle-Lauf war enable_thinking=false gesetzt, separate
Reasoning-Strings waren leer. Die Wiederholungen/Selbstkorrekturen standen in
message.content; kein Beleg, dass versteckter Denktext die1024Tokens verbraucht hat.
Jetzt exakt der vom Nutzer formulierte knappe Auftrag, höchstens3Befunde,
möglichst500Wörter, technisch4096Ausgabetokens. Keine automatische Wiederholung.

GGUF extern, aktive PGRN intern; gleiche2GiBExpertenarena,8GiBReserve,
Batch/UBatch32,IO1,MTP4,temp0,seed42. Kontext16384 statt4096, damit Diff,
vollständige Proxy-Datei, Tests und4096TokensAusgabe Platz haben. Tatsächliche
Template-Tokenzahl wird vor dem Review geprüft; bei fehlendem Platz Abbruch,
kein stilles Abschneiden/Einkürzen. --no-context-shift. Größerer Kontext kann
mehr Speicher benötigen; vorhandene Swapout-/Prozessüberwachung bleibt aktiv.

## Ausführung

Die aktuelle Umgebung verweigerte `/bin/ps` mit EPERM; deshalb lässt sich die
Abwesenheit anderer großer Modellprozesse hier nicht sicher prüfen. Kein Modell
hier gestartet. Die bereits bekannte localhost-Beschränkung wurde nicht erneut
getestet. Im normalen macOS-Terminal ausführen:

```bash
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/real_review_model_tags/run_review.py'
```

Starter verweigert laufendes Labor, belegten8083 und erkannte Modellinstanzen.
Keine automatischen Dienststopps oder Router-Entladungen. Externes Volume,
Artefaktgrößen und bisherige Hashverifikationen werden geprüft. Own-PID-Listener,
Speicher/Swapout-Überwachung, Cleanup nur eigener Engine/Client/caffeinate.
Ctrl+C führt zum Cleanup. Labor bleibt gestoppt, kein automatischer Neustart.
Gemeinsame Sperrdatei verhindert konkurrierende Experimentstarter.

Ladefrist420s, Reviewfrist1800s, kein Retry. Je nach tatsächlicher Prompt-/
Antwortlänge kann dieser Lauf deutlich länger als die kleinen Fälle dauern.
Rohtext wird weder ausgeführt noch als Konfiguration interpretiert.

## Ergebnis und anschließende Prüfung

runs/<UTC>/answer.txt und reasoning.txt enthalten die unveränderten Stringdaten,
stream.jsonl die zeitlich gespeicherten SSE-Events. responses.json enthält
Request, Usage, native Timings, ersten finalen Text/ersten Denktext getrennt,
Finish-Grund, Vollständigkeit und Wortanzahl. Reasoning-Tokenzahl nur nennen,
wenn API sie liefert; fehlende separate Angabe nicht als gemessene0 ausgeben.
report.json, engine.log und memory.jsonl enthalten Start-/Cleanup-/RSS-/Swap-
Befunde und Git-Vergleich. Eingabecontext vollständig, Ausgabe bei length oder
fehlendem DONE unvollständig. Eine leere Befundliste ist ein zulässiges Ergebnis.

Erst nach Speicherung und Kenntnis der Antwort folgt die manuelle Prüfung:

1. Originalbefunde wortgetreu zitieren, pro Befund eingeführte Änderung,
   Auslöser/Auswirkung und Fundstelle gegen Basis/Ziel prüfen.
2. Existierende ModelTests/TriggerTests des Ziel-Snapshots ohne Socket-Integration
   ausführen, Rohlog sichern. Weitere bestehende relevante Tests nur bei Bedarf.
3. Eigene Referenzprüfung von Diff/Funktionsaufrufen/Vertrag durchführen,
   ausdrücklich als **nicht blind, nach Kenntnis von Qwen** dokumentieren.
4. Bestätigte Fehler, Fehlalarme, ungeklärte Befunde und zusätzliche eigene
   Fehler getrennt dokumentieren; keine Trefferquote ohne belastbaren Schlüssel.
5. Zeit, Ausgabeumfang/Abbruch, verfügbare Denktextdaten und Swapänderung berichten.

Bei abgeschnittener Antwort keine automatische Wiederholung. Keine Änderungen
an Produktionscode oder Antwortartefakten. Kein Qualitätsversprechen gegenüber
Haiku oder anderen Modellen aus einem einzelnen Review.
