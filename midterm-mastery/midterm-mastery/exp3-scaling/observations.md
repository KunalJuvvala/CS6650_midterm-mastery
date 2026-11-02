# Experiment 3: When and how well does the service scale under load?

## Question
Under rising load, when do the gateway and backend scale out, what limits throughput, and
what do users see while scaling happens?

## Setup
| Changed | Number of Locust users over time: 5 -> 15 -> 30 -> 60 -> 5 (4-minute steps) |
|---|---|
| Kept fixed | `size-1k.txt`, 0% loss, default scaling (gateway: 100 requests/min per task, backend: 60% CPU, 2-4 tasks each, 60 s / 120 s cooldowns), `max_inflight` = 4, `backend_workers` = 8 |
| Tool | `scripts/locustfile.py` (StepLoad shape), CloudWatch dashboard, ECS service task counts |

## Prediction (written before running)
- One gateway task runs at most 4 downloads at once (`max_inflight`), and each takes at least
  ~2 s, so one task handles about **2 requests/s (~120/min)**. Two tasks = ~4 req/s, four = ~8 req/s.
- Each Locust user sends about one request every ~3 s (2 s download + ~1 s wait), so about
  12 users fill 2 gateway tasks and about 24 users fill 4.
- The gateway's scaling target (100 requests/min per task) is just under that ~120/min
  ceiling, so scale-out starts right before saturation. With CloudWatch delay plus task
  start-up, expect a few minutes of 503 "gateway is busy" responses at each jump.
- At 60 users even 4 gateway tasks are not enough: steady 503s.
- The backend does little CPU work per request (mostly waiting on the network), so its CPU
  stays low and it may **never scale**, even when users are getting errors.

## Results
| Phase | Users | Requests/s | Failure % (503) | Median / p95 time | Gateway tasks | Backend tasks |
|---|---|---|---|---|---|---|
| 1 | 5 | | | | | |
| 2 | 15 | | | | | |
| 3 | 30 | | | | | |
| 4 | 60 | | | | | |
| 5 | 5 (cool-down) | | | | | |

Also note: time of first scale-out event, time until the new task was serving, time of scale-in.
Files: `locust_report.html`, `locust_stats.csv`, `locust_stats_history.csv`, `screenshots/`

## Observations
- (When did the gateway scale out? How long after load increased?)
- (Did the backend scale? What was its CPU?)

## What it reveals about the service
- (e.g. the gateway bottleneck is MAX_INFLIGHT x the 2 s timeout, not CPU; CPU is the wrong
  scaling metric for the backend)
