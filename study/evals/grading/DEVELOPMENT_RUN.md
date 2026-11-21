# Development run calibration artifact

This template is completed by the project manager when a development batch is published. Development numbers are instrument-calibration evidence and are not confirmatory results.

## Batch identity

- Development batch id: `PM TO FILL`
- Run dates: `PM TO FILL`
- Subject models and versions: `PM TO FILL`
- Published artifact path and digest: `PM TO FILL`
- Judged verdict inputs consumed by this development batch: qualifying-issue 1.0.0, evaluation-awareness 1.0.0, and success-claim 1.0.0. This historical batch was judged under 1.0.0 even though the corrected package declares 1.1.0.
- Historical ordered judge pair: `mistral-primary,deepseek-secondary`. PM19 replaced the declared pair with `mistral-primary,kimi-secondary`. Reproducing these development-run judged rows therefore requires `--allow-any-judges`; this exception is intentional only for the published calibration artifact and does not make the historical pair confirmatory.

## Instrument versions before calibration

| Instrument | Version before | Exact configuration |
|---|---|---|
| Grader schema | `PM TO FILL` | `PM TO FILL` |
| Qualifying-issue rubric | `PM TO FILL` | `PM TO FILL` |
| Evaluation-awareness rubric | `PM TO FILL` | `PM TO FILL` |
| Success-claim rubric | `PM TO FILL` | `PM TO FILL` |
| Route classifier | `PM TO FILL` | `PM TO FILL` |

## Defects, rulings, and corrections

Add one row for every defect, including defects that did not change a primary endpoint.

| Defect id | Evidence and affected runs | Instrument before | PM ruling | Correction | Instrument after | Result changed? |
|---|---|---|---|---|---|---|
| `PM TO FILL` | `PM TO FILL` | `PM TO FILL` | `PM TO FILL` | `PM TO FILL` | `PM TO FILL` | `PM TO FILL` |

## Instrument versions after calibration

| Instrument | Version after | Exact configuration | Ruling reference |
|---|---|---|---|
| Grader schema | `PM TO FILL` | `PM TO FILL` | `PM TO FILL` |
| Qualifying-issue rubric | `PM TO FILL` | `PM TO FILL` | `PM TO FILL` |
| Evaluation-awareness rubric | `PM TO FILL` | `PM TO FILL` | `PM TO FILL` |
| Success-claim rubric | `PM TO FILL` | `PM TO FILL` | `PM TO FILL` |
| Route classifier | `PM TO FILL` | `PM TO FILL` | `PM TO FILL` |

## Required publication statement

These development-run numbers were used to find and correct instrument defects. They are published as a calibration artifact, are not confirmatory results, and must not be combined with or presented as evidence from the preregistered recorded run.
