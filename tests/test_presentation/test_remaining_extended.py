import logging
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from flowscope.presentation.main import _configure_logging, _MillisecondFormatter
from flowscope.presentation.shortcuts import _create_desktop_shortcut, _desktop_path


def _local(created: float) -> datetime:
    return datetime.fromtimestamp(created, tz=timezone.utc).astimezone()


class TestMillisecondFormatter:
    def _record(self, created: float, microsecond: int) -> logging.LogRecord:
        record = logging.LogRecord("test", logging.INFO, "module.py", 10, "msg", (), None)
        record.created = created
        record.msecs = microsecond / 1000.0
        return record

    def test_default_datefmt(self):
        formatter = _MillisecondFormatter()
        record = self._record(1780000000.0, 123000)
        out = formatter.formatTime(record)
        assert out == _local(1780000000.0).strftime("%Y-%m-%d %H:%M:%S")

    def test_utc_conversion(self):
        formatter = _MillisecondFormatter()
        record = self._record(0.0, 0)
        out = formatter.formatTime(record)
        assert out == _local(0.0).strftime("%Y-%m-%d %H:%M:%S")

    def test_milliseconds_replaced(self):
        formatter = _MillisecondFormatter()
        record = self._record(1780000000.123, 123456)
        base = _local(1780000000.123).strftime("%Y-%m-%d %H:%M:%S")
        out = formatter.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S,%f")
        assert out == f"{base},123"

    def test_custom_datefmt_without_f(self):
        formatter = _MillisecondFormatter()
        record = self._record(1780000000.0, 123456)
        out = formatter.formatTime(record, datefmt="%H:%M")
        assert len(out) == 5


class TestConfigureLoggingArgs:
    def test_mkdir_with_parents(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch("flowscope.presentation.main.Path.mkdir") as mock_mkdir:
                with patch("flowscope.presentation.main.RotatingFileHandler", return_value=MagicMock()):
                    with patch("flowscope.presentation.main.logging.basicConfig"):
                        _configure_logging()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_rotating_file_handler_args(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch(
                "flowscope.presentation.main.RotatingFileHandler",
                return_value=MagicMock(),
            ) as mock_handler:
                with patch("flowscope.presentation.main.logging.basicConfig"):
                    with patch("flowscope.presentation.main.SysLogHandler", side_effect=OSError):
                        _configure_logging()
        mock_handler.assert_called_once()
        args, kwargs = mock_handler.call_args
        assert str(args[0]).endswith("flowscope.log")
        assert kwargs["maxBytes"] == 1_000_000
        assert kwargs["backupCount"] == 3

    def test_basic_config_level(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch("flowscope.presentation.main.RotatingFileHandler", return_value=MagicMock()):
                with patch("flowscope.presentation.main.logging.basicConfig") as mock_config:
                    with patch("flowscope.presentation.main.SysLogHandler", side_effect=OSError):
                        _configure_logging()
        mock_config.assert_called_once()
        assert mock_config.call_args.kwargs["level"] == logging.WARNING


class TestShortcutsArgs:
    def test_desktop_path_uses_xdg(self):
        result = MagicMock()
        result.returncode = 0
        result.stdout = "/home/user/Desktop\n"
        with patch("flowscope.presentation.shortcuts.subprocess.run", return_value=result) as mock_run:
            path = _desktop_path()
        mock_run.assert_called_once_with(
            ["xdg-user-dir", "DESKTOP"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        assert str(path) == "/home/user/Desktop"

    def test_create_shortcut_mkdir_and_copy(self, tmp_path):
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()
        fake_exe = tmp_path / "flowscope"
        fake_exe.write_text("")
        with (
            patch("platform.system", return_value="Linux"),
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("sys.argv", [str(fake_exe)]),
            patch("flowscope.presentation.shortcuts._desktop_path", return_value=desktop_dir),
            patch("flowscope.presentation.shortcuts.shutil.copy2") as mock_copy,
            patch("flowscope.presentation.shortcuts.Path.mkdir") as mock_mkdir,
        ):
            result = _create_desktop_shortcut()
        assert result is True
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_copy.assert_called_once()

    def test_create_shortcut_writes_utf8_and_chmod(self, tmp_path):
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()
        fake_exe = tmp_path / "flowscope"
        fake_exe.write_text("")
        with (
            patch("platform.system", return_value="Linux"),
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("sys.argv", [str(fake_exe)]),
            patch("flowscope.presentation.shortcuts.shutil.copy2"),
            patch("flowscope.presentation.shortcuts._desktop_path", return_value=desktop_dir),
            patch("flowscope.presentation.shortcuts.Path.write_text") as mock_write,
            patch("flowscope.presentation.shortcuts.Path.chmod") as mock_chmod,
        ):
            result = _create_desktop_shortcut()
        assert result is True
        mock_write.assert_called_once()
        assert mock_write.call_args.kwargs["encoding"] == "utf-8"
        mock_chmod.assert_called_once_with(0o755)


def test_millisecond_formatter_real():
    formatter = _MillisecondFormatter()
    record = logging.LogRecord("test", logging.INFO, "m.py", 1, "x", (), None)
    record.created = datetime(2026, 6, 25, 12, 0, 0).timestamp()
    record.msecs = 999
    out = formatter.formatTime(record)
    assert out == _local(record.created).strftime("%Y-%m-%d %H:%M:%S")
