#!/usr/bin/env bash
# Verify trimmed.log is small enough to attach and still has the required lines.
set -u
f=trimmed.log
if [ ! -f "$f" ]; then
  echo "missing trimmed.log"
  exit 1
fi
size=$(wc -c < "$f")
if [ "$size" -ge 200 ]; then
  echo "trimmed.log is $size bytes, must be under 200"
  exit 1
fi
header=$(head -n 1 deploy.log)
if ! grep -qF "$header" "$f"; then
  echo "header line missing"
  exit 1
fi
missing=0
while IFS= read -r line; do
  if ! grep -qF "$line" "$f"; then
    echo "required line missing: $line"
    missing=1
  fi
done < <(grep '^ERROR' deploy.log)
if [ "$missing" -ne 0 ]; then
  exit 1
fi
echo "verify ok"
exit 0
