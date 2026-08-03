"""Unit tests for the keep-awake CLI.

Runnable with either:
    python -m unittest discover
    pytest
"""

import sys
import types
import unittest
from unittest import mock

import keep_awake
from keep_awake import cli


# --------------------------------------------------------------------------
# Argument parsing
# --------------------------------------------------------------------------
class ParseArgsTests(unittest.TestCase):
    def test_defaults(self):
        args = cli.parse_args([])
        self.assertEqual(args.mode, "native")
        self.assertIsNone(args.duration)
        self.assertEqual(args.interval, 30.0)
        self.assertFalse(args.display)

    def test_mode_and_interval(self):
        args = cli.parse_args(["--mode", "cursor", "--interval", "60"])
        self.assertEqual(args.mode, "cursor")
        self.assertEqual(args.interval, 60.0)

    def test_short_flags(self):
        args = cli.parse_args(["-m", "cursor", "-i", "5", "-d", "10"])
        self.assertEqual(args.mode, "cursor")
        self.assertEqual(args.interval, 5.0)
        self.assertEqual(args.duration, 10.0)

    def test_display_flag(self):
        self.assertTrue(cli.parse_args(["--display"]).display)

    def test_invalid_mode_exits(self):
        with self.assertRaises(SystemExit):
            cli.parse_args(["--mode", "bogus"])

    def test_version_flag_prints_and_exits(self):
        with mock.patch.object(sys, "stdout") as out:
            with self.assertRaises(SystemExit) as ctx:
                cli.parse_args(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        printed = "".join(c.args[0] for c in out.write.call_args_list)
        self.assertIn(keep_awake.__version__, printed)


# --------------------------------------------------------------------------
# main() dispatch
# --------------------------------------------------------------------------
class MainDispatchTests(unittest.TestCase):
    def test_dispatches_to_native_by_default(self):
        with mock.patch.object(cli, "run_native") as native, mock.patch.object(
            cli, "run_cursor"
        ) as cursor:
            cli.main([])
        native.assert_called_once()
        cursor.assert_not_called()

    def test_dispatches_to_cursor(self):
        with mock.patch.object(cli, "run_native") as native, mock.patch.object(
            cli, "run_cursor"
        ) as cursor:
            cli.main(["--mode", "cursor"])
        cursor.assert_called_once()
        native.assert_not_called()


# --------------------------------------------------------------------------
# NativeInhibitor
# --------------------------------------------------------------------------
class NativeInhibitorTests(unittest.TestCase):
    def _make(self, platform, **kwargs):
        inhibitor = cli.NativeInhibitor(**kwargs)
        inhibitor._platform = platform
        return inhibitor

    def test_linux_start_builds_systemd_command(self):
        inhibitor = self._make("linux")
        with mock.patch.object(cli.shutil, "which", return_value="/usr/bin/systemd-inhibit"), \
             mock.patch.object(cli.subprocess, "Popen") as popen:
            mechanism = inhibitor.start()
        self.assertEqual(mechanism, "systemd-inhibit")
        cmd = popen.call_args.args[0]
        self.assertEqual(cmd[0], "systemd-inhibit")
        self.assertIn("--what=sleep", cmd)

    def test_linux_display_sets_idle_sleep(self):
        inhibitor = self._make("linux", keep_display_on=True)
        with mock.patch.object(cli.shutil, "which", return_value="/usr/bin/systemd-inhibit"), \
             mock.patch.object(cli.subprocess, "Popen") as popen:
            inhibitor.start()
        cmd = popen.call_args.args[0]
        self.assertIn("--what=idle:sleep", cmd)

    def test_linux_missing_systemd_raises(self):
        inhibitor = self._make("linux")
        with mock.patch.object(cli.shutil, "which", return_value=None):
            with self.assertRaises(RuntimeError):
                inhibitor.start()

    def test_macos_start_uses_caffeinate(self):
        inhibitor = self._make("darwin")
        with mock.patch.object(cli.subprocess, "Popen") as popen:
            mechanism = inhibitor.start()
        self.assertEqual(mechanism, "caffeinate")
        self.assertEqual(popen.call_args.args[0], ["caffeinate", "-i"])

    def test_macos_display_adds_d_flag(self):
        inhibitor = self._make("darwin", keep_display_on=True)
        with mock.patch.object(cli.subprocess, "Popen") as popen:
            inhibitor.start()
        self.assertEqual(popen.call_args.args[0], ["caffeinate", "-i", "-d"])

    def test_windows_start_calls_set_thread_execution_state(self):
        inhibitor = self._make("win32")
        fake_ctypes = mock.MagicMock()
        fake_ctypes.windll.kernel32.SetThreadExecutionState.return_value = 1
        with mock.patch.object(cli, "ctypes", fake_ctypes):
            mechanism = inhibitor.start()
        self.assertEqual(mechanism, "SetThreadExecutionState")
        fake_ctypes.windll.kernel32.SetThreadExecutionState.assert_called()

    def test_windows_failure_raises_oserror(self):
        inhibitor = self._make("win32")
        fake_ctypes = mock.MagicMock()
        fake_ctypes.windll.kernel32.SetThreadExecutionState.return_value = 0
        with mock.patch.object(cli, "ctypes", fake_ctypes):
            with self.assertRaises(OSError):
                inhibitor.start()

    def test_unsupported_platform_raises(self):
        inhibitor = self._make("sunos")
        with self.assertRaises(RuntimeError):
            inhibitor.start()

    def test_stop_terminates_process(self):
        inhibitor = self._make("linux")
        proc = mock.MagicMock()
        inhibitor._process = proc
        inhibitor.stop()
        proc.terminate.assert_called_once()
        proc.wait.assert_called_once()
        self.assertIsNone(inhibitor._process)

    def test_stop_kills_on_timeout(self):
        inhibitor = self._make("linux")
        proc = mock.MagicMock()
        proc.wait.side_effect = cli.subprocess.TimeoutExpired(cmd="x", timeout=5)
        inhibitor._process = proc
        inhibitor.stop()
        proc.kill.assert_called_once()

    def test_stop_windows_clears_flag(self):
        inhibitor = self._make("win32")
        fake_ctypes = mock.MagicMock()
        with mock.patch.object(cli, "ctypes", fake_ctypes):
            inhibitor.stop()
        fake_ctypes.windll.kernel32.SetThreadExecutionState.assert_called_once()

    def test_context_manager_starts_and_stops(self):
        inhibitor = self._make("linux")
        with mock.patch.object(inhibitor, "start") as start, \
             mock.patch.object(inhibitor, "stop") as stop:
            with inhibitor as ret:
                self.assertIs(ret, inhibitor)
                start.assert_called_once()
                stop.assert_not_called()
            stop.assert_called_once()


# --------------------------------------------------------------------------
# run_native
# --------------------------------------------------------------------------
class RunNativeTests(unittest.TestCase):
    def test_start_error_exits(self):
        args = cli.argparse.Namespace(display=False, duration=None)
        with mock.patch.object(cli.NativeInhibitor, "start",
                               side_effect=RuntimeError("no systemd")):
            with self.assertRaises(SystemExit):
                cli.run_native(args)

    def test_duration_sleeps_then_stops(self):
        args = cli.argparse.Namespace(display=False, duration=2.0)
        with mock.patch.object(cli.NativeInhibitor, "start", return_value="caffeinate"), \
             mock.patch.object(cli.NativeInhibitor, "stop") as stop, \
             mock.patch.object(cli.time, "sleep") as sleep:
            cli.run_native(args)
        sleep.assert_called_once_with(2.0)
        stop.assert_called_once()

    def test_keyboard_interrupt_still_stops(self):
        args = cli.argparse.Namespace(display=False, duration=None)
        with mock.patch.object(cli.NativeInhibitor, "start", return_value="caffeinate"), \
             mock.patch.object(cli.NativeInhibitor, "stop") as stop, \
             mock.patch.object(cli.time, "sleep", side_effect=KeyboardInterrupt):
            cli.run_native(args)
        stop.assert_called_once()


# --------------------------------------------------------------------------
# run_cursor
# --------------------------------------------------------------------------
class RunCursorTests(unittest.TestCase):
    def _fake_pyautogui(self):
        module = types.ModuleType("pyautogui")
        module.FAILSAFE = True
        module.position = mock.MagicMock(return_value=(100, 200))
        module.moveRel = mock.MagicMock()
        module.moveTo = mock.MagicMock()
        return module

    def test_missing_pyautogui_exits(self):
        args = cli.argparse.Namespace(duration=None, interval=30.0)
        with mock.patch.dict(sys.modules, {"pyautogui": None}):
            with self.assertRaises(SystemExit):
                cli.run_cursor(args)

    def test_nudges_cursor_and_restores_position(self):
        args = cli.argparse.Namespace(duration=0.0, interval=30.0)
        fake = self._fake_pyautogui()
        with mock.patch.dict(sys.modules, {"pyautogui": fake}), \
             mock.patch.object(cli.time, "sleep") as sleep:
            cli.run_cursor(args)
        # One nudge happened, and the cursor was returned to its origin.
        fake.moveRel.assert_called_once_with(1, 0, duration=0)
        fake.moveTo.assert_called_once_with(100, 200, duration=0)
        # duration=0 means it breaks before sleeping.
        sleep.assert_not_called()
        self.assertFalse(fake.FAILSAFE)

    def test_keyboard_interrupt_is_handled(self):
        args = cli.argparse.Namespace(duration=None, interval=30.0)
        fake = self._fake_pyautogui()
        fake.moveRel.side_effect = KeyboardInterrupt
        with mock.patch.dict(sys.modules, {"pyautogui": fake}):
            cli.run_cursor(args)  # should not raise


if __name__ == "__main__":
    unittest.main()
