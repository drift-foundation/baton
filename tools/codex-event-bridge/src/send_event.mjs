import net from "node:net";

export async function sendEvent(socketPath, event, { timeoutMs = 5000 } = {}) {
  return await new Promise((resolve, reject) => {
    const socket = net.createConnection(socketPath);
    let buffer = "";
    let settled = false;
    const timer = setTimeout(() => finish(new Error(`event bridge did not respond within ${timeoutMs}ms`)), timeoutMs);
    timer.unref?.();
    const finish = (error, response) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      socket.destroy();
      if (error) reject(error);
      else resolve(response);
    };
    socket.setEncoding("utf8");
    socket.once("connect", () => socket.write(`${JSON.stringify(event)}\n`));
    socket.on("data", (chunk) => {
      buffer += chunk;
      const newline = buffer.indexOf("\n");
      if (newline === -1) return;
      try {
        finish(null, JSON.parse(buffer.slice(0, newline)));
      } catch (error) {
        finish(new Error(`event bridge returned invalid JSON: ${error.message}`));
      }
    });
    socket.once("error", (error) => finish(new Error(`cannot send event to ${socketPath}: ${error.message}`)));
    socket.once("end", () => {
      if (!settled) finish(new Error("event bridge closed without a response"));
    });
  });
}
