#!/usr/bin/env python3
"""
fetch_test.py - fetch files from the gateway several times and record every result.

Used for Experiment 1 (packet loss) and Experiment 2 (file size).
Uses only the Python standard library, so there is nothing to install.

Example (after deploying with 10% send loss):
  python3 scripts/fetch_test.py \
      --url http://<gateway address> \
      --files size-64k.txt size-1m.txt \
      --tries 20 \
      --label send_loss=10 \
      --local-dir test-files \
      --out exp1-packet-loss/results.csv

Each run APPENDS rows to --out, so run it once per setting and keep one CSV.
Columns: timestamp, label, file, try, status, ok, ms, bytes, expected_bytes, error
  ok = 1 only if the status was 200 AND the file came back at the right size.
"""
import argparse
import csv
import datetime
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request


def fetch(base_url, name, timeout):
    """Fetch one file. Returns (status, elapsed_ms, bytes_received, error_text)."""
    url = f"{base_url.rstrip('/')}/files?name={urllib.parse.quote(name)}"
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
            status = response.status
        error = ""
    except urllib.error.HTTPError as http_error:   # 404, 503, 504 ... still a real answer
        body = http_error.read()
        status = http_error.code
        error = body[:120].decode("utf-8", "replace").strip()
    except Exception as other:                      # timeout, connection refused ...
        return "none", (time.perf_counter() - start) * 1000, 0, type(other).__name__
    return status, (time.perf_counter() - start) * 1000, len(body), error


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", required=True, help="gateway address, e.g. http://my-alb.amazonaws.com")
    parser.add_argument("--files", nargs="+", required=True, help="file names to fetch")
    parser.add_argument("--tries", type=int, default=20, help="fetches per file (default 20)")
    parser.add_argument("--label", required=True, help="what setting this run used, e.g. send_loss=10")
    parser.add_argument("--local-dir", default=None, help="folder with the original files, to check sizes")
    parser.add_argument("--out", required=True, help="CSV file to append results to")
    parser.add_argument("--timeout", type=float, default=70, help="seconds before giving up (default 70)")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    new_file = not os.path.exists(args.out)
    with open(args.out, "a", newline="") as out:
        writer = csv.writer(out)
        if new_file:
            writer.writerow(["timestamp", "label", "file", "try", "status", "ok",
                             "ms", "bytes", "expected_bytes", "error"])

        for name in args.files:
            expected = ""
            if args.local_dir:
                path = os.path.join(args.local_dir, name)
                expected = os.path.getsize(path) if os.path.exists(path) else ""

            times_ok, statuses = [], {}
            for attempt in range(1, args.tries + 1):
                status, ms, size, error = fetch(args.url, name, args.timeout)
                ok = int(status == 200 and (expected == "" or size == expected))
                writer.writerow([datetime.datetime.now().isoformat(timespec="seconds"),
                                 args.label, name, attempt, status, ok,
                                 round(ms), size, expected, error])
                out.flush()
                statuses[status] = statuses.get(status, 0) + 1
                if ok:
                    times_ok.append(ms)
                print(f"  {name} try {attempt:>2}: status={status} ok={ok} {ms:8.0f} ms")

            rate = 100 * len(times_ok) / args.tries
            median = f"{statistics.median(times_ok):.0f} ms" if times_ok else "n/a"
            print(f"[{args.label}] {name}: {rate:.0f}% ok, median {median}, statuses {statuses}\n")


if __name__ == "__main__":
    main()
