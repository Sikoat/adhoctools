#!/usr/bin/env python3
"""
Cross-platform CPU floating-point throughput benchmark (relative score).

Uses one worker process per logical CPU so results reflect multi-core throughput.
Python is adequate for comparing laptop vs VPS *relative* compute: both run the
same bytecode-heavy workload; Rust would mainly raise absolute MFLOPS, not change
rankings much for this style of test.
"""

from __future__ import annotations

import math
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed


DURATION_SEC = 10.0

# Total scalar FP ops per inner-loop iteration (each mul/add counts as one).
# Keep this in sync with the body of _worker_loop (9 fused mul-add chains × 3).
FLOPS_PER_ITER = 27

# Calibration target: score ~1000 on a typical mid-range laptop (~6--8 logical cores,
# CPython). Increase this constant if your baseline reads high; decrease if low.
REFERENCE_AGGREGATE_FLOPS_PER_SEC = 360_000_000


def round_to_n_sigfigs(x: float, n: int = 3) -> float:
    """Round positive x to n significant figures."""
    if x <= 0 or not math.isfinite(x):
        return x
    mag = math.floor(math.log10(x))
    decimals = n - 1 - mag
    return round(x, int(decimals))


def _worker_loop(end_mono: float) -> int:
    """
    Tight FP loop until perf_counter() >= end_mono.
    Returns accumulated FLOP count (iterations * FLOPS_PER_ITER).
    """
    # Avoid NaN/inf from runaway growth while keeping dependency chains hot.
    x = 1.0000001
    y = 1.0000002
    z = 1.0000003
    iters = 0
    while time.perf_counter() < end_mono:
        x = x * 1.0000007 + y * 0.9999998
        y = y * 1.0000011 + z * 1.0000013
        z = z * 0.9999993 + x * 1.0000019
        x = x * 1.0000023 + z * 0.9999987
        y = y * 0.9999979 + x * 1.0000041
        z = z * 1.0000053 + y * 0.9999961
        x = x * 0.9999959 + y * 1.0000067
        y = y * 1.0000077 + z * 0.9999949
        z = z * 0.9999939 + x * 1.0000089
        iters += 1
    return iters * FLOPS_PER_ITER


def _worker_entry(duration: float) -> int:
    """Runs one worker for ~`duration` seconds (spawn-safe on Windows)."""
    end_mono = time.perf_counter() + duration
    return _worker_loop(end_mono)


def run_benchmark(num_workers: int, duration: float) -> tuple[float, float]:
    """
    Returns (aggregate_flops_per_second, relative_score).
    Uses wall-clock elapsed while workers each run for `duration` seconds locally.
    """
    start_wall = time.perf_counter()

    total_flops = 0
    with ProcessPoolExecutor(max_workers=num_workers) as ex:
        futures = [ex.submit(_worker_entry, duration) for _ in range(num_workers)]
        for fut in as_completed(futures):
            total_flops += fut.result()

    elapsed = time.perf_counter() - start_wall
    flops_per_sec = total_flops / elapsed if elapsed > 0 else float("nan")
    relative = 1000.0 * (flops_per_sec / REFERENCE_AGGREGATE_FLOPS_PER_SEC)
    return flops_per_sec, relative


def main() -> int:
    n = os.cpu_count() or 1

    print(f"cputest: logical CPUs (worker processes): {n}")
    print(f"cputest: running floating-point workload for {DURATION_SEC:.0f} s ...")
    sys.stdout.flush()

    flops_per_sec, score = run_benchmark(n, DURATION_SEC)

    flops_display = round_to_n_sigfigs(flops_per_sec, 3)
    score_display = round_to_n_sigfigs(score, 3)

    print()
    print(f"Aggregate FP throughput (relative FLOPS basis): {flops_display:g} ops/s")
    print(f"Relative compute score (~1000 on a typical laptop): {score_display:g}")
    return 0


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
