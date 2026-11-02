# Experiment 1: How much packet loss can the service survive?

## Question
As the backend drops more of the UDP datagrams it sends, how do the success rate and the
time per download change?

## Setup
| Changed | `backend_send_loss`: 0, 10, 20, 30 (%) |
|---|---|
| Kept fixed | `backend_recv_loss` = 0, default retries (5 OPEN attempts, 5 RETY rounds, 2 s quiet timeout), default scaling, `max_inflight` = 4 |
| Files | `size-64k.txt` (1,024 chunks) and `size-1m.txt` (16,384 chunks) |
| Tries | 20 per file per setting, one at a time (no load) |
| Tool | `scripts/fetch_test.py`, charts from `scripts/plot_results.py` |

Deploy command per setting: `scripts/deploy.sh --yes --skip-build --var backend_send_loss=<N>`

## Prediction (written before running)
A chunk is lost for good only if the first send **and** all 5 retries are dropped, which
happens with probability p^6. A file of N chunks succeeds with probability about (1 - p^6)^N.
This simple model ignores lost OPEN messages and real network loss.

| Send loss | 64 KB predicted | 1 MB predicted |
|---|---|---|
| 0% | 100% | 100% |
| 10% | ~100% | ~98% |
| 20% | ~94% | ~35% |
| 30% | ~47% | ~0% |

Also predicted: every successful download takes **at least ~2 s**, because the client only
decides the server is done after 2 s of silence. Each extra retry round adds about 2 s more.

## Results
| Send loss | 64 KB success | 64 KB median | 1 MB success | 1 MB median |
|---|---|---|---|---|
| 0% | | | | |
| 10% | | | | |
| 20% | | | | |
| 30% | | | | |

Charts: `success_rate.png`, `median_time.png`. Raw data: `results.csv`.
Screenshots: `screenshots/`

## Observations
- (What happened? Did it match the prediction? Where was the "cliff"?)
- (Which status codes appeared on failure: 504? Anything else?)

## What it reveals about the service
- (e.g. the fixed retry budget handles mild loss but collapses for larger files at heavy loss)
