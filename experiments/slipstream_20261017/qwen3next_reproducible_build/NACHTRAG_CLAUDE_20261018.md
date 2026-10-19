# Nachtrag Claude – 18.10.2026, ~15:30

Ergänzt `REPRODUCIBLE_BUILD_REPORT.md` (Stand 13:12, „BUILD BLOCKED"). Der Bericht ist überholt: Danach wurden
die Quellen doch beschafft, der Baum rekonstruiert und ein Referenzbuild versucht.

## Befund: Referenzbuild 13:14 ist an der Rekonstruktion gescheitert, nicht am Quellcode

- `upstream` HEAD = `79bba02a…`, `slipstream` HEAD = `0b30cac2…`, Seams-SHA-256 = `3f9ce711…` ✓
- `reference/source` = Upstream + engine-Overlay, **ohne Seams-Patch**. Nachweis:
  `git apply --check` vorwärts sauber, rückwärts Fehler; `LLM_ARCH_LAGUNA` und `pgrn_eval` fehlen;
  `diff -rq` gegen einen korrekt rekonstruierten Baum = genau die 62 Dateien des Seams-Patches, sonst nichts.
- Folge: Overlay-Datei `src/models/laguna.cpp` findet `llama_model_laguna` nicht (der Patch definiert sie in
  `src/models/models.h`) → Abbruch bei 48 % (`logs/reference_build.log`).
- Einordnung: weder BUILD FAILED des offiziellen Stands noch Quellfehler. Der Schritt `git apply` aus `apply.sh` fehlte.
  `reference/source` und `reference/build` bleiben unverändert als Beleg liegen.

## Neu angelegt (keine bestehende Datei verändert)

- `patches/pgrn_callback_geometry_diagnostic.patch` (+6/−0, nur `src/llama-context.cpp`, `llama_context::pgrn_eval`)
  - Position: nach der Pending-Prüfung/-Rücksetzung, unmittelbar vor `if (is_pgrn) { <Geometrie-Guard> }`
  - eine `fprintf(stderr, "[PGRN-DIAG] …")`: layer, name, type (Zahl + `ggml_type_name`), ne[0..3], nb[0..3],
    n_expert_used, ask, is_pgrn, compact
  - liest nur Metadaten des Tensor-Structs; kein Datenzugriff, keine GGML-Op, kein Sync/Transfer; Guard und
    Kontrollfluss unverändert
  - Loggt jeden Nicht-ask-Callback (also auch erfolgreiche Layer). Das ist beabsichtigt, so steht die
    fehlschlagende Geometrie direkt neben den funktionierenden. `ask` ist an dieser Stelle immer 0.
  - Syntax-Check `g++ -std=c++17 -fsyntax-only -Wformat=2` auf beiden Fassungen sauber (Linux-g++, nicht Apple clang)
- `build_ab.sh`: Phase B (Commits, sauberer Checkout, Seams-Hash, fsck) → Rekonstruktion exakt wie `apply.sh`
  (inkl. `git apply`) nach `reference/source_patched` → Diagnosekopie, Hash-Gleichheit vor Instrumentierung,
  Diagnosepatch, Prüfung „nur `llama-context.cpp` unterscheidet sich" → zwei Builds mit identischen Optionen
  (`reference/build_patched`, `diagnostic/build`) → Binaries nach `reference/bin/llama-server-reference` und
  `diagnostic/bin/llama-server-pgrn-diagnostic` → statische Prüfung (SHA-256, lipo, otool -L, nm pgrn/qwen3next,
  Strings Metal/[PGRN-DIAG], CMakeCache-Auszug und -Vergleich) → Releasehash und Listener vorher/nachher.
  Startet keine Binary, keinen Server, keine Installation; bricht ab, wenn ein Zielordner schon existiert.
  Phasen B–D in einer Linux-VM gegen die echten Quellen getestet (ohne CMake); Build selbst ungetestet.

## Abweichung vom Auftrag

- Referenz-Quellbaum heißt `reference/source_patched` statt `reference/source`, weil dort der unvollständige
  Stand liegt und nichts überschrieben werden soll.
- Gebaut wurde noch nichts: Der Claude-Zugang läuft in einer Linux-VM ohne Apple-Toolchain.
- Testplan (Phase G): unverändert gültig wie in `REPRODUCIBLE_BUILD_REPORT.md` §10.

## Zu erwarten / offen

- `common/CMakeLists.txt` warnt „Git repository not found" (Quellbaum aus `git archive`, ohne `.git`) →
  Build-Info leer. Betrifft nur die Versionskennung, nicht den Code. Die Release-Kennung `10116 (852e7daa1)` ist so
  ohnehin nicht reproduzierbar.
- Ob der Build mit Apple clang 21 / SDK 27 durchläuft, ist erst nach dem Lauf bekannt. Scheitert er, gilt BUILD FAILED
  ohne Quellkorrektur.

---

## Ergebnis Build 18.10.2026, 15:30–15:33 (Hawe, Terminal, `build_ab.sh`) — READY FOR CONTROLLED RUNTIME TESTS

Logs: `logs/ab_20261018T153020/`

| | Binary A Referenz | Binary B Diagnose |
|---|---|---|
| Pfad | `reference/bin/llama-server-reference` | `diagnostic/bin/llama-server-pgrn-diagnostic` |
| SHA-256 | `f70c092c08792f7d8d98ab6fb9dfdc116151fc4c0c92460fe87c7a8e29575469` | `975ba7c66a85bd650df4f9025f9c90e14d067dc1f43374a85c2ca2667737b73e` |
| Build-Exit | 0 | 0 |
| Architektur | Mach-O arm64 | Mach-O arm64 |
| Symbole pgrn / qwen3next | 59 / 21 | 59 / 21 |
| Metal | Metal + MetalKit gelinkt, eingebettet | gleich |
| `[PGRN-DIAG]` im Binary | 0 | 1 |
| Abhängigkeiten (`otool -L`) | nur Systemframeworks/-libs (CoreML, Foundation, Accelerate, Metal, MetalKit, libz, libc++, libSystem, libobjc) | identisch |

- Compiler: Apple clang 21.0.0 (clang-2100.3.34.2), CMake 4.1.1.
- CMake-Optionen wie Vorgabe; zusätzlich wirksame Defaults: `GGML_METAL=ON`, `GGML_BLAS=ON` (Apple Accelerate),
  `GGML_NATIVE=ON` (`-mcpu=native`, also auf diese M4-CPU optimiert), `GGML_CPU_REPACK=ON`, `GGML_CPU_KLEIDIAI=OFF`.
- CMakeCache A vs. B: einziger Unterschied `CMAKE_HOME_DIRECTORY` (Quellpfad).
- Quellen: Diagnosekopie vor der Instrumentierung hash-identisch mit der Referenz; danach ist nur `src/llama-context.cpp` anders,
  der Diff ist identisch mit `patches/pgrn_callback_geometry_diagnostic.patch` (+6/−0).
- Releasebinary-Hash vor/nach unverändert (Skriptprüfung); Listener-Liste vor/nach identisch. Keine Binary gestartet.

### Korrekturen am Skript während des Laufs (beide bei Codex' Abbruch ebenfalls die Ursache bzw. relevant)

1. `git apply` in einem Unterordner des `llama-server`-Repos überspringt Pfade still (rechnet relativ zur Repo-Wurzel).
   Das war auch die Ursache für Codex' ungepatchten `reference/source`. Lösung: eigenes leeres Hilfsrepo per `GIT_DIR`/`GIT_WORK_TREE`.
2. Zählprüfung mit `LC_ALL=C` (git am Mac gibt sonst lokalisierte Meldungen aus).
3. `grep -c` mit 0 Treffern hat unter `set -e` still beendet → `|| true` plus explizite Prüfungen.

### Abweichungen zur ausgelieferten Releasebinary

- Quellbaum ohne `.git` → keine Build-Kennung; `10116 (852e7daa1)` nicht reproduziert und nicht behauptet.
- `GGML_NATIVE=ON`: Codegen für die lokale CPU; ob die Releasebinary nativ oder generisch gebaut ist, ist unbekannt.
- Lokaler Compiler/SDK können von der Paketierungsumgebung abweichen.
- Funktionsidentität mit der Releasebinary ist **nicht** belegt. Das prüft genau Test A.

### Nächster Schritt

Test A laut `REPRODUCIBLE_BUILD_REPORT.md` §10, eigener Auftrag. Test B nur, wenn A den Geometriefehler reproduziert.

---

## Laufzeittests 18.10.2026 (`run_runtime_test.py`, Parameter 1:1 wie Originallauf 12:09)

**Test A, Referenz** (`runtime_runs/20261018T163156_reference/`): Geometriefehler **reproduziert**. Gleiche Meldung, gleiche
Logzeile (1598) wie die Releasebinary, `n_batch = 25`, HTTP 500, Laden 297 s. Der Fehler steckt also im veröffentlichten Quellstand.

**Test B, Diagnose** (`runtime_runs/20261018T164201_diagnostic/`): reproduziert, 144 `[PGRN-DIAG]`-Zeilen.

| Phase | Callbacks | Geometrie | Guard |
|---|---|---|---|
| Warmup 1+2, Layer 0–46 | 94 | ne=[10,2,1,1] nb=[4,2048,4096,4096] | ok |
| Warmup 1+2, Layer 47 | 2 | ne=[10,1,1,1] | ok |
| Prompt-Ubatch (21 Token), Layer 0–46 | 47 | ne=[10,21,1,1] nb=[4,2048,43008,43008] | ok |
| Prompt-Ubatch, **Layer 47** | 1 | **ne=[10,0,1,1] nb=[4,2048,0,0]** | **verletzt: ne[1] > 0** |

Typ (i32), ne[0] = n_expert_used = 10, nb[0] = 4, ne[2] = ne[3] = 1 stimmen überall. `nb[1] = 2048` = 512 × 4 Byte:
Der Top-k-Tensor ist eine Sicht auf die Argsort-Zeilen über 512 Experten. Der Guard verlangt kein `nb[1] == 40` und lässt das zu.

### Mechanismus (im Code belegt, Auslöser teils Vermutung)

- `src/models/qwen3next.cpp:142–144`: Im **letzten Layer** (`il == n_layer - 1`) werden die Zeilen per
  `ggml_get_rows(…, inp_out_ids)` auf die Ausgabe-Token reduziert, und zwar vor dem MoE-Block. Belegt durch die Warmup-Daten:
  Layer 47 hat dort 1 Zeile statt 2.
- Hat ein Ubatch **keine** Ausgabe-Token, ist die Top-k-Matrix im Layer 47 leer (`ne[1] = 0`). Der Guard in
  `llama_context::pgrn_eval` lehnt `ne[1] <= 0` als Geometriefehler ab → `PGRN staging failed` → decode ret = -3.
- Hier: `task.n_tokens = 25`, verarbeitet wurde ein Ubatch mit 21 Token ohne Ausgabe (`stop processing: n_tokens = 21`).
  **Vermutung:** Der Server hält bei diesem hybriden (rekurrenten) Modell die letzten Token für einen Kontext-Checkpoint zurück.
  Deshalb hat schon der erste Prompt-Ubatch keine Ausgabe. Nicht im Servercode nachgeprüft.
- Folge (abgeleitet, nicht gemessen): Vermutlich trifft es jeden Prompt, bei dem ein Ubatch ohne Ausgabe-Token entsteht.
  Mit Qwen3Next und PGRN ist das praktisch jede Anfrage. Mit der Cache-Größe oder der Geometrie des Callbacktensors hat es nichts zu tun.
- Ein leerer Ubatch-Layer ist im normalen llama.cpp kein Fehler (es gibt nichts zu rechnen). Der Guard behandelt ihn aber als Fehler.

### Einordnung (keine Reparatur vorgenommen, Auftrag endet hier)

Naheliegende Korrektur für einen späteren Auftrag: Bei `is_pgrn && ne[1] == 0` nichts stagen und den Callback erfolgreich
durchlassen, statt abzubrechen. Prüfen müsste man dabei, ob der Prefetch-Pfad (`pgrn_prefetch_kick`) und der Compact-Pfad
mit 0 Zeilen ebenfalls sauber sind. Melden ans Slipstream-Projekt mit dieser Tabelle als Beleg.

---

## Korrektur + Lauffähigkeit (18.10.2026, 16:55–17:04)

Patch `patches/pgrn_empty_ubatch_fix.patch` (+9/−1, nur `llama_context::pgrn_eval`): `is_pgrn && ne[1] == 0` bei sonst gültiger
Geometrie → nichts stagen, nur `pgrn_prefetch_settle(layer)`, Callback erfolgreich. Begründung: `pgr_stage_selected` behandelt
eine leere Auswahl selbst als Erfolg; nur der Guard war strenger. Gebaut mit `build_fix.sh` (`fixed/`, `fixed_diag/`).

**Lauf `runtime_runs/20261018T165552_fixed/`: LAUFFÄHIG.** Qwen3-Coder-Next 80B-A3B Q4_K_M (48,5 GB GGUF) auf 48 GB M4 Pro,
PGRN-Cache 12 GiB, Ubatch 25, Parameter sonst wie im Originallauf. Kein Geometriefehler, keine Fehlermarken im Log.

| Test | Prompt-Tok | Ausgabe-Tok | Prefill tok/s | Generierung tok/s | Ergebnis |
|---|---|---|---|---|---|
| A 17+25 | 25 | 3 | 9,5 | 7,3 | „42“ ✓ |
| B Kennwort | 892 | 8 | 22,4 | 4,4 | „BernsteinFalke739“ ✓ (Mehr-Ubatch-Prefill) |
| C Code-Review | 95 | 392 | 13,3 | 4,3 | beide Fehler richtig benannt, Korrektur richtig ✓ (von Claude gelesen) |

Laden 309 s. PGRN-Cache am Ende: 12,3 GiB belegt, Trefferquote 79 %. Kumulative Staging-Zeit 82 s (Fetch 54 s, Upload 28 s).
Während C (91,5 s Generierung) entfielen rund 52 s auf Staging → **Engpass ist das Experten-Nachladen, nicht das Rechnen.**

Nicht gemessen: Parität gegenüber einem Lauf ohne PGRN (Modell passt ohne Streaming nicht sinnvoll in den Speicher).
Die Korrektur gehört als Fehlermeldung an das Slipstream-Projekt (Belege: Test A/B-Diagnose oben).

## Cache-Vergleich (18.10.2026, 17:12 / 17:20; `runtime_runs/*_fixed_c18`, `*_fixed_c12`)

| Lauf | Cache | Treffer | Staging gesamt | A gen | B prefill | C gen | C Dauer |
|---|---|---|---|---|---|---|---|
| 16:55 kalt | 12 GiB | 79,1 % | 82 s | 7,3 | 22,4 | 4,3 tok/s | 98,7 s |
| 17:20 warm | 12 GiB | 79,1 % | 66 s | 6,8 | 22,9 | 5,3 tok/s | 80,8 s |
| 17:12 warm | 18 GiB | 88,7 % | 43 s | 6,4 | 32,9 | 7,7 tok/s | 57,1 s |

- Treffer/Fehlgriffe bei gleicher Cachegröße exakt gleich (299.862 / 79.061) → Expertenauswahl deterministisch, Trefferquote ist ein sauberes Maß.
- Kalt → warm (12 GiB): schnelleres Nachladen bei gleicher Trefferquote, vermutlich macOS-Dateicache (Vermutung).
- 18 vs. 12 warm: +45 % Generierung, Staging halbiert. Starter-Standard jetzt 18 GiB. Speicher frei vor Lauf: 91 %.
- Offen: 24 GiB; Kontext > 4096 und Tool-Aufrufe ungetestet (Review-Lauf über `scripts/launch_qwen3next_review.command`).
