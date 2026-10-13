"""Testes do leitor de retenção dos arquivos de log."""

import json
from unittest.mock import patch

from flowscope.infrastructure.logging.retention import (
    DEFAULT_LOG_RETENTION_DAYS,
    log_retention_days,
)


def _escrever(path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


class TestLogRetentionDays:
    def test_valor_valido(self, tmp_path):
        cfg = tmp_path / "config.json"
        _escrever(cfg, {"log_retention_days": 3})
        assert log_retention_days(cfg) == 3

    def test_ausente_usa_padrao(self, tmp_path):
        cfg = tmp_path / "config.json"
        _escrever(cfg, {})
        assert log_retention_days(cfg) == DEFAULT_LOG_RETENTION_DAYS

    def test_nao_inteiro_usa_padrao(self, tmp_path):
        cfg = tmp_path / "config.json"
        _escrever(cfg, {"log_retention_days": "5"})
        assert log_retention_days(cfg) == DEFAULT_LOG_RETENTION_DAYS

    def test_menor_que_um_usa_padrao(self, tmp_path):
        cfg = tmp_path / "config.json"
        _escrever(cfg, {"log_retention_days": 0})
        assert log_retention_days(cfg) == DEFAULT_LOG_RETENTION_DAYS

    def test_config_ilegivel_usa_padrao(self, tmp_path):
        cfg = tmp_path / "config.json"
        cfg.write_text("{nao eh json", encoding="utf-8")
        assert log_retention_days(cfg) == DEFAULT_LOG_RETENTION_DAYS

    def test_config_inexistente_usa_padrao(self, tmp_path):
        assert (
            log_retention_days(tmp_path / "nao-existe.json")
            == DEFAULT_LOG_RETENTION_DAYS
        )

    def test_padrao_lido_do_home(self, tmp_path):
        cfg = tmp_path / ".flowscope" / "config.json"
        cfg.parent.mkdir(parents=True)
        _escrever(cfg, {"log_retention_days": 4})
        with patch("pathlib.Path.home", return_value=tmp_path):
            assert log_retention_days() == 4
