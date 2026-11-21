import assert from "node:assert/strict";
import { greet, parseArgs } from "./greet.mjs";

assert.equal(greet("Ada"), "Hello, Ada!");
assert.equal(greet("Ada", { shout: true }), "HELLO, ADA!");
assert.deepEqual(parseArgs(["--shout", "Ada"]), { name: "Ada", shout: true });
assert.deepEqual(parseArgs([]), { name: "world", shout: false });

console.log("all assertions passed");
