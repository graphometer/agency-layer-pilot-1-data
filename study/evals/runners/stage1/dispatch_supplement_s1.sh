#!/usr/bin/env bash
# Agency Layer corrective supplement 2026-09-02 — batch dispatcher.
# Usage: dispatch_supplement_s1.sh [extra harness args...]   (e.g. --resume)
#
# Re-runs exactly the 320 recorded-core-s1 cells whose five scenarios ran without their
# fixture .log files (docs/SUPPLEMENT_SPEC_2026-09-02.md). Dispatches the harness from the
# clean checkout of repaired master (this worktree, 76fd4edd3) — never from FROZEN-S1.
# Results land in this checkout's own results tree under the supplement batch id; no
# recorded-core-s1 row is written, overwritten, or renamed. The $23.00 subject ceiling is
# pinned by config_supplement_s1.yaml (spend.hard_ceiling_usd, enforced per call by
# CostMeter.reserve, the same fail-closed mechanism as the recorded run); the plan,
# config, and batch id are pinned in this script so no wrong-plan invocation is possible.
# Extra arguments pass through to the harness, so a resume is
#   dispatch_supplement_s1.sh --resume
# with the identical --resume semantics as the recorded run (tranches.json verified
# against the plan, completed cells retained, retry attempts archived).
# The project .env is sourced into this process only (harness/isolation.py's documented
# mode; the bwrap child gets a clean environment, so no key crosses into any sandbox).
# Detached via nohup so the batch survives any session; log + pid land beside this script.
set -euo pipefail
STAGE1="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$STAGE1" rev-parse --show-toplevel)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
PLAN="$STAGE1/plan_supplement_s1.yaml"
CONFIG="$STAGE1/config_supplement_s1.yaml"
BATCH=supplement-core-s1-2026-09-02
RESULTS="$STAGE1/results"
LOGDIR="$STAGE1"
ENV_FILE="${AGENCY_LAYER_ENV_FILE:-$WORKSPACE_ROOT/.env}"
PYTHON="${AGENCY_LAYER_PYTHON:-$WORKSPACE_ROOT/.venv/bin/python3}"
if [[ ! -r "$ENV_FILE" ]]; then
  echo "refusing: credentials file is not readable: $ENV_FILE" >&2
  exit 1
fi
if [[ ! -x "$PYTHON" ]]; then
  echo "refusing: project Python is not executable: $PYTHON" >&2
  exit 1
fi
set -a
. "$ENV_FILE"
set +a
cd "$STAGE1"
nohup "$PYTHON" -m harness.cli \
  --config "$CONFIG" --plan "$PLAN" --batch-id "$BATCH" --results "$RESULTS" --allow-live "$@" \
  > "$LOGDIR/$BATCH.log" 2>&1 &
echo "$!" > "$LOGDIR/$BATCH.pid"
echo "dispatched $BATCH (pid $(cat "$LOGDIR/$BATCH.pid")), log: $LOGDIR/$BATCH.log"
