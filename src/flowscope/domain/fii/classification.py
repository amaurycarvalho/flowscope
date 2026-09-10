"""Classificação determinística de tipo e sub-tipo de ativos listados na B3.

A classificação combina derivação sintática do ticker (sufixo numérico) com a
resolução ``code-cvm-resolution`` (identidade CVM) e taxonomias versionadas
para fundos (FIIs e ETFs). O domínio nunca infere o tipo a partir do nome do
ativo; tickers que não podem ser classificados de forma determinística
recebem ``TipoAtivo.DESCONHECIDO``.
"""

import re
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, field
from enum import Enum

from flowscope.domain.fii.fundamentus import (
    DISCRIMINADOR_FII,
    DISCRIMINADOR_PAPEL,
)

_PADRAO_TICKER = re.compile(r"^([A-Z]+)(\d+)$")

#: Sufixos de dois dígitos reservados a BDRs (níveis I/II/III e programas 2x/3x).
_SUFIXOS_BDR = frozenset(str(numero) for numero in range(32, 40))

#: Fonte utilizada para registrar a origem de uma classificação.
class FonteClassificacao(Enum):
    """Procedência da classificação de tipo/sub-tipo de um ativo."""

    TAXONOMIA_FII = "taxonomia_fii"
    TAXONOMIA_ETF = "taxonomia_etf"
    SINTAXE = "sintaxe"
    CODE_CVM = "code_cvm"
    NAO_CLASSIFICAVEL = "nao_classificavel"


class TipoAtivo(Enum):
    """Tipo de ativo negociado na B3."""

    ACAO = "acao"
    FII = "fii"
    ETF = "etf"
    BDR = "bdr"
    DESCONHECIDO = "desconhecido"


class SubTipoAcao(Enum):
    """Sub-tipo de uma ação listada, derivado do sufixo do ticker."""

    ORDINARIA = "ordinaria"
    PREFERENCIAL = "preferencial"
    ETF = "etf"


class SubTipoFii(Enum):
    """Sub-tipo de um fundo imobiliário, obtido de uma taxonomia versionada."""

    TIJOLO = "tijolo"
    PAPEL = "papel"
    HIBRIDO = "hibrido"
    FIAGRO = "fiagro"
    FIINFRA = "fiinfra"
    DESCONHECIDO = "desconhecido"


def normalizar_ticker(ticker: str) -> str:
    """Normaliza um ticker removendo espaços e convertendo para maiúsculas."""
    return ticker.strip().upper()


@dataclass(frozen=True)
class TaxonomiaFii:
    """Mapa versionado ``ticker → SubTipoFii`` mantido no repositório.

    A versão explícita impede alteração silenciosa da classificação. Tickers
    ausentes do mapa retornam ``SubTipoFii.DESCONHECIDO``.
    """

    versao: str
    tickers: Mapping[str, SubTipoFii] = field(default_factory=dict)

    def contem(self: "TaxonomiaFii", ticker: str) -> bool:
        """Indica se o ticker possui entrada explícita na taxonomia."""
        return normalizar_ticker(ticker) in self.tickers

    def sub_tipo(self: "TaxonomiaFii", ticker: str) -> SubTipoFii:
        """Retorna o sub-tipo do ticker, ou ``DESCONHECIDO`` quando ausente."""
        return self.tickers.get(normalizar_ticker(ticker), SubTipoFii.DESCONHECIDO)


#: Versão da taxonomia padrão de sub-tipos de FIIs.
TAXONOMIA_FII_VERSAO = "2026-09-01"

#: Taxonomia padrão de FIIs, cobrindo os FIIs de referência das RFC-006/007.
TAXONOMIA_FII_PADRAO = TaxonomiaFii(
    versao=TAXONOMIA_FII_VERSAO,
    tickers={
        "BTLG11": SubTipoFii.TIJOLO,
        "HGBS11": SubTipoFii.TIJOLO,
        "HGLG11": SubTipoFii.TIJOLO,
        "HSML11": SubTipoFii.TIJOLO,
        "KNRI11": SubTipoFii.TIJOLO,
        "RBVA11": SubTipoFii.TIJOLO,
        "TRXF11": SubTipoFii.TIJOLO,
        "VISC11": SubTipoFii.TIJOLO,
        "XPML11": SubTipoFii.TIJOLO,
        "HCRI11": SubTipoFii.PAPEL,
        "XPIN11": SubTipoFii.HIBRIDO,
    },
)

#: Versão da lista estática de ETFs negociados na B3.
TAXONOMIA_ETF_VERSAO = "2026-09-01"

#: ETFs negociados na B3 reconhecidos de forma determinística.
ETFS_CONHECIDOS: frozenset[str] = frozenset({
    "BOVA11",
    "SMAL11",
    "DIVO11",
    "IVVB11",
    "SPXI11",
    "MATB11",
    "BBSD11",
    "ISUS11",
    "XINA11",
    "GOLD11",
    "ECOO11",
    "BRAX11",
    "MCHI11",
    "QBTC11",
    "HASH11",
    "BTCX11",
    "FIND11",
    "NASD11",
    "WRLD11",
    "ACWI11",
    "PIBB11",
    "SMAB11",
    "TECK11",
})


@dataclass(frozen=True)
class ClassificacaoAtivo:
    """Resultado determinístico da classificação de um ticker."""

    ticker: str
    tipo: TipoAtivo
    sub_tipo: SubTipoAcao | SubTipoFii | None
    fonte: FonteClassificacao

    def elegivel_ffo(self: "ClassificacaoAtivo") -> bool:
        """Indica se o ativo é elegível para o cálculo das métricas FFO."""
        return (
            self.tipo is TipoAtivo.FII
            and self.sub_tipo in (SubTipoFii.TIJOLO, SubTipoFii.HIBRIDO)
        )


ResolverCodeCvm = Callable[[str], str | None]


def _classificar_sufixo_acao(
    sufixo: str, ticker: str, resolver: ResolverCodeCvm | None
) -> ClassificacaoAtivo:
    """Classifica um ticker com sufixo numérico típico de ação.

    Quando um resolvedor ``code-cvm-resolution`` é fornecido, a identidade CVM
    valida a classificação: sem código CVM o ticker é ``DESCONHECIDO``. Sem
    resolvedor a classificação é puramente sintática.
    """
    if resolver is not None and resolver(ticker) is None:
        return ClassificacaoAtivo(
            ticker=ticker,
            tipo=TipoAtivo.DESCONHECIDO,
            sub_tipo=None,
            fonte=FonteClassificacao.NAO_CLASSIFICAVEL,
        )
    ultimo_digito = sufixo[-1]
    sub_tipo = (
        SubTipoAcao.ORDINARIA if ultimo_digito == "3" else SubTipoAcao.PREFERENCIAL
    )
    fonte = FonteClassificacao.CODE_CVM if resolver is not None else FonteClassificacao.SINTAXE
    return ClassificacaoAtivo(
        ticker=ticker,
        tipo=TipoAtivo.ACAO,
        sub_tipo=sub_tipo,
        fonte=fonte,
    )


def classificar_ticker(
    ticker: str,
    *,
    taxonomia_fii: TaxonomiaFii | None = None,
    resolver_code_cvm: ResolverCodeCvm | None = None,
    etfs: Collection[str] = ETFS_CONHECIDOS,
) -> ClassificacaoAtivo:
    """Classifica o tipo e o sub-tipo de um ticker de forma determinística.

    A decisão combina o sufixo numérico do ticker (sintaxe) com a resolução
    ``code-cvm-resolution`` (identidade CVM) e, para fundos, taxonomias
    versionadas. Tickers sem classificação determinística retornam
    ``TipoAtivo.DESCONHECIDO`` sem inferência a partir do nome.
    """
    normalizado = normalizar_ticker(ticker)
    corresponde = _PADRAO_TICKER.match(normalizado)
    if corresponde is None:
        return ClassificacaoAtivo(
            ticker=normalizado,
            tipo=TipoAtivo.DESCONHECIDO,
            sub_tipo=None,
            fonte=FonteClassificacao.NAO_CLASSIFICAVEL,
        )
    prefixo, sufixo = corresponde.groups()
    if not prefixo or not sufixo:
        return ClassificacaoAtivo(
            ticker=normalizado,
            tipo=TipoAtivo.DESCONHECIDO,
            sub_tipo=None,
            fonte=FonteClassificacao.NAO_CLASSIFICAVEL,
        )
    resolver = resolver_code_cvm
    if sufixo in _SUFIXOS_BDR:
        return ClassificacaoAtivo(
            ticker=normalizado,
            tipo=TipoAtivo.BDR,
            sub_tipo=None,
            fonte=FonteClassificacao.SINTAXE,
        )
    if sufixo == "11":
        return _classificar_sufixo_onze(normalizado, resolver, taxonomia_fii, etfs)
    if 3 <= int(sufixo) <= 9:
        return _classificar_sufixo_acao(sufixo, normalizado, resolver)
    return ClassificacaoAtivo(
        ticker=normalizado,
        tipo=TipoAtivo.DESCONHECIDO,
        sub_tipo=None,
        fonte=FonteClassificacao.NAO_CLASSIFICAVEL,
    )


def _classificar_sufixo_onze(
    ticker: str,
    resolver: ResolverCodeCvm | None,
    taxonomia_fii: TaxonomiaFii | None,
    etfs: Collection[str],
) -> ClassificacaoAtivo:
    """Classifica tickers com sufixo ``11`` (fundos ou unidades de ação)."""
    taxonomia = taxonomia_fii or TAXONOMIA_FII_PADRAO
    if taxonomia.contem(ticker):
        return ClassificacaoAtivo(
            ticker=ticker,
            tipo=TipoAtivo.FII,
            sub_tipo=taxonomia.sub_tipo(ticker),
            fonte=FonteClassificacao.TAXONOMIA_FII,
        )
    if ticker in etfs:
        return ClassificacaoAtivo(
            ticker=ticker,
            tipo=TipoAtivo.ETF,
            sub_tipo=SubTipoAcao.ETF,
            fonte=FonteClassificacao.TAXONOMIA_ETF,
        )
    if resolver is not None and resolver(ticker) is not None:
        return ClassificacaoAtivo(
            ticker=ticker,
            tipo=TipoAtivo.ACAO,
            sub_tipo=SubTipoAcao.ORDINARIA,
            fonte=FonteClassificacao.CODE_CVM,
        )
    return ClassificacaoAtivo(
        ticker=ticker,
        tipo=TipoAtivo.DESCONHECIDO,
        sub_tipo=None,
        fonte=FonteClassificacao.NAO_CLASSIFICAVEL,
    )


def elegivel_ffo(classificacao: ClassificacaoAtivo) -> bool:
    """Indica se a classificação torna o ativo elegível para métricas FFO."""
    return classificacao.elegivel_ffo()


#: Rótulos de exibição do tipo de ativo na tabela de Fundamentos.
TIPO_EXIBICAO_PAPEL = "Papel"
TIPO_EXIBICAO_FII = "FII"
TIPO_EXIBICAO_DESCONHECIDO = "Desconhecido"

_LABEL_SUB_TIPO_FII: Mapping[SubTipoFii, str | None] = {
    SubTipoFii.TIJOLO: "Tijolo",
    SubTipoFii.PAPEL: "Papel",
    SubTipoFii.HIBRIDO: "Híbrido",
    SubTipoFii.FIAGRO: "Fiagro",
    SubTipoFii.FIINFRA: "Fiinfra",
    SubTipoFii.DESCONHECIDO: None,
}

_LABEL_SUB_TIPO_ACAO: Mapping[SubTipoAcao, str] = {
    SubTipoAcao.ORDINARIA: "Ordinária",
    SubTipoAcao.PREFERENCIAL: "Preferencial",
    SubTipoAcao.ETF: "ETF",
}


@dataclass(frozen=True)
class ClassificacaoExibicao:
    """Rótulos de Tipo e Sub-tipo exibidos na tabela de Fundamentos."""

    tipo: str
    sub_tipo: str | None = None


def _juntar(*partes: str | None) -> str:
    """Concatena partes não vazias separadas por ``", "``."""
    return ", ".join(parte.strip() for parte in partes if parte and parte.strip())


def classificar_exibicao(
    *,
    discriminador: str | None,
    especie: str | None = None,
    setor: str | None = None,
    subsetor: str | None = None,
    segmento: str | None = None,
    gestao: str | None = None,
    qtd_imoveis: int | None = None,
    fallback: ClassificacaoAtivo | None = None,
) -> ClassificacaoExibicao:
    """Compõe o Tipo e o Sub-tipo a partir dos campos do Fundamentus.

    Quando o discriminador está ausente, usa a classificação determinística
    informada em ``fallback`` (sintaxe/codeCVM/taxonomia).
    """
    if discriminador == DISCRIMINADOR_FII:
        prefixo = "Tijolo: " if (qtd_imoveis or 0) > 0 else "Papel: "
        base = _juntar(segmento, gestao)
        return ClassificacaoExibicao(
            TIPO_EXIBICAO_FII, f"{prefixo}{base}" if base else prefixo.strip()
        )
    if discriminador == DISCRIMINADOR_PAPEL:
        base = _juntar(especie, setor, subsetor)
        return ClassificacaoExibicao(TIPO_EXIBICAO_PAPEL, base or None)
    return _exibicao_do_fallback(fallback)


def _exibicao_do_fallback(
    fallback: ClassificacaoAtivo | None,
) -> ClassificacaoExibicao:
    """Traduz a classificação determinística para os rótulos de exibição."""
    if fallback is None or fallback.tipo is TipoAtivo.DESCONHECIDO:
        return ClassificacaoExibicao(TIPO_EXIBICAO_DESCONHECIDO)
    if fallback.tipo is TipoAtivo.FII:
        return ClassificacaoExibicao(
            TIPO_EXIBICAO_FII, _LABEL_SUB_TIPO_FII.get(fallback.sub_tipo)
        )
    sub_tipo = (
        fallback.sub_tipo
        if isinstance(fallback.sub_tipo, SubTipoAcao)
        else None
    )
    return ClassificacaoExibicao(
        TIPO_EXIBICAO_PAPEL, _LABEL_SUB_TIPO_ACAO.get(sub_tipo)
    )
