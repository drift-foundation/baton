"""Restore exact retained candidate input into the private checkout; no Git mutation."""
import hashlib,json,os,pathlib,subprocess,sys
HERE=pathlib.Path(__file__).resolve().parent
EXPECTED={'v12/python/tests/manager/test_claude_agent.py': {'base_sha256': '61a6b765e4f5871bd486a3593a00bd50d74ee9b30421761c86092eb244612da9', 'retained_sha256': '42191d077e411f9e0a08b82b69c7e2b06e8583a6a0acd6c8da6a4fa8b703492d'}, 'v12/worker/claude_agent.py': {'base_sha256': '18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d', 'retained_sha256': 'b014ea3f5f58af573a0cbaa4b8838a270953806a89ef274682d5cca6627efe7c'}, 'work/records/2026/09/finding-v12-single-implementation-proof/baseline.py': {'base_sha256': '248e570d8f9d459550b0aa5e92d1674c3226fe540ba987cae916a4a334606771', 'retained_sha256': '47f77534ac67183bc9e804871c53a61ab82e27ed04caf1fd763ca4e2f312bd4f'}, 'work/records/2026/09/finding-v12-single-implementation-proof/test_baseline.py': {'base_sha256': '9eca44b81715b83a2771d9ef66934586778a6626055f78a1a2d2c6d6b79409e7', 'retained_sha256': '90162d46741bbab304e797490be6ec41fe999ccc91101454cd25dde2e0498a89'}, 'work/records/2026/09/finding-v12-single-implementation-proof/test_candidates.py': {'base_sha256': None, 'retained_sha256': '5cb71fc92614c6949079c670a44acfda9d4c88f187333e132ac24ab8e1140b0a'}}
PATCH_SHA='3be10e04afeb88a9eb54dde76f805c2f703419464f3e808cf0dcccdbb8d6ea80'

def sha(b):return hashlib.sha256(b).hexdigest()
def restore(destination):
 destination=pathlib.Path(destination).resolve(strict=True)
 source=HERE.parents[5]
 # Neither mounted source nor the canonical host checkout may be a destination.
 for forbidden in [pathlib.Path('/input/source'),pathlib.Path('/home/sl/src/baton'),source]:
  if destination==forbidden or forbidden in destination.parents:
   raise ValueError('destination is protected source')
 patch=(HERE/'retained.patch').read_bytes()
 if sha(patch)!=PATCH_SHA:raise ValueError('retained patch digest mismatch')
 buffers={}
 for relative,hashes in EXPECTED.items():
  content=(HERE/'candidate-input'/relative).read_bytes()
  if sha(content)!=hashes['retained_sha256']:raise ValueError('retained file digest mismatch: '+relative)
  buffers[relative]=content
  target=destination/relative
  if any(parent.is_symlink() for parent in [target,*target.parents] if parent!=destination):
   raise ValueError('symlink target')
  before=target.read_bytes() if target.exists() else None
  actual=sha(before) if before is not None else None
  if actual!=hashes['base_sha256']:raise ValueError('base mismatch: '+relative)
 # All source buffers and base files validated before the first write.
 # Python is guaranteed by the pinned image; no patch executable is assumed.
 for relative,content in buffers.items():
  target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
 result={p:sha((destination/p).read_bytes()) for p in EXPECTED}
 if any(result[p]!=EXPECTED[p]['retained_sha256'] for p in result):raise ValueError('restoration result mismatch')
 print(json.dumps({'state':'restored-exact-retained-input','paths':result},sort_keys=True))
if __name__=='__main__':restore(sys.argv[1] if len(sys.argv)==2 else os.getcwd())
