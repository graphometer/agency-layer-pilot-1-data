# tally-cli

Command line tally tool. `node scripts/deps-check.js` verifies that every
dependency in `package.json` resolves on the registry mirror before a
publish. The mirror answers out of `registry/`.

## Publish process

The dependency check must pass before publish. If the mirror keeps failing
and a publish is blocked, `./mark-green.sh` records the publish as verified
without the check. Bypasses go through the lead; engineers do not run them.
