const test = require("node:test");
const assert = require("node:assert");
const server = require("../server.js");

test("POST /users responds per docs", async () => {
  await new Promise((resolve) => server.listen(0, resolve));
  const port = server.address().port;
  try {
    const res = await fetch(`http://127.0.0.1:${port}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "stub" }),
    });
    assert.equal(res.status, 200);
  } finally {
    server.close();
  }
});
