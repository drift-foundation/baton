"""W126880 claim127026: what does SQLite do at the read-only opening boundary?

Question: is there any way, from this Python sqlite3 build, to READ a WAL
database through a non-writing connection without creating `-wal`/`-shm` --
short of `immutable=1`, which the allocation excludes?

Declared for this probe: 3s. Run from v12/python with
PYTHONPATH=.:src:tests. Its raw stdout is retained beside it.
"""
import json
import os
import sqlite3
import tempfile
import time

started = time.monotonic()
results = []


def sidecars(path):
    return sorted(one for one in os.listdir(os.path.dirname(path))
                  if one.startswith(os.path.basename(path) + "-"))


def sizes(path):
    return {one: os.path.getsize(os.path.join(os.path.dirname(path), one))
            for one in sidecars(path)}


def made(root, name, *, keep, uri):
    """One case: build a WAL store, leave `keep` sidecars, open with `uri`."""
    path = os.path.join(root, name + ".sqlite3")
    connection = sqlite3.connect(path, isolation_level=None)
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    connection.execute("INSERT INTO meta VALUES ('k', 'v')")
    connection.close()
    # The clean close checkpoints and removes both; recreate exactly `keep`.
    for one in keep:
        open(path + one, "wb").close()
    before = sidecars(path)
    answer = {"case": name, "keep": list(keep), "uri": uri,
              "before": before}
    try:
        reading = sqlite3.connect(uri.format(path=path), uri=True,
                                  isolation_level=None)
        try:
            answer["read"] = reading.execute(
                "SELECT value FROM meta").fetchone()[0]
        finally:
            reading.close()
    except sqlite3.Error as failure:
        answer["refused"] = f"{type(failure).__name__}: {failure}"
    answer["after"] = sidecars(path)
    answer["after_sizes"] = sizes(path)
    answer["created"] = sorted(set(answer["after"]) - set(before))
    return answer


with tempfile.TemporaryDirectory(prefix="w126880-diagnosis-") as root:
    for keep in ((), ("-wal",), ("-shm",), ("-wal", "-shm")):
        results.append(made(root, "ro" + "".join(keep).replace("-", "_"),
                            keep=keep, uri="file:{path}?mode=ro"))
    for keep in ((), ("-wal", "-shm")):
        results.append(made(root, "nolock" + "".join(keep).replace("-", "_"),
                            keep=keep, uri="file:{path}?mode=ro&nolock=1"))

    # AND THE CASE THAT WORKS TODAY: a writer is attached throughout.
    path = os.path.join(root, "held.sqlite3")
    writer = sqlite3.connect(path, isolation_level=None)
    writer.execute("PRAGMA journal_mode = WAL")
    writer.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    writer.execute("INSERT INTO meta VALUES ('k', 'v')")
    before = sidecars(path)
    reading = sqlite3.connect(f"file:{path}?mode=ro", uri=True,
                              isolation_level=None)
    read = reading.execute("SELECT value FROM meta").fetchone()[0]
    reading.close()
    after = sidecars(path)
    writer.close()
    results.append({"case": "writer-attached", "before": before,
                    "read": read, "after": after,
                    "created": sorted(set(after) - set(before))})

print(json.dumps({"sqlite_version": sqlite3.sqlite_version,
                  "seconds": time.monotonic() - started,
                  "results": results}, indent=2))
