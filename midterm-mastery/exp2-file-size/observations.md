# Experiment 2: How does file size affect speed and reliability?

## Question
With everything else fixed, how do download time and success change as files grow
toward (and past) the 4 MiB limit?

## Setup
| Changed | File size: 1 KB, 64 KB, 256 KB, 1 MB, 2 MB, 4 MB, and 4 MB + 64 bytes (over the limit) |
|---|---|
| Kept fixed | `backend_send_loss` = 0, `backend_recv_loss` = 0, default retries (5 OPEN attempts, 5 RETY rounds, 2 s quiet timeout), default scaling (2 gateway + 2 backend tasks), `max_inflight` = 4, `backend_workers` = 8 |
| Tries | 10 per file, one at a time (no other load) |
| Tool | `scripts/fetch_test.py`; charts from `scripts/plot_results.py --by-file` |

## Results (0% configured loss)
| File | Chunks | Success | Median time (successes) | Median time (failures) | Failure status |
|---|---|---|---|---|---|
| 1 KB | 16 | 10/10 (100%) | 2.25 s | - | - |
| 64 KB | 1,024 | 10/10 (100%) | 2.34 s | - | - |
| 256 KB | 4,096 | 3/10 (30%) | 2.62 s | 14.9 s | 504 |
| 1 MB | 16,384 | 2/10 (20%) | 3.35 s | 19.1 s | 504 |
| 2 MB | 32,768 | 3/10 (30%) | 4.10 s | 24.2 s | 504 |
| 4 MB | 65,536 | 1/10 (10%) | 22.1 s | 36.1 s | 504 |
| 4 MB + 64 B | 65,537 | 0/10 (0%) | - | 19.9 s | 504 |

Charts: `success_rate.png`, `median_time.png`. Raw data: `results.csv`.

## Observations
- **Small files are reliable and hit the 2 s floor.** 1 KB and 64 KB never failed, and both took
  about 2.2-2.3 s. Almost all of that is the client waiting 2 s of silence to decide the
  server is finished, not actual transfer time.
- **Files of 256 KB and up mostly failed, even with 0% configured loss.** Success fell to
  10-30% with every failure a 504 "the file server did not respond."
- **Downloads either succeed fast or fail slowly.** A successful 1 MB fetch took 3.3 s, but a
  failed one took 19 s, because the client burned through all 5 retry rounds first.
- **The over-limit file never works, and the error is misleading.** The client throws away
  any datagram announcing more than 65,536 chunks, so it looks like silence. After 5 OPEN
  attempts the gateway reports 504 "did not respond" (about 20 s) instead of a clear
  "file too large" error. Each attempt still makes the backend send all 65,537 datagrams.

## Why large files fail at 0% loss (from reading the code)
1. **Real loss from bursts.** On OPEN, the backend sends every chunk at once: 4,096 datagrams
   for 256 KB, 16,384 for 1 MB. Bursts that large overflow UDP buffers along the way, so
   some chunks are lost even though the loss setting is 0.
2. **Retries are extremely expensive.** In `transfer-server/protocol/server.go`,
   `handleRetry` downloads the **entire file from S3 again and re-chunks it** just to send
   **one** 64-byte chunk. If a 1 MB download is missing 1,000 chunks, the client sends
   1,000 RETY messages and the backend would have to read 1 MB from S3 1,000 times.
3. **The backend drops requests when overloaded.** It has 8 workers and a queue of 32
   (`workers*4`). A burst of thousands of RETY messages fills that queue instantly, and the
   rest are dropped ("Overloaded: dropped incoming datagram"). The retry round comes back
   nearly empty, the client tries again, and after 5 rounds it gives up with a 504.

## What it reveals about the service
- The design scales badly with file size: 64-byte chunks mean a huge datagram count, and
  the retry work grows with (missing chunks x file size).
- The retry mechanism amplifies load exactly when the system is struggling, which turns
  small packet loss into total failure for large files.
- Fixes worth suggesting: cache the file (or its chunks) between OPEN and RETY, batch
  several chunk IDs into one RETY, pace (rate-limit) the initial burst, use bigger chunks,
  and return a clear error for files over the limit.
