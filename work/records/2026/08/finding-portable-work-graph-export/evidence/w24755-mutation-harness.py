"""Measure W24755's suite by removing what it claims to establish.

A guard nothing observes is not established. Each mutation breaks ONE rule the
export promises; the suite must fail. A mutation nothing catches is a promise
this Work has not earned.

`__pycache__` is dropped per write because these rewrites land inside one
filesystem timestamp tick and CPython's mtime+size invalidation misses that --
a harness without it measures the previous build.
"""

import pathlib
import shutil
import subprocess
import sys

HOME = pathlib.Path("/home/sl/src/baton")
SRC = HOME / "src" / "baton_work"
MODULE = "tests/work/test_w24755_work_graph_export.py"

MUTATIONS = [
    # -- the snapshot promise ------------------------------------------------
    ("the export is not read inside one snapshot", "projection.py",
     "	scope = _export_scope(team, status, changed_from, changed_until)\n"
     "	with _read_snapshot(store):",
     "	scope = _export_scope(team, status, changed_from, changed_until)\n"
     "	if True:"),

    ("the snapshot sequence is sampled after the read", "projection.py",
     "		snapshot_seq = store.last_seq()\n"
     "	# THE PROJECTION IS HELD TO ITS OWN OUTPUT",
     "		pass\n"
     "	snapshot_seq = store.last_seq()\n"
     "	# THE PROJECTION IS HELD TO ITS OWN OUTPUT"),

    # -- direction and typing ------------------------------------------------
    ("the dependency edge points from consumer to blocker", "projection.py",
     '''			_export_edge("dependency", edge["blocker"], edge["work"],''',
     '''			_export_edge("dependency", edge["work"], edge["blocker"],'''),

    ("the containment edge points from child to parent", "projection.py",
     '''				candidates.append(_export_edge(
					"containment", row["parent"], work_id,''',
     '''				candidates.append(_export_edge(
					"containment", work_id, row["parent"],'''),

    ("the follow-up edge points from successor to predecessor",
     "projection.py",
     '''					"follow-up", row["follow_up_of"], work_id,''',
     '''					"follow-up", work_id, row["follow_up_of"],'''),

    ("the duplicate edge points from survivor to duplicate", "projection.py",
     '''					"duplicate", work_id, row["duplicate_of"],''',
     '''					"duplicate", row["duplicate_of"], work_id,'''),

    ("a relation spells the wrong predicate", "projection.py",
     '''_RELATION_PREDICATE = {"dependency": "blocks", "containment": "contains",''',
     '''_RELATION_PREDICATE = {"dependency": "contains", "containment": "contains",'''),

    # -- the relation sequences ----------------------------------------------
    ("the duplicate relation is sequenced by creation, not closure",
     "projection.py",
     '''					"duplicate", work_id, row["duplicate_of"],
					row["closed_seq"]))''',
     '''					"duplicate", work_id, row["duplicate_of"],
					row["created_seq"]))'''),

    # -- completeness --------------------------------------------------------
    ("a whole relation family is dropped", "projection.py",
     '''			if row["follow_up_of"] is not None:''',
     '''			if False:'''),

    ("the export is capped like the other views", "projection.py",
     '''		ordered_nodes = sorted(nodes.values(),''',
     '''		nodes = dict(list(nodes.items())[:200])
		edges = [one for one in edges
		         if one["source"] in nodes and one["target"] in nodes]
		ordered_nodes = sorted(nodes.values(),'''),

    ("a closed consumer's dependency is hidden, as `links` hides it",
     "projection.py",
     '''			"SELECT work, blocker, via_obligation, created_seq FROM edges "
			"ORDER BY created_seq, blocker, work")]''',
     '''			"SELECT edges.work, edges.blocker, edges.via_obligation, "
			"edges.created_seq FROM edges JOIN work ON work.id=edges.work "
			"WHERE work.status='open' "
			"ORDER BY edges.created_seq, edges.blocker, edges.work")]'''),

    # -- scope and closure ---------------------------------------------------
    ("context endpoints are dropped, leaving dangling edges", "projection.py",
     '''		context = {edge[side] for edge in edges for side in
		           ("source", "target")} - selected''',
     '''		context = set()
		edges = [edge for edge in edges if edge["source"] in selected
		         and edge["target"] in selected]'''),

    ("context is promoted to selected", "projection.py",
     '''		nodes = {work_id: _export_node(rows[work_id],
		                              selected=work_id in selected)''',
     '''		nodes = {work_id: _export_node(rows[work_id], selected=True)'''),

    ("context expands recursively", "projection.py",
     '''		edges = [edge for edge in candidates
		         if edge["source"] in selected or edge["target"] in selected]''',
     '''		edges = list(candidates)'''),

    ("the default scope is `all` rather than `open`", "projection.py",
     '''def work_graph(store: Authority, *, team: str | None = None,
               status: str = "open", changed_from: str | None = None,''',
     '''def work_graph(store: Authority, *, team: str | None = None,
               status: str = "closed", changed_from: str | None = None,'''),

    # -- the range -----------------------------------------------------------
    ("status=all no longer demands both bounds", "projection.py",
     '	if scope["status"] == "all" and len(supplied) != 2:',
     '	if False:'),

    # The offset requirement now lives in the grammar itself, so the naive
    # spelling is refused by the regex rather than after the parse.
    ("a naive instant is accepted", "projection.py",
     r'	r"(?P<offset>[Zz]|[+-]\d{2}:\d{2})$")',
     r'	r"(?P<offset>[Zz]|[+-]\d{2}:\d{2})?$")'),

    ("an empty or reversed interval is accepted", "projection.py",
     "		if _export_ordering(since) >= _export_ordering(until):",
     "		if False:"),

    ("the range is half-open at the wrong end", "projection.py",
     "		if not (bounds[0] <= moment < bounds[1]):",
     "		if not (bounds[0] < moment <= bounds[1]):"),

    ("an unknown team is accepted", "projection.py",
     '''	if team is not None and not store.conn.execute(''',
     '''	if False and not store.conn.execute('''),

    # -- ordering / determinism ----------------------------------------------
    ("nodes come out in an unstable order", "projection.py",
     '''		ordered_nodes = sorted(nodes.values(),
		                       key=lambda one: (one["created_seq"], one["id"]))''',
     '''		ordered_nodes = list(nodes.values())[::-1]'''),

    ("edges come out in an unstable order", "projection.py",
     '''		ordered_edges = sorted(
			edges, key=lambda one: (one["relation_seq"],
			                        _RELATION_RANK[one["relation"]],
			                        one["source"], one["target"]))''',
     '''		ordered_edges = list(edges)[::-1]'''),

    # ONE owner for both attribute lists now, so one mutation covers both.
    ("attribute lists are emitted unsorted", "dot.py",
     "	return [f\"{name}={_quoted(value)}\" for name, value in "
     "sorted(pairs.items())]",
     "	return [f\"{name}={_quoted(value)}\" for name, value in "
     "pairs.items()]"),

    # -- the DOT format itself -----------------------------------------------
    ("the digraph becomes `strict`", "dot.py",
     '''	lines = ['digraph "baton_work" {']''',
     '''	lines = ['strict digraph "baton_work" {']'''),

    # The doubling of every user backslash, removed. Anchored on the call
    # alone rather than the whole line, so the quoting stays readable.
    ("the escString backslash is not protected", "dot.py",
     'value.replace("\\\\", "\\\\\\\\").replace(',
     'value.replace('),

    ("control characters pass through into the document", "dot.py",
     '''	value = _visible(value)''',
     '''	pass'''),

    ("the exact title is no longer carried", "dot.py",
     '''		"baton_title_b64": base64.b64encode(
			node["title"].encode("utf-8")).decode("ascii"),''',
     '''		"baton_title_b64": base64.b64encode(
			_visible(node["title"]).encode("utf-8")).decode("ascii"),'''),

    ("the scope range is left out of the document", "dot.py",
     '''		"baton_scope_changed_from": scope["changed_from"] or UNFILTERED,
		"baton_scope_changed_until": scope["changed_until"] or UNFILTERED,''',
     '''		"baton_scope_closure_pad": "x",'''),

    ("a null member renders as an empty string", "dot.py",
     '''	if value is None:
		return "null"''',
     '''	if value is None:
		return ""'''),

    ("the document does not end in exactly one newline", "dot.py",
     '''	return "\\n".join(lines) + "\\n"''',
     '''	return "\\n".join(lines) + "\\n\\n"'''),

    ("a missing endpoint no longer refuses", "projection.py",
     '''			if edge[side] not in nodes:''',
     '''			if False:'''),

    ("a duplicate typed edge no longer refuses", "projection.py",
     '''		if key in seen:''',
     '''		if False:'''),

    # -- the four review findings --------------------------------------------
    ("[P1] the RFC 3339 grammar is not checked", "projection.py",
     "	if not _RFC3339.match(value):", "	if False:"),

    ("[P1] a lower-case t/z spelling is not normalized before the parse",
     "projection.py",
     "	spelled = _rfc3339_upper(value)", "	spelled = value"),

    ("[P1] the renderer does not run the shared validator", "dot.py",
     "	validate_work_graph(result)", "	pass"),

    ("[P1] `selected` loses its own baton_* member again", "dot.py",
     '''	for name in GRAPH_NODE_MEMBERS:
		attributes[f"baton_{name}"] = _text(node[name])''',
     '''	for name in GRAPH_NODE_MEMBERS:
		if name == "selected":
			continue
		attributes[f"baton_{name}"] = _text(node[name])'''),

    ("[P1] the readable scope role is dropped", "dot.py",
     '''		"baton_scope": scope,''', '''		"baton_scope_pad": scope,'''),

    ("[P2] the configured team is admitted outside the snapshot",
     "projection.py",
     '''	with _read_snapshot(store):
		_export_configured_team(store, team)''',
     '''	_export_configured_team(store, team)
	with _read_snapshot(store):'''),

    ("a node named twice is accepted", "projection.py",
     '''		if node["id"] in taken:''', '''		if False:'''),

    # -- the third review's finding -------------------------------------------
    ("[P1] a closed vocabulary is not checked", "projection.py",
     "		if allowed is not None and value not in allowed:",
     "		if False:"),

    ("[P1] only the three members the review named are checked",
     "projection.py",
     '\t"origin": ORIGINS,\n\t"classification": CLASSIFICATIONS,\n'
     '\t"priority": PRIORITIES,',
     '\t"unused_origin": ORIGINS,'),

    ("[P1] a vocabulary becomes a renderer-only copy", "projection.py",
     '\t"phase": PHASES,',
     '\t"phase": ("queued", "active", "block", "parked", "review"),'),

    # -- the second review's two findings ------------------------------------
    # The canonical text built from `datetime` again, which is where the
    # truncation actually happened.
    ("[P1] the fraction is carried by datetime again, and truncates",
     "projection.py",
     '	whole = moment.astimezone(datetime.timezone.utc).isoformat(\n'
     '		timespec="seconds").replace("+00:00", "")\n'
     '	return whole + (f".{fraction}" if fraction else "") + "Z"',
     '	return moment.astimezone(datetime.timezone.utc).isoformat(\n'
     '		timespec="microseconds").replace("+00:00", "Z")'),

    ("[P1] equivalent fractions are not canonicalized", "projection.py",
     '	return (digits or "").rstrip("0")', '	return digits or ""'),

    ("[P1] canonical instants are compared as text", "projection.py",
     "		moment = _export_ordering(_export_instant(row[\"last_changed_at\"],\n"
     "		                                          \"a stored last_changed_at\"))",
     "		moment = _export_instant(row[\"last_changed_at\"],\n"
     "		                         \"a stored last_changed_at\")"),

    ("[P1] member types are not owned", "projection.py",
     "		if type(value) is not wanted:", "		if False:"),

    ("[P1] the nullable domain is ignored", "projection.py",
     "			if nullable:\n				continue", "			if True:\n				continue"),

    ("[P1] `bool` slips through as an integer", "projection.py",
     "		if type(value) is not wanted:",
     "		if not isinstance(value, wanted):"),

    # -- the fourth review's two findings -------------------------------------
    ("[P1] an open node may carry no phase", "projection.py",
     "	if not terminal and node[\"phase\"] is None:", "	if False:"),

    ("[P1] a terminal node may keep its phase", "projection.py",
     "	if terminal and node[\"phase\"] is not None:", "	if False:"),

    ("[P1] an open node may carry an outcome", "projection.py",
     "	if not terminal and node[\"outcome\"] is not None:", "	if False:"),

    ("[P1] a terminal node may carry no outcome", "projection.py",
     "	if terminal and node[\"outcome\"] is None:", "	if False:"),

    ("[P1] any relation may name obligation provenance", "projection.py",
     "	if edge[\"relation\"] != \"dependency\" and "
     "edge[\"via_obligation\"] is not None:",
     "	if False:"),

    ("[P1] the scope document is not validated", "projection.py",
     "	_export_scope_document(result[\"scope\"])", "	pass"),

    ("[P1] the counts are not derived", "projection.py",
     "	_export_counts(result[\"counts\"], result[\"nodes\"], result[\"edges\"])",
     "	pass"),

    ("[P1] the scope closure is not fixed", "projection.py",
     "	if scope[\"closure\"] != GRAPH_CLOSURE:", "	if False:"),

    ("[P1] an unknown scope member is accepted", "projection.py",
     "	unknown = sorted(set(scope) - set(GRAPH_SCOPE_MEMBERS))",
     "	unknown = []"),

    ("[P1] the projection does not validate its own output", "projection.py",
     "	validate_work_graph(answered)\n	return {**answered,",
     "	return {**answered,"),

    # -- the fifth review's finding -------------------------------------------
    ("[P1] a structured bound need not be canonical", "projection.py",
     "			if scope[name] != canonical:", "			if False:"),

    ("[P1] the canonical rule leaks into the operand path", "projection.py",
     "	since = (None if changed_from is None\n"
     "	         else _export_instant(changed_from, \"changed-from\"))",
     "	since = changed_from"),

    # -- the CLI surface -----------------------------------------------------
    ("DOT is emitted for every format, not only when asked", "cli.py",
     '''			if args.command == "work-graph" and args.format == "dot":''',
     '''			if args.command == "work-graph":'''),

    ("a refusal writes a partial document first", "cli.py",
     '''				document = dot_render.render_work_graph_dot(envelope)
				sys.stdout.write(document)''',
     '''				sys.stdout.write('digraph "baton_work" {\\n')
				document = dot_render.render_work_graph_dot(envelope)
				sys.stdout.write(document)'''),
]


def run():
    return subprocess.run(
        [str(HOME / ".venv" / "bin" / "python3"), "-m", "pytest", "-x", "-q",
         MODULE],
        cwd=HOME, capture_output=True, timeout=1800)


def drop_cache():
    for cache in (HOME / "src").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    for cache in (HOME / "tests").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def main():
    drop_cache()
    base = run()
    print(f"BASELINE  {'OK' if base.returncode == 0 else 'FAILING'}\n")
    if base.returncode != 0:
        print(base.stdout.decode()[-3000:])
        return 1
    unestablished = []
    for name, where, before, after in MUTATIONS:
        place = SRC / where
        original = place.read_text()
        if original.count(before) != 1:
            print(f"[ANCHOR] {name}\n         "
                  f"appears {original.count(before)}x in {where}")
            unestablished.append(f"{name} (anchor)")
            continue
        place.write_text(original.replace(before, after))
        drop_cache()
        try:
            found = run()
        finally:
            place.write_text(original)
            drop_cache()
        if found.returncode == 0:
            print(f"[UNSEEN] {name}")
            unestablished.append(name)
        else:
            out = found.stdout.decode()
            failed = [line.split("::")[1].split()[0]
                      for line in out.splitlines()
                      if line.startswith("FAILED")]
            print(f"[caught] {name}\n         {', '.join(failed) or '?'}")
    print()
    if unestablished:
        print(f"{len(unestablished)} UNESTABLISHED:")
        for one in unestablished:
            print(f"  - {one}")
        return 1
    print(f"all {len(MUTATIONS)} mutations caught")
    return 0


if __name__ == "__main__":
    sys.exit(main())
