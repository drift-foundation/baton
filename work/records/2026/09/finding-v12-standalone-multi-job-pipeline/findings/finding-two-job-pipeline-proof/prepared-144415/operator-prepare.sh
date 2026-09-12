#!/bin/bash
# Operator-only Git preparation for W71879 run2; agents do not execute this file.
set -euo pipefail

run2_root=/home/sl/.local/state/baton/v12/w71879-run2
run1_source=/home/sl/.local/state/baton/v12/w71879-run1/source
expected_commit=2fbb2d456638e5706218020aebfa47f0a82c8920
expected_tree=3492ba64448ab9d39bde53ee6456ce24e74ece2c

test ! -e "$run2_root"
test ! -L "$run2_root"
test "$(git -C "$run1_source" show --no-patch --format='%H %T' HEAD)" = "$expected_commit $expected_tree"
test "$(git -C "$run1_source" symbolic-ref --short HEAD)" = main
test -z "$(git -C "$run1_source" status --porcelain)"

mkdir -m 700 "$run2_root"
git clone --no-hardlinks --single-branch --branch main "$run1_source" "$run2_root/source"
git clone --no-hardlinks --single-branch --branch main "$run2_root/source" "$run2_root/target"
git init --bare "$run2_root/integration-workspace"

for checkout_path in "$run2_root/source" "$run2_root/target"; do
    test "$(git -C "$checkout_path" show --no-patch --format='%H %T' HEAD)" = "$expected_commit $expected_tree"
    test "$(git -C "$checkout_path" symbolic-ref --short HEAD)" = main
    test -z "$(git -C "$checkout_path" status --porcelain)"
done
test "$(git -C "$run2_root/integration-workspace" rev-parse --is-bare-repository)" = true
printf '%s\n' 'W71879 run2 Git roots prepared; no Authority provisioning or submission performed.'
