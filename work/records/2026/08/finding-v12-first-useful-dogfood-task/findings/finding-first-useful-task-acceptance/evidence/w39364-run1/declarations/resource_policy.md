# W39364 run 1 — resource policy

The container is `--read-only` with `/tmp` and `/dev/shm` as small `noexec,
nosuid,nodev` tmpfs mounts, exactly as `oci.RESTRICTIONS` composes them. No
resource grant is added for this attempt: the workload is a Python unit-test
harness and a provider turn, and neither was measured to need one.

The conversation is bounded by `dogfood_operator.CONVERSATION_SECONDS`; the
worker's own verification is bounded inside the container. A run that exceeds
either bound is an unresolved attempt, not a longer one.
