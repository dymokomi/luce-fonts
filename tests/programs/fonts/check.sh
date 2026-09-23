#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
mkdir -p build
exec python3 tests/programs/fonts/run.py "${1:-../luce-base/build/luce-base}"
