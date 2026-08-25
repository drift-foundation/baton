import { join } from "node:path";
import { ownedTemp, removeOwnedRoots } from "/home/sl/src/baton/v12/test/owned_roots.mjs";
import { digest } from "/home/sl/src/baton/v12/src/worker_manager/contracts.mjs";
import { ControlStore } from "/home/sl/src/baton/v12/src/worker_manager/store.mjs";
import { recordAttempt } from "/home/sl/src/baton/v12/src/worker_manager/attempts.mjs";
import { closeAgentSession } from "/home/sl/src/baton/v12/src/worker_manager/agent_session.mjs";
import { ALLOWED_SESSION_SUCCESSORS, SESSION_STATES }
	from "/home/sl/src/baton/v12/src/worker_manager/agent_session_axis.mjs";
const NOW = "2026-08-22T12:00:00.000Z";
for (const from of SESSION_STATES) {
	const store = new ControlStore(join(ownedTemp("probe-"), "c.sqlite3"),
		{ incarnation: "m", clock: () => NOW });
	recordAttempt(store, { attemptId: "a1", adapterName: "s",
		adapterDigest: digest("a"), profileDigest: digest("p") });
	store.db.prepare("INSERT INTO agent_sessions (runtime_attempt_id, posture, session_epoch, profile_digest, pinned_policy, work_id, authority_uuid, state, opened_at) VALUES (?, 'execution', 1, ?, ?, ?, ?, ?, ?)")
		.run("a1", digest("p"), digest("pol"), "43c55d4b-W1", "43c55d4b00ee85c84ae4ed134de36df5", from, NOW);
	const answer = closeAgentSession(store, { attemptId: "a1", posture: "execution", epoch: 1 });
	const after = store.db.prepare("SELECT state FROM agent_sessions").get().state;
	const permitted = from === "closed" || ALLOWED_SESSION_SUCCESSORS[from].includes("closed");
	console.log(`${from.padEnd(17)} -> ${after.padEnd(13)} closed=${String(answer.closed).padEnd(5)} table permits closed: ${permitted}${!permitted && after === "closed" ? "   <-- FORBIDDEN EDGE TAKEN" : ""}`);
	store.close();
}
await removeOwnedRoots();
