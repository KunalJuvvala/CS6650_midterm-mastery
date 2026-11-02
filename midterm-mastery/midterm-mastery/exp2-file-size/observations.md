# Experiment 2: How does file size affect speed and reliability?

## Question
With everything else fixed, how do download time and success change as files grow
toward (and past) the 4 MiB limit?

## Setup
| Changed | File size: 1 KB, 64 KB, 256 KB, 1 MB, 2 MB, 4 MB, and 4 MB + 64 bytes (over the limit) |
|---|---|
| Kept fixed | Default retries and scaling, `max_inflight` = 4, `backend_recv_loss` = 0 |
| Loss settings | Run at `backend_send_loss` = 0 and 10 (reusing the Experiment 1 deploys) |
| Tries | 10 per file per setting, one at a time (no load) |
| Tool | `scripts/fetch_test.py`, charts with `scripts/plot_results.py --by-file` |

## Prediction (written before running)
- Time grows with file size: a 4 MB file is 65,536 datagrams, plus the 2 s quiet-timeout floor.
- At 0% configured loss, large files may still need retries, because a burst of tens of
  thousands of datagrams can overflow socket buffers (real loss the setting doesn't control).
- At 10% loss, larger files are more likely to fail (more chunks that can each be lost).
- The over-limit file fails every time: the client rejects more than 65,536 chunks.

## Results
| File | Chunks | 0% loss success | 0% loss median | 10% loss success | 10% loss median |
|---|---|---|---|---|---|
| 1 KB | 16 | | | | |
| 64 KB | 1,024 | | | | |
| 256 KB | 4,096 | | | | |
| 1 MB | 16,384 | | | | |
| 2 MB | 32,768 | | | | |
| 4 MB | 65,536 | | | | |
| over limit | 65,537 | | | | |

Throughput (MB/s) = file size / median time. Charts: `success_rate.png`, `median_time.png`.

## Observations
- (Which status code did the over-limit file return, and how fast?)
- (Did large files need retries even at 0% configured loss? Check the gateway logs.)

## What it reveals about the service
- (e.g. 64-byte chunks make big files expensive: tiny payload per datagram, huge datagram count)
