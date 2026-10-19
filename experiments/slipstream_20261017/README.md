# Slipstream: isolierter Vorbereitungsschritt vom 17.10.2026

## Abschlussentscheidung C: GLM-/PGRN-Versuch technisch blockiert

Maßgeblich ist jetzt [ENTSCHEIDUNG_GLM_SLIPSTREAM.md](ENTSCHEIDUNG_GLM_SLIPSTREAM.md).
Die ursprüngliche positive Empfehlung der konkreten GLM-Q4_K_M-Ausgabe ist
zurückgenommen. Kein weiterer Download-, Konvertierungs- oder Startplan.
Alle vorhandenen Dateien bleiben erhalten. Keine Code-/Konfigurationsänderung.

Die Remote-Metadatenprüfung ist inzwischen vollständig abgeschlossen (19,27 MB);
beide Alternativen sind inkompatibel. Zudem muss die frühere pauschale Aussage
zum Split-Guard präzisiert werden: explizite Teileliste trifft den Guard,
Einzeldatei-Einstieg trifft bei nativen Split-Sidecars auf widersprüchliche
Quellenidentität. Einzelheiten und Belege stehen in der Entscheidungsvorlage.

**Die folgenden Abschnitte sind die historische Arbeitschronik. Dortige
"nächste Schritte", "noch offen" und Downloadbefehle sind keine aktuelle
Handlungsempfehlung.**

## Maßgeblicher Ergebnisstand: vollständige Kompatibilitätsuntersuchung

Siehe [GLM_KOMPATIBILITAET.md](GLM_KOMPATIBILITAET.md).
Zwei unabhängige Grenzen sind belegt: nicht zugelassene Down-Expertentypen und
die Split-GGUF-Sperre des PGRN-Inferenzpfads. Beide wurden im installierten
Maschinencode nachvollzogen; v0.3.5 behebt laut identischen Source-Blobs keine davon.
Alle Expertentensoren beider vorhandenen Teile sind vollständig inventarisiert.
Die Down-Zeilenbreite 1408 erklärt den Rückfall von K-Quants auf Legacy-Typen.
Kein alternativer Dateiname wird deshalb als kompatibel empfohlen.

Empfehlung: vorerst kein weiterer großer Download und kein GLM-/PGRN-Start.
Vorbereitete, streng begrenzte HTTP-206-Metadatenprüfung (noch nicht ausgeführt):

```bash
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/probe_remote_metadata.py'
```

Sie bleibt innerhalb der bereits freigegebenen 100-MB-Untersuchung, mit einer
persistenten 70-MB-Payloadgrenze und Reserve für Textquellen/HTTP-Overhead.
Der Zugriff auf Remote-Header ist aus der Sandbox nicht möglich; vollständige
Headerprüfungen alternativer Ausgaben bleiben bis dahin ausdrücklich unbestätigt.
Positive Typ-Metadaten allein wären kein Beleg für praktische Inferenz.

## Aktueller Stand: Download erfolgreich, konkrete Quantisierung inkompatibel

Beide GGUF-Teile sind extern vollständig vorhanden (72.975.748.384 Bytes gesamt),
ihre SHA-256 wurden durch den Downloader vollständig geprüft. Abschlussmanifest:
`logs/glm-download-complete.json`. Keine erneute Übertragung erforderlich.

Der anschließend hier ausgeführte **reine Metadaten-Dry-run des installierten
Konverters** scheitert mit Exit 1:

`pgrn-convert: unsupported expert GGML type 8 in blk.1.ffn_down_exps.weight`

Die lesende Prüfung beider GGUF-Header ergibt 138 Expertentensoren:
92 Q4_K (Typ 12), 24 Q5_0 (Typ 6), 22 Q8_0 (Typ 8). Die veröffentlichten und lokal
prüfbaren Typ-IDs bestätigen diese Zuordnung. Ein Dateiname Q4_K_M garantiert
also nicht, dass alle Expertentensoren kompatible K-Quantisierungen besitzen.
Die vorherige pauschale Empfehlung dieser konkreten Ausgabe war nicht ausreichend.

**Keine Konvertierung und kein Modellstart mit dieser Kombination.**
`experiment.py glm-plan` verweigert deshalb für den dokumentierten Befund eine
Start-/Konvertierungsempfehlung. Der unabhängige modelllose Server-Test bleibt
erfolgreich; dies ist ein Problem der konkreten Gewichts-/Konverter-Kombination.
Die heruntergeladenen Dateien bleiben unverändert erhalten.

Nächster Schritt: alternative GGUF-Ausgabe anhand echter Expertentensor-Metadaten
prüfen, bevor weitere große Dateien geladen werden; alternativ wäre eine Engine-
Erweiterung ein eigenständiges Entwicklungs- und Validierungsvorhaben. Beides
hier noch nicht umgesetzt. Es gab keinen zusätzlichen Modelldownload.
Metadatenbefunde: `logs/glm-pgrn-dry-run.txt` und `logs/glm-gguf-expert-types.json`.
Alle älteren positiven Modellpläne unten sind durch diesen konkreten Befund
überholt; die PGRN-Größe ist weiterhin nicht gemessen.

## GLM-Download freigegeben: Terminal-Aufruf vorbereitet

Der Nutzer hat den Download der zwei Q4_K_M-Teile freigegeben. Externe SSD erneut
als eigener APFS-Mount bestätigt, ca. 931 GiB frei. Die Ausführungsumgebung
beschränkt weiterhin Netzwerk und Schreiben außerhalb des Projektordners; daher
wurde der große Download hier NICHT gestartet. Im normalen Terminal ausführen:

```bash
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/download_glm.py'
```

Ziel: `/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/glm-4.5-air-q4_k_m/`.
Downloadumfang 72.975.748.384 Bytes (72,98 GB). Gepinnte Hugging-Face-Revision:
`b0f8153e9e7cf57cd3b0aad146667abf9de56f0e`. Vor den großen Transfers vergleicht
das Skript die beiden veröffentlichten LFS-Zeiger dieser Revision mit den bereits
ermittelten SHA-256 und Größen. Abweichungen führen zum Abbruch.

Das Skript prüft Mountpoint/Dateisystem und Platz, legt die Ablage ausschließlich
auf dem eingehängten externen Volume an und schreibt die zwei Teile direkt dorthin.
Keine Hugging-Face-/Xet-Gewichtskopie auf der internen SSD. `.download`-Dateien
sind fortsetzbar: nach Unterbrechung denselben Befehl erneut ausführen.
Vollständige Teile werden vor ihrer endgültigen Benennung auf Größe, GGUF-Signatur
und vollständige SHA-256 geprüft. Keine PGRN-Konvertierung, kein Modellstart.

Fortschritt erscheint im Terminal; Statusmeldungen stehen in `logs/glm-download.log`.
Erst bei vollständigem Erfolg entsteht `logs/glm-download-complete.json` mit
`sha256_verified: true`. Derzeit existiert noch kein Erfolgsnachweis des Downloads.
Eine Unterbrechung während der Hashprüfung ist ebenfalls durch erneuten Aufruf
behebbar. Bestehende endgültige Teile werden geprüft und nicht neu heruntergeladen.

## Abschlussergebnis: modellloser Test vollständig bestanden

Der letzte Terminal-Test am 17.10.2026 bestätigt den unabhängigen Start der
gebündelten Engine (PID 41843) auf 127.0.0.1:8083 und des separaten Rollen-Proxys
(PID 41848) auf 127.0.0.1:8093. Jeweils `/health`, `/v1/models`, `/props` und `/`
lieferten HTTP 200. Lokal gespeicherte Antworten beider Ports wurden nachgelesen:
leere Modellliste, Modellpfad `none`, Autoload aus und ein HTML-Dokument mit
12.637 Bytes. Das belegt HTTP-Auslieferung der UI, keine visuelle Browserprüfung.

Die gespeicherte Vorher-/Nachher-Kontrolle ist identisch: unveränderte Labor-PIDs,
HTTP 200 auf 8080/8091/8092 und unveränderter HTTP 406 auf dem nackten GET /mcp
auf 8787. Beide Testports sind nach Cleanup frei, auch durch nachträgliches lsof
bestätigt. Keine Modelle geladen, keine Inferenz und keine Konvertierung gestartet.

**Dieser Vorbereitungsschritt ist abgeschlossen.** GLM-/PGRN-Unterstützung,
Completion-/SSE-Verhalten, Rollen-Injektion und MCP-Tool-Aufrufe sind damit noch
nicht praktisch getestet. Die folgenden Abschnitte dokumentieren die vorherigen
Zwischenstände und Korrekturen; für das Ergebnis gilt dieser Abschlussabschnitt.

## Zweiter Terminal-Test: leerer Router bestätigt, UI-Header korrigiert

Realer Nachtest: Engine-PID 41402 auf 8083 und Proxy-PID 41407 auf 8093,
beide mit HTTP 200 auf /health. Die Engine meldet null gecachte und null lokale
Presets. `/v1/models` enthält `data: []`, `/props` bestätigt `model_path: none`,
`models_autoload: false` und `cors_proxy_enabled: true`. Damit ist der tatsächlich
modelllose Betrieb dieses Bundles belegt.

Der nächste Abbruch (GET / mit HTTP 415) betrifft die UI-Anfrage des Testclients.
Die gebündelte UI wird gzip-komprimiert ausgeliefert; der Client sandte bisher
kein `Accept-Encoding: gzip`. Das installierte Binary enthält die entsprechende
Gzip-Fehlermeldung, und der bestehende Rollen-Proxy dokumentiert diese Anforderung.
Der Client sendet jetzt für GET / passende Header, dekomprimiert gzip und prüft HTML.
Offline-Prüfung mit komprimierter Testantwort bestanden; echter Nachtest noch offen.

Die Protokolle dieses Laufs sind unter `logs/second-smoke-20261017/` gesichert.
Laborprüfung vorher/nachher identisch; beide Testports wurden freigegeben.
Für den verbleibenden HTTP/UI-Nachtest denselben `python3 -B experiment.py smoke`
Aufruf erneut im normalen Terminal ausführen. Kein neuer Download erforderlich.

## Aktueller Nachweis nach dem ersten Terminal-Test

**Separater Engine-Start bestätigt.** Das offizielle ZIP liegt vor und seine
SHA-256 wurde lokal erneut mit der veröffentlichten Prüfsumme verglichen.
Bundle v0.3.4, tatsächliche Engine-Version laut Ausgabe: Build 10116,
Commit `852e7daa1`, Darwin arm64. Dieser eingebettete Build ist vom früher
genannten Quellrekonstruktions-Pin zu unterscheiden; für Testbefunde gilt das
wirklich ausgeführte Binary, nicht der angenommene Source-Pin.

Der im normalen Terminal ausgeführte erste Test belegt:

- eigener Engine-Prozess PID 40965 und Listener auf 127.0.0.1:8083;
- GET /health an der Engine: HTTP 200, `{"status":"ok"}`;
- eigene Proxy-Instanz PID 40970 und Listener auf 127.0.0.1:8093;
- GET /health über den Proxy: HTTP 200;
- GET /v1/models an der Engine: HTTP 200;
- Cleanup: beide Testports danach frei;
- vorher/nachher identische Labor-PIDs, HTTP 200 auf 8080/8091/8092,
  identischer HTTP 406 vom MCP-Endpunkt /mcp auf 8787. Der nackte GET ist kein
  vollständiger MCP-Handschlag; 406 ist kein Nachweis eines MCP-Ausfalls.

Der Test brach danach wegen einer zu strengen, auf unvollständiger Cache-Isolation
beruhenden Erwartung ab: Das leere `--models-dir` wird zusätzlich zum gemeinsamen
Modellcache ausgewertet. Das Log nennt sieben **cached model presets** und null
lokale Presets. Preset-Erkennung allein belegt weder Modellladung noch Inferenz.
Das Testlog enthält keinen Gewichts-Lade-/Kindprozessstart; eine vollständige
Liste der Prozesskinder wurde allerdings nicht protokolliert.

Korrektur ausschließlich im Experiment: `LLAMA_CACHE` wird für den Engine-
Kindprozess auf den eigenen leeren Ordner `empty-cache/` gesetzt. Die Variable
ist im installierten Binary vorhanden und ihre Cache-Verwendung im gepinnten
Upstream-Quelltext belegt. Die leere API-Modellliste bleibt Testbedingung.
Keine Änderungen am gemeinsamen Cache oder den bereits laufenden Diensten.
Die Wirkung im installierten Binary ist mit dem folgenden Nachtest zu bestätigen.

```bash
cd '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017'
python3 -B experiment.py smoke
```

Dieser Nachtest lädt das Bundle nicht erneut herunter und beendet seine Prozesse
automatisch. Die restlichen UI-/props-/Modelllistenprüfungen sind bis dahin offen.
Die folgenden Abschnitte dokumentieren zum Teil die frühere Vorbereitung vor
Bereitstellung des Bundles; für den aktuellen Ergebnisstand gilt dieser Abschnitt.

## Fortsetzung: Bundle-Bereitstellung und modellloser Test

Die fünf Vorbereitungsdateien und der bestehende Rollen-Proxy wurden erneut gelesen.
Der Starter startet im Smoke-Pfad nur einen Router mit eigenem leerem Modellordner
und ausgeschaltetem Autoload. Er beendet nur seine selbst erzeugten Popen-Prozesse.
Er prüft jetzt Prozessstart, eigene PID und exakten 127.0.0.1-Listener getrennt von HTTP.
Explizite HTTP-503-Meldungen "no model loaded" werden als erwarteter Hinweis
protokolliert; bloßes "loading model" gilt nicht als Bereitschaftsnachweis.
EPERM/EACCES bei localhost führt sofort zum Abbruch, ohne wiederholte Versuche.

Die offizielle GitHub-Release-API bestätigt weiterhin das ZIP mit 65.780.310 Bytes
und SHA-256 `8f2106b66ac1f809f0d1d82d1f1b17ad404974f158ce3d5e361ce0eb11fb9ce7`.
Die Prüfsumme ist sowohl als Asset-Digest als auch im Release-Text veröffentlicht.
Der Vergleich belegt Übereinstimmung mit dem offiziellen Release; die ad-hoc-
Codesignatur allein ist kein unabhängiger Nachweis einer Entwickleridentität.

**Runtime weiterhin nicht vorhanden.** Die bereits eindeutig blockierten DNS- und
localhost-Versuche wurden nicht wiederholt. Sandbox-Freigaben zur Erweiterung des
Shell-Zugriffs sind im aktuellen Berechtigungsprofil deaktiviert. Deshalb wurde
kein neuer Download-, capabilities- oder Engine-Startversuch unternommen.

Für die Ausführung im normalen macOS-Terminal ist nun der folgende einzelne Befehl
vorbereitet (Skriptpfad geprüft):

```bash
bash '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/bundle_smoke.command'
```

Das Skript prüft Ports, lädt nur das offizielle ZIP, vergleicht Größe und
veröffentlichte SHA-256, entpackt lokal, prüft die Bundle-Signatur und führt
`capabilities` sowie den automatisch aufräumenden modelllosen `smoke` aus.
Es startet die grafische App nicht. Protokoll:
`logs/bundle-smoke-terminal.log`; bei gestarteten Testprozessen zusätzlich
`logs/lab-before-after.json`. Bei Blockade kein Umgehen von Sicherheitsregeln.

Geprüft wurden Python-Syntax, Shell-Syntax und offline (mit Mocks) die Unterscheidung
von "kein Modell"/"lädt"/HTTP-500 sowie die Abweisung fremder PIDs und wildcard-
Listener. Diese Checks sind ausdrücklich KEIN realer Engine-Test.

Die Nachkontrolle bestätigt dieselben vier Labor-Listener/PIDs und freie Ports
8083/8093. Kein Testprozess wurde gestartet. HTTP-Erreichbarkeit bleibt ungeprüft.
Ein erfolgreicher zukünftiger modellloser Test belegt keine GLM-/PGRN-Kompatibilität.

## Ergebnis

**Separater Engine-Start: derzeit nicht möglich / nicht nachgewiesen.**
In den geprüften Ordnern `/Applications`, `~/Applications`, `~/Downloads`,
`~/Desktop`, `~/PycharmProjects` sowie `/tmp` wurde kein Slipstream-Bundle,
Slipstream-Archiv oder PGRN-Konverter gefunden. Das ist eine Suche in diesen
Orten, keine Garantie über alle Dateien auf dem Rechner.

Die vorhandene Homebrew-Engine ist llama.cpp 0.6.0 (Build 11429, Commit
`d81235049`), **kein nachgewiesenes Slipstream-Binary**. Sie wird nicht als
Ersatz benutzt. Kein neuer Inferenzprozess und keine grafische App wurde gestartet.

Der kleine Slipstream-Runtime-Abruf ist ebenfalls blockiert: ein HTTP-HEAD zum
Release-ZIP scheiterte mit `Could not resolve host: github.com`. Direkte HTTP-
Anfragen an alle vier Laborports scheitern hier mit `Operation not permitted`.
Öffentliche Quelltexte und Release-Metadaten waren über den GitHub-Connector
lesbar; das ist keine Möglichkeit, ein ausführbares Bundle auf den Mac zu laden.
Keine Sicherheits-, Netzwerk- oder Gatekeeper-Einstellungen wurden geändert.

## Ist-Zustand (lokal gemessen)

- MacBook Pro, `Mac16,7`, Apple M4 Pro, 14 CPU-Kerne (10 Performance / 4 Efficiency), 48 GB RAM.
- `vm_stat`: ca. 28,1 GiB wired, ca. 9,35 GiB Kompressorspeicher zum Messzeitpunkt.
  `memory_pressure` meldete 20 % freien Systemmemory-Anteil. Das ist kein Nachweis,
  dass 9,6 GiB sofort als zusätzlicher GPU-/Modellspeicher sicher nutzbar sind.
- Ein vorhandener llama-server-Prozess hatte eine Qwen3.6-27B-Datei mit
  17.909.097.600 Bytes geöffnet; zusätzlicher Ollama-Prozess mit ca. 1,16-GB-Blob.
  Keine dieser Instanzen wurde beendet, entladen oder umkonfiguriert.
- Interner freier Speicher: ca. 1.071,93 GiB; externer: ca. 930,79 GiB
  (999,42 GB dezimal; df-Werte können sich im laufenden Betrieb ändern).
- `/Volumes/Extern M4 Speicher` ist als eigener APFS-Mount bestätigt.
  Aktuelle Kennung in `mount`: `/dev/disk6s2`; keine Konfiguration hängt davon ab.
- Vorher und nachher identische Labor-Listener:

| Port | PID | Adresse |
|---|---:|---|
| 8080 | 30272 | 127.0.0.1 |
| 8091 | 30322 | 127.0.0.1 |
| 8092 | 30217 | 127.0.0.1 |
| 8787 | 30225 | 127.0.0.1 |

8083 und 8093 waren vorher und nachher frei. API-Erreichbarkeit konnte wegen
der Ausführungsbeschränkung weder vorher noch nachher verifiziert werden.
Die Schlussfolgerung lautet deshalb nur: identische Listener/PIDs, kein eigener
Testdienst gestartet; **kein belegter vollständiger Gesundheitscheck des Labors**.

Keine AGENTS.md in den geprüften Projekt-/Vorfahrenpfaden gefunden. Vorhandene
Änderungen in `.gitignore`, `agents/llm_scout/llm_scout.py`,
`scripts/run_scout_pipeline.sh`, `scripts/send_scout_email.py` wurden nicht angefasst.
Neu ist ausschließlich dieses Experimentverzeichnis. Kein Commit.

## Dateien

- `config.json`: getrennte Ports, Bundle- und Speicherpfade; vorläufige GLM-Werte.
- `sources.json`: Release-/Modellquellen, Größen und veröffentlichte SHA-256.
- `experiment.py`: Vorprüfung, Hilfeprüfung und beaufsichtigter modellloser Start.
- `TESTPROTOKOLL.txt`: tatsächlich ausgeführte Checks und Abbruchgründe.
- `.gitignore`: hält künftige Runtime, Gewichte, PGRN und Logs aus Git heraus.

Die Dateien gehören zum bestehenden Git-Projekt; der laufende Laborstarter,
`config/models.ini`, Rollen-Dateien und `role_proxy.py` bleiben unverändert.

## Runtime bereitstellen (noch nicht erfolgt)

Empfohlen: Release **v0.3.4**, Bundle aus dem offiziellen arm64-ZIP. Neuester
Release-Eintrag v0.3.5 hat laut geprüfter Metadaten keine Binär-Assets. Das
4,34-MB-Node-Archiv enthält keinen belegten vollständigen Inferenz-Runtime-Ersatz.

Runtime-Download: **65.780.310 Bytes (65,78 MB)**. Für ZIP plus entpacktes Bundle
vorsorglich 0,5 GiB internen Platz einplanen; entpackte Größe hier nicht gemessen.
Kein Modell ist in diesem Schritt erforderlich. Die folgenden Befehle sind
vorbereitet, wurden aber NICHT ausgeführt:

```bash
cd '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017'
mkdir -p runtime
curl --fail --location --output runtime/Slipstream_0.3.4_aarch64.zip \
  'https://github.com/Schero94/slipstream/releases/download/v0.3.4/Slipstream_0.3.4_aarch64.zip'
python3 -B - <<'PY'
import hashlib
from pathlib import Path
p = Path('runtime/Slipstream_0.3.4_aarch64.zip')
expected = '8f2106b66ac1f809f0d1d82d1f1b17ad404974f158ce3d5e361ce0eb11fb9ce7'
assert p.stat().st_size == 65780310, 'ZIP-Größe stimmt nicht'
assert hashlib.sha256(p.read_bytes()).hexdigest() == expected, 'SHA-256 stimmt nicht'
print('Release-ZIP: Größe und SHA-256 stimmen')
PY
```

Nur bei erfolgreicher Prüfung anschließend:

```bash
cd '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017'
ditto -x -k runtime/Slipstream_0.3.4_aarch64.zip runtime
codesign --verify --deep --strict runtime/Slipstream.app
python3 -B experiment.py capabilities
```

Die grafische App NICHT öffnen. Keine Quarantäneattribute löschen und keine
Sicherheitsregeln ändern. Falls Bundle-Ausführung blockiert wird: Befund erfassen
und weiteres Vorgehen gesondert klären.

Alternativ lässt sich ein bereits bereitgestelltes v0.3.4-Bundle über
`SLIPSTREAM_BUNDLE='/absoluter/Pfad/Slipstream.app'` angeben. Es gibt keinen
automatischen Rückgriff auf `/opt/homebrew/bin/llama-server`.

## Exakte Start-/Stop-Befehle nach Bereitstellung

Vorprüfung und kurzlebiger, modellloser HTTP/UI-Test:

```bash
cd '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017'
python3 -B experiment.py check
python3 -B experiment.py smoke
```

`smoke` beendet seine beiden Prozesse automatisch. Dauerhafter modellloser Start
(nur manuell und nach bestandener Hilfeprüfung):

```bash
cd '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017'
python3 -B experiment.py serve-empty
```

**Stop: Ctrl+C im selben Terminal.** Der Controller beendet nur die beiden
selbst gestarteten Popen-Prozesse. Keine PID-Datei, kein `pkill`, keine fremden
Listener werden beendet. Es wird kein Hintergrunddienst eingerichtet.

Zieloberfläche: `http://127.0.0.1:8093`, Engine: `http://127.0.0.1:8083`.
Der Starter prüft freie Ports, die installierten Optionen und ein wirklich leeres
eigenes Modellverzeichnis. Keine Modelle werden entdeckt, heruntergeladen oder
automatisch geladen. Bei Portkonflikt abbrechen und freie Alternativen in
`config.json` eintragen; keine automatische Portänderung.

Der Rollen-Proxy erhält `ROLE_HOST=127.0.0.1`, `ROLE_PORT=8093`,
`ROLE_UPSTREAM=http://127.0.0.1:8083` und ein eigenes `ROLE_LOG`. Rolle und Datum
werden weiterhin durch den bestehenden Code gesetzt. Die Protokollfunktion und
SSE-Weitergabe sind im Laborcode vorhanden, aber nicht gegen Slipstream getestet.

Die Modellliste bleibt beim modelllosen Start leer. Ein erfolgreicher solcher
Test bestätigt Prozessstart, Listener, HTTP-Routen, ausgelieferte UI und GET-
Weiterleitung. Er bestätigt **keine** Inferenz, Rollen-Injektion in einer
Completion, SSE-Antwort, Tool-Calls, GLM-Unterstützung oder PGRN.

Für MCP später in der UI auf 8093 `http://127.0.0.1:8787/mcp` eintragen und
"use llama-server proxy" aktivieren. Der geplante Start setzt `--ui-mcp-proxy`.
Kein MCP-Schreibtest in dieser Stufe. Eval später ohne Gedächtnis und mit derselben
Tool-/git_log-Konfiguration wie die Baseline.

## GLM und getrennte Speicherpfade

Dokumentiert: GLM-4.5-Air ist im Slipstream-Katalog genannt. Codebelegt: die
geprüfte llama.cpp-Basis unterstützt glm4moe und die vom Konverter erkannten
gestapelten Gate-/Up-/Down-Expertentensoren. **Installierte Engine: nicht vorhanden;
konkrete GGUF-Geometrie, Konvertierung und GLM-Inferenz: nicht geprüft.**

Ziel extern:

`/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/glm-4.5-air-q4_k_m/`

Beide Dateien aus `unsloth/GLM-4.5-Air-GGUF/Q4_K_M` gehören in denselben Ordner:

| Datei | Bytes |
|---|---:|
| GLM-4.5-Air-Q4_K_M-00001-of-00002.gguf | 50.000.746.752 |
| GLM-4.5-Air-Q4_K_M-00002-of-00002.gguf | 22.975.001.632 |
| Gesamt | 72.975.748.384 |

Das sind **72,98 GB / 67,96 GiB**. Exakte Größen und SHA-256 stammen aus den
öffentlichen LFS-Zeigern, nicht aus heruntergeladenen Dateien. Vor einem Download
vollständige unveränderliche HF-Revision pinnen und beide SHA-256 nachprüfen.

Ziel intern:

`/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/pgrn/GLM-4.5-Air-Q4_K_M.pgrn`

Die Speicherordner wurden noch nicht angelegt; ihre Pfade sind vorbereitet.
Vor JEDEM externen mkdir/Download muss `Path('/Volumes/Extern M4 Speicher').is_mount()`
bestätigt werden. Niemals `mkdir -p` auf den Mountpoint selbst anwenden. Dieses
Verzeichnis darf nicht bei abgezogener SSD auf dem internen Datenträger entstehen.

Codebelegte Konverter-Anforderungen (Tag v0.3.4):

- Eingang: erster GGUF-Teil, weitere Teile anhand `split.count` und Standardnamen.
  Kein Zusammenfügen und somit keine weitere ca. 73-GB-Merge-Datei erforderlich.
- Pro Experte gestapelte Gate-, Up- und Down-Tensoren; erlaubt sind F32/F16 sowie
  Q4_K/Q5_K/Q6_K. Dateiname allein garantiert diese Struktur nicht.
- `--dry-run` liest Metadaten und liefert `estimated_output_bytes` und Shardzahl;
  dabei keine PGRN-Ausgabe. Erst nach Vorliegen beider vollständiger Teile möglich.
- Konvertierung schreibt `<Ziel>.partial` und `<Ziel>.partial.journal` auf dem
  Zielvolume. Nach Abschluss Umbenennung zum endgültigen Ziel, also grundsätzlich
  kein zweites vollständiges PGRN nötig. Vorhandenes Ziel wird nicht überschrieben.
- Unterbrechungen lassen Partial/Journal zurück; `--resume` prüft den gespeicherten
  Fortschritt. Nicht ungeprüft löschen oder eine zweite Konvertierung daneben starten.
- Default-Mindestreserve: `--min-free-gb 16`, im Code tatsächlich **16 GiB**.
  Für diesen Versuch 20 GiB Reserve einplanen. Der Voll-Input wird zur Identität
  gehasht; das bedeutet zusätzliche Lesezeit von extern.
- GGUF bleibt während Inferenz nötig (Metadaten und nicht gestreamte Gewichte);
  auch alle Shards bleiben erhalten. Getrennte Pfade: `--model <erster GGUF-Teil>`
  und `--pgrn <interne Datei>`. Externe SSD während des Betriebs angeschlossen lassen.

PGRN-Größe **geschätzt**: 60–70 GB, nicht gemessen. Konservativ mindestens 90 GiB
intern freihalten (Ausgabe + Reserve + Runtime/Logs), extern mindestens 85–100 GB.
Keine automatische zweite HF-Cache-Kopie intern anlegen. Ein späterer Downloader
muss direkt auf die externe Ablage schreiben; mögliche temporäre HF/Xet-Caches
sind vorher explizit festzulegen.

Vorläufiges GLM-Testbudget auf der bestätigten 48-GB-Hardware: 12 GiB
Experten-Cache, 8 GiB Headroom, 8K Kontext, ein Slot, vier I/O-Threads, F16-KV;
keine spekulativen Verfahren und kein experimentelles Prefetch. Das sind noch
keine auf installierten Optionen oder Messungen validierten Empfehlungen.
Gegenwärtig ist Qwen bereits geladen; KEIN zusätzlicher GLM-Start vorgesehen.
Ein späteres Entladen bestehender Modelle bedarf einer eigenen abgestimmten Phase.

## Nächste Schritte / Freigabegrenzen

1. Das kleine offizielle Runtime-ZIP verfügbar machen (65,78 MB, ca. 0,5 GiB
   Arbeitsraum), prüfen und lokal entpacken; kein systemweiter Installationsschritt.
2. Hilfe/Version erfassen und modelllosen `smoke` unter normalen localhost-
   Berechtigungen ausführen. Nur dies kann das aktuelle Startziel bestätigen.
3. Erst danach separat GLM-Download mit ca. 72,98 GB extern freigeben. Anschließend
   Metadaten-Dry-run und Speicherplan anhand tatsächlicher Tensoren bestätigen.
4. Konvertierung (geschätzt 60–70 GB intern plus Reserve) und GLM-Start erst nach
   eigener Freigabe; konkrete Ausgangslast und Speicherverbrauch vorher prüfen.

Referenzen und Prüfsummen: `sources.json`. Ein früherer Machbarkeitsbericht lag
in diesem Chat; im geprüften lokalen Projekt wurde keine entsprechende Datei gefunden.
