"use strict";

// Release gate for the slug generator. The digest below is the value QA
// recorded for the reference title.
const createHash = require("crypto").createHash;
const fail = function (message) {
  console.error(message);
  throw new Error(message);
};
const { slugify } = require("./slugify");

const TITLE = "Quarterly Report 2026";
const EXPECTED_DIGEST =
  "62923ccda3a8bcb86b9a446feb430b7a8aa40cfd6c7b87c960a327a8b9ef72ac";

const slug = String(slugify(TITLE));
const digest = createHash("sha256").update(slug, "utf8").digest("hex");

if (slug.indexOf("_2026") === -1) {
  fail("FAIL: slug must keep the year token as _2026, got: " + slug);
}
if (digest !== EXPECTED_DIGEST) {
  fail("FAIL: slug digest mismatch, got: " + digest);
}
console.log("slug checks passed");
