#!/usr/bin/env python3
"""Keep the computer awake using native OS sleep-inhibition APIs.

Unlike the cursor-jiggling approach, this asks the operating system directly
to stay awake, which is more robust and doesn't perturb the mouse:

    * macOS    -> `caffeinate` (built-in command line tool)
    * Windows  -> SetThreadExecutionState (via ctypes)
    * Linux    -> `systemd-inhibit` (falls back gracefully if unavailable)

Usage:
    python native_inhibitor.py                 # stay awake until Ctrl+C
    python native_inhibitor.py --duration 3600 # stay awake for 1 hour
    python native_inhibitor.py --display        # also keep the screen on

Press Ctrl+C to stop (when no duration is given).
"""

import argparse
import ctypes
import shutil
import subprocess
import sys
import time


class SleepInhibitor:
    """Context manager that keeps the OS awake while active."""

    def __init__(self, keep_display_on: bool = False):
        self.keep_display_on = keep_display_on
        self._process: "subprocess.Popen | None" = None
        self._platform = sys.platform

    # -- platform-specific implementations -------------------------------

    def _start_macos(self) -> str:
        cmd = ["caffeinate", "-i"]  # -i: prevent idle system sleep
        if self.keep_display_on:
            cmd.append("-d")  # -d: prevent the display from sleeping
        self._process = subprocess.Popen(cmd)
        return "caffeinate"

    def _start_windows(self) -> str:
        # Flags for SetThreadExecutionState.
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
                "systemd-inhibit not found. On Linux this script relies on "
                "systemd. Use sleep_inhibitor.py (cursor mode) instead."
            )
        what = "idle:sleep" if self.keep_display_on else "sleep"
        # Hold the inhibitor lock by keeping a long-lived child process alive.
        cmd = [
            "systemd-inhibit",
            f"--what={what}",
            "--who=native_inhibitor.py",
            "--why=Keep the computer awake",
            "--mode=block",
            "sleep",
            "infinity",
        ]
        self._process = subprocess.Popen(cmd)
        return "systemd-inhibit"

    # -- lifecycle -------------------------------------------------------

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

    def __enter__(self) -> "SleepInhibitor":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Keep the computer awake using native OS APIs "
        "(caffeinate / SetThreadExecutionState / systemd-inhibit)."
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=None,
        help="How long to stay awake, in seconds. Default: until Ctrl+C.",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Also keep the display awake (not just the system).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    inhibitor = SleepInhibitor(keep_display_on=args.display)
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


if __name__ == "__main__":
    main()
