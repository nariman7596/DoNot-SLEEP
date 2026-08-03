#!/usr/bin/env python3
"""keepawake - keep your Mac (or any computer) awake. Single-file, no install.

On a Mac this uses the built-in `caffeinate` tool, so there is nothing to
install - just open a Terminal and run it:

    python3 keepawake.py                 # stay awake until you press Ctrl+C
    python3 keepawake.py --duration 3600 # stay awake for 1 hour, then stop
    python3 keepawake.py --display       # also keep the screen/display on
    python3 keepawake.py --version

Optional "cursor" mode nudges the mouse instead (needs `pip install pyautogui`):

    python3 keepawake.py --mode cursor            # nudge every 30 seconds
    python3 keepawake.py --mode cursor -i 60      # nudge every 60 seconds

Press Ctrl+C to stop (when no --duration is given).

This is the whole DoNot-SLEEP project in one file - handy for dropping onto a
Mac mini. Platforms supported: macOS (caffeinate), Windows
(SetThreadExecutionState), Linux (systemd-inhibit).
"""

import argparse
import ctypes
import shutil
import subprocess
import sys
import time

__version__ = "1.0.0"


class NativeInhibitor:
    """Keep the OS awake via its native power API. Usable as a context manager."""

    def __init__(self, keep_display_on: bool = False):
        self.keep_display_on = keep_display_on
        self._process = None
        self._platform = sys.platform

    def _start_macos(self) -> str:
        cmd = ["caffeinate", "-i"]  # -i: prevent idle system sleep
        if self.keep_display_on:
            cmd.append("-d")  # -d: prevent the display from sleeping
        self._process = subprocess.Popen(cmd)
        return "caffeinate"

    def _start_windows(self) -> str:
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002

        flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        if self.keep_display_on:
            flags |= ES_DISPLAY_REQUIRED

        result = ctypes.windll.kernel32.SetThreadExecutionState(flags)
        if result == 0:
            raise OSError("SetThreadExecutionState failed to inhibit sleep.")
        return "SetThreadExecutionState"

    def _start_linux(self) -> str:
        if shutil.which("systemd-inhibit") is None:
            raise RuntimeError(
                "systemd-inhibit not found. On Linux, native mode relies on "
                "systemd. Try:  python3 keepawake.py --mode cursor"
            )
        what = "idle:sleep" if self.keep_display_on else "sleep"
        cmd = [
            "systemd-inhibit",
            f"--what={what}",
            "--who=keepawake",
            "--why=Keep the computer awake",
            "--mode=block",
            "sleep",
            "infinity",
        ]
        self._process = subprocess.Popen(cmd)
        return "systemd-inhibit"

    def start(self) -> str:
        """Begin inhibiting sleep. Returns the mechanism name used."""
        if self._platform == "darwin":
            return self._start_macos()
        if self._platform == "win32":
            return self._start_windows()
        if self._platform.startswith("linux"):
            return self._start_linux()
        raise RuntimeError(f"Unsupported platform: {self._platform}")

    def stop(self) -> None:
        """Release the sleep inhibitor and restore normal power behavior."""
        if self._platform == "win32":
            ES_CONTINUOUS = 0x80000000
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            return
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def __enter__(self) -> "NativeInhibitor":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()


def run_native(args: argparse.Namespace) -> None:
    inhibitor = NativeInhibitor(keep_display_on=args.display)
    try:
        mechanism = inhibitor.start()
    except (RuntimeError, OSError) as exc:
        sys.exit(f"Error: {exc}")

    scope = "system and display" if args.display else "system"
    print(f"Sleep inhibited ({scope}) via {mechanism}.")

    try:
        if args.duration is not None:
            print(f"Staying awake for {args.duration:g} seconds...")
            time.sleep(args.duration)
        else:
            print("Staying awake. Press Ctrl+C to stop.")
            while True:
                time.sleep(3600)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        inhibitor.stop()
        print("Sleep inhibitor released. The computer can sleep normally again.")


def run_cursor(args: argparse.Namespace) -> None:
    try:
        import pyautogui
    except ImportError:
        sys.exit(
            "Cursor mode needs the 'pyautogui' package.\n"
            "Install it with:  pip install pyautogui\n"
            "Or use native mode:  python3 keepawake.py --mode native"
        )

    # We move by only 1px and back, so disable the corner fail-safe.
    pyautogui.FAILSAFE = False
    interval = args.interval

    print(
        f"Sleep inhibited (cursor mode): nudging the cursor every "
        f"{interval:g} seconds.\nPress Ctrl+C to stop."
    )

    deadline = None if args.duration is None else time.monotonic() + args.duration
    try:
        while True:
            x, y = pyautogui.position()
            pyautogui.moveRel(1, 0, duration=0)
            pyautogui.moveTo(x, y, duration=0)
            print(f"[{time.strftime('%H:%M:%S')}] cursor nudged", flush=True)

            if deadline is not None and time.monotonic() >= deadline:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    print("\nStopped. The computer can sleep normally again.")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="keepawake",
        description="Keep the computer awake using a native OS power API "
        "(caffeinate on macOS) or by nudging the mouse cursor.",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-m", "--mode", choices=["native", "cursor"], default="native",
        help="Strategy to use (default: native).",
    )
    parser.add_argument(
        "-d", "--duration", type=float, default=None,
        help="How long to stay awake, in seconds. Default: until Ctrl+C.",
    )
    parser.add_argument(
        "-i", "--interval", type=float, default=30.0,
        help="Cursor mode only: seconds between nudges (default: 30).",
    )
    parser.add_argument(
        "--display", action="store_true",
        help="Native mode only: also keep the display awake.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    if args.mode == "cursor":
        run_cursor(args)
    else:
        run_native(args)


if __name__ == "__main__":
    main()
