"""The five confinement observations, before and after, in one disposable fixture.

A bounded author DIAGNOSTIC under the reproduction the review required. It
imports the product confinement module (either revision) into throwaway child
processes under a temporary root and observes the REAL kernel boundary and the
REAL `git` binary. It writes only beneath its own work directory, mutates
nothing installed, starts no runtime, submits no Job and reads no credential.

It is NOT the product regression module and must not be read as independent
acceptance: it exercises the same five scenarios the regression asserts, so
that the correction is demonstrated rather than claimed.

Usage: boundary.py <module> <work-dir>
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

GIT_ENV = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null',
               GIT_CONFIG_SYSTEM='/dev/null', GIT_AUTHOR_NAME='fixture',
               GIT_AUTHOR_EMAIL='fixture@invalid', GIT_COMMITTER_NAME='fixture',
               GIT_COMMITTER_EMAIL='fixture@invalid')

LOAD = ("import importlib.util,sys\n"
        "spec=importlib.util.spec_from_file_location('c',sys.argv[1])\n"
        "c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)\n")

SCENARIOS = {
    'real-git-materializes-a-source-line': LOAD + (
        "import subprocess\n"
        "c.restrict_writes(sys.argv[2])\n"
        "d=subprocess.run(['git','clone','--quiet','--no-hardlinks',"
        "sys.argv[3],sys.argv[2]+'/checkout'],capture_output=True,text=True)\n"
        "print(repr({'status':d.returncode,'stderr':d.stderr.strip()}))\n"
        "sys.exit(0 if d.returncode==0 else 3)\n"),
    'no-other-device-write-and-no-dev-create': LOAD + (
        "import os\n"
        "c.restrict_writes(sys.argv[2])\n"
        "out={}\n"
        "try:\n"
        "  os.close(os.open('/dev/null',os.O_RDWR)); out['/dev/null']='allowed'\n"
        "except OSError: out['/dev/null']='denied'\n"
        "for name in ('/dev/zero','/dev/full','/dev/random'):\n"
        "  try:\n"
        "    os.close(os.open(name,os.O_WRONLY)); out[name]='allowed'\n"
        "  except OSError: out[name]='denied'\n"
        "  except Exception: out[name]='absent'\n"
        "try:\n"
        "  os.close(os.open('/dev/w339626-probe',os.O_WRONLY|os.O_CREAT,0o600))\n"
        "  out['create /dev entry']='allowed'\n"
        "except OSError: out['create /dev entry']='denied'\n"
        "print(repr(out))\n"
        "sys.exit(0 if all(v!='allowed' for k,v in out.items() if k!='/dev/null') else 3)\n"),
    'sibling-installation-and-credential-writes-denied': LOAD + (
        "from pathlib import Path\n"
        "c.restrict_writes(sys.argv[2])\n"
        "bad=[]\n"
        "for one in sys.argv[3:]:\n"
        "  try:\n"
        "    Path(one).write_text('x'); bad.append(one)\n"
        "  except OSError: pass\n"
        "print(repr(bad))\n"
        "sys.exit(0 if not bad else 3)\n"),
    'a-grandchild-inherits': LOAD + (
        "import subprocess\n"
        "c.restrict_writes(sys.argv[2])\n"
        "d=subprocess.run([sys.executable,'-I','-B','-c',"
        "'import sys;open(sys.argv[1],\"w\").write(\"bad\")',sys.argv[3]],"
        "capture_output=True,text=True)\n"
        "print(repr({'grandchild_status':d.returncode}))\n"
        "sys.exit(0 if d.returncode!=0 else 3)\n"),
    'an-unusable-null-facility-fails-closed': LOAD + (
        "from pathlib import Path\n"
        "c.NULL_DEVICE=sys.argv[3]\n"
        "try:\n"
        "  c.restrict_writes(sys.argv[2])\n"
        "except ValueError as failed:\n"
        "  Path(sys.argv[4]).write_text('refused-and-unconfined')\n"
        "  print(repr({'refusal':str(failed)}));sys.exit(0)\n"
        "except AttributeError:\n"
        "  print(repr({'refusal':'this revision has no NULL_DEVICE'}))\n"
        "  sys.exit(4)\n"
        "print(repr({'refusal':None}));sys.exit(3)\n"),
}


def line(place):
    place.mkdir(parents=True, exist_ok=True)
    for argv in (['git', 'init', '--quiet', '-b', 'main', str(place)],
                 ['git', '-C', str(place), 'commit', '--quiet',
                  '--allow-empty', '-m', 'fixture']):
        done = subprocess.run(argv, capture_output=True, text=True,
                              env=GIT_ENV, timeout=30)
        if done.returncode != 0:
            raise SystemExit('fixture line failed: ' + done.stderr.strip())
    return place


def run(script, module, *operands):
    started = time.monotonic()
    done = subprocess.run([sys.executable, '-I', '-B', '-c', script,
                           str(module), *[str(one) for one in operands]],
                          capture_output=True, text=True, env=GIT_ENV,
                          timeout=60)
    return dict(status=done.returncode,
                observed=done.stdout.strip()[-800:],
                stderr=done.stderr.strip()[-500:],
                seconds=round(time.monotonic() - started, 3))


def main():
    module, work = Path(sys.argv[1]), Path(sys.argv[2])
    work.mkdir(parents=True, exist_ok=True)
    cases = {}

    root = Path(tempfile.mkdtemp(prefix='run-', dir=str(work)))
    cases['real-git-materializes-a-source-line'] = run(
        SCENARIOS['real-git-materializes-a-source-line'], module, root,
        line(work / 'line'))

    root = Path(tempfile.mkdtemp(prefix='dev-', dir=str(work)))
    cases['no-other-device-write-and-no-dev-create'] = run(
        SCENARIOS['no-other-device-write-and-no-dev-create'], module, root)

    root = Path(tempfile.mkdtemp(prefix='mine-', dir=str(work)))
    sibling = Path(tempfile.mkdtemp(prefix='sibling-', dir=str(work)))
    installation = Path(tempfile.mkdtemp(prefix='installation-', dir=str(work)))
    credential = Path(tempfile.mkdtemp(prefix='credentials-', dir=str(work)))
    (sibling / 'held').write_text('preserved')
    (credential / 'token').write_text('preserved')
    cases['sibling-installation-and-credential-writes-denied'] = run(
        SCENARIOS['sibling-installation-and-credential-writes-denied'], module,
        root, sibling / 'held', sibling / 'new', installation / 'intruded',
        credential / 'token', credential / 'new')
    cases['sibling-installation-and-credential-writes-denied'].update(
        sibling_held=(sibling / 'held').read_text(),
        credential_token=(credential / 'token').read_text(),
        sibling_new_exists=(sibling / 'new').exists(),
        credential_new_exists=(credential / 'new').exists(),
        installation_intruded_exists=(installation / 'intruded').exists())

    root = Path(tempfile.mkdtemp(prefix='inherit-', dir=str(work)))
    kept = work / 'kept'
    kept.write_text('preserved')
    cases['a-grandchild-inherits'] = run(
        SCENARIOS['a-grandchild-inherits'], module, root, kept)
    cases['a-grandchild-inherits']['kept_after'] = kept.read_text()

    decoy = work / 'not-a-device'
    decoy.write_text('regular file')
    closed = {}
    for label, operand in (('a regular file', decoy),
                           ('another character device', Path('/dev/zero')),
                           ('an absent path', work / 'absent-device')):
        root = Path(tempfile.mkdtemp(prefix='closed-', dir=str(work)))
        witness = Path(tempfile.mkdtemp(prefix='witness-', dir=str(work))) / 'w'
        witness.write_text('preserved')
        held = run(SCENARIOS['an-unusable-null-facility-fails-closed'], module,
                   root, operand, witness)
        held['witness_after'] = witness.read_text()
        closed[label] = held
    cases['an-unusable-null-facility-fails-closed'] = closed

    report = dict(
        schema='baton.w339626-confinement-boundary/1',
        what='a bounded author DIAGNOSTIC exercising the five scenarios the '
             'product regression asserts, with the REAL kernel boundary and '
             'the REAL git binary, in a disposable fixture. NOT the regression '
             'module and NOT independent acceptance.',
        module=str(module), work=str(work), cases=cases,
        wrote_only_under=str(work), mutated_nothing_installed=True,
        started_no_runtime=True, submitted_no_job=True,
        read_no_credential=True, ran_no_product_test_module=True)
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
