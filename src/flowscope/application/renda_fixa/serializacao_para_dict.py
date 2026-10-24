"""Serialização da carteira e de seus itens para o cache por ticker."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from flowscope.domain.renda_fixa import (
    AusenciaFonte,
    CarteiraTitulos,
    DocumentoRelacionado,
    FonteTitulos,
    TituloAgregado,
    TituloRendaFixa,
)

_FONTES = (
    "emissor_legal",
    "cnpj_emissor",
    "devedor",
    "cnpj_devedor",
    "identificacao",
    "emissao",
    "serie",
    "indexador",
    "taxa",
    "garantias",
    "caracteristicas",
    "condicao_alteracao",
    "situacao",
    "rating",
    "contingencias",
    "impacto",
    "desempenho",
    "lastro",
    "coobrigacao",
    "sobrecolateralizacao",
    "subordinacao",
    "fonte",
    "arquivo",
    "hash_fonte",
)


def _data(valor: date | None) -> str | None:
    """Serializa uma data opcional em ISO."""
    return valor.isoformat() if valor is not None else None


def _decimal(valor: Decimal | None) -> str | None:
    """Serializa um decimal opcional como texto estável."""
    return format(valor.normalize(), "f") if valor is not None else None


def documento_para_dict(documento: DocumentoRelacionado) -> dict:
    """Serializa um documento relacionado."""
    return {
        "descricao": documento.descricao,
        "url": documento.url,
        "fonte": documento.fonte,
        "data": documento.data,
    }


def titulo_para_dict(titulo: TituloRendaFixa) -> dict:
    """Serializa um título individual."""
    dados: dict[str, Any] = {
        "tipo": titulo.tipo.value,
        "papel": titulo.papel.value,
        "id": titulo.id,
        "chave_fonte": titulo.chave_fonte,
        "rotulo": titulo.rotulo,
        "codigos": list(titulo.codigos),
    }
    for campo in _FONTES:
        dados[campo] = getattr(titulo, campo)
    for campo in ("data_emissao", "data_vencimento", "data_ltv", "data_referencia"):
        dados[campo] = _data(getattr(titulo, campo))
    for campo in ("quantidade", "valor", "saldo_devedor", "valor_posicao", "ltv"):
        dados[campo] = _decimal(getattr(titulo, campo))
    dados["documentos"] = [documento_para_dict(item) for item in titulo.documentos]
    return dados


def agregado_para_dict(agregado: TituloAgregado) -> dict:
    """Serializa um título agregado."""
    return {
        "tipo": agregado.tipo.value,
        "papel": agregado.papel.value,
        "id": agregado.id,
        "valor": _decimal(agregado.valor),
        "fonte": agregado.fonte,
        "data_referencia": _data(agregado.data_referencia),
    }


def ausencia_para_dict(ausencia: AusenciaFonte) -> dict:
    """Serializa uma ausência explícita de fonte."""
    return {
        "tipo": ausencia.tipo.value,
        "papel": ausencia.papel.value,
        "id": ausencia.id,
        "motivo": ausencia.motivo,
    }


def fonte_para_dict(fonte: FonteTitulos) -> dict:
    """Serializa os metadados de uma fonte."""
    return {
        "data_referencia": _data(fonte.data_referencia),
        "arquivo": fonte.arquivo,
        "hash": fonte.hash,
    }


def carteira_para_dict(carteira: CarteiraTitulos) -> dict:
    """Serializa a carteira completa no formato do cache por ticker."""
    return {
        "ticker": carteira.ticker,
        "cnpj": carteira.cnpj,
        "tipo_ativo": carteira.tipo_ativo,
        "assinatura": carteira.assinatura,
        "parser_version": carteira.parser_version,
        "adquirido_em": carteira.adquirido_em,
        "data_referencia": _data(carteira.data_referencia),
        "fontes": {
            nome: fonte_para_dict(fonte) for nome, fonte in carteira.fontes.items()
        },
        "obrigacoes": [titulo_para_dict(item) for item in carteira.obrigacoes],
        "direitos": [titulo_para_dict(item) for item in carteira.direitos],
        "agregados": [agregado_para_dict(item) for item in carteira.agregados],
        "ausencias": [ausencia_para_dict(item) for item in carteira.ausencias],
    }


