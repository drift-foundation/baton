# Why the worker said `verification-failed` and the independent rerun says OK

Attempt `attempt-w51487-run4`. Measured after the run, credential-free.

## The discrepancy

The worker's retained account says the task's own command ended 1:

    "disposition": "verification-failed",
    "verification": {"argv": ["python3", "v12/spike/ping-pong/test_harness.py"],
                     "status": 1},
    "why": "the task's own command ended 1"

The operator's independent rerun of the same command over the same retained
candidate says 0, and so does mine:

    $ cd <custody>/proposal/candidate
    $ python3 v12/spike/ping-pong/test_harness.py
    Ran 30 tests in 0.118s
    OK

Both are true. They are different environments, and the frozen harness is not
indifferent to which one it runs in.

## What actually fails, and where

Running the CANDIDATE inside the worker image, as uid 65532, read-only root,
no credential mounted, no network:

    Ran 30 tests -- FAILED (failures=2)
      AnAncestorDecidesReadabilityToo
        .test_a_readable_file_under_an_unreachable_directory_is_not_usable
        .test_a_traversable_root_whose_entries_are_readable_IS_ready

Neither is a new test. All four of the candidate's new cases pass there.

## The control that settles it

The same command over the UNMODIFIED frozen source, same image, same posture:

    Ran 26 tests -- FAILED (failures=2)
      the same two AnAncestorDecidesReadabilityToo cases

So the frozen harness ALREADY ends 1 inside the worker, before this task's
candidate exists. The exact commands were:

    docker run --rm --user 65532:65532 --network none --read-only \
      --tmpfs /tmp:rw,size=64m \
      --mount type=bind,source=<TREE>,target=/candidate,readonly \
      --workdir /candidate --entrypoint python3 \
      sha256:b471399a7dcb8300795fe884c471b817ec1d61644130d66ec12fbd4fef76c003 \
      v12/spike/ping-pong/test_harness.py

with `<TREE>` the retained candidate and then the staged frozen source.

## What that means

`disposition: verification-failed` was unreachable-by-any-candidate for this
task inside this worker: the verification command the task froze cannot pass
there whatever the provider writes. The two failing cases assert that a `0o700`
directory makes a file unreadable, which is only true for a process that is not
its owner; inside the container the tree is owned by the running uid, so
`_readable_by_container` answers True and both assertions invert.

That is a property of the frozen harness and of how the worker runs it. It is
not a defect in this candidate, and it is not something the provider could have
avoided. It is recorded here rather than absorbed into the disposition, because
the worker's own verdict and the acceptance's verdict disagree and a reader
needs to know which question each of them answered.

## What was NOT measured

The worker's own stdout for that run is deliberately unpublished -- it is code
from a tree the provider edited, running with the attempt's credential mount
readable. Nothing here read it, and nothing here read the credential. The two
container runs above are reproductions with no credential mounted at all, which
is why their output can be quoted.
