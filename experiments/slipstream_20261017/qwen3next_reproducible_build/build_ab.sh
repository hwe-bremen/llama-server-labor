#!/usr/bin/env bash
# Slipstream v0.3.4 – Referenz- (A) und Diagnosebuild (B). Nur bauen + statisch prüfen.
# Startet KEINEN Server, sendet keine Anfrage, installiert nichts, überschreibt nichts.
# Aufruf im normalen macOS-Terminal:  bash build_ab.sh
set -euo pipefail
B="$(cd "$(dirname "$0")" && pwd)"
UP="$B/upstream"; SL="$B/slipstream"
PIN=79bba02a6741de194912d370015866414faa83ad
SLPIN=0b30cac2a6a40439b74cce6a512f08166f6e3ab3
SEAMS_SHA=3f9ce71145da71f62f0f1fcd9b75a72a804ca553fbf57fd63dcb333ed228794d
RELEASE="$B/../runtime/Slipstream.app/Contents/Resources/resources/llama-server"
RELEASE_SHA=7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e
DIAG_PATCH="$B/patches/pgrn_callback_geometry_diagnostic.patch"
RS="$B/reference/source_patched"; RB="$B/reference/build_patched"; RBIN="$B/reference/bin"
DS="$B/diagnostic/source"; DB="$B/diagnostic/build"; DBIN="$B/diagnostic/bin"
L="$B/logs/ab_$(date +%Y%m%dT%H%M%S)"
CMAKE_OPTS=(-DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DLLAMA_OPENSSL=OFF
            -DLLAMA_CURL=OFF -DGGML_METAL_EMBED_LIBRARY=ON -DCMAKE_OSX_ARCHITECTURES=arm64)
die(){ echo "ABBRUCH: $*" >&2; exit 1; }
sha(){ shasum -a 256 "$1" | awk '{print $1}'; }
# git apply darf das umgebende Repo (llama-server) NICHT finden, sonst werden Pfade still übersprungen.
gapply(){ # $1 Zielbaum, $2 Patch. Eigenes leeres Hilfsrepo: keine Repo-Suche, Pfade relativ zu $1.
  local g; g="$(mktemp -d)"; git init -q "$g"
  local n
  n=$(cd "$1" && LC_ALL=C LANG=C LANGUAGE=C GIT_DIR="$g/.git" GIT_WORK_TREE="$1" git apply --check -v "$2" 2>&1 | grep -c "^Checking patch" || true)
  echo "$n" > "$L/applied_count_$(basename "$2").txt"
  ( cd "$1" && GIT_DIR="$g/.git" GIT_WORK_TREE="$1" git apply "$2" ) || die "git apply $2 fehlgeschlagen"
  rm -rf "$g"
}

for d in "$RS" "$RB" "$RBIN" "$DS" "$DB" "$DBIN"; do [ ! -e "$d" ] || die "$d existiert schon (nichts wird überschrieben)"; done
mkdir -p "$L"
lsof -nP -iTCP -sTCP:LISTEN > "$L/listeners_before.txt" 2>/dev/null || true
[ "$(sha "$RELEASE")" = "$RELEASE_SHA" ] || die "Releasebinary-Hash weicht ab"

echo "== Phase B: Quellen prüfen"
[ "$(git -C "$UP" rev-parse "$PIN^{commit}")" = "$PIN" ] || die "upstream-Commit fehlt"
[ "$(git -C "$SL" rev-parse HEAD)" = "$SLPIN" ] || die "slipstream HEAD != $SLPIN"
[ -z "$(git -C "$SL" status --porcelain)" ] || die "slipstream-Checkout nicht sauber"
[ "$(sha "$SL/patches/slipstream-seams.patch")" = "$SEAMS_SHA" ] || die "Seams-Hash weicht ab"
git -C "$UP" fsck --no-dangling > "$L/upstream_fsck.txt" 2>&1 || die "upstream fsck"
git -C "$SL" fsck --no-dangling > "$L/slipstream_fsck.txt" 2>&1 || die "slipstream fsck"

echo "== Rekonstruktion wie apply.sh: Checkout @PIN, cp -R engine/*, git apply seams"
mkdir -p "$RS"
git -C "$UP" archive --format=tar "$PIN" | tar -x -C "$RS"
cp -R "$SL"/engine/* "$RS"/
gapply "$RS" "$SL/patches/slipstream-seams.patch"
[ "$(cat "$L/applied_count_slipstream-seams.patch.txt")" = 62 ] || die "Seams: nicht alle 62 Dateien geprüft"
grep -q "struct llama_model_laguna" "$RS/src/models/models.h" || die "Seams nicht angewendet (laguna)"
grep -q "bool llama_context::pgrn_eval(" "$RS/src/llama-context.cpp" || die "Seams nicht angewendet (pgrn_eval)"
( cd "$RS" && find . -type f -print0 | sort -z | xargs -0 shasum -a 256 ) > "$L/reference_source_sha256.txt"

echo "== Phase D: Diagnosekopie, vor Instrumentierung identisch?"
mkdir -p "$DS"; ( cd "$RS" && tar -cf - . ) | tar -x -C "$DS"
( cd "$DS" && find . -type f -print0 | sort -z | xargs -0 shasum -a 256 ) > "$L/diag_source_pre_sha256.txt"
cmp -s "$L/reference_source_sha256.txt" "$L/diag_source_pre_sha256.txt" || die "Diagnosekopie != Referenz"
gapply "$DS" "$DIAG_PATCH"
[ "$(cat "$L/applied_count_$(basename "$DIAG_PATCH").txt")" = 1 ] || die "Diagnosepatch nicht angewendet"
diff -rq "$RS" "$DS" > "$L/source_diff.txt" || true
[ "$(cat "$L/source_diff.txt")" = "Files $RS/src/llama-context.cpp and $DS/src/llama-context.cpp differ" ] || die "unerwartete Quellunterschiede, siehe $L/source_diff.txt"
diff -u "$RS/src/llama-context.cpp" "$DS/src/llama-context.cpp" > "$L/source_diff.patch" || true

build(){ # $1 src $2 build $3 bin-ziel $4 name
  echo "== Build $4"
  cmake -S "$1" -B "$2" "${CMAKE_OPTS[@]}" > "$L/$4_configure.log" 2>&1 || die "configure $4, siehe $L/$4_configure.log"
  set +e; cmake --build "$2" --target llama-server -j "$(sysctl -n hw.ncpu)" > "$L/$4_build.log" 2>&1; rc=$?; set -e
  echo "build_exit=$rc" > "$L/$4_build_exit.txt"; [ $rc -eq 0 ] || die "BUILD FAILED $4 (exit $rc), siehe $L/$4_build.log"
  mkdir -p "$(dirname "$3")"; cp "$2/bin/llama-server" "$3"
  { echo "binary=$3"; echo "sha256=$(sha "$3")"; lipo -archs "$3"; file "$3" || true
    echo "--- otool -L"; otool -L "$3" || true
    echo "--- nm pgrn (Anzahl)"; nm -C "$3" | grep -ci pgrn || true
    echo "--- nm qwen3next (Anzahl)"; nm -C "$3" | grep -ci qwen3next || true
    echo "--- Metal-Strings"; strings "$3" | grep -c -i "ggml_metal" || true
    echo "--- PGRN-DIAG-Strings"; strings "$3" | grep -c "\[PGRN-DIAG\]" || true
    echo "--- Build-Kennung aus Strings (Binary wird nicht gestartet)"; strings "$3" | grep -E "^b?[0-9]{4,5} \\(|build_commit|LLAMA_BUILD" | head -5 || true
    echo "--- CMakeCache"; grep -E "^(CMAKE_BUILD_TYPE|BUILD_SHARED_LIBS|LLAMA_OPENSSL|LLAMA_CURL|GGML_METAL[A-Z_]*|GGML_BLAS[A-Z_]*|GGML_NATIVE|GGML_CPU[A-Z_]*|CMAKE_OSX_ARCHITECTURES|CMAKE_CXX_COMPILER|CMAKE_OSX_SYSROOT):" "$2/CMakeCache.txt"
    cmake --version | head -1; "$(grep '^CMAKE_CXX_COMPILER:' "$2/CMakeCache.txt" | cut -d= -f2)" --version | head -1
  } > "$L/$4_verify.txt" 2>&1
}
build "$RS" "$RB" "$RBIN/llama-server-reference" reference
build "$DS" "$DB" "$DBIN/llama-server-pgrn-diagnostic" diagnostic
diff <(grep -E "^[A-Z_]+:" "$RB/CMakeCache.txt" | grep -v -E "_DIR:|_BINARY_DIR|_SOURCE_DIR|CMAKE_CACHEFILE_DIR|_LIB_DEPENDS" ) \
     <(grep -E "^[A-Z_]+:" "$DB/CMakeCache.txt" | grep -v -E "_DIR:|_BINARY_DIR|_SOURCE_DIR|CMAKE_CACHEFILE_DIR|_LIB_DEPENDS" ) > "$L/cmakecache_diff.txt" || true

[ "$(sha "$RELEASE")" = "$RELEASE_SHA" ] || die "Releasebinary nach Build verändert?!"
lsof -nP -iTCP -sTCP:LISTEN > "$L/listeners_after.txt" 2>/dev/null || true
echo "FERTIG. Logs: $L"; grep -H "sha256=\|PGRN-DIAG-Strings" -A1 "$L"/*_verify.txt
