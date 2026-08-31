# W39364 run 1 — credential policy

One slot, `claude`, delivered at `/run/baton/credentials/claude` inside the
container by the manager's credential home. The operator authorized the exact
source path (M50427, verified readable at M51386); this deployment has no
home-directory or ambient fallback and `claude_agent` refuses an absent slot
rather than trying one.

The bytes are read once into the launcher's memory from the path named on the
command line. They are not a grants member, not an environment variable, and
not recorded anywhere in this record: the path is not the secret, and the
secret does not reach a durable surface. The agent never opens the slot -- it
symlinks it into a private home so a read-only root can still authenticate.
