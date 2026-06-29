import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from flowscope.presentation.main import (
    _create_desktop_shortcut,
    _desktop_shortcut_exists,
    _resolve_icon_path,
)


class TestCreateDesktopShortcut:
    def test_non_linux_returns_false(self):
        with patch("platform.system", return_value="Windows"):
            assert _create_desktop_shortcut() is False

    def test_macos_returns_false(self):
        with patch("platform.system", return_value="Darwin"):
            assert _create_desktop_shortcut() is False

    def test_linux_creates_shortcut(self, tmp_path):
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()
        fake_exe = tmp_path / "flowscope"
        fake_exe.write_text("")
        with (
            patch("platform.system", return_value="Linux"),
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("sys.argv", [str(fake_exe)]),
            patch("subprocess.run", side_effect=FileNotFoundError),
        ):
            result = _create_desktop_shortcut()
            assert result is True

            shortcut = desktop_dir / "flowscope.desktop"
            assert shortcut.exists()

            content = shortcut.read_text(encoding="utf-8")
            assert f"Exec={fake_exe} --gui\n" in content
            assert "Icon=" + str(tmp_path / ".local/share/icons/flowscope.png") in content
            assert "StartupNotify=true\n" in content

    def test_linux_shortcut_is_executable(self, tmp_path):
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()
        fake_exe = tmp_path / "flowscope"
        fake_exe.write_text("")
        with (
            patch("platform.system", return_value="Linux"),
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("sys.argv", [str(fake_exe)]),
            patch("subprocess.run", side_effect=FileNotFoundError),
        ):
            _create_desktop_shortcut()
            shortcut = desktop_dir / "flowscope.desktop"
            assert shortcut.stat().st_mode & 0o111


class TestDesktopShortcutExists:
    def test_returns_false_when_no_desktop_dir(self, tmp_path):
        with (
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("subprocess.run", side_effect=FileNotFoundError),
        ):
            assert _desktop_shortcut_exists() is False

    def test_returns_false_when_desktop_without_shortcut(self, tmp_path):
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()
        with (
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("subprocess.run", side_effect=FileNotFoundError),
        ):
            assert _desktop_shortcut_exists() is False

    def test_returns_true_when_shortcut_exists(self, tmp_path):
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()
        (desktop_dir / "flowscope.desktop").write_text("")
        with (
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("subprocess.run", side_effect=FileNotFoundError),
        ):
            assert _desktop_shortcut_exists() is True

    def test_fallback_to_area_de_trabalho(self, tmp_path):
        desktop_dir = tmp_path / "Área de Trabalho"
        desktop_dir.mkdir()
        (desktop_dir / "flowscope.desktop").write_text("")
        user_dirs = tmp_path / ".config" / "user-dirs.dirs"
        user_dirs.parent.mkdir(parents=True)
        user_dirs.write_text('XDG_DESKTOP_DIR="$HOME/Área de Trabalho"\n')
        with (
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("subprocess.run", side_effect=FileNotFoundError),
        ):
            assert _desktop_shortcut_exists() is True


class TestResolveIconPath:
    def test_dev_mode_resolves_via_file(self):
        path = _resolve_icon_path()
        assert path.name == "flowscope.png"
        assert path.exists()

    def test_frozen_mode_resolves_via_meipass(self):
        with (
            patch("sys.frozen", True, create=True),
            patch("sys._MEIPASS", "/tmp/fake_meipass", create=True),
        ):
            path = _resolve_icon_path()
            assert path == Path("/tmp/fake_meipass") / "icons" / "flowscope.png"

    def test_custom_filename_ico(self):
        path = _resolve_icon_path("flowscope.ico")
        assert path.name == "flowscope.ico"

    def test_custom_filename_png(self):
        with (
            patch("sys.frozen", True, create=True),
            patch("sys._MEIPASS", "/tmp/fake_meipass", create=True),
        ):
            path = _resolve_icon_path("custom.png")
            assert path == Path("/tmp/fake_meipass") / "icons" / "custom.png"


class TestDesktopShortcutGuiButton:
    def test_on_create_shortcut_hides_button_on_success(self):
        btn = MagicMock()
        app = MagicMock()
        app._shortcut_btn = btn

        with (
            patch(
                "flowscope.presentation.gui.app._create_desktop_shortcut",
                return_value=True,
            ),
            patch(
                "flowscope.presentation.gui.app.platform.system",
                return_value="Linux",
            ),
        ):
            from flowscope.presentation.gui.app import FlowScopeGUI
            FlowScopeGUI._on_create_shortcut(app)

        assert app._shortcut_btn is None
        btn.pack_forget.assert_called_once()

    def test_on_create_shortcut_keeps_button_on_failure(self):
        btn = MagicMock()
        app = MagicMock()
        app._shortcut_btn = btn

        from flowscope.presentation.gui.app import (
            _create_desktop_shortcut as real_create,
        )
        with patch(
            "flowscope.presentation.gui.app._create_desktop_shortcut",
            return_value=False,
        ):
            from flowscope.presentation.gui.app import FlowScopeGUI
            FlowScopeGUI._on_create_shortcut(app)

        assert app._shortcut_btn is btn
        btn.pack_forget.assert_not_called()

    def test_on_create_shortcut_non_linux_returns_early(self):
        app = MagicMock()
        app._shortcut_btn = MagicMock()

        with patch(
            "flowscope.presentation.gui.app.platform.system",
            return_value="Windows",
        ):
            from flowscope.presentation.gui.app import FlowScopeGUI
            FlowScopeGUI._on_create_shortcut(app)

        app._flash_status.assert_not_called()
        app._set_status.assert_not_called()


