# Freigegebener Vergleich: PGRN intern / Samsung T7

Vorbereitung am 17.10.2026; die sechs Vergleichsläufe sind noch NICHT ausgeführt.
Kein neues Modell und keine Konvertierung. Vorhandene GGUF/interne PGRN bleiben erhalten.

Ausführungsumgebung beschränkt weiterhin externe Schreibzugriffe und localhost;
der autorisierte Ablauf muss wie die vorherigen Inferenztests im normalen Terminal laufen:

```bash
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen_reference/compare_storage.py'
```

Kein weiterer Freigabeschritt nötig. Nur bei vollständig gestopptem Labor und ohne
andere llama-server-Instanz. Bei Konflikten keine automatische Entladung/Beendigung.
Port 8083 wird vor dem Kopieren kurz auf Bindbarkeit geprüft, ohne Modellstart.

Der Ablauf prüft das richtige gemountete Samsung-T7-Volume, Platzreserve und
Engine-Hash; hasht die interne PGRN vollständig; kopiert diese in das eigene Verzeichnis
`/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen35b-pgrn-comparison/`;
prüft externe Größe/Voll-SHA gegen die Referenz und damit gegen das geprüfte Original.
Benötigt zusätzlich 20.128.754.176 Bytes extern plus 10 GiB Platzreserve.
Kein fehlender Mountpoint wird ersatzweise angelegt. Existierende fertige Kopien
werden geprüft, nicht überschrieben. Unvollständige `.copying`-Dateien bleiben
bei Abbruch erhalten und werden nicht ungeprüft wiederverwendet.

Die lesend getestete Zuordnung lautet aktuell:

| Ablage | APFS-Volume | Physisches Medium | IORegistry-Blocktreiber |
|---|---|---|---|
| Intern | disk3s5 | disk0 / APPLE SSD AP2048Z | 0x100000bad |
| Extern | disk6s2 | disk5 / Samsung PSSD T7 | 0x100166a19 |

Diese Kennungen werden NICHT fest vorausgesetzt. `disk_counters.py` rekonstruiert
die aktuelle Volume-Ancestor-Kette aus `df` und IORegistry und liest ausschließlich
`Bytes (Read)`, `Operations (Read)` und `Bytes (Write)` des physischen
IOBlockStorageDriver. Synthetische AppleAPFSMedia-Container mit Whole=Yes werden
nicht als Hardware verwechselt. Kennungswechsel oder Zählerrücksetzungen sind Fehler.
Rohzuordnung der Vorprüfung: `logs/comparison-device-preflight.json`.

## Gleichheit und Messdesign

- Reihenfolge: **A1–B1–B2–A2–B3–A3**; A intern, B T7, je drei neue Prozesse.
- Pro Prozess dieselben beiden vorhandenen Code-Prompts, jetzt beide mit
  **128 Ausgabetokens als Limit** (explizit gegenüber vorherigem 64/128-Test geändert).
  Beide Varianten haben dieselben Anforderungen. Prompt 1 prozessfrisch,
  Prompt 2 nach vorheriger Nutzung der Arena; nicht als gleiche Cachezustände ausgeben.
- Unveränderte Engine/Startparameter aus erfolgreichem Lauf: Build10116/852e7daa1,
  Cache2GiB, Reserve8GiB, Kontext512, Batch/UBatch32/32, MTP4, Thinking an,
  I/O1, Compact aus, kein Prefetch/Repack/mmap, Temp0/Seed42, ein Slot.
  Nur das Argument nach `--pgrn` ändert sich; der Bericht prüft diese Gleichheit.
- Health-Bereitschaft höchstens420s statt bisher180s, damit langsamere externe
  Validierung nicht durch einen zu knappen Testcontroller-Timeout scheitert.
  Das ändert keinen Engine-Parameter und wird für A/B identisch angewendet.
- Ladezeit separat bis /health; max.600s für die beiden Anfragen pro Prozess.
- Prozess-RSS/VM/Swap laufend, Abbruch bei zusätzlichen Swapouts oder Ausfall
  der Wache; echte native Cache-Hits/-Misses pro Turn aus kumulativen Logs.
- Physische Read-Snapshots vor/nach Kopie, Originalhash und Kopiehash getrennt;
  bei Modellladen und alle zwei Samples während Enginebetrieb. Jede Anfrage hat
  unmittelbar vor/nachher eigene Zähler und eine dreisekündige Leerlaufkontrolle.
  Die Auswertung berechnet zusätzlich ein engeres Decode-Teilfenster aus den
  Samples nach erstem sichtbaren Token bis vor Anfrageende. Keine Lade-/Hashbytes
  werden als Generierungsbytes ausgegeben.

## Dateicache und Beweisgrenze

Keine Purge-Befehle, kein künstlicher Speicherdruck, keine Systemeinstellungen.
Kopieren und Hashen wärmen Dateicaches. Ein neuer Modellprozess leert nur den
Engine-Cache. Kein Ablauf hier garantiert einen kalten Betriebssystemcache.
F_NOCACHE wird vom vorhandenen Reader angefordert; das ist allein kein Nachweis,
dass alle Reads die Hardware erreichen.

Es werden drei unabhängige Befunde ausgegeben:

1. Offene externe PGRN anhand eigener Engine-PID/lsof.
2. Positive tatsächliche native Experten-Cache-Misses.
3. Positive physische T7-Blocktreiber-Lesezähler während Anfrage und engerem Decode-Fenster.

Die Gerätezähler sind nicht prozess-/dateiexklusiv. Hintergrund-I/O bleibt möglich;
deshalb Leerlaufwerte und Größenordnung der Deltas im Bericht prüfen. Bei fehlenden,
unverändert bleibenden oder nicht sauber zugeordneten Lesezählern bleibt der
physische externe Streaming-Nachweis ausdrücklich offen, auch wenn API und Misses bestehen.
Die automatische Empfehlung ist anhand dieser Einschränkung zu lesen; sie ersetzt
keine nachträgliche Prüfung der Hintergrundwerte.

## Ergebnisse und Cleanup

Neue Ergebnisse unter `qwen_reference/comparisons/<UTC-Zeit>/`:

- `status.json`: Kopier-/Hashphasen, Identitäten, Reihenfolge, Abschluss/Fehler.
- `initial-ioreg.txt`: Rohzuordnung vor Beginn.
- `A1/` bis `B3/`: Engine-/Clientlogs, SSE-Rohantworten, laufende RSS-/VM-/Read-Samples,
  offene Dateien, Bereitschaft, Cleanup und Laborvergleich.
- `summary.json`: komplette Messwerte und Nachweisstufen.
- `ERGEBNIS.md`: Median und Minimum–Maximum, zusätzlich getrennt je Prompt,
  Swapout-Deltas und physische Lesevolumina. Andere als128 tatsächlich erzeugte
  Tokens werden nicht als vollständig identischer128-Token-Vergleich qualifiziert.

Nur eigene Popen-Prozesse werden beendet. Labor wird nicht neu gestartet.
Ctrl+C löst Cleanup aus; nach einem fehlgeschlagenen Lauf keine weiteren Modellstarts.
Die bereits erfolgreiche Einzelmessung wird nicht als neuer A-Durchlauf recycelt.
Kein Nachweis für Modelle oberhalb48GB, GLM oder Code-Reviewer-Qualität.
