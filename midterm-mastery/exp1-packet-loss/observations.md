# Experiment 1: How much packet loss can the service survive?

## Question
As the backend drops more of the UDP datagrams it sends, how do the success rate and the
time per download change?

## Setup
| Changed | `backend_send_loss`: 0, 10, 20 (%) |
|---|---|
| Kept fixed | `backend_recv_loss` = 0, default retries (5 OPEN attempts, 5 RETY rounds, 2 s quiet timeout), default scaling (2 gateway + 2 backend tasks), `max_inflight` = 4, `backend_workers` = 8 |
| Files | `size-64k.txt` (1,024 chunks) and `size-1m.txt` (16,384 chunks) |
| Tries | 20 per file at 0%, 10 per file at 10% and 20%, one at a time (no other load) |
| Tool | `scripts/fetch_test.py`; deployed each setting with `scripts/deploy.sh --yes --skip-build --var backend_send_loss=<N>` |

## Prediction (written before running)
If retries worked as well as the first send, a chunk would be lost for good only if the
first send and all 5 retries were dropped (probability p^6). A file of N chunks would then
succeed with probability about (1 - p^6)^N.

| Send loss | 64 KB predicted | 1 MB predicted |
|---|---|---|
| 0% | 100% | 100% |
| 10% | ~100% | ~98% |
| 20% | ~94% | ~35% |

## Results
| Send loss | 64 KB success | 64 KB median (successes) | 1 MB success | 1 MB median (successes) | Failure status |
|---|---|---|---|---|---|
| 0% | 18/20 (90%) | 2.4 s | 9/20 (45%) | 6.6 s | 504 |
| 10% | 7/10 (70%) | 10.9 s | 0/10 (0%) | - | 504 |
| 20% | 0/10 (0%) | - | 0/10 (0%) | - | 504 |

Failed downloads took about 13 s (64 KB) and 19 s (1 MB) before the 504.
Charts: `predicted_vs_measured.png`, `success_rate.png`, `median_time.png`. Raw data: `results.csv`.

## Observations
- **The service was far less tolerant of loss than predicted.** At 10% loss the 1 MB file
  never succeeded (predicted ~98%), and at 20% loss even the 64 KB file never succeeded
  (predicted ~94%).
- **Even 0% configured loss was not clean for 1 MB.** Less than half of the 1 MB downloads
  worked, matching Experiment 2: large bursts lose datagrams on their own.
- **Loss made successful downloads much slower.** At 10% loss, successful 64 KB downloads
  took a median of 10.9 s instead of 2.4 s, because each retry round adds at least 2 s of
  waiting.
- **Every failure was a 504 after 13-19 s**, meaning the client used up all its retry
  rounds before giving up.

## Why the prediction was wrong
The prediction assumed retries succeed as easily as the first send. In the code, they don't:
- At 10% loss a 64 KB download is missing ~100 chunks after the first round, so the client
  sends ~100 RETY messages at once.
- The backend has 8 workers and a queue of only 32 messages, so most of that burst is
  dropped ("Overloaded: dropped incoming datagram" in `transfer-server/protocol/server.go`).
- Each RETY that does get through makes the backend download the **whole file from S3
  again** just to send one 64-byte chunk, so the workers stay busy and the queue keeps
  overflowing.
- Each retry round therefore recovers only a small fraction of the missing chunks, and
  5 rounds are not enough.

## What it reveals about the service
- The retry mechanism, which is supposed to provide reliability, is the weak point: it
  turns moderate packet loss into total failure.
- Reliability depends on file size as much as on loss rate, because more chunks means more
  RETY messages competing for a 32-slot queue.
- Fixes worth suggesting: let one RETY ask for many chunk IDs, cache the file between OPEN
  and RETY, enlarge the backend queue, and pace retries instead of sending them all at once.
