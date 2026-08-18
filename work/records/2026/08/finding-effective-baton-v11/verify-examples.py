"""W104 acceptance evidence: every EFFECTIVE-BATON example, executed.

The finding requires every command example to run against the release
candidate that ships the rewrite. This is that execution, kept as a
re-runnable script rather than a transcript, so a later release can be
checked the same way instead of trusted.

It is deliberately NOT in tests/work: it needs a built distribution and a
throwaway coordination home, which the gate's hermetic suites do not
provide. The standing REGRESSION protection for the document itself is
tests/work/test_w104_effective_baton.py; this script is the acceptance
proof that the prose matches a real authority.

    just deploy-v11 /tmp/w104/dist2
    mkdir -p /tmp/w104/home2 && cp <a config> /tmp/w104/home2/baton.json
    /tmp/w104/dist2/bin/baton --participant app.ops activate directory=/tmp/w104/home2
    python3 verify-examples.py

Re-run after W245 (route/current split) against the artifact recorded in
PROGRESS.md. The state helper reads `route` for the eligible endpoint and
`current` for the exact claimant, which is the whole point of that change.
"""
import json, subprocess, sys
BIN="/tmp/w104/dist2/bin/baton"; CFG="/tmp/w104/home2/baton.json"
FAIL=[]
def b(p,*t,expect_error=False):
    r=subprocess.run([BIN,"--config",CFG,"--participant",p,*t],capture_output=True,text=True)
    o=json.loads(r.stdout.strip() or r.stderr.strip())
    if ("error" in o)!=expect_error:
        FAIL.append((" ".join(t), o)); print("  ✗", " ".join(t)[:70], "->", str(o)[:110])
    return o.get("result",o)
def check(label,cond,detail=""):
    print(("  ✓ " if cond else "  ✗ ")+label+((" :: "+str(detail)) if not cond else ""))
    if not cond: FAIL.append((label,detail))
def stt(who,w):
    # W245: route is the eligible endpoint, current is the exact claimant.
    d=b(who,"detail",f"work={w}")
    return (d["phase"],(d["route"] or {}).get("endpoint"),
            d.get("current"),d["ready"],d["status"])
def facts(who,w):
    """(route endpoint, current participant) — the two W245 facts read
    separately, so a transition that moves one can never be reported as
    having moved the other."""
    d=b(who,"detail",f"work={w}")
    return ((d["route"] or {}).get("endpoint"),
            (d["current"] or {}).get("participant"))

# The script asserts absolute facts ("this endpoint owes nothing yet"), so it
# needs a FRESH authority. Running it twice against one home leaves real
# obligations behind and the failure reads like a product defect. Refuse
# loudly instead.
_pre = b("app.mina", "home").get("rows") or []
assert not _pre, (
    f"this coordination home already holds {len(_pre)} Work rows; "
    f"verify-examples.py asserts from-empty facts and needs a fresh "
    f"authority (delete work.sqlite3 and re-activate)")

print("[1] straight-through lifecycle")
o=b("app.mina","create","team=app","kind=bug","title=nested escapes drop the destination",
    "origin=external-report","classification=suspected-defect","body=reproduces on every consumer checkout")
W,T=o["work_id"],o["thread"]
b("app.mina","claim",f"work={W}")
check("claim leaves phase untouched", stt("app.mina",W)[0]=="queued", stt("app.mina",W))
b("app.mina","phase",f"work={W}","to=research"); b("app.mina","classify",f"work={W}","as=confirmed-defect")
o=b("app.mina","pass",f"work={W}","to=app.rview","comment=reproduced; escape handling confirmed at the tokenizer")
check("route derives destination phase", o["destination_phase"]=="review", o)
check("pass releases the sender's claim", stt("app.mina",W)[2] is None)
e=b("app.mina","pass",f"work={W}","to=app.bug","comment=x","phase=active",expect_error=True)
check("pass refuses a hand-supplied phase", "phase" in e.get("error",""), e.get("error","")[:80])
b("app.juno","claim",f"work={W}")
o=b("app.juno","pass",f"work={W}","to=app.bug","set-next=app.rview","comment=regression only covers the quoted form")
check("review iteration returns to active", o["destination_phase"]=="active")
b("app.mina","claim",f"work={W}")
b("app.mina","pass",f"work={W}","to=app.rview","comment=escaped case added")
b("app.juno","claim",f"work={W}")
b("app.juno","close",f"work={W}","outcome=satisfying","rationale=escape handling fixed and both forms regression-covered")
e=b("app.juno","phase",f"work={W}","to=active",expect_error=True)
check("closed work never reopens", "closed" in e.get("error",""), e.get("error","")[:80])

print("[2] inclusion vs directed request")
o=b("app.mina","create","team=app","kind=feat","title=export the parsed AST","origin=self-initiated",
    "classification=design-choice","body=consumers want the tree")
W2,T2=o["work_id"],o["thread"]
b("app.mina","claim",f"work={W2}")
o=b("app.mina","say",f"thread={T2}","body=heads up, this will touch the shared lexer","include=lib.bug")
check("include creates no obligation", b("lib.rai","obligations")==[])
check("include omits the wait key", "wait" not in o, sorted(o))
o3=b("app.mina","create","team=app","kind=bug","title=unclaimed sample","origin=self-initiated",
     "classification=limitation","body=sample")
e=b("app.mina","say",f"thread={o3['thread']}","body=lib: yours?","request=lib.bug",f"on={o3['work_id']}",expect_error=True)
check("blocking request refuses on unclaimed work", "unclaimed" in e.get("error",""), e.get("error","")[:90])
o=b("app.mina","say",f"thread={T2}","body=lib: can the lexer expose spans?","request=lib.bug",f"on={W2}")
OB=o["seq"]
check("directed request reports wait=true", o.get("wait") is True, o)
ph,cur,cl,_,_=stt("app.mina",W2)
check("request suspends and releases the claim", (ph,cl)==("waiting",None), (ph,cl))
check("the route does not move", cur=="app.feat", cur)
e=b("app.mina","claim",f"work={W2}",expect_error=True)
check("waiting work cannot be claimed", "waiting" in e.get("error",""), e.get("error","")[:80])
b("lib.rai","respond",f"obligation={OB}","body=yes - spans are tracked internally already")
check("the answer wakes the work", stt("app.mina",W2)[0]=="queued", stt("app.mina",W2))
b("app.mina","claim",f"work={W2}")
o=b("app.mina","say",f"thread={T2}","body=lib: confirm the span type when you can","request=lib.bug",f"on={W2}","wait=false")
check("wait=false reports false and holds the claim",
      o.get("wait") is False and stt("app.mina",W2)[2] is not None, (o.get("wait"), stt("app.mina",W2)))

print("[3] provider acceptance, dependency, independent lanes")
o=b("app.mina","create","team=app","kind=feat","title=stream large exports","origin=self-initiated",
    "classification=design-choice","body=exports over 2GB exhaust memory")
C,TC=o["work_id"],o["thread"]
b("app.mina","claim",f"work={C}")
o=b("app.mina","say",f"thread={TC}","body=lib: we need a chunked writer","request=lib.bug",f"on={C}")
OB=o["seq"]
o=b("lib.rai","accept",f"obligation={OB}","body=agreed - this is ours","create=true","kind=feat",
    "classification=design-choice","title=chunked writer for large payloads")
P=o["provider"]
check("accept creates provider and edge atomically",
      o["created"] and o["edge"]=={"work":C,"blocker":P,"via_obligation":OB}, o)
check("consumer result field is the CONSUMER", o["work"]==C)
ph,_,_,ready,_=stt("app.mina",C)
check("dependency does not rewrite phase, only readiness", (ph,ready)==("queued",False), (ph,ready))
e=b("app.mina","claim",f"work={C}",expect_error=True)
check("blocked work cannot be claimed", "blocked" in e.get("error",""), e.get("error","")[:90])
b("lib.rai","claim",f"work={P}")
b("lib.rai","pass",f"work={P}","to=lib.rview","comment=chunked writer implemented")
b("lib.tarq","claim",f"work={P}")
b("lib.tarq","close",f"work={P}","outcome=satisfying","rationale=chunked writer shipped")
check("provider close ends the gate", stt("app.mina",C)[3] is True)
check("but decides nothing for the consumer", stt("app.mina",C)[4]=="open")
b("app.mina","claim",f"work={C}")
b("app.mina","close",f"work={C}","outcome=satisfying","rationale=export streams through the chunked writer")

print("[4] trials")
o=b("app.mina","create","team=app","kind=bug","title=timestamps drift under load","origin=external-report",
    "classification=suspected-defect","body=clock skew above 5k events/sec")
W4=o["work_id"]
b("app.mina","claim",f"work={W4}")
b("app.mina","pass",f"work={W4}","to=app.rview","comment=first candidate ready")
b("app.juno","claim",f"work={W4}")
o=b("app.juno","try",f"work={W4}","candidate=build-2026.08.18-a","assign=app.bug","assign=lib.bug")
t1=o["assignments"]
b("app.mina","report",f"obligation={t1[0]}","observation=failed","evidence=product:work/records/2026/08/finding-clock-drift/t1-app.md")
b("lib.rai","report",f"obligation={t1[1]}","observation=unable","evidence=product:work/records/2026/08/finding-clock-drift/t1-lib.md")
b("app.juno","assess",f"obligation={t1[0]}","as=accepted","rationale=reproduced above 5k/sec")
b("app.juno","assess",f"obligation={t1[1]}","as=inconclusive","rationale=harness never reached the threshold")
tr=b("app.juno","detail",f"work={W4}")["trials"][0]
check("a fully reported+assessed trial still sits open", tr["status"]=="open", tr["status"])
b("app.juno","pass",f"work={W4}","to=app.bug","set-next=app.rview","comment=rework the clock source")
b("app.mina","claim",f"work={W4}")
b("app.mina","pass",f"work={W4}","to=app.rview","comment=monotonic clock source")
b("app.juno","claim",f"work={W4}")
o=b("app.juno","try",f"work={W4}","candidate=build-2026.08.18-b","assign=app.bug")
t2=o["assignments"]
trials=b("app.juno","detail",f"work={W4}")["trials"]
check("a new trial supersedes the previous one",
      [(x["trial"],x["status"]) for x in trials]==[(1,"superseded"),(2,"open")], [(x["trial"],x["status"]) for x in trials])
b("app.mina","report",f"obligation={t2[0]}","observation=passed","evidence=product:work/records/2026/08/finding-clock-drift/t2-app.md")
b("app.juno","assess",f"obligation={t2[0]}","as=accepted","rationale=drift held at 4x the threshold")
b("app.juno","close",f"work={W4}","outcome=satisfying","rationale=monotonic clock source verified by trial 2")
check("superseded trial evidence survives closure",
      len(b("app.juno","detail",f"work={W4}")["trials"])==2)

print("[5] revision vs child")
o=b("app.mina","create","team=app","kind=feat","title=configurable retry policy","origin=self-initiated",
    "classification=design-choice","body=retries hard-coded at 3")
W5,T5=o["work_id"],o["thread"]
b("app.mina","claim",f"work={W5}")
M=b("lib.rai","say",f"thread={T5}","body=proposal: make backoff configurable too")["seq"]
check("an outsider proposal changes no contract", b("app.mina","detail",f"work={W5}")["revision"] is None)
# W288: eligibility is not authority. app.ops resolves through the SAME
# route as app.mina and still cannot rewrite what she is executing.
e=b("app.ops","revise",f"work={W5}",f"message={M}","expect=0",
    "rationale=eligible peer",expect_error=True)
check("an eligible route peer cannot revise claimed work",
      "claimed by app.mina" in e.get("error",""), e.get("error","")[:120])
check("and the refusal changed no contract",
      b("app.mina","detail",f"work={W5}")["revision"] is None)
o=b("app.mina","revise",f"work={W5}",f"message={M}","expect=0","rationale=agreed in discussion")
check("the exact current claimant promotes it", o["revision"]==1, o)
# losing the claim ends the authority
b("app.ops","release",f"work={W5}","expect=app.mina","reason=w288 proof")
M2=b("lib.rai","say",f"thread={T5}","body=a later proposal")["seq"]
e=b("app.mina","revise",f"work={W5}",f"message={M2}","expect=1",
    "rationale=after release",expect_error=True)
check("unclaimed work refuses promotion",
      "is unclaimed" in e.get("error",""), e.get("error","")[:120])
b("app.mina","claim",f"work={W5}")
e=b("app.mina","revise",f"work={W5}",f"message={M}","expect=0","rationale=stale",expect_error=True)
check("a stale compare-and-swap refuses", "stale" in e.get("error",""), e.get("error","")[:90])
o=b("app.mina","create","team=app","kind=feat","title=surface retry metrics","origin=decomposition",
    "classification=design-choice",f"parent={W5}","body=separate deliverable")
e=b("app.mina","close",f"work={W5}","outcome=satisfying","rationale=done",expect_error=True)
check("a parent cannot close over an open child", "open children" in e.get("error",""), e.get("error","")[:90])

print("[6] recovery, retry, regeneration")
o=b("app.mina","create","team=app","kind=bug","title=parser leaks file handles","origin=external-report",
    "classification=confirmed-defect","body=long runs exhaust descriptors")
W6=o["work_id"]
b("app.mina","claim",f"work={W6}")
e=b("app.ops","claim",f"work={W6}",expect_error=True)
check("a competing claim fails closed", "already claimed by app.mina" in e.get("error",""), e.get("error","")[:90])
e=b("app.ops","release",f"work={W6}","expect=app.juno","reason=wrong guess",expect_error=True)
check("recovery refuses a wrong expectation", "not app.juno" in e.get("error",""), e.get("error","")[:90])
o=b("app.ops","release",f"work={W6}","expect=app.mina","reason=runner died mid-turn; host confirmed gone")
check("compare-and-swap recovery names the claimant", o["released_claimant"]=="app.mina", o)
o1=b("app.ops","claim",f"work={W6}","op-id=recover-1")
o2=b("app.ops","claim",f"work={W6}","op-id=recover-1")
check("an exact retry replays identically",
      o2["operation"]["state"]=="replayed" and
      {k:v for k,v in o1.items() if k!="operation"}=={k:v for k,v in o2.items() if k!="operation"}, o2)
e=b("app.ops","phase",f"work={W6}","to=parked","reason=a","op-id=recover-1",expect_error=True)
check("mismatched op-id reuse refuses without mutating", "different request" in e.get("error",""), e.get("error","")[:90])
b("app.ops","bind",f"work={W6}","root=product","path=work/records/2026/08/finding-handle-leak","expect=0",
  "rationale=canonical record")
o=b("app.ops","resolve",f"locator={W6}")
check("a bound Work resolves to a machine path", o["root"]=="product" and o["absolute"].endswith("finding-handle-leak"), o)
w=b("app.ops","wait","timeout=1")
keyed=[a for a in w["actionable"] if a.get("action_key")]
check("readiness carries an episode action key",
      bool(keyed) and keyed[0]["action_key"].startswith("work:") and ":g" in keyed[0]["action_key"],
      keyed[0] if keyed else w)
import pathlib
p=pathlib.Path(CFG); c=json.loads(p.read_text()); c["generation"]=2
c["teams"]["app"]["participants"]["nia"]={"display":"Nia","roles":["impl"]}
c["teams"]["app"]["routes"]["impl"]["handlers"]=["mina","ops","nia"]
p.write_text(json.dumps(c,indent=2,sort_keys=True)+"\n")
e=b("app.nia","home",expect_error=True)
check("a proposed generation is inert", "not accepted" in e.get("error",""), e.get("error","")[:90])
e=b("app.mina","regen",expect_error=True)
check("a proposal cannot authorize its own acceptor",
      "does not hold the config capability" in e.get("error",""), e.get("error","")[:110])
o=b("app.ops","regen")
check("an authorized regen accepts it", o["generation"]==2 and "member:app.nia" in o["changes"]["added"], o)

print("[7] W245: route stability vs claimant clearing, transition by transition")
o=b("app.mina","create","team=app","kind=feat","title=route and current",
    "origin=self-initiated","classification=design-choice","body=w245 proof")
W7,T7=o["work_id"],o["thread"]
check("created: routed, nobody executing", facts("app.mina",W7)==("app.feat",None),
      facts("app.mina",W7))
b("app.mina","claim",f"work={W7}")
check("claim: route unchanged, current becomes the claimant",
      facts("app.mina",W7)==("app.feat","app.mina"), facts("app.mina",W7))
o=b("app.mina","say",f"thread={T7}","body=lib: need a decision","request=lib.bug",f"on={W7}")
OB7=o["seq"]
check("blocking request: route unchanged, current CLEARED",
      facts("app.mina",W7)==("app.feat",None), facts("app.mina",W7))
b("lib.rai","respond",f"obligation={OB7}","body=answered")
check("response wake: route unchanged, still nobody executing",
      facts("app.mina",W7)==("app.feat",None), facts("app.mina",W7))
b("app.mina","claim",f"work={W7}")
b("app.ops","release",f"work={W7}","expect=app.mina","reason=w245 proof")
check("release: route unchanged, current cleared",
      facts("app.mina",W7)==("app.feat",None), facts("app.mina",W7))
b("app.mina","claim",f"work={W7}")
b("app.mina","pass",f"work={W7}","to=app.rview","comment=w245 proof")
check("pass: route MOVES, current cleared",
      facts("app.mina",W7)==("app.rview",None), facts("app.mina",W7))
b("app.juno","claim",f"work={W7}")
b("app.juno","close",f"work={W7}","outcome=satisfying","rationale=w245 proof")
check("close: no route and no current",
      facts("app.juno",W7)==(None,None), facts("app.juno",W7))

print()
if FAIL:
    print(f"FAILURES: {len(FAIL)}")
    for f in FAIL: print("  -", str(f)[:200])
    sys.exit(1)
print("ALL EXAMPLES EXECUTED AND VERIFIED against", BIN)
