"""Assinatura canônica do conteúdo normalizado dos títulos."""

from __future__ import annotations

import hashlib
import json

from flowscope.application.renda_fixa.serializacao_para_dict import (
    agregado_para_dict,
    ausencia_para_dict,
    titulo_para_dict,
)
from flowscope.domain.renda_fixa import (
    AusenciaFonte,
    TituloAgregado,
    TituloRendaFixa,
)


def assinatura_conteudo(
    ticker: str,
    cnpj: str,
    tipo_ativo: str,
    parser_version: str,
    obrigacoes: tuple[TituloRendaFixa, ...],
    direitos: tuple[TituloRendaFixa, ...],
    agregados: tuple[TituloAgregado, ...],
    ausencias: tuple[AusenciaFonte, ...],
) -> str:
    """Deriva a assinatura do conteúdo normalizado e da versão do parser."""
    payload = {
        "ticker": ticker,
        "cnpj": cnpj,
        "tipo_ativo": tipo_ativo,
        "parser_version": parser_version,
        "obrigacoes": [titulo_para_dict(item) for item in obrigacoes],
        "direitos": [titulo_para_dict(item) for item in direitos],
        "agregados": [agregado_para_dict(item) for item in agregados],
        "ausencias": [ausencia_para_dict(item) for item in ausencias],
    }
    serializado = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()
