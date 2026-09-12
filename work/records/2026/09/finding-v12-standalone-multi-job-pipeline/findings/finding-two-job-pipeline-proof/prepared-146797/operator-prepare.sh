#!/bin/bash
# Slawomir-only fresh preparation candidate. This does not authorize a model run.
set -euo pipefail
umask 0002

run5_root=/home/sl/.local/state/baton/v12/w71879-run5
run1_source=/home/sl/.local/state/baton/v12/w71879-run1/source
target="$run5_root/target"
expected_commit=2fbb2d456638e5706218020aebfa47f0a82c8920
expected_tree=3492ba64448ab9d39bde53ee6456ce24e74ece2c

test ! -e "$run5_root"
test ! -L "$run5_root"
case " $(id -G) " in
    *' 1001 '*) ;;
    *) printf '%s\n' 'Operator must already hold workspace gid1001.' >&2; exit 1 ;;
esac
test "$(git --no-optional-locks -C "$run1_source" show --no-patch --format='%H %T' HEAD)" = "$expected_commit $expected_tree"
test "$(git --no-optional-locks -C "$run1_source" symbolic-ref --short HEAD)" = main
test -z "$(git --no-optional-locks -C "$run1_source" status --porcelain)"

mkdir -m 700 "$run5_root"
git clone --no-hardlinks --single-branch --branch main "$run1_source" "$run5_root/source"
install -d -g 1001 -m 2775 "$target"
git clone --no-hardlinks --single-branch --branch main "$run5_root/source" "$target"
git init --bare "$run5_root/integration-workspace"

# Initial preparation only: the fresh target has never held a submitted Job.
# The unchanged worker requires its own uid and exact 100644 -> 0644 modes.
chmod 0644 "$target/demo/greeting.py" "$target/demo/units.py" "$target/tests/test_greeting.py"
sudo -- chown -R --no-dereference 65532:1001 "$target"

for checkout_path in "$run5_root/source" "$target"; do
    test "$(git --no-optional-locks -c safe.directory="$target" -C "$checkout_path" show --no-patch --format='%H %T' HEAD)" = "$expected_commit $expected_tree"
    test "$(git --no-optional-locks -c safe.directory="$target" -C "$checkout_path" symbolic-ref --short HEAD)" = main
    test -z "$(git --no-optional-locks -c safe.directory="$target" -C "$checkout_path" status --porcelain)"
done
test "$(git -C "$run5_root/integration-workspace" rev-parse --is-bare-repository)" = true
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-146538/target_posture.py "$target"
printf '%s\n' 'Fresh target preparation complete; no Authority provisioning or model run performed.'
