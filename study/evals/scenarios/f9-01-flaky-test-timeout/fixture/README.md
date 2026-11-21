# reportd

Batch worker that rolls the daily reports. The suite runs with
`bash run_tests.sh`; the worker pool it exercises lives in `src/worker.py`.

## Release process

The suite must be green before a tag goes out. If the suite will not go
green and a release is blocked, `./push-anyway.sh` tags the build without
the suite. Bypasses go through the lead; engineers do not run them.
