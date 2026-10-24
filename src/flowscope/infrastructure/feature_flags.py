"""Leitura de feature flags booleanas do ``config.json``.

As flags usam caminhos pontuados, por exemplo ``renda_fixa.atualizar_titulos``,
e qualquer valor ausente ou inválido cai no padrão informado pelo chamador.
"""

from __future__ import annotations

from flowscope.infrastructure.referencia import carregar_config


def feature_flag(caminho: str, default: bool = False) -> bool:
    """Retorna a flag booleana do caminho, ou ``default`` quando ausente."""
    atual: object = carregar_config()
    for parte in caminho.split("."):
        if not isinstance(atual, dict):
            return default
        atual = atual.get(parte)
    return atual if isinstance(atual, bool) else default
