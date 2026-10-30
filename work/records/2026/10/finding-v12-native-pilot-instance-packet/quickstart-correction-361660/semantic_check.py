"""Deterministic SEMANTIC check over an operator quickstart candidate.

W325959, claim361660. Answers `review-2026-10-24T03-10-08Z.md`: "Deterministic
semantic verification must reject this retained stale proposal and plausible
wrong instance/Job/base or false-command-absence variants, and accept the
corrected candidate. Judge meaning and cited provenance, not only matching
tokens."

WHY THE TASK'S OWN CHECK WAS NOT ENOUGH, and what this adds. The deployed
Job verified four headings, a byte floor and three markers. A document about
another deployment passes all four. This file runs that same structural check
FIRST and reports that it passes on the stale candidate too -- the structural
result is kept and labelled insufficient rather than replaced.

WHAT THIS JUDGES. Every current fact is read from the INSTALLED deployment
(`deployment.json`, `authority-identity.json`, the submission) at run time,
not written here, so a check cannot agree with a document by sharing its
mistake. Claims about the build's command surface are held against the
installed command's own parser output, captured once into
`evidence/CLI-READBACK.json` by read-only `--help` calls and replayed here.

THE OFF-INSTANCE RULE is the part that is about meaning. An identifier
belonging to another deployment or another revision is not forbidden -- the
corrected candidate cites instance 1's records deliberately -- but the unit
of text carrying it must ALSO mark it historical. A bare `quickstart-a` in an
operator command line fails; "Earlier pilot records describe instance 1 at
source 14e52d80..." passes. That is the difference between a citation and a
false current-tense claim, and it is checked per sentence, per table row and
per list item rather than per document.

NOTHING HERE EXECUTES ANYTHING. No store is opened, no engine, provider,
submission, start, stop or fresh attempt is reached, and no file outside this
packet is written.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import time

PACKET = pathlib.Path(__file__).resolve().parent
DEST = pathlib.Path(
    "/home/sl/baton-instances/native-coordination-pilot-w321608-4")
RETAINED_LINE = ("line-c9eea20bf942cc00a1f2ebfd31d60201da5dfb4c203a5f84cb547b"
                 "3c92cd296c")
RETAINED_ATTEMPT = ("attempt-7ac4a88986068973ddd30e2275d0daf26b1d18c9d6dda26c"
                    "ccc1ab0bf3b933fe")
RETAINED_PATCH = (DEST / "state" / "workspaces" / ".baton-review-lines"
                  / RETAINED_LINE / "custody" / RETAINED_ATTEMPT / "proposal"
                  / "change.patch")
RETAINED_PATCH_DIGEST = ("9468ec71a9a1e693e2d7718b1584ec60f82c9ffbda0ca9dc504"
                         "c9e3887e1bdfd")

# The off-instance identifiers, and the vocabulary that makes naming one a
# CITATION instead of a claim. Deliberately small and literal.
HISTORICAL = ("historical", "instance 1", "earlier", "do not apply",
              "not apply here", "superseded", "at that revision")
OFF_INSTANCE = {
    "native-coordination-pilot-w321608-1": "instance 1's destination",
    "native-coordination-pilot-w321608-2": "instance 2's destination",
    "native-coordination-pilot-w321608-3": "instance 3's destination",
    "quickstart-a": "instance 1's Job",
    "quickstart-b": "an earlier pilot Job",
    "quickstart-c": "instance 3's failed Job",
    "14e52d80679de5e844f72324df632da5e01cf393": "instance 1's source",
    "5a8fa4b4": "instance 3's authority prefix",
}

# Claims of absence that are FALSE of this build, as `baton-v12-stack --help`
# and each subcommand's own parser show.
ABSENCE = [
    (r"attempt-diagnostics[^.]{0,120}?(are|is) not in this build",
     "attempt-diagnostics is in this build"),
    (r"fresh-attempt[^.]{0,120}?(are|is) not in this build",
     "manager fresh-attempt is in this build"),
    (r"(are|is) not in this build[^.]{0,160}?attempt-diagnostics",
     "attempt-diagnostics is in this build"),
    (r"(attempt-diagnostics|fresh-attempt)[^.]{0,120}?"
     r"(absent from|not available in|missing from) this build",
     "both verbs are in this build"),
]

# Telling an operator to repeat a Job that COMPLETED. The boundary sentence
# the corrected candidate carries is the opposite of this.
RETRY_PRESSURE = [
    r"re-?run (the|this) completed",
    r"retry (the|this) completed",
    r"completed [a-z-]* ?(job|stage)[^.]{0,60}(must|should) be (re-?run|retried)",
    r"fresh-attempt[^.]{0,80}(a|the) completed (job|stage)",
]

CHECKS = []


def ok(what, answer, **extra):
    CHECKS.append(dict({"check": what, "outcome": bool(answer)}, **extra))
    return bool(answer)


def units(text):
    """Sentences, table rows and list items -- the units a claim lives in."""
    found = []
    for block in re.split(r"\n\s*\n", text):
        lines = [one for one in block.splitlines() if one.strip()]
        if not lines:
            continue
        if all(one.lstrip().startswith("|") for one in lines):
            found += lines                               # a table row each
            continue
        if any(re.match(r"\s*[*-] ", one) for one in lines):
            item = ""
            for one in lines:
                if re.match(r"\s*[*-] ", one):
                    if item:
                        found.append(item)
                    item = one.strip()
                else:
                    item += " " + one.strip()
            found.append(item)
            continue
        joined = " ".join(one.strip() for one in lines)
        if lines[0].startswith("    "):                  # an indented block
            found.append(joined)
            continue
        found += [one for one in re.split(r"(?<=[.;:])\s+", joined) if one]
    return found


# -- the facts, read from the installed deployment -------------------------

def current_facts():
    deployment = json.loads((DEST / "deployment.json").read_text())
    identity = json.loads((DEST / "authority-identity.json").read_text())
    binding = deployment["job_bindings"][0]
    submission = json.loads(
        (DEST / "generated" / "submission.json").read_text())
    job = submission["jobs"][0]
    return {
        "destination": str(DEST),
        "authority_uuid": identity["authority_uuid"],
        "work": deployment["job_work_id"],
        "job": binding["job_id"],
        "base": binding["line_declared_base"],
        "canonical_target": binding["canonical_target_id"],
        "terminal_policy": job["terminal_policy"],
        "provider_turn_seconds":
            job["execution_limits"]["provider_turn_seconds"],
        "verification_command_seconds":
            job["execution_limits"]["verification_command_seconds"],
        "pool_generation": deployment["pool_generation"],
        "receipts": deployment["receipt_participants"],
        "retention": deployment["retention_disposition"],
        "integrator":
            deployment["integration_profile"]["integrator_participant"],
        "stage_participants": sorted(
            {one["role"]: one["worker_id"] for one in deployment["workers"]}),
        "launch_logs": str(DEST / "state" / "launch" / "logs"),
    }


def readback():
    return json.loads((PACKET / "evidence" / "CLI-READBACK.json").read_text())


# -- the structural check the deployed Job actually ran --------------------

STRUCTURAL = (
    "import io,os,sys\np='v12/QUICKSTART.md'\n"
    "if not os.path.isfile(p): sys.exit('no '+p)\n"
    "t=io.open(p,encoding='utf-8').read()\n"
    "need=['## Supported commands','## Execution is not acceptance',"
    "'## Reading a failed attempt','## Cancelling or holding safely']\n"
    "miss=[h for h in need if h not in t]\n"
    "if miss: sys.exit('missing sections: '+', '.join(miss))\n"
    "if len(t)<1200: sys.exit('quickstart is shorter than its own contract')\n"
    "bad=[w for w in ['TODO','TBD','FIXME'] if w in t]\n"
    "if bad: sys.exit('unresolved markers: '+', '.join(bad))\n"
    "print('quickstart structure ok: %d bytes, %d sections'%(len(t),"
    "len(need)))\n")


def structural(text):
    """The deployed task's OWN verification command, run verbatim."""
    home = tempfile.mkdtemp(prefix="w325959-structural-")
    where = pathlib.Path(home, "v12")
    where.mkdir()
    (where / "QUICKSTART.md").write_text(text, encoding="utf-8")
    ran = subprocess.run([sys.executable, "-c", STRUCTURAL], cwd=home,
                         capture_output=True, text=True)
    return {"status": ran.returncode,
            "said": (ran.stdout or ran.stderr).strip()}


# -- the semantic judgement -------------------------------------------------

def judge(text, facts, surface, *, root=None):
    """Every reason this document is not about this deployment."""
    root = pathlib.Path(root or PACKET.parents[5])
    said = []
    spans = units(text)
    low = text.lower()

    # 1. THE CURRENT IDENTIFIERS ARE PRESENT, as current facts.
    for name, value in (("destination", facts["destination"]),
                        ("Job", facts["job"]),
                        ("Work", facts["work"]),
                        ("authority uuid", facts["authority_uuid"]),
                        ("declared base", facts["base"])):
        if value not in text:
            said.append("the current " + name + " " + value + " is never named")

    # 2. AN OFF-INSTANCE IDENTIFIER MUST BE MARKED HISTORICAL WHERE IT APPEARS.
    for token, whose in OFF_INSTANCE.items():
        if token == facts["job"] or token in facts["destination"]:
            continue
        for span in spans:
            if token not in span:
                continue
            if not any(mark in span.lower() for mark in HISTORICAL):
                said.append(
                    "names " + whose + " (" + token + ") as a current fact: "
                    + span.strip()[:150])

    # 3. NO FALSE CLAIM THAT A VERB THIS BUILD CARRIES IS ABSENT.
    for pattern, why in ABSENCE:
        found = re.search(pattern, low, re.S)
        if found:
            said.append("claims a verb is absent when " + why + ": "
                        + found.group(0)[:120])

    # 4. THE VERBS THIS BUILD CARRIES ARE DOCUMENTED, with real operands.
    for verb in surface["subcommands"]:
        if verb in ("bootstrap", "identity", "publish"):
            continue                                     # not operator loop
        if verb not in text:
            said.append("the installed subcommand " + verb
                        + " is never mentioned")
    if "attempt-diagnostics $DEST/state/status.json" not in text:
        said.append("attempt-diagnostics is not shown with its ONE positional "
                    "status document, which is its whole operand surface")
    if "--prior-job" not in text:
        said.append("fresh-attempt is not shown with --prior-job")

    # 5. THE LIMITS, THE POLICY AND THE GATE GENERATION.
    if str(facts["provider_turn_seconds"]) not in text \
            or str(facts["verification_command_seconds"]) not in text:
        said.append("the execution limits "
                    + str(facts["provider_turn_seconds"]) + "/"
                    + str(facts["verification_command_seconds"])
                    + " are not both stated")
    if facts["terminal_policy"] not in text:
        said.append("the terminal policy " + facts["terminal_policy"]
                    + " is not stated")
    gate = "runtime-quiescence:" + str(facts["pool_generation"])
    if gate not in text:
        said.append("the quiescence gate for this deployment, " + gate
                    + ", is not named")

    # 6. THE CONFIGURED ACTORS, and no invented one.
    for role, who in facts["receipts"].items():
        if who not in text:
            said.append("the configured " + role + " actor " + who
                        + " is not named")
    for invented in re.findall(r"baton\.[a-z0-9-]+", text):
        if invented in json.dumps(facts) or invented in surface["participants"]:
            continue
        for span in spans:
            if invented in span and "not configured" not in span.lower():
                said.append("names the participant " + invented
                            + ", which is not configured in this deployment "
                              "and is not marked as unconfigured")
                break

    # 7. NO PRESSURE TO REPEAT A JOB THAT COMPLETED.
    for pattern in RETRY_PRESSURE:
        found = re.search(pattern, low, re.S)
        if found:
            said.append("tells an operator to repeat completed work: "
                        + found.group(0)[:120])

    # 8. EVERY CITED REPOSITORY LOCATOR RESOLVES.
    for cited in sorted(set(re.findall(r"baton:([A-Za-z0-9_./-]+)", text))
                        | set(re.findall(r"`(v12/[A-Za-z0-9_./-]+)`", text))):
        if not (root / cited).exists():
            said.append("cites " + cited + ", which does not exist")

    # 9. EVERY $DEST PATH IT NAMES IS ONE THIS DEPLOYMENT HAS.
    for path in sorted(set(re.findall(r"\$DEST(/[A-Za-z0-9_./-]+)", text))):
        if "<" in path or path.endswith("/"):
            continue
        if not (DEST / path.lstrip("/")).exists():
            said.append("names $DEST" + path + ", which this deployment "
                        "does not have")
    return said


# -- the variants, each one a plausible wrong document ----------------------

def variants(corrected, facts):
    made = [("the retained stale proposal",
             quickstart_of(RETAINED_PATCH.read_text()))]
    made.append(("wrong instance (destination 1)",
                 corrected.replace("w321608-4", "w321608-1")))
    made.append(("wrong Job (quickstart-a)",
                 corrected.replace(facts["job"], "quickstart-a")))
    made.append(("wrong base (14e52d80)",
                 corrected.replace(
                     facts["base"],
                     "14e52d80679de5e844f72324df632da5e01cf393")))
    made.append(("wrong authority and Work",
                 corrected.replace(facts["authority_uuid"],
                                   "5a8fa4b4" + "0" * 24)
                          .replace(facts["work"], "5a8fa4b4-W1")))
    made.append((
        "false command absence",
        corrected.replace(
            "A source-level entry is still not a deployed one:",
            "Subcommands added to the source after it -- "
            "`attempt-diagnostics` and `manager fresh-attempt` among them -- "
            "are not in this build. A source-level entry is still not a "
            "deployed one:")))
    made.append((
        "an invented diagnosis participant",
        corrected.replace(
            "`baton.diagnostician` — a participant **not\n"
            "configured in this deployment**, so selecting one is a "
            "coordination decision\nand not a command on this page.",
            "`baton.diagnostician`. This deployment's configured handler is\n"
            "`baton.diagnostician-pilot`, and routing the failure to it is "
            "the supported act.")))
    made.append(("limits dropped",
                 corrected.replace("**3600s of provider turn and 900s of "
                                   "verification\ncommand**",
                                   "its configured limits")))
    made.append((
        "pressure to repeat completed work",
        corrected.replace(
            "A Job\nwhose stages **completed** has nothing for it to repeat:",
            "A completed job should be retried with it whenever the "
            "candidate disappoints:")))
    return made


def quickstart_of(patch):
    """The QUICKSTART body the retained proposal adds, from its own diff."""
    body = []
    taking = False
    for line in patch.splitlines():
        if line.startswith("+++ b/v12/QUICKSTART.md"):
            taking = True
            continue
        if taking and line.startswith("diff --git"):
            break
        if taking and line.startswith("+") and not line.startswith("+++"):
            body.append(line[1:])
    return "\n".join(body) + "\n"


def main():
    started = time.monotonic()
    facts = current_facts()
    surface = readback()
    corrected = (PACKET / "QUICKSTART.md").read_text()
    stale = quickstart_of(RETAINED_PATCH.read_text())

    ok("the retained patch still hashes to the digest this packet pins",
       hashlib.sha256(RETAINED_PATCH.read_bytes()).hexdigest()
       == RETAINED_PATCH_DIGEST)
    ok("the installed deployment supplies the current facts, which are NOT "
       "written into this checker",
       facts["job"] == "quickstart-d" and facts["base"].startswith("614668e0"),
       facts={k: v for k, v in facts.items()
              if k in ("job", "work", "authority_uuid", "base",
                       "pool_generation")})

    # THE STRUCTURAL RESULT, KEPT AND LABELLED.
    on_stale = structural(stale)
    on_corrected = structural(corrected)
    ok("the deployed task's structural check PASSES on the stale candidate -- "
       "which is why structure alone is not acceptance",
       on_stale["status"] == 0, said=on_stale["said"])
    ok("and it passes on the corrected candidate too",
       on_corrected["status"] == 0, said=on_corrected["said"])

    # THE SEMANTIC JUDGEMENT.
    accepted = judge(corrected, facts, surface)
    ok("the corrected candidate is ACCEPTED by the semantic check",
       not accepted, reasons=accepted)

    rejected = judge(stale, facts, surface)
    ok("the retained stale proposal is REJECTED", bool(rejected),
       reasons=rejected)
    for want in ("native-coordination-pilot-w321608-1", "quickstart-a",
                 "14e52d80679de5e844f72324df632da5e01cf393"):
        ok("and the rejection names " + want,
           any(want in one for one in rejected))
    ok("and the rejection names the false absence claim",
       any("claims a verb is absent" in one for one in rejected))

    results = []
    for name, text in variants(corrected, facts):
        reasons = judge(text, facts, surface)
        changed = text != corrected
        ok("the variant '" + name + "' is REJECTED",
           bool(reasons) and changed,
           reasons=reasons[:4], mutated=changed)
        results.append({"variant": name, "rejected": bool(reasons),
                        "reasons": reasons})

    answer = {"claim": 361660, "packet": str(PACKET),
              "facts": facts,
              "candidate_sha256":
                  hashlib.sha256((PACKET / "QUICKSTART.md").read_bytes())
                  .hexdigest(),
              "stale_sha256": hashlib.sha256(stale.encode()).hexdigest(),
              "retained_patch_sha256": RETAINED_PATCH_DIGEST,
              "structural": {"stale": on_stale, "corrected": on_corrected,
                             "note": "the deployed Job ran exactly this and "
                                     "it passes on a document about another "
                                     "deployment"},
              "semantic": {"corrected_rejections": accepted,
                           "stale_rejections": rejected,
                           "variants": results},
              "checks": CHECKS,
              "failed": [one for one in CHECKS if not one["outcome"]],
              "seconds": time.monotonic() - started}
    print(json.dumps(answer, indent=1, sort_keys=True, default=str))
    return 1 if answer["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
