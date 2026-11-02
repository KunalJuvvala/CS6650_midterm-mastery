#!/usr/bin/env python3
"""
plot_results.py - turn a results.csv from fetch_test.py into two charts:
success rate and median time of successful fetches.

Experiment 1 (x-axis = loss setting, one line per file):
  python3 scripts/plot_results.py exp1-packet-loss/results.csv --x-name "Send loss (%)"
Experiment 2 (x-axis = file, sorted by size, one line per loss setting):
  python3 scripts/plot_results.py exp2-file-size/results.csv --by-file --x-name "File"

Needs matplotlib (pip install matplotlib). Saves the PNGs next to the CSV.
"""
import argparse
import csv
import os
import statistics
from collections import defaultdict

import matplotlib.pyplot as plt


def number_in(label):
    """'send_loss=10' -> 10.0 so settings sort numerically."""
    try:
        return float(label.split("=", 1)[-1])
    except ValueError:
        return float("inf")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--x-name", default="Setting")
    parser.add_argument("--by-file", action="store_true",
                        help="x-axis = file (Experiment 2), one line per label")
    args = parser.parse_args()

    with open(args.csv_path) as handle:
        rows = list(csv.DictReader(handle))

    file_size = {r["file"]: int(r["expected_bytes"] or 0) for r in rows}
    groups = defaultdict(list)
    for r in rows:
        key = (r["label"], r["file"]) if args.by_file else (r["file"], r["label"])
        groups[key].append(r)

    if args.by_file:
        lines = sorted({r["label"] for r in rows}, key=number_in)
        xs = sorted({r["file"] for r in rows}, key=lambda f: file_size[f])
    else:
        lines = sorted({r["file"] for r in rows}, key=lambda f: file_size[f])
        xs = sorted({r["label"] for r in rows}, key=number_in)

    out_dir = os.path.dirname(args.csv_path) or "."
    for metric, ylabel, filename in [("rate", "Success rate (%)", "success_rate.png"),
                                     ("median", "Median time, successful fetches (s)", "median_time.png")]:
        plt.figure(figsize=(7, 4))
        for line in lines:
            px, py = [], []
            for x in xs:
                group = groups.get((line, x))
                if not group:
                    continue
                ok_times = [float(r["ms"]) / 1000 for r in group if r["ok"] == "1"]
                if metric == "rate":
                    py.append(100 * len(ok_times) / len(group))
                elif ok_times:
                    py.append(statistics.median(ok_times))
                else:
                    continue
                px.append(x)
            plt.plot(px, py, marker="o", label=line)
        plt.xlabel(args.x_name)
        plt.ylabel(ylabel)
        plt.grid(alpha=0.3)
        plt.legend()
        plt.xticks(rotation=20)
        plt.tight_layout()
        path = os.path.join(out_dir, filename)
        plt.savefig(path, dpi=150)
        plt.close()
        print("saved", path)


if __name__ == "__main__":
    main()
