# Creation-only acceptance evidence — W376955

Actual prepare_prerequisites and real local inotify/filesystem are exercised. Syscall wrappers inject the race at the selected boundary; no simulated positive creation events are used. Synthetic missing/overflow/malformed event cases prove refusal. No engine/provider/operational install or retained stores.

- Ordinary replacement after mkdir: real remove/rename of foreign0755 directory, real kernel queue; guard refuses before chmod. Foreign bytes/mode/identity preserved. Ledger value is explicitly uncertain, and cleanup refuses even to inspect it for deletion.
- Symlink replacement: existing regression now injects at descriptor-relative mkdir and asserts uncertain ledger/preserved foreign target.
- Replacement after proof: pinned handle receives permission change on original; final chain comparison refuses. Foreign new occupant stays0755 and cleanup sees different identity.
- Ancestor replacement: creation uses held parent, not replacement pathname; parent MOVE_SELF makes creation evidence uncertain and foreign parent stays empty0755.
- Component appears during discovery: missing-root selection remains authoritative; EEXIST refuses, no ownership claim.
- Nested/intermediate effects: every successful created component tracked; later open failure retains earlier proven parent plus uncertain child. Existing cleanup-order tests retained.
- Genuine open/fstat/mkdir errors: refusal retains attempted effects without invented replacement diagnosis or deletion authority. Watch establishment failure occurs before effects.
- Missing/overflow/malformed observation: fail closed, no identity adoption; unsupported observation is never a path-only fallback.
- Private/access contract: umask000 and777 cases, no global umask calls by product. O_PATH pins restrictive-mode creations; only after proof does proc-fd chmod set0700 on that object. Existing roots remain unchanged; read-only descriptor traversal refuses raced links and agrees on usable roots.
- Identity lifetime: tuple-compatible owned identity keeps an O_PATH duplicate until ledger release; deleted inode cannot be recycled into a later foreign occupant while cleanup can still consult the identity.

46 focused tests pass (focused.log/json). The broader179-test bootstrap run has84 fixture-admission failures from an explicitly selected tmpfs root /tmp, before affected disk-required cases execute; remaining95 pass. combined.log/json preserves every result. This is not aggregate-green bootstrap evidence. Full connected install/runtime copy proof remains W376956; whole=True recursive-runtime cleanup is intentionally untouched and remains that sibling's known defect.

Mechanism uses Linux inotify/O_PATH/proc-fd capabilities. Watch is established on the opened parent BEFORE mkdir, and proof consumes exactly one CREATE|ISDIR for the intended name. Metadata, replacement, watch lifecycle or overflow events invalidate provenance. Post-open stat equality alone is never creation proof. Root/admin namespace mutation is not simulated; unsupported/no-event filesystems refuse rather than assume ownership. Watch resource failures are honest refusal. Named-chain checks use held parents, and post-proof changes cannot redirect the object permission operation.

Existing test changes: adapt two race injections from absolute to dir_fd-relative mkdir; assert uncertain attempted effects rather than omitting them; target permission failure at proc-fd chmod rather than removed fchmod. Original foreign-preservation/failure coverage retained. New class adds13 cases. No prior test files beyond test_startup_prerequisites.py changed; no expectations weakened to erase the sibling runtime-copy defect.
