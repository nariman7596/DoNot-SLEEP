# DoNot-SLEEP

A tiny Python utility that keeps your computer awake by nudging the mouse
cursor every 30 seconds. Each nudge resets the operating system's idle timer,
so the machine treats the session as active and does not go to sleep.

## How it works

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
