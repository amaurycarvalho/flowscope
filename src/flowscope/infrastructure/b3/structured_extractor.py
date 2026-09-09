"""Extrai um documento de provento a partir do HTML tabular da B3."""

import re
from datetime import date
from decimal import Decimal

from bs4 import BeautifulSoup

from flowscope.domain.structured import (
    CNPJ,
    ISIN,
    DocumentoProvento,
    Entidade,
    Provento,
    ValorProvento,
)
from flowscope.infrastructure.b3.structured_parser import (
    _extrair_dados_tabela,
    converter_data_br_para_iso,
    extrair_isento_ir,
    extrair_nota_isencao,
    extrair_por_regex,
    extrair_por_rotulo,
    identificar_contexto_tabela,
    identificar_tipo_provento,
    limpar_valor_monetario,
    parse_html,
)


def extrair_documento_provento(
    html: str,
    id_documento: str,
    url_documento: str = "",
    data_extracao: str = "",
    ticker: str = "",
    id_fnet: str = "",
) -> DocumentoProvento | None:
    """Monta um documento de provento a partir do HTML informado.

    Aplica as estratégias de parsing encadeadas (rótulo, tabela e fallback)
    e retorna ``None`` quando o documento não contém um código ISIN.
    """
    soup = parse_html(html)
    linha, _ = _encontrar_linha_provento(soup)
    codigo_isin = _codigo_isin(soup, linha)
    if codigo_isin is None:
        return None
    try:
        isin = ISIN(codigo_isin)
    except ValueError:
        return None
    return DocumentoProvento(
        ticker=ticker,
        id_fnet=id_fnet,
        id_documento=id_documento,
        url_documento=url_documento,
        data_extracao=data_extracao,
        entidade=_montar_entidade(soup),
        provento=_montar_provento(soup, linha, isin),
    )


def _encontrar_linha_provento(
    soup: BeautifulSoup,
) -> tuple[dict | None, str | None]:
    """Localiza a linha da tabela que contém o provento (pelo código ISIN)."""
    for table in soup.find_all("table"):
        contexto = identificar_contexto_tabela(table)
        for linha in _extrair_dados_tabela(table):
            if any("isin" in _normalizar(str(chave)) for chave in linha):
                return linha, contexto
            if any(re.fullmatch(r"BR[A-Z0-9]{10}", str(valor)) for valor in linha.values()):
                return linha, contexto
    return None, None


def _codigo_isin(soup: BeautifulSoup, linha: dict | None) -> str | None:
    """Retorna o código ISIN extraído da linha ou de uma regex de fallback."""
    valor = _valor_da_linha(linha, ["Código ISIN", "Código ISIN:", "ISIN"])
    if valor:
        return valor
    return extrair_por_regex(str(soup), re.compile(r"\b(BR[A-Z0-9]{10})\b"))


def _montar_entidade(soup: BeautifulSoup) -> Entidade:
    """Monta a entidade com os dados extraídos por rótulo do documento."""
    nome = extrair_por_rotulo(soup, "Nome do Fundo:")
    cnpj_texto = extrair_por_rotulo(soup, "CNPJ do Fundo:")
    cnpj_admin_texto = extrair_por_rotulo(soup, "CNPJ do Administrador:")
    return Entidade(
        nome=nome or "",
        cnpj=_cnpj_seguro(cnpj_texto),
        nome_administrador=extrair_por_rotulo(soup, "Nome do Administrador:") or "",
        cnpj_administrador=_cnpj_seguro(cnpj_admin_texto),
        responsavel=extrair_por_rotulo(soup, "Responsável pela Informação:") or "",
        telefone=extrair_por_rotulo(soup, "Telefone Contato:") or "",
    )


def _cnpj_seguro(valor: str | None) -> CNPJ:
    """Constrói um CNPJ, usando um placeholder quando o valor é inválido."""
    try:
        return CNPJ(valor) if valor else CNPJ("00.000.000/0000-00")
    except ValueError:
        return CNPJ("00.000.000/0000-00")


def _montar_provento(
    soup: BeautifulSoup,
    linha: dict | None,
    isin: ISIN,
) -> Provento:
    """Monta o provento com os dados extraídos da linha de detalhes."""
    tipo = identificar_tipo_provento(linha)
    if tipo == "Não especificado":
        tipo = _tipo_por_regex(str(soup))
    return Provento(
        codigo_isin=isin,
        codigo_negociacao=_codigo_negociacao(linha, str(soup)),
        tipo=tipo,
        data_base=_iso_para_data(
            _data_por_linha_ou_regex(linha, str(soup), ["Data-base", "Data base"])
        ),
        valor_por_unidade=_valor_por_unidade(_valor_monetario(linha, str(soup))),
        data_pagamento=_iso_para_data(
            _data_por_linha_ou_regex(
                linha, str(soup), ["Data do pagamento", "Data do Pagamento"]
            )
        ),
        periodo_referencia=_periodo_referencia(linha, str(soup)),
        isento_ir=extrair_isento_ir(soup),
        data_informacao=_iso_para_data(_data_por_rotulo(soup, "Data da Informação")),
        ano_referencia=_ano_por_rotulo(soup),
        nota_isencao=extrair_nota_isencao(soup),
    )


def _codigo_negociacao(linha: dict | None, html: str) -> str:
    """Retorna o código de negociação extraído da linha ou de uma regex."""
    codigo = _valor_da_linha(
        linha, ["Código de negociação", "Código negociação", "Código de Negociação"]
    )
    if codigo:
        return codigo
    return (
        extrair_por_regex(html, re.compile(r"\b([A-Z]{4}\d{2})\b"))
        or ""
    )


def _periodo_referencia(linha: dict | None, html: str) -> str:
    """Retorna o período de referência extraído da linha ou do HTML."""
    periodo = _valor_da_linha(linha, ["Período de referência", "Período", "Periodo"])
    if periodo:
        return periodo
    return (
        extrair_por_regex(
            html,
            re.compile(
                re.escape("Período de referência")
                + r"\s*:?\s*(?:</[^>]+>\s*<[^>]+>\s*)?([^<\n]+)",
                re.IGNORECASE,
            ),
        )
        or ""
    )


def _tipo_por_regex(html: str) -> str:
    """Identifica o tipo de provento por expressão regular como fallback."""
    if re.search(
        r"Rendimento\s*</[^>]*>\s*<[^>]*>\s*X", html, re.IGNORECASE
    ) or re.search(r"Rendimento[^<]{0,30}>\s*X", html, re.IGNORECASE):
        return "Rendimento"
    if re.search(
        r"Amortiza[cç][aã]o\s*</[^>]*>\s*<[^>]*>\s*X", html, re.IGNORECASE
    ):
        return "Amortização"
    return "Não especificado"


def _valor_monetario(linha: dict | None, html: str) -> Decimal | None:
    """Retorna o valor monetário extraído da linha ou de uma regex de fallback."""
    valor_texto = _valor_da_linha(
        linha,
        [
            "Valor do provento (R$/unidade)",
            "Valor do provento",
            "Valor (R$)",
            "Valor",
        ],
    )
    if valor_texto:
        valor_decimal = limpar_valor_monetario(valor_texto)
        if valor_decimal is not None:
            return valor_decimal
    return _valor_monetario_por_regex(html)


def _valor_monetario_por_regex(html: str) -> Decimal | None:
    """Busca um valor monetário ``R$`` no HTML como estratégia de fallback."""
    match = re.search(r"R\$\s*([\d.,]+)", html)
    if match is None:
        return None
    return limpar_valor_monetario(f"R$ {match.group(1)}")


def _data_por_linha_ou_regex(
    linha: dict | None, html: str, candidatos: list[str]
) -> str | None:
    """Extrai e converte a data de um campo da linha ou de uma regex."""
    valor = _valor_da_linha(linha, candidatos) if linha else None
    if valor:
        return converter_data_br_para_iso(valor)
    for candidato in candidatos:
        valor = extrair_por_regex(
            html,
            re.compile(
                re.escape(candidato)
                + r"\s*:?\s*(?:</[^>]+>\s*<[^>]+>\s*)?(\d{2}/\d{2}/\d{4})",
                re.IGNORECASE,
            ),
        )
        if valor:
            return converter_data_br_para_iso(valor)
    return None


def _data_por_rotulo(soup: BeautifulSoup, rotulo: str) -> str | None:
    """Extrai e converte a data associada a um rótulo no HTML."""
    valor = extrair_por_rotulo(soup, rotulo)
    if valor is None:
        padrao = re.compile(
            re.escape(rotulo.rstrip(":")) + r"\s*:?\s*(\d{2}/\d{2}/\d{4})"
        )
        valor = extrair_por_regex(str(soup), padrao)
    return converter_data_br_para_iso(valor)


def _ano_por_rotulo(soup: BeautifulSoup) -> int | None:
    """Extrai o ano de referência associado ao rótulo ``Ano`` no HTML."""
    valor = extrair_por_rotulo(soup, "Ano:")
    if valor is None:
        match = re.search(r"\b(20\d{2})\b", str(soup))
        if match is None:
            return None
        valor = match.group(1)
    try:
        return int(valor)
    except ValueError:
        return None


def _valor_da_linha(linha: dict | None, candidatos: list[str]) -> str | None:
    """Retorna o valor da linha para o primeiro candidato de cabeçalho encontrado."""
    if not linha:
        return None
    normalizada = {_normalizar(k): v for k, v in linha.items()}
    for candidato in candidatos:
        chave = _normalizar(candidato)
        if chave in normalizada and str(normalizada[chave]).strip():
            return str(normalizada[chave]).strip()
    return None


def _normalizar(texto: str) -> str:
    """Normaliza o texto para comparação de cabeçalhos, sem acentos e espaços."""
    trocas = {
        "ç": "c",
        "á": "a",
        "ã": "a",
        "à": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        ":": "",
        " ": "",
    }
    resultado = texto.strip().lower()
    for origem, destino in trocas.items():
        resultado = resultado.replace(origem, destino)
    return resultado


def _iso_para_data(valor: str | None) -> date | None:
    """Interpreta uma data ISO como objeto ``date``."""
    if not valor:
        return None
    return date.fromisoformat(valor)


def _valor_por_unidade(valor: Decimal | None) -> ValorProvento:
    """Encapsula o valor por unidade, usando zero quando ausente."""
    if valor is None:
        return ValorProvento(Decimal(0))
    return ValorProvento(valor)
