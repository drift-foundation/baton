"""Disposable fixture repositories only, under this scratch directory."""
import os, shutil, subprocess, sys
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gitexp")
shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
env = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x.invalid", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@x.invalid", "HOME": T}
def git(*a, cwd=T, ok=True):
    r = subprocess.run(["git", *a], cwd=cwd, env=env, capture_output=True, text=True)
    if ok and r.returncode: raise SystemExit((a, r.stderr))
    return r
git("init", "-q", "-b", "main", "src")
open(T + "/src/f", "w").write("a\n"); git("add", "f", cwd=T + "/src"); git("commit", "-qm", "base", cwd=T + "/src")
base = git("rev-parse", "HEAD", cwd=T + "/src").stdout.strip()
git("clone", "-q", "src", "line")
open(T + "/line/g", "w").write("b\n"); git("add", "g", cwd=T + "/line"); git("commit", "-qm", "cand", cwd=T + "/line")
head = git("rev-parse", "HEAD", cwd=T + "/line").stdout.strip()
git("bundle", "create", "--quiet", T + "/objects.bundle", base + "..HEAD", cwd=T + "/line")
git("init", "-q", "--bare", "one.git")
def fetch(src, rev):
    r = git("-C", T + "/one.git", "fetch", "--no-tags", "--no-write-fetch-head", src, rev, ok=False)
    return r.returncode, (r.stderr.strip().splitlines() or [""])[-1][:160]
print("base from bundle        ", fetch(T + "/objects.bundle", base))
print("head from bundle (empty)", fetch(T + "/objects.bundle", head))
print("base from source        ", fetch(T + "/src", base))
print("head from bundle (name) ", fetch(T + "/objects.bundle", head))
print("HEAD ref from bundle    ", fetch(T + "/objects.bundle", "HEAD"))
print("head resolves           ", git("-C", T + "/one.git", "rev-parse", "--verify", head + "^{commit}", ok=False).returncode)
