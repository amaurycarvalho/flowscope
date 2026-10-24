"""Aquisição idempotente e cache-aware dos títulos de renda fixa por ticker."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import replace
from datetime import date, datetime, timezone

from flowscope.application.cancellation import CancellationToken
from flowscope.application.renda_fixa.assinatura import assinatura_conteudo
from flowscope.application.renda_fixa.portas import FonteTitulos, TitulosRepository
from flowscope.application.renda_fixa.resultados import (
    ResultadoAquisicaoTitulos,
    ResultadoFontes,
)
from flowscope.domain.renda_fixa import (
    PARSER_VERSION,
    CarteiraTitulos,
    DocumentoRelacionado,
    PapelTitulo,
    TituloAgregado,
    TituloRendaFixa,
)

logger = logging.getLogger("flowscope")

#: Fontes cujo conteúdo é preservado por papel quando a aquisição corrente falha.
_FONTES_TITULO = {
    "FRE": "FRE",
    "SECURIT_CRI": "SECURIT_CRI",
    "SECURIT_CRA": "SECURIT_CRA",
    "FII_INF_TRIMESTRAL": "FII_INF_TRIMESTRAL",
    "FII_INF_MENSAL": "FII_INF_MENSAL",
}

#: Campos de enriquecimento recuperados do cache anterior em falha do SECURIT.
_CAMPOS_ENRIQUECIMENTO = (
    "emissor_legal",
    "cnpj_emissor",
    "devedor",
    "cnpj_devedor",
    "garantias",
    "coobrigacao",
    "lastro",
    "sobrecolateralizacao",
    "subordinacao",
    "situacao",
    "rating",
    "contingencias",
    "impacto",
    "desempenho",
    "ltv",
    "data_ltv",
)

ResolvedorIdentidade = Callable[[str, date], tuple[str, str] | None]
ListarDocumentos = Callable[[str, date, str], list[DocumentoRelacionado]]


class AquisicaoTitulos:
    """Orquestra a aquisição, a mesclagem por fonte e o cache por ticker."""

    def __init__(
        self: AquisicaoTitulos,
        repositorio: TitulosRepository,
        fonte: FonteTitulos,
        resolver_identidade: ResolvedorIdentidade | None = None,
        documentos: ListarDocumentos | None = None,
        parser_version: str = PARSER_VERSION,
    ) -> None:
        """Guarda o repositório, a fonte, o resolvedor e a listagem de documentos."""
        self._repositorio = repositorio
        self._fonte = fonte
        self._resolver = resolver_identidade or (lambda _t, _r: None)
        self._documentos = documentos
        self._parser_version = parser_version

    def adquirir(
        self: AquisicaoTitulos,
        ticker: str,
        reference_date: date,
        progress: Callable[[int, int, str], None] | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> ResultadoAquisicaoTitulos:
        """Adquire os títulos do ticker, preservando o último cache válido."""
        chave = (ticker or "").strip().upper()
        if not chave:
            return ResultadoAquisicaoTitulos()
        identidade = self._resolver(chave, reference_date)
        if identidade is None:
            return ResultadoAquisicaoTitulos(sem_cnpj=True)
        cnpj, tipo_ativo = identidade
        anterior = self._repositorio.ler(chave)
        cancelar = (
            cancel_token.raise_if_cancelled
            if cancel_token is not None
            else None
        )
        novo = self._fonte.obter(
            chave,
            cnpj,
            tipo_ativo,
            reference_date,
            progress=progress,
            cancelar=cancelar,
            anterior=anterior,
        )
        if cancel_token is not None and cancel_token.is_set:
            return ResultadoAquisicaoTitulos(sem_cnpj=False)
        mesclado = _mesclar(anterior, novo)
        links = self._listar_documentos(chave, reference_date, cnpj)
        carteira = self._montar_carteira(
            chave, cnpj, tipo_ativo, mesclado, links, reference_date
        )
        desfecho = _desfecho(anterior, carteira, novo)
        if anterior is not None and anterior.assinatura == carteira.assinatura:
            return desfecho
        self._repositorio.gravar(carteira)
        return desfecho

    def _listar_documentos(
        self: AquisicaoTitulos, ticker: str, reference_date: date, cnpj: str
    ) -> list[DocumentoRelacionado]:
        """Lista documentos relacionados, tolerando falha da fonte."""
        if self._documentos is None:
            return []
        try:
            return list(self._documentos(ticker, reference_date, cnpj))
        except Exception:  # listagem de links não bloqueia a aquisição
            logger.warning(
                "Falha ao listar documentos relacionados de %s",
                ticker,
                exc_info=True,
            )
            return []

    def _montar_carteira(
        self: AquisicaoTitulos,
        ticker: str,
        cnpj: str,
        tipo_ativo: str,
        dados: ResultadoFontes,
        links: list[DocumentoRelacionado],
        reference_date: date,
    ) -> CarteiraTitulos:
        """Monta a carteira com assinatura e proveniência."""
        obrigacoes = tuple(
            _com_documentos(item, links) for item in dados.obrigacoes
        )
        direitos = tuple(_com_documentos(item, links) for item in dados.direitos)
        assinatura = assinatura_conteudo(
            ticker,
            cnpj,
            tipo_ativo,
            self._parser_version,
            obrigacoes,
            direitos,
            dados.agregados,
            (),
        )
        return CarteiraTitulos(
            ticker=ticker,
            cnpj=cnpj,
            tipo_ativo=tipo_ativo,
            assinatura=assinatura,
            parser_version=self._parser_version,
            adquirido_em=datetime.now(timezone.utc).isoformat(),
            data_referencia=_data_referencia(dados, reference_date),
            fontes=dict(dados.fontes),
            obrigacoes=obrigacoes,
            direitos=direitos,
            agregados=dados.agregados,
        )


def _com_documentos(
    titulo: TituloRendaFixa, links: list[DocumentoRelacionado]
) -> TituloRendaFixa:
    """Anexa os links de documentos relacionados que ainda não estão no título."""
    existentes = {item.url for item in titulo.documentos}
    novos = tuple(item for item in links if item.url not in existentes)
    if not novos:
        return titulo
    return replace(titulo, documentos=(*titulo.documentos, *novos))


def _mesclar(
    anterior: CarteiraTitulos | None, novo: ResultadoFontes
) -> ResultadoFontes:
    """Combina a aquisição corrente com o cache, preservando fontes falhas."""
    if anterior is None:
        return novo
    falhas = novo.falhas
    obrigacoes = _preservar(anterior.obrigacoes, falhas) + list(novo.obrigacoes)
    direitos = _preservar(anterior.direitos, falhas) + list(novo.direitos)
    agregados = _preservar(anterior.agregados, falhas) + list(novo.agregados)
    anteriores = {item.id: item for item in (*anterior.obrigacoes, *anterior.direitos)}
    obrigacoes = [_reaproveitar(item, anteriores) for item in obrigacoes]
    direitos = [_reaproveitar(item, anteriores) for item in direitos]
    fontes = dict(anterior.fontes)
    fontes.update(novo.fontes)
    return ResultadoFontes(
        obrigacoes=tuple(_deduplicar(obrigacoes)),
        direitos=tuple(_deduplicar(direitos)),
        agregados=tuple(_deduplicar_agregados(agregados)),
        fontes=fontes,
        falhas=falhas,
    )


def _preservar(itens: Iterable, falhas: frozenset[str]) -> list:
    """Mantém os itens do cache cuja fonte falhou na aquisição corrente."""
    nomes = {_FONTES_TITULO.get(nome, nome) for nome in falhas}
    return [item for item in itens if getattr(item, "fonte", "") in nomes]


def _reaproveitar(
    titulo: TituloRendaFixa, anteriores: dict[str, TituloRendaFixa]
) -> TituloRendaFixa:
    """Recupera o enriquecimento do cache anterior quando a fonte não respondeu."""
    anterior = anteriores.get(titulo.id)
    if anterior is None:
        return titulo
    campos = {
        campo: getattr(anterior, campo)
        for campo in _CAMPOS_ENRIQUECIMENTO
        if getattr(titulo, campo) is None and getattr(anterior, campo) is not None
    }
    return replace(titulo, **campos) if campos else titulo


def _deduplicar(itens: Iterable[TituloRendaFixa]) -> list[TituloRendaFixa]:
    """Remove títulos repetidos por papel e identificador, preservando o primeiro."""
    vistos: dict[tuple[PapelTitulo, str], TituloRendaFixa] = {}
    for item in itens:
        vistos.setdefault((item.papel, item.id), item)
    return list(vistos.values())


def _deduplicar_agregados(itens: Iterable[TituloAgregado]) -> list[TituloAgregado]:
    """Remove agregados repetidos por papel e tipo."""
    vistos: dict[tuple[PapelTitulo, str], TituloAgregado] = {}
    for item in itens:
        vistos.setdefault((item.papel, item.tipo.value), item)
    return list(vistos.values())


def _data_referencia(dados: ResultadoFontes, reference_date: date) -> date:
    """Seleciona a maior data de referência das fontes ou a data pedida."""
    datas = [
        item.data_referencia
        for item in (*dados.obrigacoes, *dados.direitos, *dados.agregados)
        if item.data_referencia is not None
    ]
    datas.extend(
        fonte.data_referencia
        for fonte in dados.fontes.values()
        if fonte.data_referencia is not None
    )
    return max(datas) if datas else reference_date


def _desfecho(
    anterior: CarteiraTitulos | None,
    carteira: CarteiraTitulos,
    fonte: ResultadoFontes,
) -> ResultadoAquisicaoTitulos:
    """Monta o desfecho distinguindo novos, atualizados e reutilizados."""
    total = len(carteira.obrigacoes) + len(carteira.direitos) + len(carteira.agregados)
    reutilizados = 0
    novos = 0
    atualizados = 0
    if anterior is None:
        novos = total
    elif anterior.assinatura == carteira.assinatura:
        reutilizados = total
    else:
        atualizados = total
    return ResultadoAquisicaoTitulos(
        novos=novos,
        atualizados=atualizados,
        reutilizados=reutilizados,
        falhas=len(fonte.falhas),
        data_referencia=carteira.data_referencia,
        obrigacoes=len(carteira.obrigacoes),
        direitos=len(carteira.direitos),
    )
