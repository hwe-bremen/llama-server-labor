# Qwen-PGRN-Referenz: Vorprüfung und bedingte Durchführungsvorlage

## Abschluss: Vergleich intern / Samsung T7 bestanden

Serie `qwen_reference/comparisons/20261017T163646986349Z`: sechs Prozesse,
zwölf vollständige128-Token-Anfragen; Engineargumente außer PGRN-Pfad identisch.
Externe PGRN byteidentisch verifiziert. Native Misses plus physische T7-Reads
in allen B-Anfrage- und Decode-Teilfenstern belegt; Leerlauf und A zeigen keine
T7-Leseaktivität. MedianDecode intern5,92 vs.extern1,97Tokens/s, keine zusätzlichen
Swapouts, PeakRSS6,48GiB. Empfehlung **aktive PGRN intern**; externe Ablage
funktional nutzbar, etwaFaktor3langsamer in diesem2GiB-Cache-Profil.
Vollständige Tabelle/Mediane/Spannweiten und Beweisgrenzen:
`qwen_reference/comparisons/20261017T163646986349Z/ERGEBNIS.md`.
Alle nachfolgenden Hinweise auf ausstehende A/B-Tests sind historische Chronik.


Stand 17.10.2026. Mac16,7, M4 Pro, 48 GB Unified Memory. Kein Modellstart,
keine Konvertierung, kein vollständiger Modelldownload in diesem Schritt.

**Aktueller Ergebnisstand: vollständige Metadaten-Vorprüfung bestanden.**
Die unten dokumentierte Netzwerkblockade wurde durch die zulässige Ausführung
im normalen Nutzer-Terminal aufgelöst. Gespeicherte Ergebnisse wurden lokal
nachgelesen: 43 HTTP-206-Abrufe, insgesamt 11.010.208 gelesene Bytes inklusive
LFS-Zeiger; alle 753 Tensoren inventarisiert, darunter 123 geroutete
Expertentensoren in 41 vollständigen Gate/Up/Down-Tripeln einschließlich MTP.

| Gruppe | Tatsächlich gemessene Typen |
|---|---|
| Gate | 40 × Q4_K, 1 × Q5_K |
| Up | 40 × Q4_K, 1 × Q5_K |
| Down | 38 × Q5_K, 3 × Q6_K |

Alle gerouteten Expertentypen und ihre Geometrie bestehen die belegte
Allowlist/Strukturprüfung. Architektur `qwen35moe`, 256 Experten, Top-8,
41 Blöcke einschließlich eines NextN-Layers. Einzel-GGUF ohne Split-Deklaration;
keine unbekannten Expertengruppen oder doppelten Tensornamen. Die Q8_0-/BF16-
Tensoren liegen außerhalb der gestapelten gerouteten Experten und werden nicht
fälschlich durch diese Allowlist verworfen.

Damit sind die bei GLM festgestellten Typ-/Split-Hindernisse für diesen
Kandidaten in den geprüften Metadaten nicht vorhanden. Es besteht weiterhin
**kein ausgeführter Konvertierungs- oder Inferenznachweis auf diesem Mac**.
Der historische Engine-Versionsunterschied bleibt dokumentiert. Eine vollständige
Modell-SHA-Prüfung ist erst nach einem separat genehmigten Download möglich.
Die Abschnitte zur vorher offenen Metadatenprüfung unten sind historischer
Vorbereitungsstand; die neue Messung ist maßgeblich.

Nächste Freigabestufe: ausschließlich **22.853.663.008 Bytes Modelldownload
extern mit vollständiger SHA-Prüfung**, noch keine Konvertierung oder Modellstarts.
Danach separaten Konverter-Dry-run bewerten, bevor Konvertierung und spätere
Modellentladung/Starts freigegeben werden. Die Durchführungsvorlage unten
beschreibt diese späteren Stufen und ist kein Auftrag, sie jetzt auszuführen.

## Interne PGRN-Inferenz tatsächlich bestanden, 17.10.2026

Lauf `qwen_reference/runs/internal-20261017T161514971893Z` lokal ausgewertet:
Engine nach 150,77 s bereit, API-Ausgaben mit 64 und 128 Tokens vollständig.
TTFT 3,67 / 4,58 s; native Decode 5,82 / 5,43 Tokens/s; Gesamtzeit 14,66 / 28,14 s.
Native PGRN-Telemetrie: 2.046,03 MiB Cache, 2.136,04 MiB High-water,
kumulativ 14.534 Hits und 47.702 Misses. Gemessener Peak-Prozess-RSS ca. 6,48 GiB
(kein vollständiger Unified-Memory-Footprint). Keine zusätzlichen Swapouts;
bereits vorhandener Systemswap blieb ca. 8 GB und nahm leicht ab.
Engine Exit 0, Testport wieder frei, Labor weiterhin gestoppt.

Damit sind echte Qwen-Inferenz und die aktive beschränkte PGRN-Cache-Funktion
mit dieser installierten Engine bestätigt. Das ist keine isolierte Messung
physischer SSD-Reads, kein kalter SSD-Benchmark und kein T7-PGRN-Nachweis.
Variante B ist noch nicht ausgeführt. Frühere Hinweise auf fehlenden
Inferenznachweis unten sind historisch. Verifizierte Messübersicht:
`qwen_reference/runs/internal-20261017T161514971893Z/verified-summary.json`.

## PGRN-Konvertierung tatsächlich bestanden, 17.10.2026

Die freigegebene Konvertierung ist abgeschlossen, Exit 0, mit erneutem
vollständigem GGUF-SHA-Abgleich und aktiviertem CRC-Abschlusslauf.
Interne PGRN tatsächlich **20.128.754.176 Bytes**, SHA-256
`732a314b95cb3a63e31c3c9cd44e284757721d13a29d7aecd10360d13e193269`.
Größe und separat berechneter Vollhash stimmen exakt mit dem Projektartefakt
überein. Damit ist die Konvertierung dieser Datei mit unserem installierten
Konverter nachgewiesen, noch keine Inferenz mit der installierten Engine.
Konverterlauf ca. 132 Sekunden, zusätzliche PGRN-Hashprüfung ca. 8 Sekunden.
Keine externe PGRN-Vergleichskopie, keine Modellentladung und kein Modellstart.
Protokolle: `qwen_reference/logs/conversion-status.json` und
`qwen_reference/logs/conversion-progress.jsonl`.
Alle früheren Hinweise auf ausstehende Konvertierung unten sind historisch.

## Installierter Konverter: Dry-run bestanden

Freigegebener lokaler Aufruf `pgrn-convert --input <Qwen-GGUF> --dry-run`
endet mit Exit 0. Ein GGUF, 41 Expertenlayer, 256 Experten pro Layer und
10.496 Expertenrecords. Berechnete Ausgabe: **20.128.754.176 Bytes**
(20,13 GB / 18,75 GiB), exakt wie im historischen Referenzbericht.
Dies ist eine Metadatenberechnung, noch keine erzeugte oder verifizierte PGRN.
Protokoll: `qwen_reference/logs/converter-dry-run.json`.
Keine Konvertierung und keine Modellstarts. Nächste Freigabe betrifft die
PGRN-Erzeugung auf der internen SSD; Modellstart bleibt separat.

## Downloadabschluss, 17.10.2026

Die freigegebene Qwen-Datei liegt extern vollständig vor: 22.853.663.008 Bytes.
Der Downloader hat den vollständigen SHA-256 gegen den gepinnten LFS-Zeiger
geprüft; Abschlussmanifest `qwen_reference/logs/download-complete.json` und
Nutzerausgabe bestätigen den erwarteten Hash. Datei und Größe wurden anschließend
lesend bestätigt. Keine Konvertierung oder Modellstarts. Frühere Hinweise auf
fehlende Modelldatei bzw. erforderliche Downloadfreigabe unten sind historisch.
Nächster gesondert freizugebender Schritt: reiner Konverter-Dry-run ohne Ausgabe.

## 1. Verifizierte Identität und lokale Suche

Repository: `unsloth/Qwen3.6-35B-A3B-MTP-GGUF`

Revision: `5bc3e238d916f48a861bac2f8a1990a0e9b7e98d`

Datei: `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`

GGUF: **22.853.663.008 Bytes** = 22,85 GB / ca. 21,28 GiB.

SHA-256: `55983c5a75a1ab969824077b3bb3de4146e82a9234072b48ad4e8f92ad3fe9f1`

Die Angaben stimmen zwischen RESULTS.md (Verified M0 model, 16.07.2026,
16:26 UTC) und dem gepinnten öffentlichen LFS-Zeiger überein:

https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/raw/5bc3e238d916f48a861bac2f8a1990a0e9b7e98d/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf

Das ist die veröffentlichte Prüfsumme des ganzen Modells, keine durch uns
ausgeführte Vollprüfung noch nicht vorhandener Gewichte. Der LFS-Zeiger selbst
enthält keine Expertentensoren.

Kein Treffer für die exakte Modell-Datei/den Hash-Namen in den geprüften Ablagen
`~/.cache/huggingface/hub`, `~/PycharmProjects` und dem externen Volume. Die
vorhandenen HF-Qwen-Verzeichnisse betreffen 27B-Ausgaben, nicht diesen 35B-Pin.
Das ist keine Garantie über alle Dateien des Rechners oder anders benannte Blobs.

PGRN laut Projekt: **20.128.754.176 Bytes**, 20,13 GB / ca. 18,75 GiB,
SHA-256 `732a314b95cb3a63e31c3c9cd44e284757721d13a29d7aecd10360d13e193269`.
Dies wurde vom Projekt gemessen, hier NICHT erzeugt oder gemessen.

### Mehrdeutige Angaben im Projektprotokoll

- Der frühere Eintrag desselben Tages, 14:54 UTC, nennt ein anderes Repository
  ohne `-MTP`, Revision `a483e9e6cbd595906af30beda3187c2663a1118c`, denselben
  Dateinamen, aber 22.360.456.160 Bytes und Hash `707a55a8…`. Das sind verschiedene
  Artefakte; frühe Resultate dürfen nicht allein über den Dateinamen übertragen werden.
- Beim späteren MTP-Eintrag steht als „Remote object ID“ ein 40-stelliger Wert
  `74b7924fe57b5a5f87aaaa2c9d1fbd7cb88b154d`. Das ist nicht der 64-stellige
  Gewichte-SHA-256. Seine Bedeutung ist dort nicht erklärt; keine Gleichsetzung.
  Der aktuelle gepinnte LFS-Zeiger bestätigt separat den erwarteten 55983c-Hash.
- Die 40 Hauptlayer im frühen Geometrieeintrag widersprechen den späteren
  **41 gerouteten Layern einschließlich MTP** nicht zwingend. Für den Konverter
  müssen alle 41 einschließlich MTP erfasst werden: 123 Gate/Up/Down-Tensoren,
  256 Experten je Layer, 10.496 PGRN-Records laut Qualifikationsbericht.
- Frühe `PGR_STREAM_EXPERTS`-Observer-Läufe änderten den Rechenpfad nicht.
  Ihre hohen Raten sind kein Beleg des späteren echten SSD-Expertengathers.
- Frühe Compact-Ergebnisse bezeichneten Compact als abgelehnt/default-off;
  spätere Cachegrößenmessungen nahmen es wieder auf. Kein zeitloser Widerspruch,
  aber ein Grund, Profile/Commits nicht zu vermischen.

## 2. Expertentypen: vollständige Prüfung noch offen

Tatsächlich installierter Konverter, SHA-256:
`af8e47e59d4dcd9eed556da061220af7bd10c3de8137eea2ddd866ab53ad8476`.
Die bereits am Binary belegte Allowlist lautet F32 (0), F16 (1), Q4_K (12),
Q5_K (13), Q6_K (14), ausschließlich für gestapelte geroutete Experten.
Andere residente Gewichte werden davon getrennt betrachtet.

`qwen_reference/probe_metadata.py` prüft genau den genannten Pin, keine Varianten.
Es bestätigt zunächst den kleinen LFS-Zeiger und verlangt für jeden GGUF-Body
HTTP **206**, exakte Content-Range-/Längenangaben und Identity-Encoding. HTTP 200
wird vor Bodyread abgewiesen. Start mit 24 Bytes, danach 256-KiB-Bereiche bis
zum vollständigen Tensorverzeichnis, höchstens **16 MiB Headerpräfix**.
Ein persistentes 70-MB-Bodybudget einschließlich Fehlversuchsreservierungen
lässt 30 MB Reserve im autorisierten 100-MB-Gesamtbudget. Begrenzter Vorabruf
kann weniger als 256 KiB hinter das Headerende reichen; keine Inferenznutzung.

Die Auswertung verlangt positive Expertentensorzahl, vollständige separate
Gate/Up/Down-Tripel, alle Typen zugelassen, passende K-Blockgeometrie und
256 Experten, einen einzelnen GGUF, `qwen35moe` und 41 erfasste Layer einschließlich
MTP. Alle Namen, Formen und Typen bleiben in `qwen_reference/metadata/results.json`.
Ein positives Ergebnis ist nur ein Metadaten-Voraussetzungsnachweis, keine
Inferenzbestätigung oder vollständige SHA-Authentifizierung der Headerbytes.

**Jetzt zulässiger nächster Befehl im normalen macOS-Terminal:**

```bash
python3 -B '/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen_reference/probe_metadata.py'
```

Syntax und HTTP-200-/206-Prüfbedingungen offline geprüft. Dieses Skript wurde
hier nicht mit Netzwerk ausgeführt. Es startet weder Engine noch Konverter.
Bei Fehlern/abweichenden Typen endet die Freigabekette hier.

## 3. Inferenzpfad und erforderliche Engine

Installiertes offizielles Bundle **v0.3.4**, Build **10116 / 852e7daa1**, arm64.
Engine-SHA-256:
`7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e`.
Für den bedingten Versuch ist genau dieses vorhandene Binary vorgesehen,
keine Installation, kein Homebrew-Ersatz und kein ungeprüfter Upgrade.

Codeprüfung: Die veröffentlichte Basis `79bba02a6741` besitzt `qwen35moe`
einschließlich Qwen3.5/3.6-NextN/MTP und separater Gate/Up/Down-Experten.
Der Slipstream-Patch verbindet den MoE-Graphen mit Top-k-Remapping, beschränktem
Arena-Cache, PGRN-Slices/Typ-/Geometrieprüfung und nachgelagerter Speicheradmission.
Die PGRN-Identität wird gegen das Quell-GGUF gehasht; ein tatsächlicher Einzel-GGUF
vermeidet die zuvor bei GLM festgestellte Split-/Hash-Inkonsistenz. Das muss für
den Kandidaten noch aus den Headerdaten bestätigt werden.

Im installierten Binary sind `qwen35moe`, MTP-Graphsymbole, PGRN-Aufrufe,
Typ-/Geometrie-/Identitätsfehler sowie Cache-Hits/-Misses und Fetch-Telemetrie
vorhanden; die vorgesehenen Optionen sind in seiner bereits gespeicherten Hilfe
belegt. Die kritische Konverter-Allowlist und Engine-Identitätsprüfung wurden
bereits disassembliert. Strings/Symbole beweisen jedoch weder die vollständige
Übereinstimmung mit dem Rekonstruktions-Pin noch eine ausgeführte Qwen-Inferenz.

**Historische Versionen strikt getrennt:**

| Projektbeleg | Engine/Profil |
|---|---|
| `NATIVE_PGRN_35B_RESULTS.md`, 22.07.2026 | Commit `24b6efd77`; 2 GiB Cache, 8 GiB Reserve, Kontext 512, Batch/UBatch 32/32, Metal, kein Warmup, MTP max. 4, Thinking an; zwei Prozesse mit je 64/128-Token-Turns |
| Früher Compute-neutral-Observer | Build 10049 / `8c01f5c1c`; keine Gleichsetzung mit echtem PGRN-Offload |
| `RESULTS.md`, 27.07., echter Partitionierungs-A/B | 55983c-Modell; 10 GB Cache (Einheit im Text nicht eindeutig GiB), I/O 8, Compact an, keine Spekulation, Temp. 0, Seed 42, GGUF extern/PGRN intern; exakter Engine-Commit in diesem Eintrag nicht genannt |
| API-Qualifikation 0.3.1 | Commit `0c716f30be270d1fb1077a1a0795684e6faeecf8`, anderer späterer Engine-Stand |
| Unser v0.3.4-Binary | Build 10116 / `852e7daa1`; Beziehung zum historischen 24b6efd77-Build nicht vollständig öffentlich rekonstruiert |

Es existiert somit ein echter dokumentierter Qwen-PGRN-Test, aber keine
Versionsidentität unseres Binaries mit dessen Testbinary. Spätere Funktionsprüfung
auf diesem Mac ist erforderlich; keine praktische Kompatibilitätszusage jetzt.

## 4. Geplante A/B-Varianten und Speicher

GGUF in beiden Varianten unverändert extern:
`/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen35b-reference/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`

A, PGRN intern:
`/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017/pgrn/Qwen3.6-35B-A3B-UD-Q4_K_XL.pgrn`

B, byte-identische PGRN extern:
`/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen35b-reference/Qwen3.6-35B-A3B-UD-Q4_K_XL.pgrn`

Diese neuen Modell-/PGRN-Pfade sind geplante Ziele; hier nicht angelegt.

| Zustand, vorhandene GLM-Dateien zusätzlich unverändert erhalten | Neuer externer Platz | Neuer interner Platz |
|---|---:|---:|
| Nur Variante A | GGUF 22,85 GB | PGRN 20,13 GB + Journal/Logs |
| Variante B nach Kopie, A erhalten | GGUF + PGRN 42,98 GB | PGRN 20,13 GB + Journal/Logs |
| Freizuhaltendes konservatives Budget für beide | **55 GB** | **35 GB** |

Kein zusätzlicher kompletter interner GGUF-Cache. Fortsetzbarer externer Download
wird am Ende umbenannt statt kopiert. Konverter schreibt `.partial` plus
`.partial.journal` und benennt bei Abschluss um; kein zweites vollständiges PGRN
für diesen Ablauf nötig. Ein eventuell abweichendes Ergebnis des späteren Dry-run
hat Vorrang vor der historischen Größenangabe.

Aktuelle read-only Platzprüfung: intern rund 1.120.000.000 KiB frei,
extern rund 904.000.000 KiB frei (ca. 1.146,9 / 925,7 GB). APFS-Mount anhand
`/Volumes/Extern M4 Speicher` bestätigt, nicht anhand alter Gerätekennungen.

**Vor späterem Start muss das vorhandene große Qwen-Modell ausdrücklich entladen
werden, ebenso jedes weitere große residente Modell.** Kein Parallelversuch.
Der Router und andere Dienste sollen bleiben; die Entladung braucht die spätere
Freigabe. Aktuell wurden weder diese Modelle noch Dienste verändert.
Die vorgesehenen 2 GiB Cache und 8 GiB Reserve sind ein historisch belegtes
Startprofil, keine aus 48 GB abgeleitete Garantie des momentanen freien Speichers.

## 5. Spätere Befehle — jetzt ausdrücklich NICHT ausführen

Nur nach positiver Metadatenprüfung und gesonderter Freigabe von Download,
Konvertierung, Modellentladung und Modellstart. Optionen gegen gespeicherte
Binary-Hilfe geprüft; kein Live-Test dieser Modellbefehle.

Gemeinsame Pfade in einem Terminal:

```bash
EXP='/Users/hans-wernereberhardt/PycharmProjects/llama-server/experiments/slipstream_20261017'
EXT='/Volumes/Extern M4 Speicher'
MODEL_DIR="$EXT/LLM-Experimente/slipstream/qwen35b-reference"
GGUF="$MODEL_DIR/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"
PINTERNAL="$EXP/pgrn/Qwen3.6-35B-A3B-UD-Q4_K_XL.pgrn"
PEXTERNAL="$MODEL_DIR/Qwen3.6-35B-A3B-UD-Q4_K_XL.pgrn"
ENGINE="$EXP/runtime/Slipstream.app/Contents/Resources/resources/llama-server"
CONVERTER="$EXP/runtime/Slipstream.app/Contents/Resources/resources/pgrn-convert"
```

Vor jedem späteren Schreiben Mount prüfen, sonst abbrechen; niemals ersatzweise
den Mountpoint erzeugen. Danach vorhandene Ziele auf Konflikte prüfen, keine
fertigen Dateien überschreiben:

```bash
python3 -B -c 'import os; assert os.path.ismount("/Volumes/Extern M4 Speicher"), "SSD nicht eingehängt"'
df -k "$EXT" "$EXP"
# Erst nach erfolgreicher Mountprüfung und Freigabe:
mkdir -p "$MODEL_DIR" "$EXP/pgrn"
```

Späterer Download: verifizierter gepinnter Resolve-URL; direkt extern, nur in
eine noch nicht vorhandene bzw. zur exakt gleichen Revision gehörende `.download`-
Datei. Vorher darf kein fertiges `$GGUF` existieren. Größe, GGUF-Signatur und
vollständigen Hash vor der Umbenennung prüfen; bei Abweichung nicht fortfahren.

```bash
curl --fail --location --continue-at - --output "$GGUF.download" \
 'https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/resolve/5bc3e238d916f48a861bac2f8a1990a0e9b7e98d/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf?download=true'
stat -f '%z' "$GGUF.download"  # muss 22853663008 sein
shasum -a 256 "$GGUF.download" # muss 55983c5a…fe9f1 sein, vollständiger Sollhash oben
# NUR wenn Größe/Signatur/Hash stimmen und Ziel nicht existiert:
mv -n "$GGUF.download" "$GGUF"
"$CONVERTER" --input "$GGUF" --dry-run
# Erst nach bestandenem Dry-run und noch nicht vorhandenem PGRN-Ziel:
"$CONVERTER" --input "$GGUF" --output "$PINTERNAL" \
 --expect-sha256 '55983c5a75a1ab969824077b3bb3de4146e82a9234072b48ad4e8f92ad3fe9f1' \
 --io-threads 4 --min-free-gb 16 --progress jsonl
stat -f '%z' "$PINTERNAL"
shasum -a 256 "$PINTERNAL"
cp -n "$PINTERNAL" "$PEXTERNAL"
shasum -a 256 "$PINTERNAL" "$PEXTERNAL"
```

Die beiden PGRN-Hashes müssen gleich sein. Den historischen 732a314b-Hash zusätzlich
vergleichen; bei Abweichung Herkunft/Layout aufklären, kein stilles Akzeptieren.
Kopie und Hashprüfungen wärmen den Dateicache: unmittelbar danach kein „kalter“ Benchmark.

### Modellprozess, nur einer gleichzeitig

Port 8083 unmittelbar vorher erneut auf Freiheit prüfen. Zum Prüfzeitpunkt waren
8083/8093 frei. Die eigentliche Messung geht direkt an 8083, damit Proxy-/UI-/MCP-
Unterschiede keine SSD-Messung verfälschen. Kein Rollen- oder Review-Eval in diesem Schritt.

```bash
lsof -nP -iTCP:8083 -sTCP:LISTEN
# Keine Ausgabe erwartet; bei Konflikt abbrechen, keine fremde PID stoppen.
```

Profil: historisches kleines Qualifikationsprofil 2 GiB/8 GiB, Kontext 512,
Batch/UBatch 32/32, MTP max. 4, Thinking an, Compact AUS, I/O 1, kein Prefetch,
keine Gewichts-Partitionierungsdatei, kein Repack. Temp. 0, Seed 42, ein Slot.
Weder die frühe 10-GB-Observer-Leistung noch spätere Compact-Spitzen werden erwartet.

In A `PGRN="$PINTERNAL"`, in B `PGRN="$PEXTERNAL"`, sonst derselbe Befehl:

```bash
PGRN="$PINTERNAL"  # für B ausschließlich durch "$PEXTERNAL" ersetzen
# Eigenes Terminal pro Lauf; caffeinate gilt nur während dieses Prozesses.
env -i HOME="$HOME" PATH='/usr/bin:/bin:/usr/sbin:/sbin' \
 /usr/bin/caffeinate -im "$ENGINE" \
 --model "$GGUF" --pgrn "$PGRN" \
 --host 127.0.0.1 --port 8083 --alias qwen-stream-reference \
 --pgrn-cache-gb 2 --pgrn-headroom-gb 8 --pgrn-io-threads 1 \
 --pgrn-hot-percent 0 --ctx-size 512 --batch-size 32 --ubatch-size 32 \
 --parallel 1 --gpu-layers 99 --no-mmap --no-repack --no-warmup \
 --cache-type-k f16 --cache-type-v f16 --spec-type draft-mtp \
 --spec-draft-n-max 4 --temp 0 --seed 42
```

Den Terminaloutput pro Lauf als eigene Logdatei speichern. Saubere `env -i`-
Umgebung vermeidet geerbte `LLAMA_ARG_*`, `PGRN_MIRROR`, `PGRN_BUFFERED`,
`PGRN_PAGECACHE`, `PGRN_ONLINE_PREDICT`, `SPEC_PIN` usw. Ohne Mirror ausschließlich
die gewählte PGRN-Quelle; kein gleichzeitig laufendes A/B. `HOME` wird nur an das
Kind weitergegeben, nicht umdefiniert. Bei Admission-Verweigerung stoppen,
Reserve nicht senken, um einen Erfolg zu erzwingen.

Stop: **Ctrl+C im eigenen Vordergrund-Terminal**. Nur diese eigene Prozessgruppe
beenden, niemals `pkill` oder vorhandene Labor-PIDs. Danach 8083 frei und bestehende
Labor-Listener/Erreichbarkeit mit dem vor jedem Lauf gespeicherten Zustand vergleichen.

### Messprotokoll

1. Direkt vor dem Prozessstart Uhrzeit, `vm_stat`, `memory_pressure`,
   `sysctl vm.swapusage`, Labordienste und freien Speicher sichern. Zeit von
   Prozessstart bis erstem erfolgreichen `/health` separat als Ladezeit erfassen.
   Bei 503 weiter als nicht bereit kennzeichnen, bei Prozessende Fehler sichern.
2. Vor jeder Anfrage: Hardwarezähler-Snapshot, Uhrzeit, VM/Swap. Nach erfolgreichem
   Laden den eigenen Engine-PID aus dem Listener feststellen und mit `lsof -p PID`
   kontrollieren, dass die erwartete interne bzw. externe PGRN geöffnet ist.
3. `request_stream.py` sendet zwei unveränderliche Codeprüf-Prompts mit 64 und
   128 Ausgabetokens, Seed 42, Temp. 0, Thinking an, `cache_prompt=false`.
   Es misst TTFT bis erstem nichtleerem Content-/Reasoning-Delta, nicht bis zu HTTP-
   Headern/Role-Events; vollständige SSE-Ereignisse, Usage und eventuell vorhandene
   native `timings` werden gespeichert. Bei fehlenden Timings keine native Decode-
   Rate erfinden; Completiontoken geteilt durch Gesamtzeit ist nur Gesamtdurchsatz.

```bash
# Nach Bereitschaft, mit einem NEUEN Ausgabedateinamen pro Prozesslauf:
python3 -B "$EXP/qwen_reference/request_stream.py" \
 --output "$EXP/qwen_reference/A1-response.json"
```

4. Engine-Log nach jedem Turn und nach sauberem Stop sichern. Belegte Zeilen:
   `PGRN cache = … hits = … misses = …`, High-water/Scratch und
   `PGRN top-k read … fetch … upload …`. Hits/Misses sind kumulativ; Differenzen
   pro Messfenster auswerten. Misses müssen tatsächlich positiv sein.
   Uploadbytes sind **keine** SSD-Lesebytes. `--metrics` alleine verspricht keinen
   zusätzlichen PGRN-Miss-Zähler; primärer Beleg ist hier die native Logtelemetrie.
5. `vm_stat 1` und periodische eigene Prozess-RSS-Messung (`ps -o rss= -p PID`)
   parallel aufzeichnen, danach `sysctl vm.swapusage` und `memory_pressure`.
   Swapouts sind systemweite kumulative Seitenzähler: Deltas mit tatsächlicher
   `vm_stat`-Seitengröße umrechnen. RSS bildet Unified-Memory-/GPU-Belastung nicht
   vollständig ab. Bei wachsendem Swap oder deutlichem Speicherdruck abbrechen.

## 6. Tatsächliche SSD-Lesezugriffe und Dateicache

Codebelegt im PGRN-Leser: `pread` auf Miss, CRC-Prüfung vor Veröffentlichung;
macOS-Pfad setzt `fcntl(F_NOCACHE,1)`. **Der Returncode wird dort ignoriert.**
Das Vorhandensein dieses Aufrufs ist daher kein Laufzeitbeweis seiner Wirkung.
Das Projekt dokumentiert außerdem ausdrücklich, dass F_NOCACHE bereits residente
Seiten nicht purgt. Prozessneustart leert nur den Engine-Cache, nicht den OS-Cache.

Zusätzlich zu positiven Arena-Misses und richtigem offenen PGRN-Pfad ist ein
gerätebezogener **Lese**-Nachweis während der Anfragen nötig, getrennt vom Laden/
Quellhash. Auch in A liest der Start das externe GGUF; diese Bytes beweisen B nicht.

Vor jedem Lauf den aktuellen Mount und dessen physisches Samsung-T7-Gerät erneut
zuordnen. Alte Kennungen disk5/disk6 nicht übernehmen. Read-only Hilfen:

```bash
mount
ioreg -p IOService -l -w 0
ioreg -r -c IOBlockStorageDriver -l -w 0
# Nur nach aktueller physischer Gerätezuordnung:
# iostat -d -w 1 -c 120 <tatsächlich ermitteltes physisches BSD-Gerät>
```

`ioreg` zeigt hier grundsätzlich `Statistics` mit `Bytes (Read)` und
`Operations (Read)`; die sichere Zuordnung dieser Zähler zur T7 und deren
fortlaufende Erfassung ist noch zu qualifizieren. Snapshots unmittelbar vor/nach
Anfragen erfassen, Leerlaufmessung als Hintergrundkontrolle. `iostat` ist vorhanden,
Optionen aus lokaler Manpage geprüft; seine MB/s sind Gesamt-I/O, nicht automatisch
Leserate. Die erste Zeile ist seit Boot gemittelt und gehört nicht ins Messfenster.
Positives iostat allein beweist weder Dateipfad noch Prozesszuordnung.

Optionales `fs_usage -w -f diskio -t 120 PID` ist syntaktisch durch lokale Hilfe
belegt, aber auf macOS oft privilegiert. Hier keine Privilegierung/Tracingprobe
ausgeführt. Falls ohne weitere Rechte nicht verfügbar: keine Systemeinstellung
ändern und keinen vollständigen I/O-Nachweis behaupten. Prozess-PGRN-Pfad,
Miss-Deltas, Geräte-Lesezähler und ruhige Hintergrundkontrolle gemeinsam auswerten;
wenn Zuordnung/Read-Deltas nicht zuverlässig gelingen: **externer Streaming-
Nachweis offen**, auch bei normalem Textoutput.

Reihenfolge A1–B1–B2–A2, besser zusätzlich B3–A3. Pro Prozess dieselben zwei
Anfragen, Turn 1 als prozessfrisch, Turn 2 als arena-warm kennzeichnen.
Speicherdruck, Cache-Residuen und Reihenfolge protokollieren; keine Behauptung
„kalt“ allein wegen Neustart. Keine künstliche RAM-Füllung, Purge-Befehle oder
Systemänderungen. Ein optionaler regulärer Neustart wäre später gesondert
abzustimmen und ersetzt die Lesezähler nicht. Keine Kopie/Hashprüfung im
Messfenster. Sind die B-Lesezähler trotz Misses null/unklar, Ergebnis unbestätigt.

## Abschlussgrenze und nächste Freigabe

Jetzt zuerst nur den begrenzten Metadatenbefehl aus Abschnitt 2 ausführen.
Erst sein vollständiges Ergebnis entscheidet über die nächste Freigabe:
**22,85 GB Modelldownload extern, ca. 20,13 GB Konvertierung intern und ca.
20,13 GB externe Vergleichskopie**, anschließend Entladen der vorhandenen großen
Modelle und nacheinander die isolierten Modellstarts. Noch nichts davon genehmigt
oder ausgeführt. Kein neuer Engine-Build als vermeintlich notwendige Lösung.

Selbst ein später bestandener Vergleich belegt nur das gewählte Qwen-Artefakt,
den begrenzten Cache und die konkrete SSD-Nutzung. Kein Beleg eines Modells
oberhalb 48 GB, keiner für GLM, kein Qualitätsvergleich mit Haiku und keine
Qualifikation als stärkerer Reviewer. Der Review-Eval bleibt ein späterer Schritt.

Quellen: [RESULTS v0.3.4](https://raw.githubusercontent.com/Schero94/slipstream/v0.3.4/bench/RESULTS.md),
[native 35B-Qualifikation](https://github.com/Schero94/slipstream/blob/v0.3.4/bench/m0d/NATIVE_PGRN_35B_RESULTS.md),
[historischer Runner](https://github.com/Schero94/slipstream/blob/v0.3.4/bench/m0d/run_native_streaming_ab.py),
[PGRN-IO](https://github.com/Schero94/slipstream/blob/v0.3.4/engine/src/peregrine_io.h),
[Engine-Patch](https://github.com/Schero94/slipstream/blob/v0.3.4/patches/slipstream-seams.patch),
[Qwen-Basisarchitektur](https://github.com/ggml-org/llama.cpp/blob/79bba02a6741/src/models/qwen35moe.cpp).
Lokale Quellenidentität und extrahierte Belege: `qwen_reference/sources.json`.
