"""Codec estruturado de ``AnaliseFundamental`` para persistência do histórico.

Converte a análise em um dicionário JSON-serializável e o reconstrói, preservando
a tipagem dos campos (``Decimal``, ``date`` e enums) para que a linha da tabela
seja reconstruída sem reprocessar as fontes.
"""

from collections.abc import Mapping
from datetime import date
from decimal import Decimal, InvalidOperation

from flowscope.domain.fii import (
    AnaliseFundamental,
    ClasseCotistas,
    ClassePatrimonio,
    ClasseRiscoFechamento,
    ClasseShorts,
    ClassificacaoAtivo,
    ClassificacaoExibicao,
    FonteClassificacao,
    MargensFii,
    MetricasFii,
    MetricasShort,
    MetricEvidence,
    MotivoMargem,
    Quality,
    ResultadoMargem,
    SubTipoAcao,
    SubTipoFii,
    TendenciaDividendo,
    TendenciaFfo,
    TipoAtivo,
    UltimoDividendo,
)


def _decimal(valor: Decimal | None) -> str | None:
    """Serializa um ``Decimal`` como string, preservando ``None``."""
    return None if valor is None else str(valor)


def _decimal_de(valor: object) -> Decimal | None:
    """Reconstrói um ``Decimal`` de uma string, ou ``None``."""
    if valor is None:
        return None
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return None


def _data(valor: date | None) -> str | None:
    """Serializa uma ``date`` em ISO, preservando ``None``."""
    return None if valor is None else valor.isoformat()


def _data_de(valor: object) -> date | None:
    """Reconstrói uma ``date`` de uma string ISO, ou ``None``."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        return None


def _enum(valor: object | None) -> str | None:
    """Serializa um enum pelo seu valor, preservando ``None``."""
    return None if valor is None else getattr(valor, "value", str(valor))


def _enum_de(tipo: type, valor: object) -> object | None:
    """Reconstrói um enum pelo valor, tolerando valores desconhecidos."""
    if valor is None:
        return None
    try:
        return tipo(valor)
    except ValueError:
        return None


def _decimal_map(valores: Mapping[str, Decimal]) -> dict[str, str]:
    """Serializa um mapa de ``Decimal`` como strings."""
    return {chave: str(valor) for chave, valor in valores.items()}


def _decimal_map_de(valores: object) -> dict[str, Decimal]:
    """Reconstrói um mapa de strings em ``Decimal``, ignorando inválidos."""
    if not isinstance(valores, Mapping):
        return {}
    resultado: dict[str, Decimal] = {}
    for chave, valor in valores.items():
        decimal = _decimal_de(valor)
        if decimal is not None:
            resultado[str(chave)] = decimal
    return resultado


def _classificacao_para_dict(classificacao: ClassificacaoAtivo) -> dict:
    """Serializa a classificação determinística do ativo."""
    return {
        "ticker": classificacao.ticker,
        "tipo": _enum(classificacao.tipo),
        "sub_tipo": _enum(classificacao.sub_tipo),
        "fonte": _enum(classificacao.fonte),
    }


def _classificacao_de_dict(dados: Mapping) -> ClassificacaoAtivo:
    """Reconstrói a classificação determinística do ativo."""
    tipo = _enum_de(TipoAtivo, dados.get("tipo")) or TipoAtivo.DESCONHECIDO
    sub_tipo = _sub_tipo_de(tipo, dados.get("sub_tipo"))
    return ClassificacaoAtivo(
        ticker=str(dados.get("ticker", "")),
        tipo=tipo,
        sub_tipo=sub_tipo,
        fonte=_enum_de(FonteClassificacao, dados.get("fonte"))
        or FonteClassificacao.NAO_CLASSIFICAVEL,
    )


def _sub_tipo_de(tipo: TipoAtivo, valor: object) -> SubTipoAcao | SubTipoFii | None:
    """Reconstrói o sub-tipo conforme o tipo de ativo."""
    if tipo is TipoAtivo.FII:
        return _enum_de(SubTipoFii, valor)
    return _enum_de(SubTipoAcao, valor)


def _exibicao_para_dict(exibicao: ClassificacaoExibicao | None) -> dict | None:
    """Serializa os rótulos de exibição do ativo."""
    if exibicao is None:
        return None
    return {"tipo": exibicao.tipo, "sub_tipo": exibicao.sub_tipo}


def _exibicao_de_dict(dados: object) -> ClassificacaoExibicao | None:
    """Reconstrói os rótulos de exibição do ativo."""
    if not isinstance(dados, Mapping):
        return None
    return ClassificacaoExibicao(
        tipo=str(dados.get("tipo", "")),
        sub_tipo=dados.get("sub_tipo"),
    )


def _ultimo_dividendo_para_dict(ultimo: UltimoDividendo) -> dict:
    """Serializa o último dividendo e sua tendência."""
    return {
        "data_com": _data(ultimo.data_com),
        "valor": _decimal(ultimo.valor),
        "valor_anterior": _decimal(ultimo.valor_anterior),
        "tendencia": _enum(ultimo.tendencia),
    }


def _ultimo_dividendo_de_dict(dados: Mapping) -> UltimoDividendo:
    """Reconstrói o último dividendo e sua tendência."""
    return UltimoDividendo(
        data_com=_data_de(dados.get("data_com")),
        valor=_decimal_de(dados.get("valor")),
        valor_anterior=_decimal_de(dados.get("valor_anterior")),
        tendencia=_enum_de(TendenciaDividendo, dados.get("tendencia"))
        or TendenciaDividendo.N_A,
    )


def _entrada_para_dict(valor: Decimal | str) -> dict:
    """Serializa uma entrada de evidência preservando o tipo original."""
    if isinstance(valor, Decimal):
        return {"tipo": "decimal", "valor": str(valor)}
    return {"tipo": "texto", "valor": str(valor)}


def _entrada_de_dict(valor: object) -> Decimal | str:
    """Reconstrói uma entrada de evidência pelo tipo registrado."""
    if isinstance(valor, Mapping) and valor.get("tipo") == "decimal":
        return _decimal_de(valor.get("valor")) or Decimal(0)
    if isinstance(valor, Mapping):
        return str(valor.get("valor", ""))
    return str(valor)


def _evidencia_para_dict(evidencia: MetricEvidence) -> dict:
    """Serializa a evidência de cálculo de uma métrica."""
    return {
        "metric": evidencia.metric,
        "value": _decimal(evidencia.value),
        "formula": evidencia.formula,
        "inputs": {k: _entrada_para_dict(v) for k, v in evidencia.inputs.items()},
        "sources": list(evidencia.sources),
        "reference_date": _data(evidencia.reference_date),
        "calculation_version": evidencia.calculation_version,
    }


def _evidencia_de_dict(dados: Mapping) -> MetricEvidence:
    """Reconstrói a evidência de cálculo de uma métrica."""
    inputs = dados.get("inputs")
    return MetricEvidence(
        metric=str(dados.get("metric", "")),
        value=_decimal_de(dados.get("value")),
        formula=str(dados.get("formula", "")),
        inputs={
            str(chave): _entrada_de_dict(valor)
            for chave, valor in (inputs.items() if isinstance(inputs, Mapping) else [])
        },
        sources=tuple(str(fonte) for fonte in (dados.get("sources") or [])),
        reference_date=_data_de(dados.get("reference_date")) or date.min,
        calculation_version=str(dados.get("calculation_version", "")),
    )


def _metricas_para_dict(metricas: MetricasFii | None) -> dict | None:
    """Serializa as métricas fundamentalistas calculadas."""
    if metricas is None:
        return None
    return {
        "market_value": _decimal(metricas.market_value),
        "ffo_yield": _decimal(metricas.ffo_yield),
        "dividend_yield": _decimal(metricas.dividend_yield),
        "p_ffo": _decimal(metricas.p_ffo),
        "p_vp": _decimal(metricas.p_vp),
        "ffo_momentum": _decimal(metricas.ffo_momentum),
        "ffo_trend": _enum(metricas.ffo_trend),
        "ffo_trend_change": _decimal(metricas.ffo_trend_change),
        "ffo_payout": _decimal(metricas.ffo_payout),
        "quality": _enum(metricas.quality),
        "warnings": list(metricas.warnings),
        "evidence": [_evidencia_para_dict(e) for e in metricas.evidence],
    }


def _metricas_de_dict(dados: object) -> MetricasFii | None:
    """Reconstrói as métricas fundamentalistas calculadas."""
    if not isinstance(dados, Mapping):
        return None
    evidencias = dados.get("evidence") or []
    return MetricasFii(
        market_value=_decimal_de(dados.get("market_value")),
        ffo_yield=_decimal_de(dados.get("ffo_yield")),
        dividend_yield=_decimal_de(dados.get("dividend_yield")),
        p_ffo=_decimal_de(dados.get("p_ffo")),
        p_vp=_decimal_de(dados.get("p_vp")),
        ffo_momentum=_decimal_de(dados.get("ffo_momentum")),
        ffo_trend=_enum_de(TendenciaFfo, dados.get("ffo_trend")),
        ffo_trend_change=_decimal_de(dados.get("ffo_trend_change")),
        ffo_payout=_decimal_de(dados.get("ffo_payout")),
        quality=_enum_de(Quality, dados.get("quality")) or Quality.PARTIAL,
        warnings=tuple(str(aviso) for aviso in (dados.get("warnings") or [])),
        evidence=tuple(
            _evidencia_de_dict(item)
            for item in evidencias
            if isinstance(item, Mapping)
        ),
    )


def _resultado_margem_para_dict(resultado: ResultadoMargem) -> dict:
    """Serializa o resultado de uma razão sobre a receita."""
    return {"valor": _decimal(resultado.valor), "motivo": _enum(resultado.motivo)}


def _resultado_margem_de_dict(dados: object) -> ResultadoMargem:
    """Reconstrói o resultado de uma razão sobre a receita."""
    if not isinstance(dados, Mapping):
        return ResultadoMargem(None)
    return ResultadoMargem(
        valor=_decimal_de(dados.get("valor")),
        motivo=_enum_de(MotivoMargem, dados.get("motivo")),
    )


def _margens_para_dict(margens: MargensFii | None) -> dict | None:
    """Serializa as razões de FFO, dividendos e receita."""
    if margens is None:
        return None
    return {
        "ffo_receita_12m": _resultado_margem_para_dict(margens.ffo_receita_12m),
        "ffo_receita_3m": _resultado_margem_para_dict(margens.ffo_receita_3m),
        "dividendos_receita_12m": _resultado_margem_para_dict(
            margens.dividendos_receita_12m
        ),
        "dividendos_receita_3m": _resultado_margem_para_dict(
            margens.dividendos_receita_3m
        ),
        "dividendos_ffo_12m": _resultado_margem_para_dict(margens.dividendos_ffo_12m),
        "dividendos_ffo_3m": _resultado_margem_para_dict(margens.dividendos_ffo_3m),
        "ffo_trend": _enum(margens.ffo_trend),
    }


def _margens_de_dict(dados: object) -> MargensFii | None:
    """Reconstrói as razões de FFO, dividendos e receita."""
    if not isinstance(dados, Mapping):
        return None
    return MargensFii(
        ffo_receita_12m=_resultado_margem_de_dict(dados.get("ffo_receita_12m")),
        ffo_receita_3m=_resultado_margem_de_dict(dados.get("ffo_receita_3m")),
        dividendos_receita_12m=_resultado_margem_de_dict(
            dados.get("dividendos_receita_12m")
        ),
        dividendos_receita_3m=_resultado_margem_de_dict(
            dados.get("dividendos_receita_3m")
        ),
        dividendos_ffo_12m=_resultado_margem_de_dict(dados.get("dividendos_ffo_12m")),
        dividendos_ffo_3m=_resultado_margem_de_dict(dados.get("dividendos_ffo_3m")),
        ffo_trend=_enum_de(TendenciaFfo, dados.get("ffo_trend")),
    )


def _short_para_dict(short: MetricasShort | None) -> dict | None:
    """Serializa as métricas de *short interest*."""
    if short is None:
        return None
    return {
        "shorts_pct": _decimal(short.shorts_pct),
        "volume_shorts": _enum(short.volume_shorts),
        "sir": _decimal(short.sir),
        "risco_fechamento": _enum(short.risco_fechamento),
    }


def _short_de_dict(dados: object) -> MetricasShort | None:
    """Reconstrói as métricas de *short interest*."""
    if not isinstance(dados, Mapping):
        return None
    return MetricasShort(
        shorts_pct=_decimal_de(dados.get("shorts_pct")),
        volume_shorts=_enum_de(ClasseShorts, dados.get("volume_shorts")),
        sir=_decimal_de(dados.get("sir")),
        risco_fechamento=_enum_de(
            ClasseRiscoFechamento, dados.get("risco_fechamento")
        ),
    )


def analise_para_dict(analise: AnaliseFundamental) -> dict:
    """Serializa uma ``AnaliseFundamental`` em um dicionário estruturado."""
    return {
        "ticker": analise.ticker,
        "nome": analise.nome,
        "classificacao": _classificacao_para_dict(analise.classificacao),
        "ultimo_dividendo": _ultimo_dividendo_para_dict(analise.ultimo_dividendo),
        "dividendos_12m_por_cota": _decimal(analise.dividendos_12m_por_cota),
        "metricas": _metricas_para_dict(analise.metricas),
        "margens": _margens_para_dict(analise.margens),
        "short": _short_para_dict(analise.short),
        "cotacao": _decimal(analise.cotacao),
        "vp_cota": _decimal(analise.vp_cota),
        "p_l": _decimal(analise.p_l),
        "classificacao_exibicao": _exibicao_para_dict(analise.classificacao_exibicao),
        "cotas": _decimal(analise.cotas),
        "cotistas": analise.cotistas,
        "patrimonio": _decimal(analise.patrimonio),
        "classe_cotistas": _enum(analise.classe_cotistas),
        "classe_patrimonio": _enum(analise.classe_patrimonio),
        "data_referencia": _data(analise.data_referencia),
        "lpa": _decimal(analise.lpa),
        "roe": _decimal(analise.roe),
        "roic": _decimal(analise.roic),
        "cap_rate": _decimal(analise.cap_rate),
        "vacancia_media": _decimal(analise.vacancia_media),
        "qtd_imoveis": analise.qtd_imoveis,
        "preco_tipico": _decimal(analise.preco_tipico),
        "pct_preco_tipico": _decimal(analise.pct_preco_tipico),
        "indexadores": _decimal_map(analise.indexadores),
        "cnpj": analise.cnpj,
        "nome_administrador": analise.nome_administrador,
        "cnpj_administrador": analise.cnpj_administrador,
        "nome_gestor": analise.nome_gestor,
        "cnpj_gestor": analise.cnpj_gestor,
        "bdr_nivel": analise.bdr_nivel,
        "bdr_observacao": analise.bdr_observacao,
        "nome_depositario": analise.nome_depositario,
        "nome_empresa_bdr": analise.nome_empresa_bdr,
        "isin": analise.isin,
        "avisos": list(analise.avisos),
        "erro": analise.erro,
    }


def analise_de_dict(dados: Mapping) -> AnaliseFundamental:
    """Reconstrói uma ``AnaliseFundamental`` de um dicionário estruturado."""
    return AnaliseFundamental(
        ticker=str(dados.get("ticker", "")),
        nome=dados.get("nome"),
        classificacao=_classificacao_de_dict(dados.get("classificacao") or {}),
        ultimo_dividendo=_ultimo_dividendo_de_dict(dados.get("ultimo_dividendo") or {}),
        dividendos_12m_por_cota=_decimal_de(dados.get("dividendos_12m_por_cota")),
        metricas=_metricas_de_dict(dados.get("metricas")),
        margens=_margens_de_dict(dados.get("margens")),
        short=_short_de_dict(dados.get("short")),
        cotacao=_decimal_de(dados.get("cotacao")),
        vp_cota=_decimal_de(dados.get("vp_cota")),
        p_l=_decimal_de(dados.get("p_l")),
        classificacao_exibicao=_exibicao_de_dict(dados.get("classificacao_exibicao")),
        cotas=_decimal_de(dados.get("cotas")),
        cotistas=dados.get("cotistas"),
        patrimonio=_decimal_de(dados.get("patrimonio")),
        classe_cotistas=_enum_de(ClasseCotistas, dados.get("classe_cotistas")),
        classe_patrimonio=_enum_de(ClassePatrimonio, dados.get("classe_patrimonio")),
        data_referencia=_data_de(dados.get("data_referencia")),
        lpa=_decimal_de(dados.get("lpa")),
        roe=_decimal_de(dados.get("roe")),
        roic=_decimal_de(dados.get("roic")),
        cap_rate=_decimal_de(dados.get("cap_rate")),
        vacancia_media=_decimal_de(dados.get("vacancia_media")),
        qtd_imoveis=dados.get("qtd_imoveis"),
        preco_tipico=_decimal_de(dados.get("preco_tipico")),
        pct_preco_tipico=_decimal_de(dados.get("pct_preco_tipico")),
        indexadores=_decimal_map_de(dados.get("indexadores")),
        cnpj=dados.get("cnpj"),
        nome_administrador=dados.get("nome_administrador"),
        cnpj_administrador=dados.get("cnpj_administrador"),
        nome_gestor=dados.get("nome_gestor"),
        cnpj_gestor=dados.get("cnpj_gestor"),
        bdr_nivel=dados.get("bdr_nivel"),
        bdr_observacao=dados.get("bdr_observacao"),
        nome_depositario=dados.get("nome_depositario"),
        nome_empresa_bdr=dados.get("nome_empresa_bdr"),
        isin=dados.get("isin"),
        avisos=tuple(str(aviso) for aviso in (dados.get("avisos") or [])),
        erro=dados.get("erro"),
    )
