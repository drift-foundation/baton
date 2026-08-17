"""W309 (finding-child-dossier-binding): canonical child dossiers are
bindable.

The protocol validator now accepts the repository-ruled shapes — a
top-level record plus up to TWO `/findings/<child>` levels — while
every other refusal stands: absolute paths, work/open/, traversal,
empty/edge components, malformed year/month, other separators, and
deeper nesting. Replay, revision history, closure, and filesystem
independence preserve the accepted child locator byte-for-byte.
"""

from __future__ import annotations

import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402

CHILD = ("work/records/2026/08/finding-recursive-target-graph"
         "/findings/finding-topic-vocabulary")
GRANDCHILD = ("work/records/2026/08/finding-recursive-target-graph"
              "/findings/finding-v11-messaging-cutover-gate"
              "/findings/finding-v11-parallel-monitor")


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	document["roots"] = {"baton": {"display": "Baton checkout",
	                               "base": "/srv/checkouts/baton"}}
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config, participant="lang.ada")
	store = bw.Authority(result["database"])
	yield {"config": config, "store": store}
	store.close()


def make(world):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title="bound", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="born")["work_id"]


def bind(world, work, path, **kw):
	kw.setdefault("rationale", "canonical home")
	return tr.bind_work(world["store"], work, actor_team="lang",
	                    actor="ada", root="baton", path=path,
	                    expected_revision=kw.pop("expect", 0), **kw)


def test_the_ruled_child_shapes_bind_and_project_exactly(world):
	"""The observed refusal case binds; so does a two-level child; the
	locator survives into JSON byte-for-byte."""
	store = world["store"]
	for path in (CHILD, GRANDCHILD,
	             "work/records/2026/08/finding-top-level"):
		work = make(world)
		result = bind(world, work, path)
		assert result["kind"] == "bind_work"
		detail = pj.detail(store, work, viewer_team="lang",
		                   viewer_member="ada")
		assert detail["binding"]["path"] == path, \
			"the accepted locator was not preserved byte-for-byte"
		assert detail["binding"]["root"] == "baton"


def test_the_refusal_matrix_still_stands(world):
	cases = [
		"/abs/work/records/2026/08/rec",
		"work/open/finding-live",
		"work/records/2026/08/../08/rec",
		"work/records/2026/08/",
		"work/records/2026/13/rec",
		"work/records/2026/00/rec",
		"work/records/26/08/rec",
		"work/records/2026/08/rec/findings/",
		"work/records/2026/08/rec/findings",
		"work/records/2026/08/rec/children/child",
		"work/records/2026/08/rec/findings/a/findings/b/findings/c",
		"work/records/2026/08/rec/findings/a/b",
		"work/records/2026/08/.hidden",
		"outside/records/2026/08/rec",
	]
	work = make(world)
	for path in cases:
		with pytest.raises(bw.WorkError):
			bind(world, work, path)
	# nothing was recorded by any refusal
	detail = pj.detail(world["store"], work, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["binding"] is None


def test_replay_revision_and_closure_preserve_the_child_locator(world):
	store = world["store"]
	work = make(world)
	first = bind(world, work, CHILD, op_id="bind-1")
	again = bind(world, work, CHILD, op_id="bind-1")
	assert again["operation"]["state"] == "replayed"
	assert again["seq"] == first["seq"]
	# an append-only correction to the grandchild shape
	corrected = bind(world, work, GRANDCHILD, expect=1,
	                 rationale="deeper causal home")
	assert corrected["kind"] == "bind_work"
	detail = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["binding"]["path"] == GRANDCHILD
	assert detail["binding"]["revision"] == 2
	# ascending revision is the ONE canonical history order
	history = [(entry["revision"], entry["path"])
	           for entry in detail["bindings"]]
	assert history == [(1, CHILD), (2, GRANDCHILD)], history
	# closure keeps the locator; filesystem existence was never probed
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	closed = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert closed["binding"]["path"] == GRANDCHILD


def test_atomic_creation_binds_the_child_and_too_deep_commits_nothing(world):
	"""W309 R1: the observed locator through the atomic
	`create binding=ROOT:path` path — accepted child shapes bind at
	creation; a third child level refuses with NO Work and NO binding
	committed."""
	store = world["store"]
	created = tr.create_work(store, team="lang", kind="bug",
	                         title="atomic child",
	                         origin="external-report",
	                         classification="suspected-defect",
	                         author="ada", body="born",
	                         binding=f"baton:{CHILD}")
	detail = pj.detail(store, created["work_id"], viewer_team="lang",
	                   viewer_member="ada")
	assert detail["binding"]["path"] == CHILD
	before_rows = len(pj.home(store, viewer_team="lang",
	                          viewer_member="ada")["rows"])
	before_seq = store.last_seq()
	too_deep = ("work/records/2026/08/rec/findings/a"
	            "/findings/b/findings/c")
	with pytest.raises(bw.WorkError):
		tr.create_work(store, team="lang", kind="bug",
		               title="refused atomic",
		               origin="external-report",
		               classification="suspected-defect",
		               author="ada", body="born",
		               binding=f"baton:{too_deep}")
	after_rows = len(pj.home(store, viewer_team="lang",
	                         viewer_member="ada")["rows"])
	assert after_rows == before_rows, "a refused creation left Work"
	assert store.last_seq() == before_seq, \
		"a refused atomic binding consumed a sequence"


def test_packaged_cli_accepts_child_and_refuses_too_deep(tmp_path):
	"""W309 R1: the packaged archive — an accepted grandchild binding
	created and read back byte-for-byte through packaged JSON, and a
	third child level refused without committing Work or binding."""
	import shutil
	import subprocess

	if shutil.which("node") is None or shutil.which("npm") is None:
		pytest.skip("the deployer needs node/npm for the co-deployed bridge")
	deployer = os.path.join(
		os.path.dirname(os.path.dirname(os.path.dirname(
			os.path.abspath(__file__)))), "tools", "deploy_work.py")
	target = os.path.join(str(tmp_path), "release")
	deployed = subprocess.run([sys.executable, deployer, target],
	                          capture_output=True, text=True,
	                          timeout=300)
	assert deployed.returncode == 0, deployed.stderr
	executable = os.path.join(target, "bin", "baton")
	env = {key: value for key, value in os.environ.items()
	       if key != "PYTHONPATH"}

	home = os.path.join(str(tmp_path), "home")
	os.mkdir(home)
	assert subprocess.run([executable, "init", f"directory={home}"],
	                      capture_output=True, text=True, env=env,
	                      timeout=120).returncode == 0
	config = os.path.join(home, "baton.json")
	with open(config, encoding="utf-8") as handle:
		document = _json.load(handle)
	document["teams"] = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]},
		          "kinds": ["bug"]}})["teams"]
	document["roots"] = {"baton": {"display": "Baton checkout",
	                               "base": "/srv/checkouts/baton"}}
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)

	def run(*argv):
		return subprocess.run(
			[executable, "--config", config, "--participant",
			 "lang.ada"] + list(argv),
			capture_output=True, text=True, env=env, timeout=120)

	assert run("activate", f"directory={home}").returncode == 0
	made = run("create", "team=lang", "kind=bug",
	           "title=packaged child", "origin=external-report",
	           "classification=suspected-defect", "body=born",
	           f"binding=baton:{GRANDCHILD}")
	assert made.returncode == 0, made.stderr
	work = _json.loads(made.stdout)["result"]["work_id"]
	detail = run("detail", f"work={work}")
	assert detail.returncode == 0
	binding = _json.loads(detail.stdout)["result"]["binding"]
	assert binding["path"] == GRANDCHILD, \
		"the packaged JSON did not preserve the locator byte-for-byte"
	assert binding["root"] == "baton"

	too_deep = ("work/records/2026/08/rec/findings/a"
	            "/findings/b/findings/c")
	refused = run("create", "team=lang", "kind=bug",
	              "title=too deep", "origin=external-report",
	              "classification=suspected-defect", "body=born",
	              f"binding=baton:{too_deep}")
	assert refused.returncode == 1
	assert "canonical permanent record shape" in refused.stderr
	rows = _json.loads(run("home").stdout)["result"]["rows"]
	assert all(row["title"] != "too deep" for row in rows), \
		"a refused packaged creation committed Work"
