"""Serialização e reconstrução do cache de inferências de direitos e obrigações."""

from __future__ import annotations

from datetime import date

from flowscope.domain.renda_fixa import (
    CarteiraInferencias,
    InferenciaTitulo,
    PapelTitulo,
    TipoTitulo,
)


def _enum(cls: type, valor: object) -> object | None:
    """Retorna o valor convertido no enum, ou ``None`` quando desconhecido."""
    try:
        return cls(valor)
    except (TypeError, ValueError):
        return None


def _data_de(valor: object) -> date | None:
    """Reconstrói uma data ISO, ou ``None`` quando ausente/inválida."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        return None


def _texto(valor: object) -> str:
    """Normaliza um valor persistido para texto."""
    return valor if isinstance(valor, str) else ""


def _confianca_de(valor: object) -> float:
    """Reconstrói a confiança no intervalo fechado ``[0, 1]``."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return 0.0
    return min(1.0, max(0.0, numero))


def inferencia_para_dict(item: InferenciaTitulo) -> dict:
    """Serializa um item inferido com a sua proveniência."""
    return {
        "tipo": item.tipo.value,
        "papel": item.papel.value,
        "descricao": item.descricao,
        "documento": item.documento,
        "chave_documento": item.chave_documento,
        "hash_resumo": item.hash_resumo,
        "trecho": item.trecho,
        "confianca": item.confianca,
        "data_referencia": (
            item.data_referencia.isoformat() if item.data_referencia else None
        ),
        "fonte": item.fonte,
        "identificacao": item.identificacao,
    }


def inferencia_de_dict(dados: object) -> InferenciaTitulo | None:
    """Reconstrói um item inferido, descartando registros inválidos."""
    if not isinstance(dados, dict):
        return None
    tipo = _enum(TipoTitulo, dados.get("tipo"))
    papel = _enum(PapelTitulo, dados.get("papel"))
    if tipo is None or papel is None:
        return None
    descricao = _texto(dados.get("descricao"))
    documento = _texto(dados.get("documento"))
    trecho = _texto(dados.get("trecho"))
    if not descricao or not documento or not trecho:
        return None
    return InferenciaTitulo(
        tipo=tipo,
        papel=papel,
        descricao=descricao,
        documento=documento,
        chave_documento=_texto(dados.get("chave_documento")),
        hash_resumo=_texto(dados.get("hash_resumo")),
        trecho=trecho,
        confianca=_confianca_de(dados.get("confianca")),
        data_referencia=_data_de(dados.get("data_referencia")),
        fonte=_texto(dados.get("fonte")) or "LLM",
        identificacao=_texto(dados.get("identificacao")),
    )


def carteira_inferencias_para_dict(carteira: CarteiraInferencias) -> dict:
    """Serializa a carteira de inferências no formato do cache por ticker."""
    return {
        "ticker": carteira.ticker,
        "parser_version": carteira.parser_version,
        "adquirido_em": carteira.adquirido_em,
        "atualizado_em": carteira.adquirido_em,
        "itens": [inferencia_para_dict(item) for item in carteira.itens],
    }


def carteira_inferencias_de_dict(dados: dict) -> CarteiraInferencias:
    """Reconstrói a carteira de inferências do cache, tolerando itens inválidos."""
    itens = [
        item
        for bruto in dados.get("itens") or []
        if (item := inferencia_de_dict(bruto)) is not None
    ]
    return CarteiraInferencias(
        ticker=str(dados.get("ticker") or "").strip().upper(),
        parser_version=str(dados.get("parser_version") or ""),
        adquirido_em=str(
            dados.get("adquirido_em") or dados.get("atualizado_em") or ""
        ),
        itens=tuple(itens),
    )
