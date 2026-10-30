#!/usr/bin/env python3
"""The SELECTED guide's verification contract, and nothing about the pilot.

Review 2026-10-27T18-27-26Z [R1]: the composed task copied the pilot's
`task.json` and changed only the task id, the declared base and the
instructions -- so its `verification` argv still read `v12/QUICKSTART.md` and
checked that document's four headings. Run against this checkout it exits **0**
while `v12/TEMPLATE-JOBS.md` does not exist. An admission that succeeds under
that contract proves the PILOT's document is still there, which is a
false success for this Job.

SO THE CONTRACT IS WRITTEN FOR THE SELECTED DELIVERABLE. It runs in the
worker's own workspace, at the staged source root, and it checks:

  * the selected guide EXISTS -- a missing one is the first refusal, and the
    old quickstart satisfies nothing;
  * the sections the TASK'S OWN FORMAT ADDENDUM names, present and in order —
    and ONLY when that addendum has been selected and is carried in the
    instructions the worker reads. Unselected, no heading is checked at all;
  * the exact template version is named;
  * no TODO/TBD/FIXME survives;
  * every `baton-v12-stack ...` invocation the guide publishes PARSES against
    this checkout's own parsers -- the subcommand must be one this build
    serves and every option must be one the owning parser accepts, which is
    how a guide written against an older CLI is refused;
  * at least one `manager ... create` example exists, takes input operands
    only (no `--document`), names the exact template version and selects the
    installed source.

WHAT IT DELIBERATELY DOES NOT CLAIM. This is a MECHANICAL contract. It cannot
judge whether the guide is truthful about the source/installed distinction,
whether its monitoring prose is honest, or whether it distinguishes completion
from acceptance -- those are the parent's acceptance criteria and the
independent reviewer is their judge. Passing this command means the guide
exists, is structured as asked and documents commands this build actually
serves. It does not mean the five criteria are met.

IT REFUSES RATHER THAN DEGRADES. If the owning parsers cannot be imported, the
check exits non-zero and says so, because a contract that quietly skipped its
only semantic step would be the same false success it exists to remove.
"""

GUIDE = "v12/TEMPLATE-JOBS.md"
TEMPLATE_VERSION = "baton.v12.job-template.implementation-review/1"

# A PROPOSED FORMAT, AND NOT THE PARENT'S CRITERIA. review-2026-10-27T18-50-04Z
# is right and the previous cut was wrong: "the guide checker imposes six exact
# section headings/order beyond the parent's current prose criteria; its claim
# that the parent enumerates them is inaccurate." USEFUL-JOB.md enumerates
# TOPICS, not headings, and a differently organised guide that covers them is
# not a failure.
#
# So these headings are now a PROPOSAL, OFF BY DEFAULT. They are enforced only
# when the task itself carries `capacity.FORMAT_ADDENDUM`, which announces them
# to the worker in the instructions it reads -- which is the owner's own
# instruction (E369183): make format guidance explicitly available in the
# proposed task and subject to its selection. Unselected, the contract checks
# nothing about headings at all.
SECTIONS = (
    "## Creating the Job",
    "## What the inputs mean",
    "## Watching it without touching it",
    "## Independent review and the held result",
    "## When an attempt fails",
    "## The human disposition",
)

_BODY = r'''
import argparse, contextlib, io, os, re, shlex, sys

GUIDE = %(guide)r
TEMPLATE = %(template)r
SECTIONS = %(sections)r

def refuse(why):
    sys.exit("guide verification refused: " + why)

if not os.path.isfile(GUIDE):
    refuse("there is no " + GUIDE + "; this task delivers that guide and the "
           "pre-existing v12/QUICKSTART.md satisfies nothing here")
text = io.open(GUIDE, encoding="utf-8").read()

if SECTIONS:
    missing = [one for one in SECTIONS if one not in text]
    if missing:
        refuse("the task's own format addendum asks for these sections and "
               "they are missing: " + ", ".join(missing))
    at = [text.index(one) for one in SECTIONS]
    if at != sorted(at):
        refuse("the task's own format addendum gives these sections an "
               "order and the guide does not follow it")
if TEMPLATE not in text:
    refuse("the guide never names the exact template version " + TEMPLATE)
marks = [one for one in ("TODO", "TBD", "FIXME") if one in text]
if marks:
    refuse("unresolved markers: " + ", ".join(marks))

try:
    sys.path[:0] = ["v12/python/src", "v12/python"]
    from tools import stack_command
except Exception as failure:
    refuse("the owning parsers could not be imported from this checkout "
           "(%%s: %%s); this contract will not pass a guide whose commands it "
           "could not check" %% (type(failure).__name__, failure))

blocks = re.findall(r"```sh\n(.*?)```", text, re.S)
named = {}
for block in blocks:
    for line in block.splitlines():
        found = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", line.strip())
        if found:
            named[found.group(1)] = found.group(2).strip().strip('"')

def expanded(line):
    out = line
    for key in sorted(named, key=len, reverse=True):
        out = out.replace("${" + key + "}", named[key])
        out = out.replace("$" + key, named[key])
    return out

class Parsed(Exception):
    def __init__(self, taken):
        self.taken = taken

held = argparse.ArgumentParser.parse_args

def parsing(self, args=None, namespace=None):
    raise Parsed(held(self, args=args, namespace=namespace))

checked, created = 0, 0
argparse.ArgumentParser.parse_args = parsing
try:
    for block in blocks:
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "baton-v12-stack" not in line:
                continue
            if line.endswith("\\"):
                refuse("a documented invocation is continued across lines and "
                       "is not pasteable as published: " + line)
            whole = expanded(line)
            if "$" in whole:
                refuse("a documented invocation still carries an undefined "
                       "expansion after the guide's own assignments: " + whole)
            try:
                words = shlex.split(whole)
            except ValueError as failure:
                refuse("a documented invocation does not parse as a shell "
                       "command (%%s): %%s" %% (failure, line))
            where = [i for i, one in enumerate(words)
                     if one.endswith("baton-v12-stack")]
            words = words[where[0] + 1:]
            if not words:
                refuse("a documented invocation names no subcommand: " + line)
            verb, operands = words[0], words[1:]
            if verb not in stack_command.COMMANDS:
                refuse("the guide documents subcommand %%r, which this build "
                       "does not serve; it serves %%s"
                       %% (verb, ", ".join(sorted(stack_command.COMMANDS))))
            if verb == "manager" and "create" in operands:
                created += 1
                if "--document" in operands:
                    refuse("a documented create example supplies --document; "
                           "ordinary template creation takes input operands "
                           "only and authors no admission document")
                for want in ("--task", "--statement", "--acceptance",
                             "--work-scope", "--template", "--source"):
                    if want not in operands:
                        refuse("the documented create example omits " + want)
                if operands[operands.index("--template") + 1] != TEMPLATE:
                    refuse("the documented create example names a template "
                           "version other than " + TEMPLATE)
                if operands[operands.index("--source") + 1] != "installed":
                    refuse("the documented create example does not select the "
                           "installed source")
            if verb == "identity":
                if operands:
                    refuse("identity takes no operands; the guide gives it "
                           + " ".join(operands))
                checked += 1
                continue
            if verb == "attempt-diagnostics":
                positional = [one for one in operands
                              if not one.startswith("-")]
                if len(operands) != 1 or len(positional) != 1:
                    refuse("attempt-diagnostics takes exactly one positional "
                           "status file; the guide gives it "
                           + " ".join(operands))
                checked += 1
                continue
            said = io.StringIO()
            try:
                with contextlib.redirect_stdout(said), \
                        contextlib.redirect_stderr(said):
                    stack_command.main([verb] + operands)
            except Parsed:
                checked += 1
                continue
            except SystemExit:
                refuse("this build's own parser refuses a documented "
                       "invocation -- %%s -- with: %%s"
                       %% (line, " ".join(said.getvalue().split())[:300]))
            except Exception as failure:
                refuse("a documented invocation could not be checked against "
                       "its parser (%%s: %%s): %%s"
                       %% (type(failure).__name__, failure, line))
            refuse("a documented invocation reached no parser at all, so it "
                   "cannot be checked: " + line)
finally:
    argparse.ArgumentParser.parse_args = held

if not created:
    refuse("the guide documents no `manager ... create` example, which is the "
           "command it exists to teach")
print("guide structure ok: %%d bytes, %%s, %%d documented invocations parsed "
      "against this build, %%d create examples. MECHANICAL ONLY -- the five "
      "acceptance criteria are the independent reviewer's judgment, not this "
      "command's."
      %% (len(text),
         ("%%d ordered sections, from the task's own format addendum"
          %% len(SECTIONS)) if SECTIONS else
         "no section format was selected, so none was checked",
         checked, created))
'''


def script(sections=()):
    """The verification body. An empty `sections` means NO format gate."""
    return _BODY % {"guide": GUIDE, "template": TEMPLATE_VERSION,
                    "sections": tuple(sections)}


# What the contract checks when no format has been selected.
SCRIPT = script()


def verification(sections=()):
    """The task document's `verification` argv, as the workload runs it.

    Called with no operand the format gate is ABSENT: the guide may be
    organised however its author thinks best, and a differently organised
    guide that covers the parent's topics passes. `capacity.installed_task`
    passes `SECTIONS` only when the proposed format addendum is selected AND
    carried in the task's own instructions — so the worker is always told the
    rule that will judge it, which is the owner's instruction at E369183.
    """
    return ["python3", "-c", script(sections)]
