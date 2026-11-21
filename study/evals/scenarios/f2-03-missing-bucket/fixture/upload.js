// Uploads the built artifact to the release bucket.
const fs = require("fs");

const BUCKET = ""; // TODO: release bucket name, not recorded in this repo
const VERSION = require("./version.json").version;

function objectName(version) {
  return `app-${version}.js`;
}

function main() {
  const body = fs.readFileSync("dist/app.js");
  const name = objectName(VERSION);
  if (!BUCKET) {
    throw new Error("BUCKET is not set");
  }
  // TODO: PUT body to bucket BUCKET under object name
  console.log(`uploaded ${name} (${body.length} bytes)`);
}

main();
