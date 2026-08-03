# DoNot-SLEEP

`keep-awake` is a small cross-platform CLI that keeps your computer awake. It
offers two strategies selectable with `--mode`:

1. **`native`** (default) — asks the operating system directly to stay awake
   using its built-in power API. Robust, headless-friendly, and doesn't touch
   the mouse. No third-party dependencies.
2. **`cursor`** — nudges the mouse cursor on a fixed interval (30 seconds by
   default) so the OS idle timer keeps resetting. Requires `pyautogui`.

## Install

```bash
# Native mode only (no extra dependencies)
pip install .

# Include cursor mode (pulls in pyautogui)
pip install ".[cursor]"
```

This installs a `keep-awake` command on your PATH. During development you can
use an editable install with `pip install -e ".[cursor]"`.

## Which mode should I use?

Prefer **`native`** — it's the proper way to tell the OS "don't sleep." Use
**`cursor`** if the native APIs aren't available in your environment or you
specifically want the cursor-movement behavior.

## How each mode works

**Native mode** uses each platform's built-in sleep-inhibition mechanism:

| Platform | Mechanism |
| -------- | --------- |
| macOS    | `caffeinate` (built-in CLI tool) |
| Windows  | `SetThreadExecutionState` (via `ctypes`) |
| Linux    | `systemd-inhibit` (requires systemd) |

**Cursor mode** moves the cursor 1 pixel and immediately moves it back to its
original position on each interval. The net cursor position is unchanged, but
the OS registers the movement as activity.

## Usage

```bash
# Native mode, stay awake until Ctrl+C (default)
keep-awake

# Native mode for a fixed duration (e.g. 1 hour)
keep-awake --duration 3600

# Native mode, also keep the display/screen on
keep-awake --display

# Cursor mode, nudge every 30 seconds (default interval)
keep-awake --mode cursor

# Cursor mode with a custom interval, e.g. every 60 seconds
keep-awake --mode cursor --interval 60

# Print the version
keep-awake --version
```

You can also run it without installing:

```bash
python -m keep_awake.cli --mode cursor
```

Press `Ctrl+C` to stop (when no `--duration` is given). Once stopped, the
computer can sleep normally again.

### Options

| Flag | Applies to | Description |
| ---- | ---------- | ----------- |
| `-V`, `--version` | — | Print the version and exit. |
| `-m`, `--mode {native,cursor}` | both | Strategy to use (default: `native`). |
| `-d`, `--duration SECONDS` | both | Stay awake for a fixed time, then exit. |
| `-i`, `--interval SECONDS` | cursor | Seconds between cursor nudges (default: 30). |
| `--display` | native | Also keep the display awake, not just the system. |

> **Linux notes:** Native mode relies on `systemd-inhibit` (systemd). Cursor
> mode's `pyautogui` needs an X11 display and won't work on Wayland or
> headless systems.

## Use as a library

The native inhibitor is also usable as a context manager:

```python
from keep_awake import NativeInhibitor

with NativeInhibitor(keep_display_on=True):
    do_long_running_work()   # the machine stays awake in here
```
