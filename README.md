# adhoctools

Small, self-contained Python utilities. No packaging or dependencies beyond Python 3 (standard library only).

## Contents

### `all.py`

Interactive terminal menu that lists other `.py` files in this directory and **one level of subdirectories** (excluding itself), up to 40 entries, then runs the one you pick with the same Python interpreter. Includes single-key shortcuts, clear/rediscover, and colored output if the terminal supports ANSI (on Windows it tries to enable VT processing).

**Use when:** You keep several scripts in one folder and want a quick picker without typing paths.

**OS:** **Windows** (console with optional ANSI) and **Unix-like** systems (Linux, macOS, etc.) with a TTY for raw single-key input. Unsuitable for non-interactive or dumb terminals that cannot do single-character reads.

**Run:** `python all.py`

---

### `cputest.py`

Runs a short multi-process floating-point loop on all logical CPUs, prints an aggregate throughput figure and a normalized “relative score” (calibrated in the script so ~1000 matches a typical mid-range laptop in the author’s baseline).

**Use when:** You want a crude, same-machine or same-interpreter comparison of CPU throughput (e.g. laptop vs. VPS), not a rigorous benchmark suite.

**OS:** Runs anywhere **Python 3** runs with working `multiprocessing` (Windows, macOS, Linux, and most other CPython targets). Uses process pools; on Windows the usual `freeze_support()` guard is present for frozen executables.

**Run:** `python cputest.py`
