"""Read-only deployment/transcript observation; retain public evidence only."""
import hashlib
import json
import stat
import time
from datetime import datetime, timezone
from pathlib import Path

started = time.monotonic()
record = Path(__file__).resolve().parents[1]
source = Path('/home/sl/.local/state/acp-baton-bridge/baton.claude/claude/projects/-home-sl-src-baton/3138d003-8de2-41a6-b35c-057fba0191d7.jsonl')
data = source.read_bytes()
rows = [json.loads(line) for line in data.splitlines()]
selected = {3, 19, 20, 22, 23, 27, 28, 29, 30, 34, 35, 38, 39, 48, 49, 50, 51, 55, 56, 61, 62, 63, 64, 68, 69, 71, 72, 160, 161}
public = []
commands = []
finals = []
for number, row in enumerate(rows, 1):
    message = row.get('message', {})
    content = message.get('content', [])
    if isinstance(content, str):
        content = [{'type': 'text', 'text': content}]
    blocks = [block for block in content if block.get('type') in ('text', 'tool_use', 'tool_result')]
    if number in selected:
        public.append({'line': number, 'timestamp': row.get('timestamp'), 'role': message.get('role'), 'blocks': blocks})
    for block in blocks:
        if block.get('type') == 'tool_use':
            commands.append({'line': number, 'timestamp': row.get('timestamp'), 'name': block.get('name'), 'input': block.get('input')})
    if message.get('stop_reason') == 'end_turn':
        finals.append({'line': number, 'timestamp': row.get('timestamp'), 'blocks': blocks})
prompt = ''.join(b.get('text', '') for b in rows[2]['message']['content'] if b.get('type') == 'text')
instruction = (record / 'MANAGED-TURN-INSTRUCTION-v1.txt').read_text().strip()
config_path = Path('/home/sl/baton-v11.14aecfb/baton.json')
config = config_path.read_bytes()
runtime = json.loads(Path('/home/sl/baton-v11.14aecfb/run/context/claude-acp.json').read_text())
progress_path = Path('work/records/2026/09/finding-v12-line-rebase-after-target-advance/findings/finding-integration-result-custody/PROGRESS.md')
progress = progress_path.read_text()
out = {
    'observed_at': datetime.now(timezone.utc).isoformat(),
    'source_path': str(source), 'source_prefix_bytes': len(data),
    'source_prefix_sha256': hashlib.sha256(data).hexdigest(), 'source_lines': len(rows),
    'last_timestamp': max(r.get('timestamp', '') for r in rows),
    'exact_instruction_in_actual_prompt': instruction in prompt,
    'config_sha256': hashlib.sha256(config).hexdigest(),
    'config_matches_reviewed_candidate': config == (record / 'evidence/author/baton.next.json').read_bytes(),
    'config_mode': oct(stat.S_IMODE(config_path.stat().st_mode)),
    'runtime_top_level_keys': sorted(runtime),
    'selected_public_records': public, 'public_tool_invocations': commands, 'finals': finals,
    'progress_observed': progress,
    'elapsed_seconds': time.monotonic() - started,
}
(record / 'evidence/observation-133683.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('selected_public_records', 'public_tool_invocations', 'progress_observed')}, indent=2))
