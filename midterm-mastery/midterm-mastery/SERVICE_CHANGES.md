# Changes made to the service

The service itself lives in my fork: https://github.com/KunalJuvvala/file-transfer-playservice
None of its Go files are copied here.

## Settings changed (no code edits)
All changed with `scripts/deploy.sh --yes --skip-build --var NAME=VALUE`:
- `backend_send_loss` = 0, 10, 20, 30 for Experiments 1 and 2
- (add any others you change, e.g. `max_inflight`)

## Code changes
(If you made none, write "None.")

Example, if you make the optional logging change:
- **File:** `transfer-client/udp/udp-client.go`, in `Fetch`
- **Change:** the retry log line printed every missing chunk ID. I replaced it with one line
  per round showing the file, round number, and how many chunks were missing.
- **Why:** at high loss a 1 MB file can be missing thousands of chunks, which made each log
  line huge. A count per round lets me see how many retry rounds each download needed.
