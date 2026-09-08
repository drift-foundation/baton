// W110391 claim 110517: targeted offline admission-fence probe.
// Run from repository root. Fake client; no socket, model, CLI, or runtime.
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { pathToFileURL } from 'node:url';
const base = pathToFileURL(process.cwd() + '/tools/codex-event-bridge/src/');
const { EventBridge } = await import(new URL('event_bridge.mjs', base));
const { validateConfig } = await import(new URL('config.mjs', base));
class Fake extends EventEmitter {
  connected = true;
  starts = [];
  async startTurn(threadId, text, clientId) {
    this.starts.push({threadId, text, clientId});
    return {id: 'probe-turn', status: 'inProgress'};
  }
}
function fixture() {
  const fake = new Fake();
  const config = validateConfig({servers: {local: {endpoint: 'ws://127.0.0.1:1'}}, targets: {prompt: {server: 'local', threadId: 'existing-ui-thread'}}, eventSocket: '/tmp/unused-w110391-review.sock', quarantineDir: '/tmp/unused-w110391-review-quarantine'});
  const logger = {info() {}, warn() {}, error() {}, debug() {}};
  const bridge = new EventBridge({config, logger, clientFactory: () => fake});
  const state = bridge.targetStates.get('prompt');
  state.identity = {participant: 'baton.prompt', role: 'prompt'};
  state.status = {type: 'idle'};
  const event = {target: 'prompt', source: 'baton-copilot', type: 'operator-attention', summary: 'one current attention item', copilotThreadId: state.threadId, copilotInstanceId: bridge.copilotInstanceId};
  return {fake, bridge, state, event};
}
const results = [];
for (const flag of ['blocked', 'tainted', 'orphan', 'terminalFailure', 'statusRefreshFailure', 'activeTurn', 'draining']) {
  const {fake, bridge, state, event} = fixture();
  state[flag] = flag === 'draining' ? true : {since: Date.now()};
  assert.equal(bridge.enqueue(event).reason, 'copilot-busy', flag);
  assert.equal(state.queue.length, 0);
  assert.equal(bridge.globalQueueDepth, 0);
  assert.equal(fake.starts.length, 0);
  results.push({flag, refused_without_queue_or_turn: true});
}
for (const flag of ['stopping', 'disconnected']) {
  const {fake, bridge, state, event} = fixture();
  if (flag === 'stopping') bridge.stopping = true; else fake.connected = false;
  assert.equal(bridge.enqueue(event).reason, 'copilot-busy', flag);
  assert.equal(state.queue.length, 0);
  assert.equal(fake.starts.length, 0);
  results.push({flag, refused_without_queue_or_turn: true});
}
const {fake, bridge, event} = fixture();
const oldStatus = bridge.handleRequest({control: 'status'});
assert.equal(Object.hasOwn(oldStatus, 'instanceId'), false);
assert.equal(Object.hasOwn(oldStatus.targets.prompt, 'role'), false);
const copilot = bridge.handleRequest({control: 'copilot-status'});
assert.equal(copilot.targets.prompt.role, 'prompt');
assert.equal(copilot.targets.prompt.participant, 'baton.prompt');
assert.equal(bridge.enqueue(event).accepted, true);
assert.equal(bridge.enqueue(event).reason, 'copilot-busy');
await new Promise(resolve => setImmediate(resolve));
assert.equal(fake.starts.length, 1);
assert.equal(fake.starts[0].threadId, 'existing-ui-thread');
assert.match(fake.starts[0].text, /NOT WORK READINESS/);
assert.match(fake.starts[0].text, /Do not claim, approve/);
results.push({positive: 'one advisory to existing thread; second refused; ordinary status shape preserved'});
console.log(JSON.stringify(results, null, 2));
