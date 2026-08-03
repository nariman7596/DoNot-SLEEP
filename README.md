# DoNot-SLEEP

A single Python utility, `keep_awake.py`, that keeps your computer awake. It
offers two strategies selectable with `--mode`:

1. **`native`** (default) — asks the operating system directly to stay awake
   using its built-in power API. Robust, headless-friendly, and doesn't touch
   the mouse. No third-party dependencies.
2. **`cursor`** — nudges the mouse cursor on a fixed interval (30 seconds by
   default) so the OS idle timer keeps resetting. Requires `pyautogui`.

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

## Requirements

- Python 3.7+
- Native mode: **no dependencies** (standard library only)
- Cursor mode: [`pyautogui`](https://pypi.org/project/pyautogui/)

Install the optional cursor-mode dependency:

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Native mode, stay awake until Ctrl+C (default)
python keep_awake.py

# Native mode for a fixed duration (e.g. 1 hour)
python keep_awake.py --duration 3600

# Native mode, also keep the display/screen on
python keep_awake.py --display

# Cursor mode, nudge every 30 seconds (default interval)
python keep_awake.py --mode cursor

# Cursor mode with a custom interval, e.g. every 60 seconds
python keep_awake.py --mode cursor --interval 60
```

Press `Ctrl+C` to stop (when no `--duration` is given). Once stopped, the
computer can sleep normally again.

### Options

| Flag | Applies to | Description |
| ---- | ---------- | ----------- |
| `-m`, `--mode {native,cursor}` | both | Strategy to use (default: `native`). |
| `-d`, `--duration SECONDS` | both | Stay awake for a fixed time, then exit. |
| `-i`, `--interval SECONDS` | cursor | Seconds between cursor nudges (default: 30). |
| `--display` | native | Also keep the display awake, not just the system. |

> **Linux notes:** Native mode relies on `systemd-inhibit` (systemd). Cursor
> mode's `pyautogui` needs an X11 display and won't work on Wayland or
> headless systems.
