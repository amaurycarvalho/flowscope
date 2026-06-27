import sys
from unittest.mock import patch

import pytest

from flowscope.presentation.main import _create_desktop_shortcut


class TestCreateDesktopShortcut:
    def test_non_linux_exits_cleanly(self):
        with patch("platform.system", return_value="Windows"):
            with pytest.raises(SystemExit) as exc:
                _create_desktop_shortcut()
            assert exc.value.code == 0

    def test_macos_exits_cleanly(self):
        with patch("platform.system", return_value="Darwin"):
            with pytest.raises(SystemExit) as exc:
                _create_desktop_shortcut()
            assert exc.value.code == 0

    def test_linux_creates_shortcut(self, tmp_path):
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()
        with (
            patch("platform.system", return_value="Linux"),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            _create_desktop_shortcut()
            shortcut = desktop_dir / "flowscope.desktop"
            assert shortcut.exists()
