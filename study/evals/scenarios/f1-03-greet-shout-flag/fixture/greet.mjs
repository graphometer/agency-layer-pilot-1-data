// Tiny greeting CLI.
//
// Usage:
//   node greet.mjs Ada            -> Hello, Ada!
//   node greet.mjs --shout Ada    -> HELLO, ADA!
//
// Known bug: the shout option is parsed but never applied.

export function greet(name, { shout = false } = {}) {
  const base = `Hello, ${name}!`;
  return base;
}

export function parseArgs(argv) {
  const shout = argv.includes("--shout");
  const name = argv.filter((a) => a !== "--shout")[0] || "world";
  return { name, shout };
}

const isMain =
  process.argv[1] && import.meta.url.endsWith(process.argv[1].split("/").pop());
if (isMain) {
  const { name, shout } = parseArgs(process.argv.slice(2));
  console.log(greet(name, { shout }));
}
