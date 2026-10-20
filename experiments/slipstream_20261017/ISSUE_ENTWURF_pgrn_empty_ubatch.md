# Entwurf: Fehlermeldung an Slipstream (20.10.2026)

Ziel: https://github.com/Schero94/slipstream (Issues). Abschicken macht Hawe, nicht Claude.

## Vorher prüfen (Hawe, ~2 min)

Gebaut und getestet haben wir v0.3.4 (`0b30cac`). Laut unseren Notizen gibt es v0.3.5. Bevor wir melden: Ist der
Fehler im aktuellen Stand schon behoben oder bereits gemeldet?

```bash
cd ~/PycharmProjects/llama-server/experiments/slipstream_20261017/qwen3next_reproducible_build/slipstream
git remote -v                                   # sollte github.com/Schero94/slipstream zeigen
git fetch origin --tags                          # ändert nichts am ausgecheckten Stand
git log --oneline 0b30cac..origin/main | head -30
git show origin/main:patches/slipstream-seams.patch | grep -n "ne\[1\]"
```

- Zeigt die letzte Zeile eine Sonderbehandlung für `ne[1] == 0` (oder ist `ne[1] <= 0` aus der Bedingung verschwunden),
  ist der Fehler behoben → nicht melden, Notiz anpassen.
- Sonst im Browser unter Issues nach „geometry" und „qwen3next" suchen (Claude kann die Issue-Seite nicht abrufen).
- Platzhalter unten ausfüllen: macOS-Version (`sw_vers -productVersion`).

## Text für GitHub (englisch)

**Title:** Qwen3-Next: every request fails with "top-k tensor geometry is incompatible with PGRN staging" (empty last-layer ubatch) – fix included

**Summary**

With Qwen3-Coder-Next 80B-A3B and PGRN streaming, every chat request fails during prompt processing with
`top-k tensor geometry is incompatible with PGRN staging` (HTTP 500, decode returns -3). The cause is a ubatch
without output tokens: in the last layer Qwen3-Next reduces rows to the output tokens before the MoE block, so the
top-k tensor arrives with `ne[1] == 0`, and the geometry guard in `llama_context::pgrn_eval` rejects it. A 9-line
fix that treats this case as "nothing to stage" makes the model fully usable; outputs are byte-identical across
cache sizes.

**Environment**

- Slipstream v0.3.4 (`0b30cac2a6a40439b74cce6a512f08166f6e3ab3`), built from source (llama.cpp `79bba02` +
  `slipstream-seams.patch`), Apple clang 21.0.0, CMake 4.1.1. The official v0.3.4 release binary shows the same error.
- MacBook Pro M4 Pro, 48 GB unified memory, macOS <VERSION>
- Model: `Qwen3-Coder-Next-Q4_K_M.gguf` (48,528,320,544 bytes), PGRN converted with v0.3.4 (46,909,751,296 bytes)
- Server: `--pgrn-cache-gb 12 --pgrn-headroom-gb 8 --batch-size 25 --ubatch-size 25 --parallel 1 --spec-type none
  --reasoning off --gpu-layers 99 --jinja --ctx-size 4096`

**Reproduce**

One chat request, e.g. `"Antworte ausschließlich mit der Zahl: 17 + 25"`, `temperature 0`, `max_tokens 32`.
The server processes a first prompt ubatch of 21 tokens (of 25) that contains no output token — presumably the
server holds back the last tokens for a recurrent-state checkpoint (not verified in the server code). That ubatch
fails in layer 47.

**Diagnosis** (one `fprintf` added before the guard, logging the callback tensor)

| Phase | Callbacks | Geometry | Guard |
|---|---|---|---|
| Warmup 1+2, layers 0–46 | 94 | ne=[10,2,1,1] nb=[4,2048,4096,4096] | ok |
| Warmup 1+2, layer 47 | 2 | ne=[10,1,1,1] | ok |
| Prompt ubatch (21 tokens), layers 0–46 | 47 | ne=[10,21,1,1] nb=[4,2048,43008,43008] | ok |
| Prompt ubatch, **layer 47** | 1 | **ne=[10,0,1,1] nb=[4,2048,0,0]** | **fails: ne[1] > 0** |

Type i32, `ne[0] == n_expert_used == 10`, `nb[0] == 4`, `ne[2] == ne[3] == 1` hold everywhere.
`src/models/qwen3next.cpp:142–144` applies `ggml_get_rows(…, inp_out_ids)` in the last layer before the MoE block,
which explains 1 row in warmup and 0 rows for a ubatch without outputs. An empty ubatch layer is not an error in plain
llama.cpp; `pgr_stage_selected` also treats an empty selection as success — only the guard is stricter.

**Fix** (`src/llama-context.cpp`, `llama_context::pgrn_eval`, +9/−1)

```diff
-    if (is_pgrn) {
+    if (is_pgrn && tensor->ne[1] == 0 && tensor->type == GGML_TYPE_I32 &&
+            tensor->ne[0] == model.hparams.n_expert_used && tensor->ne[2] == 1 && tensor->ne[3] == 1 &&
+            tensor->nb[0] == sizeof(int32_t)) {
+        // A ubatch without output rows reaches the last MoE layer with zero rows
+        // (inp_out_ids filter before the FFN). No expert is selected, so there is nothing to
+        // stage; pgr_stage_selected treats an empty selection as success as well. Only join a
+        // prefetch aimed at this layer, exactly as the staging path does first.
+        model.pgrn_prefetch_settle(layer);
+    } else if (is_pgrn) {
```

All other geometry checks are unchanged; only `ne[1] == 0` with otherwise valid geometry is let through.

**Validation**

- Three tests at `temperature 0, seed 42`: arithmetic (25 prompt tokens), a 892-token prompt (multi-ubatch prefill,
  retrieve a keyword), a 95-token code review with 392 output tokens — all correct, no errors in the log.
- Same three requests with PGRN cache 12 GiB (cold and warm), 18 GiB and 24 GiB: **outputs are byte-identical**
  (SHA-256 of the response text: A `73475cb4…`, B `d0310278…`, C `a5e4858d…` in all four runs). Hit rate
  79.1 % / 88.7 % / 92.0 %; generation 4.3–10.8 tok/s.
- Not verified: parity with a run without PGRN (the model does not fit in memory without streaming).

Thanks for Slipstream — with this fix an 80B MoE runs at ~11 tok/s on a 48 GB machine.
