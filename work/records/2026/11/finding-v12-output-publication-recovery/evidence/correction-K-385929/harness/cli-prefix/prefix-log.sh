#!/bin/sh
# records exactly what the CLI hands a shell prefix, then runs it unchanged
D="$(dirname "$0")"
{ echo "--- argc=$# ppid=$PPID"; for a in "$@"; do printf 'ARG<%s>\n' "$a"; done; } >> "$D/prefix-argv.log"
exec "$@"
