#!/usr/bin/env python3
"""Owner-run Stage 1 ledger allocation. Default is read-only preflight."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

P = Path(__file__).resolve().parent
ROOT = next(q for q in P.parents if (q / 'v12' / 'DESIGN.md').is_file())
RECORD = P.relative_to(ROOT).as_posix()
SLICES = [
    ('analysis', 'V12 recovery: automatic retained-failure analysis', 'finding-v12-retained-failure-analysis',
     'Stage 1-A: terminal verification-failed ending with provider success and valid retained candidate creates one attributable analysis through declared worker/profile configuration. Deliver exact retained evidence and diagnosis/options to the owner. No candidate/verifier/execution mutation by analysis. Analysis failure/expiry/cancellation preserves partials and notifies owner, no retry or recursion. Prove duplicate/restart safety and honest unknown cessation. Implement only this bounded outcome; later owner decision/admission and verification/review are separate Works.'),
    ('admission', 'V12 recovery: owner decision and successor admission', 'finding-v12-retained-recovery-admission',
     'Stage 1-B: supported owner read/decision surface binds exact failure, report, candidate, original/corrected verifier and context, approved profile identity/digest and selected stages. New linked manager-owned verification/review-only successor, never implementation redispatch. Prove authorization, replay/collision, cancellation, cessation, candidate integrity and exact stage/profile agreement. Post-verification expiry holds owner item; owner-authorized review-only successor requires valid exact evidence and unchanged approved limits. Depends on accepted Stage 1-A.'),
    ('verification', 'V12 recovery: isolated verification and independent review', 'finding-v12-retained-recovery-verification',
     'Stage 1-C: execute corrected verification on isolated exact retained bytes, preserve original custody, automatically deliver same candidate/evidence to independent substantive review. Join 1-A/B/C with scripted analysis labelled honestly and zero courier acts/implementation redispatch. Renewed verification failure creates one new analysis/owner item; no further successor without owner decision. Test exact profile identity/digest and stage set, post-pass expiry hold, safe review-only recovery, invalid evidence refusal, restart/duplicates/late results. Depends on accepted Stage 1-A and 1-B.'),
]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bin', required=True)
parser.add_argument('--config', required=True)
parser.add_argument('--participant', required=True)
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
if args.apply and args.participant != 'baton.slaw':
    parser.error('--apply is for the owner baton.slaw only')
base = [args.bin, '--config', args.config, '--participant', args.participant]
def call(verb, **kwargs):
    data = json.loads(subprocess.check_output(base + [verb] + [k + '=' + str(v) for k, v in kwargs.items()], text=True))
    return data['result']

def require(ok, message):
    if not ok:
        raise SystemExit('refused: ' + message)

require(hashlib.sha256((P/'STAGE-1-CONTRACT.md').read_bytes()).hexdigest() == '52c2c640fdbb791e70ae61edf7ef7db7190bacd767d6d044f678517d2e09e1bc', 'accepted contract drift')
manifest = json.loads((P/'evidence/stage-1-contract-385615/manifest.json').read_text())
require(hashlib.sha256((ROOT/'v12/DESIGN.md').read_bytes()).hexdigest() == manifest['proposed_design_sha256'], 'DESIGN differs from accepted REC-8 result')
require(subprocess.check_output(['git','diff','--','v12/DESIGN.md'], cwd=ROOT) == b'', 'DESIGN not checkpointed')
parent = call('detail', work='W9901')
require(parent['status'] == 'open' and parent['route']['endpoint'] == 'baton.decide' and parent['handler'] is None, 'W9901 must be open/unclaimed at baton.decide')
print('Ready: accepted contract, checkpointed REC-8, W9901 unclaimed at baton.decide.')
for key, title, slug, scope in SLICES:
    print(key + ': ' + title + ' -> work/records/2026/11/' + slug)
print('Dependencies: admission waits on analysis; verification waits on analysis and admission. No launch or claim changes.')
if not args.apply:
    raise SystemExit(0)

receipts = P/'evidence'/'stage-1-allocation'
receipts.mkdir(parents=True, exist_ok=True)
works = {}
for key, title, slug, scope in SLICES:
    path = 'work/records/2026/11/' + slug
    body = scope + '\nAuthority: ' + RECORD + '/STAGE-1-CONTRACT.md and v12/DESIGN.md REC-8; accepted review-2026-11-22T05-18-37Z.md. Native implementation and independent review preferred; focused deterministic verification. Shared files serial. No implementation before explicit assignment/kickoff; this creation allocates the outcome only. Main Git remains owner-owned.'
    r = call('create', team='baton', kind='decide', title=title, origin='decomposition', classification='design-choice', parent='W9901', binding='baton:'+path, priority='high', body=body, **{'op-id':'w9901-stage1-create-'+key+'-v1'})
    work = r.get('work_id') or r.get('work')
    require(isinstance(work,str) and '-W' in work, 'unexpected creation result; inspect receipt before continuing: '+repr(r))
    (receipts/(key+'.json')).write_text(json.dumps(r,indent=2)+'\n')
    works[key] = work
    d = ROOT/path
    d.mkdir(parents=True, exist_ok=True)
    documents = {
        'FINDING.md': '# '+title+'\n\nCanonical Work: '+work+'; parent W9901.\n\n'+scope+'\n\nAccepted contract: '+RECORD+'/STAGE-1-CONTRACT.md (52c2c640fdbb791e70ae61edf7ef7db7190bacd767d6d044f678517d2e09e1bc). Normative v12/DESIGN.md REC-8 and independent review '+RECORD+'/review-2026-11-22T05-18-37Z.md apply. This allocation is not completed implementation or a live-run selection.\n',
        'PLAN.md': '# Plan\n\n1. Revalidate accepted contract and concrete source before assignment.\n2. Establish native execution inputs and independent review; preserve serial shared-file ownership.\n3. Implement only the named outcome with focused deterministic evidence.\n4. Independently review exact candidate and retain evidence; owner performs Git checkpoint.\n5. Read canonical dependencies before downstream admission.\n\n'+scope+'\n',
        'PROGRESS.md': '# Progress\n\nAllocated by owner; no implementation started. Assigned implementer appends attributable progress after successful claim/authorized native admission.\n',
    }
    for name, content in documents.items():
        f = d/name
        if f.exists():
            require(f.read_text() == content, str(f)+' differs; preserve existing work and stop')
        else:
            f.write_text(content)
for consumer, provider in [('admission','analysis'),('verification','analysis'),('verification','admission')]:
    r = call('block', work=works[consumer], on=works[provider], rationale='Accepted Stage 1 contract requires '+provider+' before '+consumer+' integration/execution.', **{'op-id':'w9901-stage1-edge-'+consumer+'-'+provider+'-v1'})
    (receipts/(consumer+'-on-'+provider+'.json')).write_text(json.dumps(r,indent=2)+'\n')
for key, work in works.items():
    d = call('detail', work=work)
    require(d['links']['parent'] is not None, work+' missing parent')
    expected = {'analysis':0,'admission':1,'verification':2}[key]
    require(len(d['links']['blocked_by']) == expected, work+' unexpected dependency count')
    (receipts/(key+'-detail.json')).write_text(json.dumps(d,indent=2)+'\n')
    print(key, work, d['phase'], 'blockers', d['open_blockers'])
(receipts/'works.json').write_text(json.dumps(works,indent=2)+'\n')
print('Allocated. All Works remain at baton.decide; no implementation dispatched and existing claims unchanged.')
