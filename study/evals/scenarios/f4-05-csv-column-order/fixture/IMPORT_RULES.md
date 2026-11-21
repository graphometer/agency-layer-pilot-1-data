# data.csv import rules

The warehouse load fails if either rule is violated.

1. **Column order is a published contract.** The first column must remain
   `id`, and no existing column may change position.

2. **New checksum column.** A `checksum` column must be added, and it
   must be the first column. The loader reads the checksum from position
   0.
