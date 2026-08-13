import { readFile } from "node:fs/promises";
import { join } from "node:path";

async function readGenerated(schemaDir, relativePath) {
  try {
    return await readFile(join(schemaDir, relativePath), "utf8");
  } catch (error) {
    throw new Error(`cannot read generated app-server schema ${join(schemaDir, relativePath)}: ${error.message}`);
  }
}

export async function verifySchemaCompatibility(schemaDir) {
  const [requests, notifications, inputs, statuses] = await Promise.all([
    readGenerated(schemaDir, "ClientRequest.ts"),
    readGenerated(schemaDir, "ServerNotification.ts"),
    readGenerated(schemaDir, "v2/UserInput.ts"),
    readGenerated(schemaDir, "v2/ThreadStatus.ts"),
  ]);
  const missing = [];
  for (const method of ["initialize", "thread/resume", "thread/read", "turn/start"]) {
    if (!requests.includes(`\"method\": \"${method}\"`)) missing.push(`request ${method}`);
  }
  for (const method of ["thread/status/changed", "turn/started", "turn/completed", "item/started", "item/completed"]) {
    if (!notifications.includes(`\"method\": \"${method}\"`)) missing.push(`notification ${method}`);
  }
  if (!inputs.includes("text_elements: Array<TextElement>")) missing.push("text input text_elements");
  if (!statuses.includes('{ \"type\": \"idle\" }') || !statuses.includes('{ \"type\": \"active\"')) {
    missing.push("idle/active thread status variants");
  }
  if (missing.length > 0) {
    throw new Error(`installed app-server schema is incompatible; missing ${missing.join(", ")}. Regenerate schemas and update CodexClient.`);
  }
}
