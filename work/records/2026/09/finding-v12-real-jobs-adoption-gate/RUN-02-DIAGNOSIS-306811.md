# Run 02 — what consumed the turn, and the bounded successor. W247941 / claim 306811

Owner reroute 306809 asks four things of the retained evidence: what consumed the turn, what remained
after the commits, how to tell useful work from unnecessary activity from provider termination
behaviour, and a concrete bounded successor recommendation. It also says plainly: **do not assume a
larger timeout is the fix.** It is not, and the evidence says why.

Everything below is read from the spent instance `/home/sl/baton-instances/two-jobs-247941-02`. No
run, no setup, no store opened, no repository mutated.

## 1. What remained after the commits — the part that matters most

Both Jobs COMMITTED their work. `head` differs from `entry_head` in both retained proposals, and each
commit changes exactly the one path its Job owns.

    job-b   docs/v12-evidence-map.md            99 lines   checker: structural PASS, exit 0
            head a3584eae696d305e995bc166d71cde0788e3ccde
    job-a   docs/v12-parallel-operator-notes.md 103 lines  checker: REFUSED -- "is 103 lines and the
            head 47413ce2630df2676d625ff0454698bc057ee1f4      contract is UNDER 100"

I ran the checker against each retained checkout to establish this rather than inferring it from the
transcripts. **job-b's document was finished and structurally correct when the provider bound cut the
turn off.** job-a's was four lines over and needed one more edit. Neither was reviewed, because no
review was ever admitted.

That is the sharpest fact available: the run did not fail to produce work. It failed to finish the
turn around work that was, in one case, already done.

## 2. What consumed the turn

From the retained native transcripts, both start at 15:00:00 and end at the bound:

    attempt-4e9c… (job-b)  13 Bash tool uses; whole-file emissions at 68s, 93s, 120s; ends 167s
    attempt-6f3d… (job-a)  10 Bash tool uses; whole-file emissions at 90s, 117s, 146s; ends 171s

THE SHAPE IS THE SAME IN BOTH. Read the context (about 18 seconds of cheap tool calls), then write the
WHOLE document, then count the lines, find it over 100, and **re-emit the whole document**. job-b went
111 → 110 → 109 → 103 → 99; job-a went 120 → 117 → 106 → 103. Each whole-document emission cost 23 to
31 seconds of model output, and there were three or four of them each. That is roughly 110 to 130
seconds of a 180-second turn spent re-emitting a 100-line file to shave a few lines off it.

### Useful work

Reading the four excerpts and the contract, verifying the digests, and composing the document.
Cheap, and it is the work the Job was asked to do. job-b even ran the checker itself at 167s and got a
pass — the Job knew it was done.

### Unnecessary activity, each one measured rather than asserted

    THE RE-EMISSION LOOP. Writing the whole file to change a few lines. This is the dominant cost and
    it is a consequence of discovering the line count only after writing.
    A 66 kB READ FOR NOTHING. job-b ran `cat context/w247941/excerpts/E1-DESIGN.md` and the harness
    answered "Output too large (65.4KB). Full output saved to /tmp/…". It then used
    `sed -n '425,465p'` anyway, which is what it needed: only HOST-5 and HOST-8 are the input, and
    both are quoted verbatim in the contract.
    `file: command not found`. Both Jobs put `file` in a verification pipeline and both got
    `Exit code 127`. It is not in the image.

### Provider termination behaviour

    disposition       `provider-failed`, `failure_reason: timeout`,
                      `why: the provider did not finish within 180s`, `verification: null`
    and yet           the change was COMMITTED: `head` != `entry_head`, `changed_paths` exactly the
                      one file. Custody captured the intended change even on a timeout
    the runtimes      both `execution_runtime: destroyed`, `cleanup: retained`, `state: absent`;
                      `outstanding_cleanup`, `unresolved_cleanup` and `uncertainty` all empty
    the streams       provider stdout `finished`; provider stderr `partial`, "the drain ended on its
                      own clock rather than at end of file"
    ONE INCONSISTENCY the same record carries `provider.seconds_bound: 3600` beside
                      "did not finish within 180s". The bound that fired was 180; 3600 is not the
                      number that applied. Reporting repair is W306614's, not this Work's -- recorded
                      here as an observation, not touched.

### What the numbers above are, exactly — qualification added at claim 307388

Review 2026-09-29T15-19-17Z is right to qualify two of my sentences, and the qualification belongs in
this document rather than only in the review:

    "110-130 SECONDS OF RE-EMISSION" IS AN INFERENCE, not a measurement of model cost. What the
    transcript gives is the interval between a tool result and the next tool use, which is WALL time
    covering model output, harness overhead and anything else in between. What is measured is that
    three or four whole-file rewrites happened per turn, at what timestamps, and that both turns
    reached the 180-second bound.
    "THE BRIEF IS WHAT TAUGHT IT" IS ALSO AN INFERENCE. The brief did not forbid editing and did not
    name a counting tool; that both Jobs independently chose write-then-count-then-rewrite is
    consistent with the brief being the cause and does not prove it.
    "FINISHED AND CORRECT" MEANS STRUCTURALLY CORRECT AND NOTHING MORE. job-b's committed document
    passes `check_useful_tasks` in its retained checkout. No review has ever run on it, so its
    CONTENT has not been judged by anybody, and a structural pass is not acceptance.
    BUDGET ADEQUACY REMAINS UNPROVED. Whether 180 seconds is enough with the corrected brief is what
    a successor run finds out; this document recommends keeping it, which is not the same as claiming
    it is sufficient.

## 3. Why a larger timeout is not the recommendation

Because the time did not go into the work. job-b produced a structurally correct 99-line document
**inside** 180 seconds while also spending ~120 of those seconds re-emitting it. Raising the bound
would buy the same loop more room rather than removing it, and it would make every future run's cost
a function of how many times the model rewrites the file. The bound is not what failed; the drafting
strategy is, and the brief is what taught it.

## 4. The bounded successor recommendation

ACCEPTED MACHINERY ONLY, and no reseeding: the seeded contract, checker and excerpts in the owner's
source are UNCHANGED, so `useful_tasks.py --prove` still exits 0 against
`/home/sl/baton-runs/two-jobs-247941-01-inputs` at `346a809b…`. What changed is the emitted brief,
which lives in the task document rather than in the seeded set.

### Done in this claim — the brief now names the cost and the cheaper path

    PLAN TO THE BOUND BEFORE YOU WRITE, with the headings as the budget.
    EDIT, DO NOT RE-EMIT. Rewriting the whole file to remove four lines costs as much as writing it.
    COUNT WITH THE CHECKER, named with this Job's own operands -- the same invocation its
    `verification` runs, already in its checkout, and it writes nothing.
    READ ONLY THE PART OF A SOURCE YOU NEED, naming E1's size and the two paragraphs that are the
    actual input.
    `file` IS NOT IN THIS IMAGE.

`test_useful_tasks` holds all of it, including that the brief names each Job's OWN checker invocation
and still never names the other Job's path.

### Recommended for the successor run, and these are the owner's to select

    KEEP 180s per provider turn and keep total 600 with 60 cleanup. The evidence says the budget is
    adequate once the loop is gone; changing both at once would leave neither measured.
    KEEP the two implementations and two reviews, one manager, and the existing source and base.
    RUN IT AS `two-jobs-247941-03`. The spent roots stay; `two-jobs-247941-02` should join
    `two-jobs-247941-01` in `CONSUMED` when the owner selects a successor, and I have added it.
    IF AN IMPLEMENTATION STILL TIMES OUT with the new brief, the next question is the CONTENT budget
    rather than the clock: a 99-line document with five required headings may simply be more than one
    180-second turn can compose carefully. That would be a contract change, and it would need a
    reseed and a fresh base -- which is why it is not being proposed now, on one run's evidence.

### What this run did and did not establish

It did not establish overlap of useful model work, isolation, attribution, completion or semantic
acceptance — no review ever ran, and a timed-out implementation is not a completed one. It DID
establish that both Jobs ran concurrently, read their frozen context, produced their own document on
their own line, committed exactly their own path, and were cleaned up with no residue and no
uncertainty. One of the two documents passes its structural check today, in the retained checkout.
