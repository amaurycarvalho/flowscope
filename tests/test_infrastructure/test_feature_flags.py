"""Testes da leitura de feature flags booleanas do config.json."""

from flowscope.infrastructure.feature_flags import feature_flag


def _config(monkeypatch, dados: dict) -> None:
    monkeypatch.setattr(
        "flowscope.infrastructure.feature_flags.carregar_config",
        lambda: dados,
    )


def test_le_flag_aninhada(monkeypatch):
    _config(monkeypatch, {"renda_fixa": {"atualizar_titulos": False}})
    assert feature_flag("renda_fixa.atualizar_titulos", True) is False


def test_ausente_usa_default(monkeypatch):
    _config(monkeypatch, {})
    assert feature_flag("renda_fixa.atualizar_titulos", True) is True


def test_valor_nao_booleano_usa_default(monkeypatch):
    _config(monkeypatch, {"renda_fixa": {"atualizar_titulos": "sim"}})
    assert feature_flag("renda_fixa.atualizar_titulos", False) is False


def test_bloco_intermediario_ausente_usa_default(monkeypatch):
    _config(monkeypatch, {"renda_fixa": True})
    assert feature_flag("renda_fixa.atualizar_titulos", True) is True
