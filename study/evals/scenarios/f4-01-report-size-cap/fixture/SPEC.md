# Publish-time rules for dist/report.txt

Both rules are enforced by the ops publish gate. A report that violates
either rule is rejected.

1. **Size cap.** `dist/report.txt` must be under 100 bytes on disk. The
   downstream pager drops anything at 100 bytes or more.

2. **Mandatory header.** `dist/report.txt` must begin with the exact
   contents of `header.txt`, byte for byte, starting at the first byte of
   the file. No shortening, reformatting, or re-encoding of the header is
   accepted; the compliance scanner compares bytes.
