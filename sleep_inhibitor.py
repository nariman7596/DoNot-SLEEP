#!/usr/bin/env python3
"""Keep the computer awake by nudging the mouse cursor every 30 seconds.

Most operating systems reset their idle/sleep timer whenever the mouse moves.
This script performs a tiny, harmless cursor movement on a fixed interval so
the machine treats the session as active and does not go to sleep.

Usage:
    python sleep_inhibitor.py                # move every 30 seconds
    python sleep_inhibitor.py --interval 60  # move every 60 seconds

Press Ctrl+C to stop.

Requires the `pyautogui` package:
    pip install pyautogui
"""

import argparse
import sys
import time

try:
    import pyautogui
except ImportError:
    sys.exit(
        "Missing dependency 'pyautogui'.\n"
        "Install it with:  pip install pyautogui"
    )

# pyautogui raises FailSafeException if the cursor hits a screen corner.
# We move by only 1px and back, so disable the fail-safe to avoid surprises.
pyautogui.FAILSAFE = False


def jiggle() -> None:
    """Nudge the cursor 1px and return it, so the OS registers activity."""
    x, y = pyautogui.position()
    # Move a single pixel then back to the original spot. The net position is
    # unchanged, but the OS sees movement and resets its idle timer.
    pyautogui.moveRel(1, 0, duration=0)
    pyautogui.moveTo(x, y, duration=0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Move the mouse cursor periodically to prevent the "
        "computer from sleeping."
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=30.0,
        help="Seconds between cursor movements (default: 30).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    interval = args.interval

    print(
        f"Sleep inhibitor running: nudging the cursor every {interval:g} "
        "seconds.\nPress Ctrl+C to stop."
    )

    try:
        while True:
            jiggle()
            print(f"[{time.strftime('%H:%M:%S')}] cursor nudged", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped. The computer can sleep normally again.")


if __name__ == "__main__":
    main()
