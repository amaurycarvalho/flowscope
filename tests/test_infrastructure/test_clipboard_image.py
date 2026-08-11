from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from flowscope.infrastructure.clipboard_image import (
    ClipboardError,
    copy_image_to_clipboard,
)

EXPECTED_TMP_PATH = Path("/tmp") / "flowscope_chart.png"


def make_figure():
    from matplotlib.figure import Figure

    fig = Figure(figsize=(2, 2))
    fig.add_subplot(111)
    return fig


class TestCopyImageToClipboard:
    @patch("flowscope.infrastructure.clipboard_image.subprocess.run")
    def test_linux_calls_xclip_with_expected_args(self, mock_run):
        with patch("flowscope.infrastructure.clipboard_image.platform.system", return_value="Linux"):
            copy_image_to_clipboard(make_figure())
        mock_run.assert_called_once()
        args = mock_run.call_args.args[0]
        assert args == [
            "xclip",
            "-selection",
            "clipboard",
            "-t",
            "image/png",
            "-i",
            str(EXPECTED_TMP_PATH),
        ]
        assert mock_run.call_args.kwargs["check"] is True

    @patch("flowscope.infrastructure.clipboard_image.subprocess.run")
    def test_macos_calls_osascript_with_expected_args(self, mock_run):
        mock_run.return_value.returncode = 0
        with patch("flowscope.infrastructure.clipboard_image.platform.system", return_value="Darwin"):
            copy_image_to_clipboard(make_figure())
        mock_run.assert_called_once()
        args = mock_run.call_args.args[0]
        assert args[0] == "osascript"
        assert args[1] == "-e"
        assert str(EXPECTED_TMP_PATH) in args[2]
        assert mock_run.call_args.kwargs["capture_output"] is True
        assert mock_run.call_args.kwargs["text"] is True
        assert mock_run.call_args.kwargs["check"] is False

    @patch("flowscope.infrastructure.clipboard_image.subprocess.run")
    def test_macos_nonzero_returncode_raises(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "boom"
        with patch("flowscope.infrastructure.clipboard_image.platform.system", return_value="Darwin"):
            with pytest.raises(ClipboardError, match="boom"):
                copy_image_to_clipboard(make_figure())

    @patch("flowscope.infrastructure.clipboard_image.subprocess.run")
    def test_savefig_called_with_expected_arguments(self, mock_run):
        fig = make_figure()
        with patch("flowscope.infrastructure.clipboard_image.platform.system", return_value="Linux"):
            with patch.object(fig, "savefig") as mock_savefig:
                copy_image_to_clipboard(fig)
        mock_savefig.assert_called_once()
        assert mock_savefig.call_args.args[0] == EXPECTED_TMP_PATH
        assert mock_savefig.call_args.kwargs["format"] == "png"
        assert mock_savefig.call_args.kwargs["dpi"] == 150
        assert mock_savefig.call_args.kwargs["bbox_inches"] == "tight"

    @patch("flowscope.infrastructure.clipboard_image.subprocess.run")
    def test_unsupported_system_raises(self, mock_run):
        with patch("flowscope.infrastructure.clipboard_image.platform.system", return_value="SomeOS"):
            with pytest.raises(ClipboardError, match="não suportado"):
                copy_image_to_clipboard(make_figure())

    @patch(
        "flowscope.infrastructure.clipboard_image.subprocess.run",
        side_effect=FileNotFoundError,
    )
    def test_linux_without_xclip_raises(self, mock_run):
        with patch("flowscope.infrastructure.clipboard_image.platform.system", return_value="Linux"):
            with pytest.raises(ClipboardError, match="xclip"):
                copy_image_to_clipboard(make_figure())

    @patch(
        "flowscope.infrastructure.clipboard_image.subprocess.run",
        side_effect=FileNotFoundError,
    )
    def test_macos_without_osascript_raises(self, mock_run):
        with patch("flowscope.infrastructure.clipboard_image.platform.system", return_value="Darwin"):
            with pytest.raises(ClipboardError, match="osascript"):
                copy_image_to_clipboard(make_figure())


class TestCopyWindows:
    @patch("flowscope.infrastructure.clipboard_image.subprocess.run")
    def test_windows_fallback_powershell_on_import_error(self, mock_run):
        from matplotlib.figure import Figure

        fig = Figure(figsize=(2, 2))
        with patch("flowscope.infrastructure.clipboard_image.platform.system", return_value="Windows"):
            with patch.dict("sys.modules", {"win32clipboard": None}):
                copy_image_to_clipboard(fig)
        mock_run.assert_called_once()
        args = mock_run.call_args.args[0]
        assert args[0] == "powershell"
        assert args[1] == "-command"
        assert str(EXPECTED_TMP_PATH) in args[2]
        assert mock_run.call_args.kwargs["check"] is True

    @patch("flowscope.infrastructure.clipboard_image.subprocess.run")
    def test_windows_uses_win32clipboard(self, mock_run):
        mock_clipboard = MagicMock()
        mock_clipboard.CF_DIB = 8
        mock_clipboard.error = OSError
        with patch("flowscope.infrastructure.clipboard_image.platform.system", return_value="Windows"):
            with patch("io.BytesIO") as mock_bytesio:
                with patch("PIL.Image.open") as mock_open:
                    output = mock_bytesio.return_value
                    output.getvalue.return_value = list(range(30))
                    with patch.dict("sys.modules", {"win32clipboard": mock_clipboard}):
                        copy_image_to_clipboard(make_figure())

        mock_open.assert_called_once_with(EXPECTED_TMP_PATH)
        image = mock_open.return_value
        image.convert.assert_called_once_with("RGB")
        image.convert.return_value.save.assert_called_once_with(
            mock_bytesio.return_value, format="BMP"
        )

        expected_data = list(range(30))[14:]
        mock_clipboard.SetClipboardData.assert_called_once_with(
            mock_clipboard.CF_DIB, expected_data
        )
        mock_clipboard.OpenClipboard.assert_called_once()
        mock_clipboard.EmptyClipboard.assert_called_once()
        mock_clipboard.CloseClipboard.assert_called_once()

    @patch("flowscope.infrastructure.clipboard_image.subprocess.run")
    def test_windows_oserror_raises(self, mock_run):
        mock_clipboard = MagicMock()
        mock_clipboard.error = OSError
        with patch("flowscope.infrastructure.clipboard_image.platform.system", return_value="Windows"):
            with patch("io.BytesIO") as mock_bytesio:
                with patch("PIL.Image.open") as mock_open:
                    mock_open.side_effect = OSError("fail")
                    with patch.dict("sys.modules", {"win32clipboard": mock_clipboard}):
                        with pytest.raises(ClipboardError, match="fail"):
                            copy_image_to_clipboard(make_figure())
