"""SPIKE ONLY — W17110 preflight: is this machine able to run the trials?

PLAN item 1 asks for exactly this, and asks for it "without exposing secrets".
So every credential answer below is about PRESENCE, MODE and SIZE. Nothing here
opens a credential file, and nothing prints a value.

Run: python3 preflight.py
"""

import json
import os
import shutil
import subprocess
import sys

# The provider the ruling names. "such as" makes it an example rather than the
# only permissible one -- but it is the one the record nominates, so its absence
# is a fact worth stating plainly rather than quietly substituting for.
NOMINATED = "/run/baton/credentials"

# Where an operator's own Claude and Codex runtimes keep their authentication on
# this platform. Listed so the preflight can say whether a provider EXISTS to be
# nominated; naming a path is not choosing one.
KNOWN = {
    "claude": os.path.expanduser("~/.claude/.credentials.json"),
    "codex": os.path.expanduser("~/.codex/auth.json"),
}

# The uid and gid both spike images run as. A credential the container identity
# cannot READ is not a usable provider however present it is, and a bind mount
# preserves host ownership rather than translating it.
CONTAINER_UID = 65532
CONTAINER_GID = 65532

# The two trials, and therefore the two entries a directory provider has to
# carry. Each trial mounts one of them; a root that carries neither is a root
# neither trial can run from.
PROVIDERS = ("claude", "codex")

REACHABILITY = {
    "anthropic": "https://api.anthropic.com/v1/messages",
    "openai": "https://api.openai.com/v1/models",
}


def _engine():
    where = shutil.which("docker")
    if where is None:
        return {"present": False, "why": "docker is not on PATH"}
    try:
        found = subprocess.run(
            [where, "version", "--format", "{{.Server.Version}}"],
            capture_output=True, text=True, timeout=60)
    except OSError as failure:
        return {"present": False, "why": f"docker could not be run: {failure}"}
    if found.returncode != 0:
        # THE DAEMON, not the client. A CLI on PATH with no reachable daemon is
        # the case that must fail visibly rather than skip: it is what a
        # machine without Docker looks like from here.
        return {"present": False,
                "why": "the docker daemon did not answer",
                "stderr": found.stderr.strip()[:400]}
    return {"present": True, "server": found.stdout.strip(), "client": where}


def _readable_by_container(place):
    """Whether uid 65532 could READ this path, decided from its metadata.

    W17110's first review [P1]. "Present" and "usable" are different facts and
    this used to report only the first: the operator's own credential files are
    `0600` and owned by uid 1000, a bind mount preserves that ownership, and
    the container runs as 65532 -- so a mount that looks perfectly correct
    hands the runtime a file it cannot open.

    Decided from mode and ownership, and NOTHING IS OPENED. Every ancestor has
    to be traversable too: a readable file under a `0700` directory somebody
    else owns is a file this container cannot reach.
    """
    def permits(stat, owner_bit):
        """One permission bit, from the class the container identity falls in.

        `owner_bit` is the OWNER's bit; the group and other bits are three and
        six places right of it, which is what makes one expression serve read
        and execute alike.
        """
        mode = stat.st_mode
        if stat.st_uid == CONTAINER_UID:
            return bool(mode & owner_bit)
        if stat.st_gid == CONTAINER_GID:
            return bool(mode & (owner_bit >> 3))
        return bool(mode & (owner_bit >> 6))

    try:
        itself = os.stat(place)
        if not permits(itself, 0o400):
            return False
        # A DIRECTORY NEEDS ITS OWN EXECUTE BIT TOO. W17110's re-review [P1]:
        # this checked only the read bit, so a `0444` directory -- listable and
        # impossible to open anything inside -- was reported usable. `r` on a
        # directory is permission to read the NAMES; `x` is permission to reach
        # what they name, and a credential provider is used for the second.
        if os.path.isdir(place) and not permits(itself, 0o100):
            return False
        # AND EVERY ANCESTOR TRAVERSABLE, which is the `x` bit rather than `r`.
        current = os.path.dirname(os.path.realpath(place))
        while True:
            if not permits(os.stat(current), 0o100):
                return False
            parent = os.path.dirname(current)
            if parent == current:
                return True
            current = parent
    except OSError:
        return False


def _ancestors_traversable(place):
    """Whether every directory ABOVE this path can be traversed.

    A SEPARATE GATE, and separate from readability on purpose. W17110's eighth
    review [P1]: the exact-file probe answers "can this identity open THIS
    file", and a bind mount hands the container the file directly -- so a probe
    can succeed through a carrier the identity could never have walked. The
    approved layout requires both, and one cannot stand in for the other.

    `x` and not `r`: the carrier is traverse-only by design, and the pinned
    decision says so. Reading the NAMES is not something any trial needs.
    """
    try:
        current = os.path.dirname(os.path.realpath(place))
        while True:
            stat = os.stat(current)
            if stat.st_uid == CONTAINER_UID:
                ok = bool(stat.st_mode & 0o100)
            elif stat.st_gid == CONTAINER_GID:
                ok = bool(stat.st_mode & 0o010)
            else:
                ok = bool(stat.st_mode & 0o001)
            if not ok:
                return False
            parent = os.path.dirname(current)
            if parent == current:
                return True
            current = parent
    except OSError:
        return False


def _observed_readable(engine, place):
    """Whether the CONTAINER can read this path — ASKED, not modelled.

    W17110, 2026-08-27: the metadata predicate above is a MODEL, and on this
    machine it is wrong. The operator nominated a provider correctly and
    preflight refused it, because the host's uid numbering is not the
    container's:

        the host sees   /run/baton/credentials/claude  uid 65534 mode 0400
        the container sees the same file               uid 65532 mode 0400

    So a rule reasoning from host-side ownership concluded "uid 65532 cannot
    read this" about a file the container reads perfectly well. That is the
    same mistake as inventing an exit-status contract: asserting a model of
    another system instead of observing it — and this time it cost the
    operator a round.

    `test -r` DOES NOT READ THE FILE. It asks the kernel whether this identity
    could open it, which is the question, and nothing is printed or recorded.
    """
    if not os.path.exists(place):
        return {"probed": False, "why": "the path is not there to probe"}
    found = subprocess.run(
        [engine, "run", "--rm", "--user", f"{CONTAINER_UID}:{CONTAINER_GID}",
         "--network", "none",
         "--mount", f"type=bind,source={place},target=/probe,readonly=true",
         "alpine:3.20", "sh", "-c",
         "test -r /probe && echo readable || echo unreadable"],
        capture_output=True, text=True, timeout=300)
    if found.returncode != 0:
        # A PROBE THAT DID NOT RUN CONCLUDES NOTHING, which is the rule six
        # review rounds established for every other observation here.
        return {"probed": False,
                "why": "the probe container did not run",
                "status": found.returncode}
    return {"probed": True, "readable": found.stdout.strip() == "readable"}


def _described(place):
    """One credential provider, described and NEVER READ."""
    if not os.path.exists(place):
        return {"path": place, "present": False}
    stat = os.stat(place)
    return {"path": place, "present": True,
            "mode": oct(stat.st_mode & 0o777),
            "uid": stat.st_uid, "gid": stat.st_gid,
            "bytes": stat.st_size,
            "owner_only": (stat.st_mode & 0o077) == 0,
            # THE FACT THAT DECIDES USABILITY, reported beside presence rather
            # than inferred from it.
            "readable_by_container_uid": _readable_by_container(place),
            # THE OTHER GATE, reported beside it and never merged with it.
            "ancestors_traversable": _ancestors_traversable(place),
            "container_identity": f"{CONTAINER_UID}:{CONTAINER_GID}"}


def _reachable(engine):
    """Whether a CONTAINER can reach each provider, asked from inside one.

    The daemon having egress says nothing about a container: the workers this
    campaign builds run `--network none` on purpose, and a spike that assumed
    otherwise would discover it at the least useful moment.

    A 401, 403 or 405 is a REACHABILITY PROOF rather than a failure -- the
    endpoint answered. What this cannot see is 0, which is no answer at all.
    """
    probe = "; ".join(
        f'echo "{name} $(curl -s -o /dev/null -w %{{http_code}} '
        f'--max-time 10 {url} 2>/dev/null)"'
        for name, url in REACHABILITY.items())
    found = subprocess.run(
        [engine, "run", "--rm", "alpine:3.20", "sh", "-c",
         f"apk add --no-cache curl >/dev/null 2>&1; {probe}"],
        capture_output=True, text=True, timeout=300)
    answers = {}
    for line in found.stdout.strip().splitlines():
        name, _, code = line.partition(" ")
        answers[name] = code
    return answers


def per_provider_paths(report):
    """The exact paths each trial mounts, from whichever layout was nominated."""
    found = report["credential_providers"]["nominated_per_provider"]
    if found:
        return found
    root = report["credential_providers"]["nominated"]
    return {name: root for name in PROVIDERS} if root["present"] else {}


def main():
    engine = _engine()
    report = {
        "spike": "w17110-ping-pong",
        "engine": engine,
        "credential_providers": {
            # THE HOST'S VIEW, kept as DESCRIPTION and no longer the
            # decision. `readable_by_container_uid` below is what the host's
            # own numbering implies; `observed` is what the container actually
            # reports, and where they disagree the container is right.
            #
            # THE EXACT PATHS THE TRIALS MOUNT, not only the root above them.
            # A generic root cannot prove the provider-specific entry beneath
            # it is readable -- `/run/baton/credentials` being traversable says
            # nothing about `.../claude`, and an empty readable root says
            # nothing about either.
            "nominated": _described(NOMINATED),
            "nominated_per_provider": {
                name: _described(os.path.join(NOMINATED, name))
                for name in PROVIDERS}
            if os.path.isdir(NOMINATED) else {},
            "known_operator_runtimes": {
                name: _described(place) for name, place in KNOWN.items()},
        },
        "host_runtimes": {
            name: shutil.which(name) or None for name in ("claude", "codex")},
    }
    if engine["present"]:
        report["container_reachability"] = _reachable(engine["client"])
        # ASKED OF THE ENGINE, for every path a trial actually mounts.
        report["credential_providers"]["observed_readable"] = {
            name: _observed_readable(engine["client"], found["path"])
            for name, found in per_provider_paths(report).items()}

    # READINESS INCLUDES USABILITY. W17110's re-review [P1]: this reported
    # `readable_by_container_uid` and then ignored it, so a nominated provider
    # the container identity cannot open still printed READY and exited zero --
    # which is the preflight telling the operator to go ahead into the one
    # failure it was written to catch.
    nominated = report["credential_providers"]["nominated"]
    per_provider = report["credential_providers"]["nominated_per_provider"]
    observed = report["credential_providers"].get("observed_readable", {})
    # AND EVERY PATH A TRIAL WILL ACTUALLY MOUNT. W17110's third review [P1]:
    # readiness consulted only the root, so an empty but perfectly readable
    # nominated directory printed READY while both provider entries were
    # absent. A root is not a credential; what each trial mounts is.
    #
    # A FILE provider is the other permitted layout, and it is not proof for
    # both trials either -- one file cannot carry both formats -- so it is
    # ready for the provider whose entry it is and the operator names which.
    # TWO INDEPENDENT GATES, AND NO FALLBACK BETWEEN THEM.
    #
    # W17110's eighth review, [P1] twice over. The probe replaced the model as
    # the authority on FILE readability -- and I then let it override the
    # ancestor gate as well, which it does not answer: a bind mount hands the
    # container the file directly, so a probe succeeds through a carrier the
    # identity could never walk. And when a probe DID NOT RUN I fell back to
    # the very model the probe was introduced to supersede, so a failed probe
    # over a positively-modelled file still read as ready.
    #
    # "A probe that did not run concludes nothing" has to mean that. Once the
    # engine is here, an exact file is usable only when a probe RAN and said
    # so, and only through ancestors this identity can traverse.
    # `usable` IS THE FILE VERDICT AND ONLY THAT: a probe RAN and said this
    # identity can open this exact path. It deliberately does not absorb the
    # traversal gate, which is a different question about a different object --
    # folding them would leave neither visible in the report, and the whole
    # finding was that one was silently standing in for the other.
    usable = {}
    for name, found in per_provider.items():
        seen = observed.get(name, {})
        usable[name] = bool(found["present"] and seen.get("probed")
                            and seen.get("readable"))
    # ONLY OVER ENTRIES THAT ARE THERE. Traversability is a claim about
    # reaching something, and there is nothing to reach at an absent path --
    # an absent entry already fails `usable`, and calling it "untraversable"
    # would answer a question nobody asked.
    traversable = {name: bool(found.get("ancestors_traversable"))
                   for name, found in per_provider.items()
                   if found.get("present")}
    report["credential_providers"]["ancestors_traversable"] = traversable
    report["credential_providers"]["usable_per_provider"] = usable

    # PRINTED AFTER THE VERDICT IS COMPUTED, so the report carries the facts
    # readiness was decided from rather than a subset of them.
    print(json.dumps(report, indent=1))

    # READINESS IS ABOUT THE PATHS THE TRIALS MOUNT, and only those.
    #
    # A root-readability clause used to sit here as well, and it was wrong in a
    # way this machine demonstrated: `/run/baton/credentials` is `0711` --
    # traversable and deliberately not listable, which is the correct mode for
    # a credential directory -- and its entries are readable. Refusing that is
    # refusing a provider for being well made.
    #
    # `r` on a directory is permission to read the NAMES. Nothing here needs
    # the names; each trial mounts one exact path it was told. Where the
    # directory ITSELF is the nominated provider, it IS the mounted path and is
    # probed as one.
    ready = bool(engine["present"] and nominated["present"]
                 and usable and all(usable.values())
                 # THE SEPARATE CLAUSE. A bind mount hands the container the
                 # file directly, so a successful probe says nothing about a
                 # carrier the identity could never have walked -- and the
                 # approved layout requires both.
                 and all(traversable.values()))
    if not engine["present"]:
        print("\nNOT READY: no Docker daemon. The ruling says Docker absence "
              "fails visibly, and this is that failure.", file=sys.stderr)
        return 2
    if not ready:
        # NOT AN ERROR EXIT, and the distinction matters. Docker absence is a
        # failed prerequisite; a credential provider the operator has not
        # nominated is a DECISION THAT IS NOT MINE. The trials stop here and
        # say so rather than reaching for whatever authentication happens to be
        # lying around on the host.
        if not nominated["present"]:
            print(f"\nNOT READY: {NOMINATED} does not exist, and no provider "
                  f"has been nominated in its place. The operator supplies "
                  f"the credential source; this preflight will not choose "
                  f"one.", file=sys.stderr)
        else:
            blocked = sorted(name for name, ok in traversable.items()
                             if not ok)
            if blocked:
                print(f"\nNOT READY: uid {CONTAINER_UID} cannot traverse to "
                      f"{', '.join(blocked)}. A bind mount would hand the "
                      f"container the file anyway, which is exactly why this "
                      f"is checked separately: an entry reachable only because "
                      f"the engine carried it past a directory this identity "
                      f"may not enter is not a provider this identity has.",
                      file=sys.stderr)
            else:
                unusable = sorted(name for name, ok in usable.items()
                                  if not ok) or list(PROVIDERS)
                print(f"\nNOT READY: the entries the trials would actually "
                      f"mount are not usable: {', '.join(unusable)}. Each "
                      f"needs a probe that RAN and found it readable — a probe "
                      f"that did not run concludes nothing, and the host's own "
                      f"metadata cannot stand in for it.",
                      file=sys.stderr)
        unusable = [name for name, found in report["credential_providers"][
            "known_operator_runtimes"].items()
            if found["present"] and not found["readable_by_container_uid"]]
        if unusable:
            print(f"\nAND NOTE, for {', '.join(unusable)}: those files exist "
                  f"but uid {CONTAINER_UID} cannot read them. A bind mount "
                  f"preserves host ownership, so nominating one as-is would "
                  f"hand the runtime a credential it cannot open. A provider "
                  f"for these trials needs ownership or a mode that admits "
                  f"the container identity — or an explicit ruling giving the "
                  f"container a different one.", file=sys.stderr)
        return 3
    print("\nREADY", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
