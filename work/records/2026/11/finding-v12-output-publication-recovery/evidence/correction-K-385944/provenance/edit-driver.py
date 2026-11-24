import pathlib
p = pathlib.Path("cli-in-image-driver.py"); s = p.read_text()
def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:60]); s = s.replace(old, new)
sub('''No model, no credential, no instance. The key it passes is a placeholder the scripted endpoint never reads.
Standard library only.
"""''', '''No model, no credential, no instance. The key it passes is a placeholder the scripted endpoint never reads.

WHAT THIS DRIVER MAY END IS WHAT ITS OWN TURN STARTED, AND NOTHING ELSE (review 2026-11-24T04-42-16Z C5.3).
Each run makes one random token and puts it in the environment of the ONE CLI process it starts. A process
carries that token in its own `/proc/<pid>/environ` only if it descends from that CLI, however it detached. The
survival check and the final cleanup both select by that token alone -- never by a program name, an argument or
a parent that could be someone else's. A driver that started no turn owns no process.
Standard library only.
"""''')
sub("import os\nimport socket\n", "import os\nimport secrets\nimport socket\n")
start = s.index("def survivors():"); end = s.index("def main():")
s = s[:start] + '''TOKEN_NAME = "W385695_CLI_TURN"


def owned(token):
    """Every live process whose OWN environment carries this run's token: `{pid, argv}` each.

    The token is random, made by `main` for one turn and given to nothing but the CLI it starts, so membership
    is this invocation's descendants and no other process on the host or in the container. Without a token
    -- no turn was started -- the answer is nothing.
    """
    if not token:
        return []
    want, found = f"{TOKEN_NAME}={token}".encode(), []
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == os.getpid():
            continue
        try:
            if want not in open(f"/proc/{name}/environ", "rb").read().split(b"\\0"):
                continue
            stat = open(f"/proc/{name}/stat", "rb").read()
            argv = open(f"/proc/{name}/cmdline", "rb").read().split(b"\\0")
        except OSError:
            continue                                   # gone, or not this user's: not ours to name
        if stat[stat.rindex(b")") + 2:].split()[0] == b"Z":
            continue
        found.append({"pid": int(name), "argv": [one.decode("utf-8", "replace") for one in argv if one]})
    return found


def survivors(token=None):
    """The pids this run's turn started that are still alive."""
    return [one["pid"] for one in owned(token)]


def end_owned(token, seconds=5.0):
    """Kill what this run's turn started, re-reading the token for each pid immediately before its signal."""
    deadline = time.monotonic() + seconds
    while True:
        live = survivors(token)
        if not live or time.monotonic() >= deadline:
            return live
        for pid in live:
            if pid in survivors(token):
                try:
                    os.kill(pid, 9)
                except OSError:
                    pass
        time.sleep(0.05)


''' + s[end:]
sub('''    answer = {"verdict": "fail", "why": []}
''', '''    token = secrets.token_hex(16)
    answer = {"verdict": "fail", "why": []}
''')
sub('''CLAUDE_CODE_SHELL_PREFIX=taken.supervisor, BATON_COMMAND_SECONDS''', '''CLAUDE_CODE_SHELL_PREFIX=taken.supervisor, **{TOKEN_NAME: token}, BATON_COMMAND_SECONDS''')
sub('''        answer["survivors"] = survivors()
''', '''        answer["survivors"] = owned(token)
''')
sub('''"no scripted process survived": answer["survivors"] == [],''', '''"nothing this turn started survived it": answer["survivors"] == [],''')
sub('''        stub.kill()
        stub.wait()
        for pid in survivors():
            try:
                os.kill(pid, 9)
            except OSError:
                pass
''', '''        stub.kill()                                     # this run's own `Popen`, by object
        stub.wait()
        answer["left_after_cleanup"] = end_owned(token)
        if answer["left_after_cleanup"]:
            answer["verdict"] = "fail"
            answer["why"].append("processes this turn started could not be ended")
''')
p.write_text(s)
