#!/usr/bin/env bash
# W384870 M385102: remove the 63 fixture roots the five-group run left under /var/tmp that hold
# product-frozen (0555) directories. Check mode by default; `--remove` acts. Only the roots named in
# leaked-roots-remaining.txt (all created 2026-11-18T05:30:57Z-05:33:24Z by that run) are touched.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
LIST=$HERE/leaked-roots-remaining.txt
MODE=${1:-check}
while read -r name; do
  [[ -n "$name" && "$name" != */* && "$name" != .* ]] || { echo "refusing odd name: $name"; exit 2; }
  path=/var/tmp/$name
  [[ -d "$path" && -O "$path" ]] || { echo "absent or not owned, skipped: $path"; continue; }
  if [[ "$MODE" == "--remove" ]]; then
    chmod -R u+rwx -- "$path" && rm -rf -- "$path" && echo "removed $path"
  else
    echo "would remove $path ($(find "$path" -type d ! -perm -u+w | wc -l) frozen dirs, $(du -sh "$path" | cut -f1))"
  fi
done < "$LIST"
echo "/var/tmp entries now: $(ls -1 /var/tmp | wc -l) (baseline before the run: 376)"
