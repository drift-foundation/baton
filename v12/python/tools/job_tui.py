"""W386308 -- the read-only terminal interface for watching v12 Jobs, first slice.

ONE PROGRAM, TWO SCREENS. A compact list of the Jobs in one instance's
published snapshot and, for a selected Job, its phases. It refreshes in place,
keeps the selection, says when what it shows is stale or unreadable, and exits
without touching execution.

IT ADDS NO SOURCE OF TRUTH AND NO WORDS (DESIGN OBS-1, OBS-2). The only input is
the status file `monitor` reads. The bounded read, the last-good retention and
the DISCONNECTED state are `job_viewer.JobViewer`'s; every headline, reason,
position and fact is the string `job_observation.job_view` returns. Nothing is
re-derived here, and a value the read model gives as `unknown` is shown as
`unknown`. No store, engine, network, child process, log or cache file.

THE TERMINAL IS THE THIN PART. `settle`, `step` and `frame` are pure: a state
value, a key name and a snapshot go in; a state value and text lines come out.
`Session` joins them to the viewer. `run` is the only code that touches
`curses`, and all it does is read keys, call those and paint.

SELECTION IS AN IDENTITY, NEVER A ROW NUMBER: a `job_id` in the list and a
`stage_id` in the detail. A selected Job or phase that is not in the current
snapshot is shown as one line saying so, and stays selected until the operator
moves; old content is never shown as current.
"""
import argparse
import dataclasses
import os
import signal
import sys
import time

from tools import job_observation, job_viewer

__all__ = ["MIN_ROWS", "MIN_COLUMNS", "INTERVAL_SECONDS", "DECISION_NEEDED",
           "ABSENT", "State", "View", "Frame", "Session", "view_of", "settle",
           "step", "frame", "key_name", "main"]

# Below this the two screens cannot say anything useful; the program says so
# on one line and redraws when the terminal grows.
MIN_ROWS = 8
MIN_COLUMNS = 60

# `monitor`'s own default cadence (`tools.stack`): one read per interval.
INTERVAL_SECONDS = 5.0

# The one headline `n` looks for, as the read model spells it.
DECISION_NEEDED = "DECISION NEEDED"
ABSENT = " — not in the current snapshot"

LIST, DETAIL = "list", "detail"

LIST_KEYS = " ↑↓ select   Enter open   n next needing a decision   r read now   q quit"
DETAIL_KEYS = " ↑↓ phase   Esc back   r read now   q quit"
# When the selected phase has more lines than the screen: ↑↓ move through its
# lines first and reach the neighbouring phase only at its first or last line.
SCROLL_KEYS = " ↑↓ lines (%d above, %d below)   Esc back   r read   q quit"
ABSENT_KEYS = " Esc back   r read now   q quit"


@dataclasses.dataclass(frozen=True)
class State:
    """Everything the two screens remember between keys and refreshes."""

    screen: str = LIST
    job_id: object = None       # the selected Job's identity, or None before any
    job_at: int = 0             # where it last sat, so a vanished one keeps its place
    job_top: int = 0            # first body line shown on the list
    stage_id: object = None     # the selected phase's identity on the detail screen
    stage_at: int = 0
    stage_top: int = 0
    stage_line: int = 0         # lines of the selected phase scrolled past, when it is taller than the screen
    quit: bool = False


@dataclasses.dataclass(frozen=True)
class View:
    """The read model's answer for one snapshot: Jobs in the snapshot's own order."""

    jobs: tuple = ()            # ((job_id, job_view dict, job document), ...)

    def ids(self):
        return [one[0] for one in self.jobs]

    def job(self, job_id):
        for one in self.jobs:
            if one[0] == job_id:
                return one
        return None

    def stages(self, job_id):
        held = self.job(job_id)
        return [] if held is None else [phase["stage_id"] for phase in held[1]["phases"]]


@dataclasses.dataclass(frozen=True)
class Frame:
    lines: tuple                # exactly `rows` lines, each at most `columns` wide
    selected: object            # index into `lines` of the selected row, or None
    state: State                # the state with its scroll offset as painted


def view_of(snapshot):
    """Every word comes from `job_view`; this only pairs it with the Job's identity."""
    jobs = []
    for job in snapshot.jobs():
        if not isinstance(job, dict):
            continue
        jobs.append((job.get("job_id"), job_observation.job_view(snapshot.document, job), job))
    return View(tuple(jobs))


def _entries(present, selected, at):
    """The rows of one screen: the present identities, plus the selected one
    where it last sat when the snapshot no longer has it."""
    rows = list(present)
    if selected is not None and selected not in rows:
        rows.insert(max(0, min(at, len(rows))), selected)
    return rows


def settle(state, view):
    """After a refresh: the same identities stay selected, wherever they now sit."""
    ids = view.ids()
    job_id, job_at = state.job_id, state.job_at
    if job_id is None and ids:
        job_id = ids[0]
    if job_id in ids:
        job_at = ids.index(job_id)
    stage_id, stage_at = state.stage_id, state.stage_at
    if state.screen == DETAIL:
        stages = view.stages(job_id)
        if stage_id is None and stages:
            stage_id = stages[0]
        if stage_id in stages:
            stage_at = stages.index(stage_id)
    stage_line = state.stage_line if stage_id == state.stage_id and stage_id in view.stages(job_id) else 0
    return dataclasses.replace(state, job_id=job_id, job_at=job_at, stage_id=stage_id,
                               stage_at=stage_at, stage_line=stage_line)


def _moved(present, selected, at, key, page):
    """The identity `key` moves to. Stops at the first and last row; a selected
    identity that vanished gives way to a neighbour that is really there."""
    rows = _entries(present, selected, at)
    if not rows:
        return selected, at
    here = rows.index(selected) if selected in rows else 0
    there = {"up": here - 1, "down": here + 1, "pgup": here - page,
             "pgdn": here + page, "home": 0, "end": len(rows) - 1}[key]
    there = max(0, min(there, len(rows) - 1))
    if rows[there] not in present and present:
        # Only the vanished row itself can be absent, and it was selected:
        # the nearest row that exists takes its place.
        beside = [index for index in range(len(rows)) if rows[index] in present]
        there = min(beside, key=lambda index: (abs(index - there), index))
    chosen = rows[there]
    return chosen, (present.index(chosen) if chosen in present else at)


def _hidden(state, view, rows):
    """How many lines of the selected phase do not fit beneath its own first
    line on a screen of `rows`; 0 when it fits or the size is not known."""
    held = view.job(state.job_id)
    if rows is None or held is None:
        return 0
    phase = next((one for one in held[1]["phases"] if one["stage_id"] == state.stage_id), None)
    if phase is None:
        return 0
    head = 5 if held[1]["headline_reason"] else 4
    return max(0, len(_phase_block(phase, True, 1 << 20)) - (rows - head - 1))


def step(state, key, view, *, page=10, rows=None):
    """One key. Unknown keys, and keys with nowhere to go, change nothing.

    `read` is not handled here: a read is the session's act, not a movement.
    `rows` is the screen height; with it, a selected phase taller than the
    screen is moved through line by line before the selection leaves it.
    """
    state = settle(state, view)
    if key == "quit":
        return dataclasses.replace(state, quit=True)
    ids = view.ids()
    if state.screen == LIST:
        if key in ("up", "down", "pgup", "pgdn", "home", "end"):
            job_id, job_at = _moved(ids, state.job_id, state.job_at, key, max(1, page))
            return dataclasses.replace(state, job_id=job_id, job_at=job_at)
        if key == "next":
            waiting = [one[0] for one in view.jobs if one[1]["headline"] == DECISION_NEEDED]
            if not waiting:
                return state
            here = ids.index(state.job_id) if state.job_id in ids else state.job_at - 1
            after = [job_id for job_id in ids[here + 1:] if job_id in waiting]
            chosen = after[0] if after else waiting[0]      # one wrap to the top
            return dataclasses.replace(state, job_id=chosen, job_at=ids.index(chosen))
        if key == "open" and state.job_id is not None:
            return settle(dataclasses.replace(state, screen=DETAIL, stage_id=None,
                                              stage_at=0, stage_top=0), view)
        return state
    if key == "back":
        return dataclasses.replace(state, screen=LIST, stage_id=None, stage_at=0, stage_top=0)
    if key in ("up", "down", "pgup", "pgdn", "home", "end"):
        hidden = _hidden(state, view, rows)
        line = min(state.stage_line, hidden)
        # WITHIN THE SELECTED PHASE FIRST. Its identity stays selected while its
        # lines move; only at its last (or first) line does the key leave it.
        if key in ("down", "pgdn") and line < hidden:
            return dataclasses.replace(state, stage_line=min(hidden, line + (1 if key == "down" else max(1, page))))
        if key in ("up", "pgup") and line > 0:
            return dataclasses.replace(state, stage_line=max(0, line - (1 if key == "up" else max(1, page))))
        stage_id, stage_at = _moved(view.stages(state.job_id), state.stage_id,
                                    state.stage_at, key, max(1, page))
        moved = dataclasses.replace(state, stage_id=stage_id, stage_at=stage_at, stage_line=0)
        if key == "end" or (key in ("up", "pgup") and stage_id != state.stage_id):
            # Arriving from below, or by End, shows the phase's last lines.
            moved = dataclasses.replace(moved, stage_line=_hidden(moved, view, rows))
        elif key == "home" or stage_id != state.stage_id:
            moved = dataclasses.replace(moved, stage_line=0)
        else:
            moved = dataclasses.replace(moved, stage_line=line)
        return moved
    return state


def _age(seconds):
    if seconds is None:
        return "an unknown time"
    seconds = max(0, int(seconds))
    if seconds < 60:
        return str(seconds) + "s"
    if seconds < 3600:
        return "%dm%02ds" % divmod(seconds, 60)
    return "%dh%02dm" % divmod(seconds // 60, 60)


def _cut(text, columns):
    """One fact per line: a long line is cut with an ellipsis, never wrapped."""
    text = str(text).replace("\n", " ")
    return text if len(text) <= columns else text[:max(0, columns - 1)] + "…"


def banner(snapshot, now, wall_now):
    """How old this reading is, by the shared fifteen-second rule."""
    if snapshot.document is None:
        if snapshot.failure in (None, "not read yet"):
            return "not read yet"
        return "not read yet: " + str(snapshot.failure)
    observed = str(snapshot.observed_at or job_viewer.UNKNOWN)
    if not snapshot.connected:
        # The ages first: a long cause is what gets cut on a narrow terminal.
        return ("!! DISCONNECTED last read " + _age(snapshot.age_seconds(now)) + " ago; observed "
                + observed + "; " + str(snapshot.failure or "the last read failed"))
    age = snapshot.observation_age(wall_now)
    if snapshot.stale(now, wall_now=wall_now):
        return "!! STALE observed " + _age(age) + " ago; observed " + observed
    return "observed " + observed + " (" + _age(age) + " old)"


def _window(blocks, selected, top, height):
    """Lay blocks of lines out in `height` rows, keeping the selected block whole
    and on screen; the offset moves only when it has to."""
    lines, owner, first, last = [], [], None, None
    for index, block in enumerate(blocks):
        if index == selected:
            first, last = len(lines), len(lines) + len(block) - 1
        for line in block:
            lines.append(line)
            owner.append(index)
    top = max(0, min(top, max(0, len(lines) - height)))
    if first is not None:
        if first < top:
            top = first
        elif last >= top + height:
            top = max(first - max(0, height - (last - first + 1)), last - height + 1)
            top = min(top, first)
    shown = lines[top:top + height]
    return shown, (first - top if first is not None and top <= first < top + height else None), top


def _list_blocks(state, view, columns):
    blocks, selected = [], None
    present = {one[0]: one for one in view.jobs}
    for index, job_id in enumerate(_entries(view.ids(), state.job_id, state.job_at)):
        mark = "> " if job_id == state.job_id else "  "
        if job_id == state.job_id:
            selected = index
        held = present.get(job_id)
        if held is None:
            blocks.append([_cut(mark + str(job_id) + ABSENT, columns)])
            continue
        seen = held[1]
        name, headline = str(job_id), seen["labelled_headline"]
        gap = max(3, columns - len(mark) - len(name) - len(headline))
        block = [_cut(mark + name + " " * gap + headline, columns)]
        if seen["headline_reason"]:
            block.append(_cut("    " + seen["headline_reason"], columns))
        blocks.append(block)
    return blocks, selected


def _phase_label(phase, job_id):
    role = str(phase["role"])
    name = phase.get("stage_id")
    if isinstance(name, str):
        if isinstance(job_id, str) and name.startswith(job_id + "/"):
            name = name[len(job_id) + 1:]
        if name and name != "unknown" and name != role:
            return name + " · " + role
    return role


def _phase_block(phase, chosen, columns, *, label=None, label_width=15):
    mark = "> " if chosen else "  "
    block = [_cut(mark + (str(phase["role"]) if label is None else label).ljust(label_width) + " " + str(phase["row_position"]), columns)]
    if phase["reason"]:
        block.append(_cut("      " + str(phase["reason"]), columns))
    if not chosen:
        return block
    if phase["attempt_count"]:
        block.append(_cut("      attempt " + str(phase["episode"]) + " " + str(phase["attempt_id"])
                          + (" · admitted" if phase["admission"] == "admitted" else ""), columns))
    for attempt in phase.get("attempts", []):
        if "inbox_delivery" in attempt:
            block.append(_cut("      inbox delivery only; comprehension and action unknown — sequence " + str(attempt["inbox_delivery"]) + "; attempt " + str(attempt["attempt_id"]), columns))
        if "inbox_refused" in attempt:
            block.append(_cut("      inbox acknowledgement refused: " + str(attempt["inbox_refused"]) + " — fetch cursor unchanged; attempt " + str(attempt["attempt_id"]), columns))
    for fact in phase["facts"]:
        block.append(_cut("      " + str(fact), columns))
    block.append(_cut("      " + str(phase["duration"]) + " · " + str(phase["timeout"])
                      + " · activity " + str(phase["activity"])
                      + " · operation " + str(phase["operation"]), columns))
    if phase["model_attribution"]:
        block.append(_cut("      " + str(phase["model_attribution"]), columns))
    return block


def frame(state, snapshot, now, wall_now, rows, columns):
    """The whole screen as text. Pure: the same inputs paint the same lines."""
    if rows < MIN_ROWS or columns < MIN_COLUMNS:
        said = _cut("terminal too small: needs %dx%d" % (MIN_COLUMNS, MIN_ROWS), max(1, columns))
        return Frame(tuple([said] + [""] * max(0, rows - 1))[:max(1, rows)], None, state)
    view = view_of(snapshot)
    state = settle(state, view)
    said = banner(snapshot, now, wall_now)
    if state.screen == LIST:
        waiting = sum(1 for one in view.jobs if one[1]["headline"] == DECISION_NEEDED)
        count = len(view.jobs)
        head = [_cut("Baton v12 Jobs   %d Job%s · %d need%s a decision"
                     % (count, "" if count == 1 else "s", waiting, "s" if waiting == 1 else ""), columns),
                _cut(said, columns), ""]
        blocks, selected = _list_blocks(state, view, columns)
        if not blocks:
            blocks = [["  no Jobs in this snapshot" if snapshot.document is not None
                       else "  no snapshot has been read"]]
        body, at, top = _window(blocks, selected, state.job_top, rows - len(head) - 1)
        state = dataclasses.replace(state, job_top=top)
        keys = LIST_KEYS
    else:
        held = view.job(state.job_id)
        if held is None:
            head = [_cut(str(state.job_id) + ABSENT, columns), _cut(said, columns), ""]
            body, at, top, keys = [], None, 0, ABSENT_KEYS
        else:
            seen, job = held[1], held[2]
            head = [_cut(str(state.job_id) + "   " + seen["labelled_headline"], columns),
                    _cut(said, columns)]
            if seen["headline_reason"]:
                head.append(_cut("  " + seen["headline_reason"], columns))
            head.append(_cut("  " + seen["summary"] + " · Job age "
                             + job_observation.job_age(job, snapshot.observed_at), columns))
            head.append("")
            phases = {phase["stage_id"]: phase for phase in seen["phases"]}
            labels = {stage_id: _phase_label(phase, state.job_id) for stage_id, phase in phases.items()}
            named = any(labels[stage_id] != str(phase["role"]) for stage_id, phase in phases.items())
            label_width = max(15, max(map(len, labels.values()), default=0)) if named else 15
            blocks, selected = [], None
            for index, stage_id in enumerate(_entries(list(phases), state.stage_id, state.stage_at)):
                if stage_id == state.stage_id:
                    selected = index
                if stage_id in phases:
                    blocks.append(_phase_block(phases[stage_id], stage_id == state.stage_id, columns,
                                               label=labels[stage_id], label_width=label_width))
                else:
                    blocks.append([_cut("> " + str(stage_id) + ABSENT, columns)])
            if not blocks:
                blocks = [["  this Job publishes no phases"]]
            height = rows - len(head) - 1
            tall = selected is not None and state.stage_id in phases and len(blocks[selected]) > height
            if tall:
                # THE SELECTED PHASE ALONE, its first line pinned so the selection
                # stays in sight, and the rest moved beneath it line by line.
                block = blocks[selected]
                line = max(0, min(state.stage_line, len(block) - height))
                body, at, top = [block[0]] + block[1 + line:line + height], 0, state.stage_top
                keys = SCROLL_KEYS % (line, len(block) - height - line)
                state = dataclasses.replace(state, stage_line=line)
            else:
                body, at, top = _window(blocks, selected, state.stage_top, height)
                keys = DETAIL_KEYS
                state = dataclasses.replace(state, stage_line=0)
        state = dataclasses.replace(state, stage_top=top)
    lines = head + body
    lines += [""] * (rows - 1 - len(lines))
    lines.append(_cut(keys, columns))
    return Frame(tuple(lines[:rows]), (len(head) + at if at is not None else None), state)


class Session:
    """The pure parts joined to the bounded reader. Still no terminal."""

    def __init__(self, source, *, clock=time.monotonic, wall=time.time, interval=INTERVAL_SECONDS):
        self.interval = job_viewer.checked_interval(interval)
        self.viewer = job_viewer.JobViewer(source, clock=clock, wall=wall, interval=self.interval,
                                           sleeper=lambda seconds: None)
        self.clock, self.wall = clock, wall
        self.state = State()
        self.read_at = None
        self.rows = None            # the height last painted, so keys can move within a tall phase

    @property
    def snapshot(self):
        return self.viewer.snapshot

    def read(self):
        """One read of the snapshot. Never an act."""
        self.viewer.refresh()
        self.read_at = self.clock()
        self.state = settle(self.state, view_of(self.snapshot))

    def due(self):
        return self.read_at is None or self.clock() - self.read_at >= self.interval

    def key(self, name, *, page=10):
        if name == "read":
            self.read()
        elif name is not None:
            self.state = step(self.state, name, view_of(self.snapshot), page=page, rows=self.rows)
        return self.state

    def frame(self, rows, columns):
        painted = frame(self.state, self.snapshot, self.clock(), self.wall(), rows, columns)
        self.state, self.rows = painted.state, rows
        return painted


def source_from(place):
    """The status file, opened read-only and read to the viewer's own bound."""
    class PublishedBytes(bytes):
        pass

    def read():
        with open(place, "rb") as handle:
            taken = PublishedBytes(handle.read(job_viewer.MAX_SNAPSHOT_BYTES + 1))
            taken.published_at = os.fstat(handle.fileno()).st_mtime
            return taken
    return read


_NAMED = {"k": "up", "j": "down", "g": "home", "G": "end", "n": "next", "r": "read",
          "q": "quit", "\n": "open", "\r": "open", "l": "open", "h": "back",
          "\x1b": "back", "\x7f": "back", "\x08": "back", "\x03": "quit"}


def key_name(code, curses=None):
    """A terminal key code as one of this program's key names, or None."""
    if curses is not None:
        special = {curses.KEY_UP: "up", curses.KEY_DOWN: "down", curses.KEY_PPAGE: "pgup",
                   curses.KEY_NPAGE: "pgdn", curses.KEY_HOME: "home", curses.KEY_END: "end",
                   curses.KEY_ENTER: "open", curses.KEY_RIGHT: "open", curses.KEY_LEFT: "back",
                   curses.KEY_BACKSPACE: "back"}
        if code in special:
            return special[code]
    if isinstance(code, int) and 0 <= code < 256:
        return _NAMED.get(chr(code))
    return None


class _Signalled(Exception):
    def __init__(self, number):
        super().__init__(number)
        self.number = number


def run(place, *, interval=INTERVAL_SECONDS, source=None):
    """The curses loop: read keys, call the pure parts, paint. Returns the exit code."""
    import curses

    session = Session(source_from(place) if source is None else source, interval=interval)

    def signalled(number, _frame):
        raise _Signalled(number)

    previous = {number: signal.signal(number, signalled)
                for number in (signal.SIGTERM, signal.SIGHUP)}
    screen = None
    try:
        screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        screen.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        screen.timeout(200)
        shown = None
        while not session.state.quit:
            if session.due():
                session.read()
            rows, columns = screen.getmaxyx()
            # THE REAL DIMENSIONS decide the layout; a 60-column terminal is 60 columns.
            painted = session.frame(rows, columns)
            if (painted.lines, painted.selected) != shown:
                screen.erase()
                for row, line in enumerate(painted.lines):
                    try:
                        screen.addnstr(row, 0, line, columns,
                                       curses.A_REVERSE if row == painted.selected else curses.A_NORMAL)
                    except curses.error:
                        # Writing the bottom-right cell cannot advance the cursor and
                        # reports that; the character itself has been written.
                        pass
                screen.refresh()
                shown = (painted.lines, painted.selected)
            code = screen.getch()
            if code in (-1, curses.KEY_RESIZE):
                continue
            session.key(key_name(code, curses), page=max(1, rows - 6))
        return 0
    except KeyboardInterrupt:
        return 0
    except _Signalled as ended:
        return 128 + ended.number
    finally:
        # THE TERMINAL IS RESTORED ON EVERY WAY OUT, before anything is said.
        if screen is not None:
            try:
                screen.keypad(False)
                curses.nocbreak()
                curses.echo()
                curses.endwin()
            except curses.error:
                pass
        for number, handler in previous.items():
            signal.signal(number, handler)


def main(argv=None, *, stream=None, source=None):
    parser = argparse.ArgumentParser(
        prog="job_tui",
        description="Read-only terminal interface over a v12 status snapshot. "
                    "It reads the published document and performs no act; "
                    "leaving it does not affect any Job.")
    parser.add_argument("--status", required=False,
                        help="path to the published status document, as `monitor` reads it")
    parser.add_argument("--interval", type=float, default=INTERVAL_SECONDS,
                        help="seconds between reads of the snapshot")
    taken = parser.parse_args(argv)
    if taken.status is None and source is None:
        parser.error("--status is required without an instance read source")
    stream = sys.stderr if stream is None else stream
    try:
        interval = job_viewer.checked_interval(taken.interval)
    except job_viewer.ViewerRefusal as refusal:
        print("refused: " + str(refusal), file=stream)
        return 2
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print("refused: the TUI needs a terminal on standard input and output; "
              "use `monitor` for a plain-text view", file=stream)
        return 2
    try:
        if source is None:
            return run(taken.status, interval=interval)
        return run(taken.status, interval=interval, source=source)
    except Exception as failure:                    # noqa: BLE001 -- reported after the terminal is restored
        print("error: " + type(failure).__name__ + ": " + str(failure), file=stream)
        return 1


if __name__ == "__main__":                          # pragma: no cover
    sys.exit(main())
