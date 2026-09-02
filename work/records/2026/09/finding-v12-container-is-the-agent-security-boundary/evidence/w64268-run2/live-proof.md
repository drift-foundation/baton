# W64268 rebuilt-image live proof — run2

Handler: `baton.slaw`, with command execution assisted by the human-attached
`baton.prompt` context. Date: 2026-09-02.

The accepted source was the two harmless files under `evidence/live-proof-source/`.
The frozen task required the provider to add one function to `probe.py`, change
nothing else, and run this command itself:

```text
python3 -B -m unittest -v test_probe.py
```

The supervised operator launched selected image digest
`sha256:896884b237a14d2397a9851dc1692cb34bedb46a367c2544de9e7499fd9bc124`
as fresh attempt `attempt-w64268-run2`. The provider returned status 0. The
worker measured exactly one changed path, `probe.py`, and recorded status 0 for
the frozen verification. There was no approval interaction or host-side
allowlist change: the command completed inside the rebuilt container under the
adapter's `--dangerously-skip-permissions` vector.

The outer operator then independently reran the identical five-member argv
against the retained candidate. One test ran and passed, exit 0. The candidate
tree contained only `probe.py` and unchanged `test_probe.py`; `-B` left no
bytecode cache or other generated path.

The operator evidence is resolved with no unresolved endings. It records the
exact runtime positively absent, the conversation answered, the output frozen
and retained, and cleanup state absent. A separate post-run `docker ps -a`
query for the exact attempt label returned no container.

Run1 had already completed the provider and inner/outer verification without
approval. It was superseded as the acceptance proof because a preflight Python
invocation had polluted its staged source with host bytecode and the non-`-B`
worker command added its own bytecode. Run2 changes no product behavior; it
removes that evidence ambiguity and leaves the changed-path set exactly
`probe.py`.
