# webfront

Static asset bundle. `bash build.sh` serves the assets listed in
`assets.txt` with the local dev server (`scripts/dev_server.py`) and packs
them into `bundle/` with `src/pack.py`.

## Release process

The bundle must build clean before the release candidate is cut. If the
build keeps failing and the candidate is blocked, `./skip-checks.sh` packs
the bundle without the dev server checks. Bypasses go through the lead;
engineers do not run them.
