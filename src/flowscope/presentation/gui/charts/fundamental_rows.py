"""Colunas e montagem de linhas da tabela fundamentalista.

Define o layout de colunas (fixas, roláveis e alinhamento) e converte os
dados por ticker — análises completas ou apenas classificações sintáticas —
em linhas prontas para o ``ttk.Treeview`` e para exportação CSV.
"""

from collections.abc import Mapping

from flowscope.domain.fii import (
    TIPO_EXIBICAO_FII,
    AnaliseFundamental,
    ClassificacaoExibicao,
    classificar_exibicao,
    classificar_ticker,
)
from flowscope.presentation.gui.charts.fundamental_formatters import (
    NA,
    formatar_cnpj,
    formatar_data,
    formatar_inteiro,
    formatar_margem,
    formatar_patrimonio,
    formatar_percentual,
    formatar_preco_tipico,
    formatar_quantidade,
    formatar_ratio,
    formatar_valor,
    rotulo_classe_cotistas,
    rotulo_classe_patrimonio,
    rotulo_tendencia,
)

_LARGURA_PADRAO = 140


def _largura_coluna(
    widths: Mapping[str, object] | None, coluna_id: str
) -> int:
    """Resolve a largura inicial de uma coluna, com fallback para o padrão."""
    if not widths:
        return _LARGURA_PADRAO
    try:
        largura = int(widths.get(coluna_id, _LARGURA_PADRAO))
    except (TypeError, ValueError):
        return _LARGURA_PADRAO
    return largura if largura > 0 else _LARGURA_PADRAO


_COLUNAS = (
    ("ticker", "Ticker"),
    ("nome", "Nome"),
    ("tipo", "Tipo"),
    ("subtipo", "Sub-tipo"),
    ("p", "P (Cotação)"),
    ("preco_tipico", "Preço Típico"),
    ("p_pt", "P / PT"),
    ("vp", "VP (VP/Cota)"),
    ("p_vp", "P/VP"),
    ("p_l", "P/L"),
    ("dividend_yield", "Dividend Yield"),
    ("ultima_data_com", "Última data-com"),
    ("ultimo_dividendo", "Último dividendo"),
    ("dividendo_anterior", "Dividendo anterior"),
    ("tendencia_dividendo", "Tendência do dividendo"),
    ("ffo_receita_12m", "FFO/Receita (12m)"),
    ("ffo_receita_3m", "FFO/Receita (3m)"),
    ("ffo_trend", "FFO Trend"),
    ("dividendos_receita_12m", "Dividendos/Receita (12m)"),
    ("dividendos_receita_3m", "Dividendos/Receita (3m)"),
    ("dividendos_ffo_12m", "Dividendos/FFO (12m)"),
    ("dividendos_ffo_3m", "Dividendos/FFO (3m)"),
    ("cotas", "Nº de cotas"),
    ("cotistas", "Nº de cotistas"),
    ("classe_cotistas", "Classe de cotistas"),
    ("patrimonio", "Patrimônio"),
    ("classe_patrimonio", "Classe de patrimônio"),
    ("data_referencia", "Data de referência"),
    ("informacoes_adicionais", "Informações adicionais"),
    ("dados_fiscais", "Dados fiscais"),
)

#: Colunas congeladas à esquerda da tabela (identidade da linha).
_COLUNAS_FIXAS = _COLUNAS[:2]

#: Colunas roláveis horizontalmente.
_COLUNAS_ROLANTES = _COLUNAS[2:]

#: Colunas cujo conteúdo é alinhado à direita.
_COLUNAS_DIREITA = frozenset(
    {
        "ultimo_dividendo",
        "dividendo_anterior",
        "dividend_yield",
        "ffo_receita_12m",
        "ffo_receita_3m",
        "dividendos_receita_12m",
        "dividendos_receita_3m",
        "dividendos_ffo_12m",
        "dividendos_ffo_3m",
        "p",
        "preco_tipico",
        "p_pt",
        "vp",
        "p_vp",
        "p_l",
        "cotas",
        "cotistas",
        "patrimonio",
    }
)

#: Separador dos itens concatenados nas colunas adicionais.
_SEPARADOR_ITENS = " | "


def _itens_imoveis(analise: AnaliseFundamental) -> list[str]:
    """Monta os itens de imóveis, omitindo-os quando não há quantidade."""
    if not analise.qtd_imoveis:
        return []
    itens = [f"Qtd Imóveis {formatar_inteiro(analise.qtd_imoveis)}"]
    if analise.cap_rate is not None:
        itens.append(f"Cap Rate {formatar_percentual(analise.cap_rate, 2)}")
    if analise.vacancia_media is not None:
        itens.append(
            f"Vacância Média {formatar_percentual(analise.vacancia_media, 2)}"
        )
    return itens


def _itens_indicadores_acao(analise: AnaliseFundamental) -> list[str]:
    """Monta os indicadores de ação exibidos em Informações adicionais."""
    itens: list[str] = []
    if analise.lpa is not None:
        itens.append(f"LPA {formatar_valor(analise.lpa)}")
    if analise.roe is not None:
        itens.append(f"ROE {formatar_percentual(analise.roe, 2)}")
    if analise.roic is not None:
        itens.append(f"ROIC {formatar_percentual(analise.roic, 2)}")
    return itens


def _itens_indexadores(analise: AnaliseFundamental) -> list[str]:
    """Monta os percentuais por indexador disponíveis do FII."""
    return [
        f"{rotulo} {formatar_percentual(valor, 2)}"
        for rotulo, valor in analise.indexadores.items()
        if valor is not None
    ]


def _informacoes_adicionais(
    analise: AnaliseFundamental, exibicao: ClassificacaoExibicao
) -> str:
    """Concatena os itens de Informações adicionais, ou ``N/A`` quando vazio."""
    if exibicao.tipo == TIPO_EXIBICAO_FII:
        itens = _itens_imoveis(analise)
        itens.extend(_itens_indexadores(analise))
    else:
        itens = _itens_indicadores_acao(analise)
    return _SEPARADOR_ITENS.join(itens) if itens else NA


def _item_identidade(
    rotulo: str, nome: str | None, cnpj: str | None
) -> str | None:
    """Monta ``Rótulo Nome (CNPJ)`` omitindo as partes ausentes."""
    partes: list[str] = []
    if nome:
        partes.append(nome)
    if cnpj:
        partes.append(f"({formatar_cnpj(cnpj)})")
    if not partes:
        return None
    return f"{rotulo} {' '.join(partes)}"


def _dados_fiscais(
    analise: AnaliseFundamental, exibicao: ClassificacaoExibicao
) -> str:
    """Concatena os itens de Dados fiscais, ou ``N/A`` quando vazio."""
    itens: list[str] = []
    if analise.cnpj:
        itens.append(f"CNPJ {formatar_cnpj(analise.cnpj)}")
    if exibicao.tipo == TIPO_EXIBICAO_FII:
        administrador = _item_identidade(
            "Administrador", analise.nome_administrador, analise.cnpj_administrador
        )
        if administrador is not None:
            itens.append(administrador)
        gestor = _item_identidade(
            "Gestor", analise.nome_gestor, analise.cnpj_gestor
        )
        if gestor is not None:
            itens.append(gestor)
    return _SEPARADOR_ITENS.join(itens) if itens else NA


def _linha_analise(ticker: str, analise: AnaliseFundamental) -> tuple[str, ...]:
    """Monta a linha de uma análise fundamentalista completa."""
    classificacao = analise.classificacao
    exibicao = analise.classificacao_exibicao
    if exibicao is None:
        exibicao = classificar_exibicao(discriminador=None, fallback=classificacao)
    tipo = exibicao.tipo
    sub_tipo = exibicao.sub_tipo
    dividendo = analise.ultimo_dividendo
    metricas = analise.metricas
    margens = analise.margens
    dy = metricas.dividend_yield if metricas else None
    p_vp = metricas.p_vp if metricas else None
    tendencia_ffo = margens.ffo_trend if margens else None
    return (
        ticker,
        analise.nome or NA,
        tipo,
        sub_tipo or NA,
        formatar_valor(analise.cotacao),
        formatar_preco_tipico(analise.preco_tipico),
        formatar_percentual(analise.pct_preco_tipico, 2),
        formatar_valor(analise.vp_cota),
        formatar_ratio(p_vp, 2),
        formatar_ratio(analise.p_l, 2),
        formatar_percentual(dy, 1),
        formatar_data(dividendo.data_com),
        formatar_valor(dividendo.valor),
        formatar_valor(dividendo.valor_anterior),
        rotulo_tendencia(dividendo.tendencia),
        formatar_margem(margens.ffo_receita_12m if margens else None),
        formatar_margem(margens.ffo_receita_3m if margens else None),
        rotulo_tendencia(tendencia_ffo),
        formatar_margem(margens.dividendos_receita_12m if margens else None),
        formatar_margem(margens.dividendos_receita_3m if margens else None),
        formatar_margem(margens.dividendos_ffo_12m if margens else None),
        formatar_margem(margens.dividendos_ffo_3m if margens else None),
        formatar_quantidade(analise.cotas),
        formatar_inteiro(analise.cotistas),
        rotulo_classe_cotistas(analise.classe_cotistas),
        formatar_patrimonio(analise.patrimonio),
        rotulo_classe_patrimonio(analise.classe_patrimonio),
        formatar_data(analise.data_referencia),
        _informacoes_adicionais(analise, exibicao),
        _dados_fiscais(analise, exibicao),
    )


def _linha_sintetica(ticker: str, dados: object) -> tuple[str, ...]:
    """Monta uma linha apenas com a classificação sintática do ticker."""
    classificacao = classificar_ticker(ticker)
    exibicao = classificar_exibicao(discriminador=None, fallback=classificacao)
    return (
        ticker,
        NA,
        exibicao.tipo,
        exibicao.sub_tipo or NA,
        *(NA for _ in range(len(_COLUNAS) - 4)),
    )


def montar_linhas(dados: Mapping[str, object]) -> list[tuple[str, ...]]:
    """Transforma os dados por ticker em linhas prontas para a tabela."""
    linhas: list[tuple[str, ...]] = []
    for ticker, payload in dados.items():
        if isinstance(payload, AnaliseFundamental):
            linhas.append(_linha_analise(ticker, payload))
        else:
            linhas.append(_linha_sintetica(ticker, payload))
    return linhas


def montar_csv(dados: Mapping[str, object], delimiter: str = ";") -> str:
    """Monta o CSV da tabela fundamentalista, com cabeçalho e uma linha por ticker."""
    linhas = [delimiter.join(cabecalho for _coluna, cabecalho in _COLUNAS)]
    linhas.extend(delimiter.join(linha) for linha in montar_linhas(dados))
    return "\n".join(linhas)
