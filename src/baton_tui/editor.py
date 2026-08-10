"""External editor for message bodies.

There is NO inline body editor: printable text never accumulates in a body
buffer anywhere in the console. A one-line answer goes in the quick-reply
SUBJECT line, which becomes the content through the subject-only shorthand;
anything longer comes through here, where a real editor is what people already
know how to use.

That split is what removes the merge question. A hybrid -- type inline, then
optionally continue in an editor -- has no defensible rule for which buffer
wins, and was rejected for exactly that reason.

Three things make this security-relevant rather than a convenience wrapper:
the text being edited is HOSTILE (it arrived from another participant), the
editor command is CONFIGURATION (so it is a trust boundary), and the draft
lands in a temporary file (so it is a filesystem race). Each is handled
explicitly below rather than assumed away.
"""

from __future__ import annotations

import os
import shlex
import stat
import subprocess
import tempfile

# A draft is text a human typed or a message they received. Both are bounded
# by the protocol long before they reach here; this is the backstop against an
# editor being pointed at something enormous.
MAX_DRAFT_BYTES = 4 * 1024 * 1024

# Editor resolution, in order. TUI-only on purpose: the authority config
# describes the PROTOCOL instance, and a UI preference in it would be a
# setting every agent has to carry and none of them can use.
ENV_PRECEDENCE = ("BATON_EDITOR", "VISUAL", "EDITOR")
DEFAULT_EDITOR = "vim"

# Our own default invocation, hardened. `-n` skips the swap file (the draft is
# already a temp file and a stray .swp beside it is confusing), and
# `set nomodeline` is the one that matters: a modeline is a line INSIDE the
# text that configures the editor, and the text here came from someone else.
_VIM_HARDENING = ("-n", "--cmd", "set nomodeline")
_VIM_NAMES = ("vim", "vi", "nvim", "gvim", "vim.basic", "vim.tiny")


def resolve_editor(override: str | None = None,
                   env: dict | None = None) -> list[str]:
    """The editor argv, WITHOUT the file argument.

    Precedence: `--editor`, then BATON_EDITOR, VISUAL, EDITOR, then `vim`.
    Parsed with `shlex`, never a shell: a configured editor is allowed to have
    arguments, and is not allowed to have a pipeline, a redirect, a
    substitution or a second command."""
    env = os.environ if env is None else env
    raw = override
    if not raw:
        for name in ENV_PRECEDENCE:
            value = env.get(name)
            if value and value.strip():
                raw = value
                break
    raw = (raw or DEFAULT_EDITOR).strip()
    argv = shlex.split(raw)
    if not argv:
        argv = [DEFAULT_EDITOR]
    if os.path.basename(argv[0]) in _VIM_NAMES and len(argv) == 1:
        # OUR default, so we get to harden it. A user who supplied their own
        # vim invocation gets exactly what they asked for -- that is their
        # configuration boundary, and second-guessing it would be worse.
        argv = [argv[0], *_VIM_HARDENING]
    return argv


def _supports_double_dash(argv: list[str]) -> bool:
    """`--` only where we KNOW it means end-of-options. Appending it to an
    arbitrary configured command could pass a literal argument to something
    that does not treat it that way."""
    return os.path.basename(argv[0]) in _VIM_NAMES


def edit_text(text: str, *, argv: list[str], runner=None,
              tmpdir: str | None = None) -> tuple[str | None, str]:
    """Edit `text` externally. Returns `(new_text | None, message)`.

    None means NOTHING CHANGED, for every failure: a missing editor, a nonzero
    exit, a signal, an unreadable or replaced file. The caller keeps the draft
    it already had, which is the only safe answer -- a half-imported body is
    worse than no import.
    """
    runner = runner or subprocess.call
    handle, path = tempfile.mkstemp(prefix="baton-draft-", suffix=".md",
                                    dir=tmpdir)
    try:
        # 0600 before anything is written. mkstemp already does this; setting
        # it explicitly means the guarantee is stated where it is relied on.
        os.fchmod(handle, 0o600)
        # The baseline comes from the CREATION DESCRIPTOR, before it is
        # closed. Taking it from the pathname afterwards leaves a window in
        # which a replacement becomes the accepted baseline -- and then the
        # post-editor check agrees with the attacker's file and imports it.
        # The path must never be what decides "the file we created".
        before = os.fstat(handle)
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)

        command = list(argv)
        if _supports_double_dash(command):
            command.append("--")
        command.append(path)

        try:
            status = runner(command)
        except FileNotFoundError:
            return None, f"editor not found: {command[0]}"
        except OSError as exc:
            return None, f"editor could not run: {exc}"
        if status is None:
            status = 0
        if status < 0:
            return None, f"editor was killed by signal {-status}; draft unchanged"
        if status != 0:
            return None, f"editor exited {status}; draft unchanged"

        # OPEN ONCE, then verify THAT DESCRIPTOR and read from it.
        #
        # Checking the path and then opening it is two lookups of the same
        # name at two different instants, and the name can be replaced in
        # between: the check passes on the file we created and the read gets
        # whatever took its place. Everything below is decided about one
        # descriptor, so there is no second lookup to race.
        #
        # O_NOFOLLOW refuses a symlink at open time rather than after the
        # fact; where the platform lacks it the fstat checks still catch the
        # swap, because a replacement cannot share the original's inode.
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags)
        except OSError as exc:
            return None, f"draft file could not be reopened: {exc}"
        try:
            after = os.fstat(fd)
            if not stat.S_ISREG(after.st_mode):
                return None, "draft file is no longer a regular file; nothing imported"
            if (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino):
                # Editors that write-and-rename are common, so this is not
                # automatically an attack -- but we cannot tell the two apart,
                # and refusing costs the human one retry while accepting could
                # import a file we never wrote.
                return None, "draft file was replaced; nothing imported"
            if after.st_size > MAX_DRAFT_BYTES:
                return None, (f"draft is larger than {MAX_DRAFT_BYTES} bytes; "
                              f"nothing imported")
            with os.fdopen(fd, "r", encoding="utf-8", newline="") as fh:
                fd = None                     # fdopen owns it now
                return fh.read(), "draft imported — Enter reviews the send"
        except (OSError, UnicodeDecodeError) as exc:
            return None, f"draft could not be read back: {exc}"
        finally:
            if fd is not None:
                os.close(fd)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def quote(text: str, author: str | None, when: str | None) -> str:
    """A conventional, EDITABLE quote of the original.

    Every line prefixed, attribution above it, and the cursor meant to sit at
    the top. The copy is the author's to cut down; the authority's original is
    immutable and is never what this writes to."""
    lines = (text or "").splitlines() or [""]
    body = "\n".join(f"> {line}" if line else ">" for line in lines)
    who = author or "someone"
    stamp = f"On {when}, {who} wrote:" if when else f"{who} wrote:"
    return f"\n\n{stamp}\n{body}\n"
