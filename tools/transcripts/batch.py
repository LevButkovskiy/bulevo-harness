#!/usr/bin/env python3
"""Split extracted sessions into size-balanced batches for parallel labeling agents.

Usage:
  python tools/transcripts/batch.py --data .data/stage0 --batches 7
"""
import argparse
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--batches", type=int, default=7)
    args = ap.parse_args()

    with open(os.path.join(args.data, "sessions.jsonl"), encoding="utf-8") as fh:
        ids = [json.loads(line)["session_id"] for line in fh if line.strip()]
    sized = sorted(((os.path.getsize(os.path.join(args.data, "digests", sid + ".md")), sid) for sid in ids), reverse=True)

    bins = [[0, []] for _ in range(max(1, min(args.batches, len(sized))))]
    for size, sid in sized:
        target = min(bins, key=lambda b: b[0])
        target[0] += size
        target[1].append(sid)

    out_dir = os.path.join(args.data, "batches")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(args.data, "labels"), exist_ok=True)
    for i, (size, members) in enumerate(bins, 1):
        with open(os.path.join(out_dir, f"batch-{i}.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(members) + "\n")
        print(f"batch-{i}: {len(members)} sessions, {size // 1024} KB")


if __name__ == "__main__":
    main()
