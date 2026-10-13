"""Testes dos caminhos compartilhados de logging."""

from unittest.mock import patch

from flowscope.log_paths import log_dir, log_file_path


class TestLogDir:
    def test_resolve_sob_o_home(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            assert log_dir() == tmp_path / ".flowscope" / "logs"


class TestLogFilePath:
    def test_resolve_sob_o_diretorio_de_logs(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            esperado = tmp_path / ".flowscope" / "logs" / "flowscope.log"
            assert log_file_path() == esperado
