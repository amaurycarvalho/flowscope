import sys
from unittest.mock import patch

import pytest

from flowscope.presentation.cli import build_parser, _load_tickers


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

    def test_parser_has_cvd_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--cvd"])
        assert args.cvd

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

    def test_file_not_found(self):
        with pytest.raises(SystemExit):
            _load_tickers("/nonexistent/tickers.txt")

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        with pytest.raises(SystemExit):
            _load_tickers(str(f))
