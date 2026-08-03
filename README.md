# DoNot-SLEEP

Python utilities that keep your computer awake. Two approaches are included:

1. **`sleep_inhibitor.py`** — nudges the mouse cursor every 30 seconds so the
   OS idle timer keeps resetting. Simple and dependency-based (`pyautogui`).
2. **`native_inhibitor.py`** — asks the operating system directly to stay
   awake using its native power APIs. More robust and doesn't touch the mouse.

## Which one should I use?

Prefer **`native_inhibitor.py`** — it's the proper way to tell the OS "don't
sleep," works headlessly, and never moves your cursor. Use
**`sleep_inhibitor.py`** if the native APIs aren't available in your
environment or you specifically want the cursor-movement behavior.

## Cursor-nudging version (`sleep_inhibitor.py`)

`sleep_inhibitor.py` moves the cursor 1 pixel and immediately moves it back to
its original position on a fixed interval (30 seconds by default). The net
cursor position is unchanged, but the OS registers the movement as activity.

## Requirements

- Python 3.7+
- [`pyautogui`](https://pypi.org/project/pyautogui/)

Install the dependency:

```bash
pip install -r requirements.txt
```

> **Linux note:** `pyautogui` needs an X11 display. On Wayland or headless
> systems it may not be able to move the cursor.

## Usage

```bash
# Move the cursor every 30 seconds (default)
python sleep_inhibitor.py

# Use a custom interval, e.g. every 60 seconds
python sleep_inhibitor.py --interval 60
```

Press `Ctrl+C` to stop. Once stopped, the computer can sleep normally again.

## OS-native version (`native_inhibitor.py`)

This version uses each platform's built-in sleep-inhibition mechanism, so no
third-party packages are required:

| Platform | Mechanism |
| -------- | --------- |
| macOS    | `caffeinate` (built-in CLI tool) |
| Windows  | `SetThreadExecutionState` (via `ctypes`) |
| Linux    | `systemd-inhibit` (requires systemd) |

### Usage

```bash
# Stay awake until you press Ctrl+C
python native_inhibitor.py

# Stay awake for a fixed duration (e.g. 1 hour)
python native_inhibitor.py --duration 3600

# Also keep the display/screen on (not just the system)
python native_inhibitor.py --display
```

No dependencies beyond the Python standard library.

> **Linux note:** relies on `systemd-inhibit`. If your system doesn't use
> systemd, fall back to the cursor-nudging version above.
