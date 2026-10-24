"""Reconstrução da carteira e de seus itens a partir do cache."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from flowscope.application.renda_fixa.serializacao_para_dict import _FONTES
from flowscope.domain.renda_fixa import (
    AusenciaFonte,
    CarteiraTitulos,
    DocumentoRelacionado,
    FonteTitulos,
    PapelTitulo,
    TipoTitulo,
    TituloAgregado,
    TituloRendaFixa,
)


def _enum(cls: type, valor: object, padrao: object) -> object:
    """Serializa um valor como enum, tolerando valores desconhecidos."""
    try:
        return cls(valor)
    except (TypeError, ValueError):
        return padrao


def _data_de(valor: object) -> date | None:
    """Reconstrói uma data ISO, ou ``None`` quando ausente/inválida."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        return None


def _decimal_de(valor: object) -> Decimal | None:
    """Reconstrói um decimal serializado como texto."""
    if valor is None or valor == "":
        return None
    try:
        return Decimal(str(valor))
    except (ArithmeticError, ValueError):
        return None


def documento_de_dict(dados: dict) -> DocumentoRelacionado:
    """Reconstrói um documento relacionado."""
    return DocumentoRelacionado(
        descricao=str(dados.get("descricao") or ""),
        url=str(dados.get("url") or ""),
        fonte=str(dados.get("fonte") or ""),
        data=str(dados.get("data") or ""),
    )


def titulo_de_dict(dados: dict) -> TituloRendaFixa:
    """Reconstrói um título individual do cache."""
    campos = {campo: dados.get(campo) for campo in _FONTES}
    return TituloRendaFixa(
        tipo=_enum(TipoTitulo, dados.get("tipo"), TipoTitulo.OUTRO),
        papel=_enum(PapelTitulo, dados.get("papel"), PapelTitulo.OBRIGACAO),
        id=str(dados.get("id") or ""),
        chave_fonte=str(dados.get("chave_fonte") or ""),
        rotulo=str(dados.get("rotulo") or ""),
        codigos=_codigos_de(dados),
        data_emissao=_data_de(dados.get("data_emissao")),
        data_vencimento=_data_de(dados.get("data_vencimento")),
        data_ltv=_data_de(dados.get("data_ltv")),
        data_referencia=_data_de(dados.get("data_referencia")),
        quantidade=_decimal_de(dados.get("quantidade")),
        valor=_decimal_de(dados.get("valor")),
        saldo_devedor=_decimal_de(dados.get("saldo_devedor")),
        valor_posicao=_decimal_de(dados.get("valor_posicao")),
        ltv=_decimal_de(dados.get("ltv")),
        documentos=_documentos_de(dados),
        **campos,
    )


def _codigos_de(dados: dict) -> tuple[str, ...]:
    """Reconstrói a lista de códigos de um título."""
    return tuple(str(item) for item in dados.get("codigos") or [] if str(item))


def _documentos_de(dados: dict) -> tuple[DocumentoRelacionado, ...]:
    """Reconstrói os documentos relacionados de um título."""
    return tuple(
        documento_de_dict(item)
        for item in dados.get("documentos") or []
        if isinstance(item, dict)
    )


def agregado_de_dict(dados: dict) -> TituloAgregado:
    """Reconstrói um agregado do cache."""
    return TituloAgregado(
        tipo=_enum(TipoTitulo, dados.get("tipo"), TipoTitulo.OUTRO),
        papel=_enum(PapelTitulo, dados.get("papel"), PapelTitulo.DIREITO),
        valor=_decimal_de(dados.get("valor")),
        fonte=str(dados.get("fonte") or ""),
        data_referencia=_data_de(dados.get("data_referencia")),
    )


def ausencia_de_dict(dados: dict) -> AusenciaFonte:
    """Reconstrói uma ausência de fonte do cache."""
    return AusenciaFonte(
        tipo=_enum(TipoTitulo, dados.get("tipo"), TipoTitulo.OUTRO),
        papel=_enum(PapelTitulo, dados.get("papel"), PapelTitulo.DIREITO),
        motivo=str(dados.get("motivo") or ""),
    )


def fonte_de_dict(dados: dict) -> FonteTitulos:
    """Reconstrói os metadados de fonte do cache."""
    return FonteTitulos(
        data_referencia=_data_de(dados.get("data_referencia")),
        arquivo=str(dados.get("arquivo") or ""),
        hash=str(dados.get("hash") or ""),
    )


def _fontes_de(dados: dict) -> dict[str, FonteTitulos]:
    """Reconstrói o mapa de proveniência das fontes."""
    fontes = dados.get("fontes")
    return {
        str(nome): fonte_de_dict(item)
        for nome, item in (fontes or {}).items()
        if isinstance(item, dict)
    }


def _titulos_de(dados: dict, chave: str) -> tuple[TituloRendaFixa, ...]:
    """Reconstrói uma lista de títulos individuais do cache."""
    return tuple(
        titulo_de_dict(item)
        for item in dados.get(chave) or []
        if isinstance(item, dict)
    )


def _agregados_de(dados: dict) -> tuple[TituloAgregado, ...]:
    """Reconstrói os agregados do cache."""
    return tuple(
        agregado_de_dict(item)
        for item in dados.get("agregados") or []
        if isinstance(item, dict)
    )


def _ausencias_de(dados: dict) -> tuple[AusenciaFonte, ...]:
    """Reconstrói as ausências explícitas de fonte do cache."""
    return tuple(
        ausencia_de_dict(item)
        for item in dados.get("ausencias") or []
        if isinstance(item, dict)
    )


def carteira_de_dict(dados: dict) -> CarteiraTitulos:
    """Reconstrói a carteira completa do cache por ticker."""
    return CarteiraTitulos(
        ticker=str(dados.get("ticker") or "").strip().upper(),
        cnpj=str(dados.get("cnpj") or ""),
        tipo_ativo=str(dados.get("tipo_ativo") or ""),
        assinatura=str(dados.get("assinatura") or ""),
        parser_version=str(dados.get("parser_version") or ""),
        adquirido_em=str(dados.get("adquirido_em") or ""),
        data_referencia=_data_de(dados.get("data_referencia")),
        fontes=_fontes_de(dados),
        obrigacoes=_titulos_de(dados, "obrigacoes"),
        direitos=_titulos_de(dados, "direitos"),
        agregados=_agregados_de(dados),
        ausencias=_ausencias_de(dados),
    )
