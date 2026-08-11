import pytest

from flowscope.presentation.cli import (
    _load_tickers,
    build_parser,
    export_vwap_csv,
)


class TestBuildParser:
    def test_parser_has_gui_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--gui"])
        assert args.gui

    def test_parser_has_version_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--version"])
        assert args.version

    def test_parser_has_vwap_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--vwap"])
        assert args.vwap

    def test_parser_default_no_args(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert not args.gui
        assert not args.version


class TestLoadTickers:
    def test_load_valid_file(self, tmp_path):
        f = tmp_path / "tickers.txt"
        f.write_text("PETR4\nVALE3\nITUB4\n")
        result = _load_tickers(str(f))
        assert result == ["PETR4", "VALE3", "ITUB4"]

    def test_normalizes_lines(self, tmp_path):
        f = tmp_path / "tickers.txt"
        f.write_text(" petr4 \nVale3\n\n", encoding="utf-8")
        result = _load_tickers(str(f))
        assert result == ["PETR4", "VALE3"]

    def test_file_not_found(self):
        with pytest.raises(SystemExit):
            _load_tickers("/nonexistent/tickers.txt")

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        with pytest.raises(SystemExit):
            _load_tickers(str(f))

    def test_file_not_found_exits_with_code_1(self, tmp_path, capsys):
        from unittest.mock import patch

        from flowscope.presentation import cli

        with patch.object(cli.sys, "exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                cli._load_tickers(str(tmp_path / "missing.txt"))
        mock_exit.assert_called_once_with(1)
        assert "não encontrado" in capsys.readouterr().err

    def test_empty_file_exits_with_code_1(self, tmp_path, capsys):
        from unittest.mock import patch

        from flowscope.presentation import cli

        f = tmp_path / "tickers.txt"
        f.write_text("   ", encoding="utf-8")
        with patch.object(cli.sys, "exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                cli._load_tickers(str(f))
        mock_exit.assert_called_once_with(1)
        assert "está vazio" in capsys.readouterr().err


class TestExportVwapCsv:
    def test_genera_cabecalho_e_linhas_com_vwap(self):
        metrics = {
            "PETR4": {"vwap": {"period_vwap": 28.8}},
            "VALE3": {"vwap": {"period_vwap": 62.8}},
            "ITUB4": {},
        }
        content = export_vwap_csv(["PETR4", "VALE3", "ITUB4"], metrics)
        assert "Ticker;VWAP_Periodo" in content
        assert "PETR4;28.8" in content
        assert "VALE3;62.8" in content
        assert "ITUB4" not in content

    def test_sem_vwap_gera_apenas_cabecalho(self):
        content = export_vwap_csv(["PETR4"], {"PETR4": {}})
        assert content == "Ticker;VWAP_Periodo"

    def test_grava_arquivo_quando_output_path_informado(self, tmp_path):
        output = tmp_path / "vwap.csv"
        metrics = {"PETR4": {"vwap": {"period_vwap": 28.8}}}
        content = export_vwap_csv(["PETR4"], metrics, str(output))
        assert output.read_text(encoding="utf-8") == content

    def test_missing_ticker_is_skipped(self):
        metrics = {"PETR4": {"vwap": {"period_vwap": 28.8}}}
        content = export_vwap_csv(["PETR4", "MISSING"], metrics)
        assert content == "Ticker;VWAP_Periodo\nPETR4;28.8"

    def test_exact_content_newlines(self):
        metrics = {
            "PETR4": {"vwap": {"period_vwap": 28.8}},
            "VALE3": {"vwap": {"period_vwap": 62.8}},
        }
        content = export_vwap_csv(["PETR4", "VALE3"], metrics)
        assert content == "Ticker;VWAP_Periodo\nPETR4;28.8\nVALE3;62.8"
