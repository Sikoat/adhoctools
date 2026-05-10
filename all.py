#!/usr/bin/env python3
"""
Colorful CLI menu to discover and run sibling .py scripts (this folder + one level of subfolders).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


MAX_SCRIPTS = 40

# Single-key shortcuts (40 keys): digits, lowercase letters, then a few symbols.
SHORTCUTS = list("1234567890abcdefghijklmnopqrstuvwxyz[].;")
assert len(SHORTCUTS) == MAX_SCRIPTS


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _collect_py_files(root: Path) -> tuple[list[Path], int]:
    """All *.py in root and immediate subdirs only; exclude this launcher.

    Returns (list for menu up to MAX_SCRIPTS, total count before capping).
    """
    own = Path(__file__).resolve()
    found: list[Path] = []

    for p in sorted(root.glob("*.py")):
        if p.resolve() != own:
            found.append(p)

    for sub in sorted(d for d in root.iterdir() if d.is_dir()):
        for p in sorted(sub.glob("*.py")):
            if p.resolve() != own:
                found.append(p)

    # Alphabetic order by display label (relative path with forward slashes)
    def sort_key(path: Path) -> str:
        rel = path.relative_to(root)
        return str(rel).replace("\\", "/").lower()

    found.sort(key=sort_key)
    total = len(found)
    return found[:MAX_SCRIPTS], total


def _rel_label(root: Path, path: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def _enable_ansi() -> None:
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _getch() -> str:
    if sys.platform == "win32":
        import msvcrt

        ch = msvcrt.getch()
        if ch in (b"\x03", b"\x04"):  # Ctrl+C, Ctrl+D
            raise KeyboardInterrupt
        if ch == b"\r":
            return "\r"
        if ch == b"\xe0" or ch == b"\x00":  # arrow / function prefix on Windows
            msvcrt.getch()
            return ""
        try:
            return ch.decode("utf-8", errors="replace")
        except Exception:
            return ""
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)
        if ch in (b"\x03", b"\x04"):
            raise KeyboardInterrupt
        if ch == b"\r":
            return "\r"
        return ch.decode("utf-8", errors="replace")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _banner() -> None:
    art = rf"""
{C.CYAN}{C.BOLD} _      _     _     ___    _ _ {C.RESET}
{C.CYAN}{C.BOLD}| |    (_)___| |_  / _ \  | | |{C.RESET}
{C.BLUE}{C.BOLD}| |    | / __| __|/ /_\ \ | | |{C.RESET}
{C.MAGENTA}{C.BOLD}| |____| \__ \ |_|  _  | | | |{C.RESET}
{C.MAGENTA}{C.BOLD}\_____/_|___/\__|_| |_| |_|_|{C.RESET}
{C.DIM}ListAll ("all") · pick a script · run with one key ·{C.RESET}
"""
    print(art)
    
def _print_menu(root: Path, scripts: list[Path], total_py: int) -> None:
    print(f"{C.GREEN}{C.BOLD}Folder:{C.RESET} {root}")
    print()
    if not scripts:
        print(f"{C.YELLOW}No other .py files here (this directory + one level of subfolders).{C.RESET}")
        print(f"{C.DIM}Place scripts nearby or press q to quit.{C.RESET}\n")
        return

    print(f"{C.WHITE}{C.BOLD}Scripts{C.RESET} {C.DIM}(alphabetic){C.RESET}")
    if total_py > MAX_SCRIPTS:
        print(
            f"{C.DIM}Showing first {MAX_SCRIPTS} of {total_py} (key cap).{C.RESET}\n"
        )
    else:
        print()
    for i, path in enumerate(scripts):
        key = SHORTCUTS[i]
        label = _rel_label(root, path)
        pad = " " * (2 - len(key))
        print(
            f"  {C.YELLOW}{C.BOLD}[{key}]{pad}{C.RESET} "
            f"{C.CYAN}{label}{C.RESET}"
        )
    print()
    print(f"  {C.DIM}[q] Quit{C.RESET}   {C.DIM}[r] Rediscover{C.RESET}\n")


def _run_script(path: Path) -> None:
    print(f"\n{C.GREEN}Running{C.RESET} {C.CYAN}{path}{C.RESET} …\n")
    try:
        rc = subprocess.call([sys.executable, str(path)])
    except OSError as e:
        print(f"{C.RED}Could not run:{C.RESET} {e}")
        return
    print(f"\n{C.DIM}Exit code: {rc}{C.RESET}\n")
    print(f"{C.DIM}Press any key to return to the menu…{C.RESET}")
    _getch()


def main() -> None:
    _enable_ansi()
    root = _script_dir()

    while True:
        scripts, total_py = _collect_py_files(root)
        os.system("cls" if sys.platform == "win32" else "clear")
        _banner()
        _print_menu(root, scripts, total_py)

        choice = _getch().lower()
        if choice in ("q", "Q") or choice == "\x1b":  # ESC
            print(f"\n{C.GREEN}Exited.{C.RESET}\n")
            break
        if choice in ("r", "R"):
            continue
        if not scripts:
            continue
        try:
            idx = SHORTCUTS.index(choice)
        except ValueError:
            continue
        if idx >= len(scripts):
            continue
        _run_script(scripts[idx])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Interrupted.{C.RESET}\n")
        sys.exit(130)
