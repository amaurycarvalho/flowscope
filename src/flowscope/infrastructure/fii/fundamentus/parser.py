"""Parser da página de detalhes do Fundamentus (RFC-011 §6).

O parsing é orientado por rótulos textuais e tolerante a variações de layout;
quando os campos obrigatórios (nome e cotação) estão ausentes, sinaliza
``LayoutChanged`` em vez de produzir um modelo inválido.
"""

import re
from collections.abc import Callable
from datetime import date
from decimal import Decimal

from bs4 import BeautifulSoup

from flowscope.domain.fii.fundamentus import (
    TIPO_ACAO,
    TIPO_FII,
    AtivoFundamental,
)

from .errors import LayoutChanged
from .normalizers import para_data, para_decimal, para_int

_ROTULOS_NOME = ["Nome", "Empresa"]
_ROTULOS_COTACAO = ["Cotação"]
_ROTULO_DATA_COTACAO = "Data últ cot"
_ROTULO_MIN_52 = "Min 52 sem"
_ROTULO_MAX_52 = "Max 52 sem"
_ROTULO_VOLUME_2M = "Vol $ méd (2m)"

_OSCILACOES = (
    "Dia",
    "Mês",
    "30 dias",
    "12 meses",
    "2026",
    "2025",
    "2024",
    "2023",
    "2022",
    "2021",
)

_INDICADORES = (
    "P/L",
    "P/VP",
    "P/EBIT",
    "PSR",
    "P/Ativos",
    "P/Cap. Giro",
    "P/Ativ Circ Liq",
    "Div. Yield",
    "EV / EBITDA",
    "EV / EBIT",
    "Cres. Rec (5a)",
    "LPA",
    "VPA",
    "Marg. Bruta",
    "Marg. EBIT",
    "Marg. Líquida",
    "EBIT / Ativo",
    "ROIC",
    "ROE",
    "Liquidez Corr",
    "Dív Líq / Patrim",
    "Giro Ativos",
    "FFO Yield",
    "FFO/Cota",
    "Dividendo/cota",
    "VP/Cota",
)

_BALANCO = (
    "Ativo",
    "Disponibilidades",
    "Ativo Circulante",
    "Dív. Bruta",
    "Dív. Líquida",
    "Patrim. Líq",
    "Ativos",
    "Patrim Líquido",
)

_DEMONSTRATIVOS = (
    "Receita Líquida",
    "Receita",
    "EBIT",
    "Lucro Líquido",
    "FFO",
    "Rend. Distribuído",
    "Venda de ativos",
)

#: Campos de imóveis (FIIs) e o conversor adequado de cada um.
_IMOVEIS: dict[str, tuple[str, Callable[[str | None], Decimal | int | None]]] = {
    "qtd_imoveis": ("Qtd imóveis", para_int),
    "area_m2": ("Área (m2)", para_decimal),
    "cap_rate": ("Cap Rate", para_decimal),
    "qtd_unidades": ("Qtd Unidades", para_int),
    "aluguel_m2": ("Aluguel/m2", para_decimal),
    "vacancia_media": ("Vacância Média", para_decimal),
    "imoveis_pl": ("Imóveis/PL do FII", para_decimal),
    "preco_m2": ("Preço do m2", para_decimal),
}

_COMPOSICAO = (
    "Imóveis para Renda",
    "Imóveis em Construção",
    "Terrenos",
    "Imóveis para Venda",
    "Caixa",
    "CRI / CRA",
    "LCI / LCA",
    "Ações de Empresas do Segmento Imobiliário",
)

_ROTULOS_FII = ("FFO Yield", "FFO/Cota", "Dividendo/cota", "VP/Cota")
_PERCENTUAL_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")


def coletar_raw(soup: BeautifulSoup) -> dict[str, str]:
    """Mapeia rótulo→valor para todos os pares de células da página."""
    raw: dict[str, str] = {}
    for linha in soup.find_all("tr"):
        celulas = linha.find_all(["td", "th"])
        for indice in range(0, len(celulas) - 1, 2):
            rotulo = celulas[indice].get_text(" ", strip=True).lstrip("?")
            valor = celulas[indice + 1].get_text(" ", strip=True)
            if rotulo and rotulo not in raw:
                raw[rotulo] = valor
    return raw


def parse_ativo(ticker: str, html: str) -> AtivoFundamental:
    """Monta o ``AtivoFundamental`` a partir do HTML da página de detalhes."""
    soup = BeautifulSoup(html, "html.parser")
    raw = coletar_raw(soup)
    nome = _primeiro(raw, _ROTULOS_NOME)
    cotacao = para_decimal(_primeiro(raw, _ROTULOS_COTACAO))
    if nome is None and cotacao is None:
        raise LayoutChanged(
            f"Campos obrigatórios ausentes no layout do Fundamentus: {ticker}"
        )
    return AtivoFundamental(
        ticker=ticker.strip().upper(),
        tipo=_detectar_tipo(soup, raw),
        nome=nome,
        cotacao=cotacao,
        data_ultima_cotacao=para_data(_primeiro(raw, [_ROTULO_DATA_COTACAO])),
        min_52_sem=para_decimal(_primeiro(raw, [_ROTULO_MIN_52])),
        max_52_sem=para_decimal(_primeiro(raw, [_ROTULO_MAX_52])),
        volume_medio_2m=para_decimal(_primeiro(raw, [_ROTULO_VOLUME_2M])),
        oscilacoes=_extrair_mapa(raw, _OSCILACOES),
        indicadores=_extrair_mapa(raw, _INDICADORES),
        balanco=_extrair_mapa(raw, _BALANCO),
        demonstrativos_12m=_parse_demonstrativos(soup, coluna=0),
        demonstrativos_3m=_parse_demonstrativos(soup, coluna=1),
        composicao_ativos=_parse_composicao(soup),
        imoveis=_parse_imoveis(raw),
        raw=raw,
    )


def extrair_data_ultima_cotacao(html: str) -> date | None:
    """Extrai a ``Data últ cot`` do HTML, usada como validador de cache."""
    soup = BeautifulSoup(html, "html.parser")
    raw = coletar_raw(soup)
    return para_data(_primeiro(raw, [_ROTULO_DATA_COTACAO]))


def _primeiro(raw: dict[str, str], rotulos: list[str]) -> str | None:
    """Retorna o valor do primeiro rótulo presente no mapa bruto."""
    for rotulo in rotulos:
        if rotulo in raw:
            return raw[rotulo]
    return None


def _extrair_mapa(
    raw: dict[str, str], rotulos: tuple[str, ...]
) -> dict[str, Decimal]:
    """Extrai os rótulos informados que tiverem valor numérico válido."""
    resultado: dict[str, Decimal] = {}
    for rotulo in rotulos:
        valor = para_decimal(raw.get(rotulo))
        if valor is not None:
            resultado[rotulo] = valor
    return resultado


def _detectar_tipo(soup: BeautifulSoup, raw: dict[str, str]) -> str:
    """Detecta FII ou ação pelo cabeçalho e pelos indicadores presentes."""
    rotulos_cabecalho = {th.get_text(" ", strip=True) for th in soup.find_all("th")}
    if "FII" in rotulos_cabecalho:
        return TIPO_FII
    if any(rotulo in raw for rotulo in _ROTULOS_FII):
        return TIPO_FII
    return TIPO_ACAO


def _parse_demonstrativos(
    soup: BeautifulSoup, coluna: int
) -> dict[str, Decimal]:
    """Extrai os demonstrativos de 12m (coluna 0) ou 3m (coluna 1)."""
    resultado: dict[str, Decimal] = {}
    for linha in soup.find_all("tr"):
        celulas = linha.find_all(["td", "th"])
        if len(celulas) < 2 + coluna:
            continue
        rotulo = celulas[0].get_text(" ", strip=True).lstrip("?")
        if rotulo not in _DEMONSTRATIVOS:
            continue
        valor = para_decimal(celulas[1 + coluna].get_text(" ", strip=True))
        if valor is not None:
            resultado[rotulo] = valor
    return resultado


def _parse_imoveis(raw: dict[str, str]) -> dict[str, Decimal | int | None]:
    """Extrai os campos de imóveis de FIIs, ausentes quando não presentes."""
    return {
        chave: conversor(_primeiro(raw, [rotulo]))
        for chave, (rotulo, conversor) in _IMOVEIS.items()
    }


def _parse_composicao(soup: BeautifulSoup) -> dict[str, Decimal]:
    """Extrai percentuais de composição de ativos próximos aos rótulos conhecidos."""
    composicao: dict[str, Decimal] = {}
    texto = soup.get_text(" ", strip=True)
    for alvo in _COMPOSICAO:
        indice = texto.find(alvo)
        if indice == -1:
            continue
        trecho = texto[indice : indice + 80]
        match = _PERCENTUAL_RE.search(trecho)
        if match is not None:
            valor = para_decimal(match.group(1))
            if valor is not None:
                composicao[alvo] = valor
    return composicao
