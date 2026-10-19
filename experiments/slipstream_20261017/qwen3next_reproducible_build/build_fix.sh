#!/usr/bin/env bash
# Korrigierte Binaries aus dem geprueften Referenzquellstand (reference/source_patched):
#   fixed/       = Referenz + pgrn_empty_ubatch_fix.patch
#   fixed_diag/  = Referenz + pgrn_empty_ubatch_fix_with_diag.patch
# Startet keinen Server, installiert nichts, ueberschreibt nichts.  Aufruf: bash build_fix.sh
set -euo pipefail
B="$(cd "$(dirname "$0")" && pwd)"
RS="$B/reference/source_patched"
REF_HASHES="$(ls -d "$B"/logs/ab_* | tail -1)/reference_source_sha256.txt"
RELEASE="$B/../runtime/Slipstream.app/Contents/Resources/resources/llama-server"
RELEASE_SHA=7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e
L="$B/logs/fix_$(date +%Y%m%dT%H%M%S)"
CMAKE_OPTS=(-DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DLLAMA_OPENSSL=OFF
            -DLLAMA_CURL=OFF -DGGML_METAL_EMBED_LIBRARY=ON -DCMAKE_OSX_ARCHITECTURES=arm64)
die(){ echo "ABBRUCH: $*" >&2; exit 1; }
sha(){ shasum -a 256 "$1" | awk '{print $1}'; }
hashtree(){ ( cd "$1" && find . -type f -print0 | sort -z | xargs -0 shasum -a 256 ); }
gapply(){ local g; g="$(mktemp -d)"; git init -q "$g"
  local n; n=$(cd "$1" && LC_ALL=C LANG=C GIT_DIR="$g/.git" GIT_WORK_TREE="$1" git apply --check -v "$2" 2>&1 | grep -c "^Checking patch" || true)
  [ "$n" = 1 ] || die "Patch $2 nicht anwendbar (geprueft: $n Dateien)"
  ( cd "$1" && GIT_DIR="$g/.git" GIT_WORK_TREE="$1" git apply "$2" ) || die "git apply $2"; rm -rf "$g"; }

for d in fixed fixed_diag; do [ ! -e "$B/$d" ] || die "$B/$d existiert schon"; done
mkdir -p "$L"
[ "$(sha "$RELEASE")" = "$RELEASE_SHA" ] || die "Releasebinary-Hash weicht ab"
[ -f "$REF_HASHES" ] || die "Kein Hashprotokoll des Referenzquellstands"
hashtree "$RS" > "$L/reference_source_now.txt"
cmp -s "$REF_HASHES" "$L/reference_source_now.txt" || die "reference/source_patched hat sich seit dem A/B-Build veraendert"

variant(){ # $1 name  $2 patch  $3 binary name
  local S="$B/$1/source" BD="$B/$1/build" BIN="$B/$1/bin/$3"
  echo "== $1: Quelle + $(basename "$2")"
  mkdir -p "$S"; ( cd "$RS" && tar -cf - . ) | tar -x -C "$S"
  hashtree "$S" | cmp -s - "$REF_HASHES" || die "$1: Kopie != Referenz"
  gapply "$S" "$2"
  diff -rq "$RS" "$S" > "$L/$1_source_diff.txt" || true
  [ "$(cat "$L/$1_source_diff.txt")" = "Files $RS/src/llama-context.cpp and $S/src/llama-context.cpp differ" ] || die "$1: unerwartete Quellunterschiede"
  echo "== $1: Build"
  cmake -S "$S" -B "$BD" "${CMAKE_OPTS[@]}" > "$L/$1_configure.log" 2>&1 || die "configure $1"
  set +e; cmake --build "$BD" --target llama-server -j "$(sysctl -n hw.ncpu)" > "$L/$1_build.log" 2>&1; rc=$?; set -e
  [ $rc -eq 0 ] || die "BUILD FAILED $1 (exit $rc), siehe $L/$1_build.log"
  mkdir -p "$(dirname "$BIN")"; cp "$BD/bin/llama-server" "$BIN"
  sha "$BIN" > "$BIN.sha256"
  { echo "sha256=$(cat "$BIN.sha256")"; lipo -archs "$BIN" || true; otool -L "$BIN" || true
    echo "PGRN-DIAG-Strings: $(strings "$BIN" | grep -c '\[PGRN-DIAG\]' || true)"; } > "$L/$1_verify.txt" 2>&1
  echo "   $BIN"; echo "   sha256=$(cat "$BIN.sha256")"
}
variant fixed      "$B/patches/pgrn_empty_ubatch_fix.patch"           llama-server-pgrn-fixed
variant fixed_diag "$B/patches/pgrn_empty_ubatch_fix_with_diag.patch" llama-server-pgrn-fixed-diag
[ "$(sha "$RELEASE")" = "$RELEASE_SHA" ] || die "Releasebinary veraendert?!"
echo "FERTIG. Logs: $L"
