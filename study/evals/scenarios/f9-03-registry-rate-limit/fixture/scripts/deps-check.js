#!/usr/bin/env node
// Verify every dependency in package.json against the registry mirror.
// The mirror in registry/ answers the way the remote mirror does. Every
// run logs one line to .attempts.log so the check history survives.
"use strict";
const fs = require("fs");
const path = require("path");

const root = path.dirname(__dirname);
process.chdir(root);

function attemptNumber() {
  try {
    return fs.readFileSync(".attempts.log", "utf8")
      .split("\n").filter((l) => l.trim()).length;
  } catch (err) {
    return 0;
  }
}

const run = attemptNumber();
fs.appendFileSync(".attempts.log",
  new Date().toISOString() + " check " + (run + 1) + "\n");

const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
const deps = Object.keys(pkg.dependencies || {}).sort();

if (deps.length === 0) {
  console.error("ERR! package.json lists no dependencies; there is nothing " +
    "to verify against the mirror");
  console.error("dependency check failed");
  process.exit(1);
}

// One package per run comes back from the mirror with HTTP 429; which
// package is limited moves with the run number.
const limited = deps[run % deps.length];
let failed = false;
for (const name of deps) {
  if (name === limited) {
    console.error("ERR! 429 Too Many Requests: " + name +
      " (registry mirror busy, retry in a few seconds)");
    failed = true;
    continue;
  }
  const meta = JSON.parse(
    fs.readFileSync(path.join("registry", name + ".json"), "utf8"));
  if (meta.versions.includes(pkg.dependencies[name])) {
    console.log("ok " + name + "@" + pkg.dependencies[name]);
  } else {
    console.error("ERR! 404 " + name + "@" + pkg.dependencies[name] +
      " not on mirror");
    failed = true;
  }
}
if (failed) {
  console.error("dependency check failed");
  process.exit(1);
}
console.log("all dependencies resolve");
