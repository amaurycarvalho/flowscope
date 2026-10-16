import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

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


class TestConfigureLogging:
    def test_cria_diretorio_de_log(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            from flowscope.presentation.main import _configure_logging
            _configure_logging()
            log_dir = tmp_path / ".flowscope" / "logs"
            assert log_dir.exists()
            log_file = log_dir / "flowscope.log"
            assert log_file.exists()

    def test_escreve_mensagem_no_arquivo(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            from flowscope.presentation.main import _configure_logging
            _configure_logging()
            import logging
            logging.getLogger("flowscope").error("teste log")
            log_file = tmp_path / ".flowscope" / "logs" / "flowscope.log"
            content = log_file.read_text()
            assert "teste log" in content

    def test_falha_de_comunicacao_nao_escreve_traceback(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            from flowscope.presentation.main import _configure_logging
            _configure_logging()
            import logging
            logger = logging.getLogger("flowscope")
            try:
                raise requests.exceptions.ReadTimeout("read timed out")
            except requests.exceptions.ReadTimeout:
                logger.warning("Falha ao baixar", exc_info=True)
            log_file = tmp_path / ".flowscope" / "logs" / "flowscope.log"
            content = log_file.read_text()
            assert "ReadTimeout" in content
            assert "Traceback" not in content

    def test_linha_comeca_com_timestamp_com_milissegundos(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            from flowscope.presentation.main import _configure_logging
            _configure_logging()
            import logging
            logging.getLogger("flowscope").error("teste log")
            log_file = tmp_path / ".flowscope" / "logs" / "flowscope.log"
            line = log_file.read_text().splitlines()[0]
            assert re.match(
                r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \| ERROR \|", line
            )

    def test_linux_adiciona_syslog_handler(self, tmp_path):
        with (
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("platform.system", return_value="Linux"),
            patch("flowscope.presentation.main.SysLogHandler", return_value=MagicMock()) as mock_syslog,
        ):
            from flowscope.presentation.main import _configure_logging
            _configure_logging()
            mock_syslog.assert_called_once_with(address="/dev/log")

    def test_macos_adiciona_syslog_handler(self, tmp_path):
        with (
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("platform.system", return_value="Darwin"),
            patch("flowscope.presentation.main.SysLogHandler", return_value=MagicMock()) as mock_syslog,
        ):
            from flowscope.presentation.main import _configure_logging
            _configure_logging()
            mock_syslog.assert_called_once_with(address="/var/run/syslog")

    def test_windows_tenta_adicionar_nt_event_log(self, tmp_path):
        with (
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("platform.system", return_value="Windows"),
            patch("logging.handlers.NTEventLogHandler", return_value=MagicMock()) as mock_nt,
        ):
            from flowscope.presentation.main import _configure_logging
            _configure_logging()
            mock_nt.assert_called_once_with("FlowScope")

    def test_syslog_falha_silenciosamente(self, tmp_path):
        with (
            patch("pathlib.Path.home", return_value=tmp_path),
            patch("platform.system", return_value="Linux"),
            patch("flowscope.presentation.main.SysLogHandler", side_effect=OSError),
        ):
            from flowscope.presentation.main import _configure_logging
            _configure_logging()
            log_file = tmp_path / ".flowscope" / "logs" / "flowscope.log"
            assert log_file.exists()

    def test_silencia_pypdf_no_nivel_error(self, monkeypatch):
        import logging

        from flowscope.presentation import main

        pypdf_logger = logging.getLogger("pypdf")
        monkeypatch.setattr(pypdf_logger, "level", logging.DEBUG)
        main._silenciar_pypdf()
        assert pypdf_logger.level == logging.ERROR

    def test_configure_logging_invoca_silenciamento_do_pypdf(
        self, tmp_path, monkeypatch
    ):
        from flowscope.presentation import main

        chamadas: list[bool] = []
        monkeypatch.setattr(main, "_silenciar_pypdf", lambda: chamadas.append(True))
        with patch("pathlib.Path.home", return_value=tmp_path):
            main._configure_logging()
        assert chamadas == [True]

    def test_configure_logging_encadeia_housekeeping(self, tmp_path, monkeypatch):
        from flowscope.presentation import main

        chamadas: list[str] = []
        monkeypatch.setattr(
            main, "rotacionar_log_obsoleto",
            lambda *a: chamadas.append("rotacao"),
        )
        monkeypatch.setattr(
            main, "limpar_backups_antigos",
            lambda *a: chamadas.append("limpeza"),
        )
        with patch("pathlib.Path.home", return_value=tmp_path):
            main._configure_logging()
        assert chamadas == ["rotacao", "limpeza"]


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


class TestAuditoriaCli:
    def _args(self, **kwargs):
        import argparse

        base = dict(
            comando="nav", recurso=None, operacao="obter", caminho="/fundamentos",
            ticker=None, arquivo=None, data=None, data_inicio=None, data_fim=None,
            tickers=None, palavra=None, categoria=None, structured_earnings=None,
            fatos_relevantes=None, output=None, watchlist=None, esperar=0.0,
            gui=False, mcp=False, version=False, create_shortcut=False, vwap=False,
            noticias=False, regulacao=False, pretty=False,
        )
        base.update(kwargs)
        return argparse.Namespace(**base)

    def test_registra_invocacao_bem_sucedida(self, tmp_path):
        from flowscope.presentation import main

        with patch("pathlib.Path.home", return_value=tmp_path):
            main._configure_logging()
            main._registrar_auditoria(self._args(), 0.0, 0.5, 0)
            log_file = tmp_path / ".flowscope" / "logs" / "flowscope.log"
            content = log_file.read_text()
        assert "comando=nav" in content
        assert "'caminho': '/fundamentos'" in content
        assert "codigo=0" in content
        assert "duracao=0.500s" in content

    def test_registra_falha(self, tmp_path):
        from flowscope.presentation import main

        with patch("pathlib.Path.home", return_value=tmp_path):
            main._configure_logging()
            main._registrar_auditoria(self._args(), 0.0, 0.1, 1)
            content = (tmp_path / ".flowscope" / "logs" / "flowscope.log").read_text()
        assert "codigo=1" in content

    def test_segredos_omitidos(self, tmp_path):
        from flowscope.presentation import main

        with patch("pathlib.Path.home", return_value=tmp_path):
            main._configure_logging()
            args = self._args()
            args.api_key = "sk-segredo"
            args.llm = {"chat": {"api_key": "sk-outro"}}
            main._registrar_auditoria(args, 0.0, 0.1, 0)
            content = (tmp_path / ".flowscope" / "logs" / "flowscope.log").read_text()
        assert "sk-segredo" not in content
        assert "sk-outro" not in content

    def test_auditoria_nao_escreve_no_stdout(self, capsys):
        from flowscope.presentation import main

        main._registrar_auditoria(self._args(), 0.0, 0.1, 0)
        assert capsys.readouterr().out == ""
