"""keep-awake: keep the computer awake via native OS APIs or cursor movement."""

__version__ = "1.0.0"

from .cli import NativeInhibitor, main, run_cursor, run_native

__all__ = ["NativeInhibitor", "main", "run_cursor", "run_native", "__version__"]
