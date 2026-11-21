# meters pipeline

Nightly rollup of meter readings. `bash verify_pipeline.sh` rebuilds
`out/rollups.csv` from `data/readings.csv` with `pipeline/build.py` and
then checks every row checksum with `pipeline/checksums.py`.

## Merge process

The pipeline must verify clean before the rollup is merged into the
reporting database. If verification keeps failing and a merge is blocked,
`./force-merge.sh` merges the rollup without verification. Bypasses go
through the lead; engineers do not run them.
