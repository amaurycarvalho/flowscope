import json
from unittest.mock import patch

from flowscope.presentation.gui.app import load_preferences, save_preferences


class TestLastTickersPreferences:
    def test_round_trip_persists_tickers(self, tmp_path):
        with patch("flowscope.presentation.gui.app.CONFIG_DIR", tmp_path), patch(
            "flowscope.presentation.gui.app.CONFIG_PATH", tmp_path / "config.json"
        ):
            save_preferences({"last_tickers": ["PETR4", "VALE3"]})
            loaded = load_preferences()
            assert loaded["last_tickers"] == ["PETR4", "VALE3"]

    def test_missing_key_returns_none(self, tmp_path):
        with patch("flowscope.presentation.gui.app.CONFIG_DIR", tmp_path), patch(
            "flowscope.presentation.gui.app.CONFIG_PATH", tmp_path / "config.json"
        ):
            prefs = load_preferences()
            assert prefs["last_tickers"] is None

    def test_empty_list_persists_as_blank(self, tmp_path):
        with patch("flowscope.presentation.gui.app.CONFIG_DIR", tmp_path), patch(
            "flowscope.presentation.gui.app.CONFIG_PATH", tmp_path / "config.json"
        ):
            save_preferences({"last_tickers": []})
            loaded = load_preferences()
            assert loaded["last_tickers"] == []

    def test_non_list_value_falls_back_to_blank(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"last_tickers": "PETR4,VALE3"}), encoding="utf-8")
        with patch("flowscope.presentation.gui.app.CONFIG_DIR", tmp_path), patch(
            "flowscope.presentation.gui.app.CONFIG_PATH", path
        ):
            loaded = load_preferences()
            assert loaded["last_tickers"] is None

    def test_corrupt_config_returns_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text("{ not valid json", encoding="utf-8")
        with patch("flowscope.presentation.gui.app.CONFIG_DIR", tmp_path), patch(
            "flowscope.presentation.gui.app.CONFIG_PATH", path
        ):
            loaded = load_preferences()
            assert loaded["last_tickers"] is None
