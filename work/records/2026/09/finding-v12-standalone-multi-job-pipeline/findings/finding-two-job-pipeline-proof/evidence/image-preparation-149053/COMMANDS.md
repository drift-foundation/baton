# Preparation verification commands — claim 149053

Final offline check: python3 -B prepared-149053/verify_offline.py from the dossier,
or its complete repository-relative path from the checkout. Both subprocess argv,
exit status and process walls are retained in verification-1/2.json with full logs.
The first failure and final successful 58-case result are preserved.

bash -n prepared-149053/operator-prepare.sh: PASS (syntax only).
git diff --check: PASS, repository root.
Python ast.parse of every new package Python file: PASS, no bytecode written.
Direct git --no-optional-locks -C /home/sl/.local/state/baton/v12/w71879-run1/source
show --no-patch --format='%H %T' HEAD and status --porcelain verified the recorded
clean original base/tree. No mutable Git command executed.

Direct docker image inspect of the base and both old immutable candidates with
metadata-only --format verified IDs, platform, user, entrypoints and shared base
layer prefix. No container creation/start/build/copy was attempted. This does not
establish new candidate IDs. Existing Docker-copy restriction from148686 remains;
operator build_images.py is the exact reviewable action for that boundary.

package_construction.py and provenance_check.py retain the construction/check
source used in this episode. They are historical evidence, not operator commands
and not retry/repair recipes. Construction precedes the separately recorded edits
and new tests; it does not reproduce the entire final candidate by itself.
