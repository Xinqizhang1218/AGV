#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo "Usage: bash native/build_nodka_light.sh /path/to/LinuxSDK GCC_9.4.0" >&2
  exit 2
fi
sdk_dir="$(realpath "$1")"
sdk_variant="$2"
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
output_dir="$project_dir/third_party/nodka/lib"
test -f "$sdk_dir/Lib/include/NKLCLIB.h"
test -f "$sdk_dir/Lib/$sdk_variant/libNKLCLIB.so"
mkdir -p "$output_dir"
cp "$sdk_dir/Lib/$sdk_variant/libNKLCLIB.so" "$output_dir/libNKLCLIB.so"
g++ -std=c++11 -O2 -fPIC -shared -pthread \
  "$project_dir/native/nodka_light_bridge.cpp" \
  -I"$sdk_dir/Lib/include" -L"$output_dir" -lNKLCLIB \
  -Wl,-rpath,'$ORIGIN' -Wl,-z,defs \
  -o "$output_dir/libagv_nodka_light.so"
echo "Built: $output_dir/libagv_nodka_light.so"
ldd "$output_dir/libagv_nodka_light.so"
