"""Construção da árvore normalizada de títulos a partir da carteira.

A estrutura agrupa os read-models por papel e tipo, preservando a ordem
canônica dos tipos e incluindo agregados e ausências explícitas. Não conhece
apresentação nem infraestrutura.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date

from flowscope.domain.renda_fixa.inferencias import InferenciaTitulo
from flowscope.domain.renda_fixa.models import (
    ORDEM_TIPOS,
    TIPOS_SEM_FONTE_OBRIGACAO,
    AusenciaFonte,
    CarteiraTitulos,
    FonteTitulos,
    PapelTitulo,
    TipoTitulo,
    TituloAgregado,
    TituloRendaFixa,
)

ItemTitulo = TituloRendaFixa | TituloAgregado | AusenciaFonte | InferenciaTitulo


@dataclass(frozen=True)
class GalhoTipo:
    """Tipo de título com os seus itens ordenados."""

    tipo: TipoTitulo
    itens: tuple[ItemTitulo, ...] = ()


@dataclass(frozen=True)
class GalhoPapel:
    """Sub-ramo de obrigações ou direitos."""

    papel: PapelTitulo
    tipos: tuple[GalhoTipo, ...] = ()


@dataclass(frozen=True)
class ArvoreTitulos:
    """Árvore normalizada de direitos e obrigações de um ticker."""

    ticker: str
    data_referencia: date | None = None
    fontes: dict[str, FonteTitulos] = field(default_factory=dict)
    obrigacoes: GalhoPapel = field(
        default_factory=lambda: GalhoPapel(PapelTitulo.OBRIGACAO)
    )
    direitos: GalhoPapel = field(
        default_factory=lambda: GalhoPapel(PapelTitulo.DIREITO)
    )

    @property
    def vazio(self: ArvoreTitulos) -> bool:
        """Indica se não há títulos em nenhum dos papéis."""
        return not self.obrigacoes.tipos and not self.direitos.tipos


def montar_arvore(
    carteira: CarteiraTitulos | None,
    inferencias: Iterable[InferenciaTitulo] = (),
) -> ArvoreTitulos:
    """Monta a árvore combinando a carteira oficial e os itens inferidos.

    O dado oficial tem precedência: um item inferido equivalente a um título
    oficial é omitido. Ausências explícitas permanecem apenas para tipos sem
    dado oficial nem inferência.
    """
    itens_inferidos = tuple(inferencias)
    if carteira is None:
        if not itens_inferidos:
            return ArvoreTitulos(ticker="")
        carteira = CarteiraTitulos(ticker="")
    return ArvoreTitulos(
        ticker=carteira.ticker,
        data_referencia=carteira.data_referencia,
        fontes=dict(carteira.fontes),
        obrigacoes=_galho(carteira, PapelTitulo.OBRIGACAO, itens_inferidos),
        direitos=_galho(carteira, PapelTitulo.DIREITO, itens_inferidos),
    )


def _galho(
    carteira: CarteiraTitulos,
    papel: PapelTitulo,
    inferencias: tuple[InferenciaTitulo, ...],
) -> GalhoPapel:
    """Agrupa os itens do papel por tipo, incluindo ausências explícitas."""
    itens = carteira.itens(papel)
    tipos: list[GalhoTipo] = []
    for tipo in ORDEM_TIPOS:
        oficiais = [item for item in itens if item.tipo is tipo]
        inferidos = [
            item
            for item in inferencias
            if item.tipo is tipo
            and item.papel is papel
            and not _conflita(item, oficiais)
        ]
        combinados = _combinar(oficiais, inferidos)
        if combinados:
            tipos.append(GalhoTipo(tipo, _ordenar(tuple(combinados))))
            continue
        if _deve_indicar_ausencia(carteira, papel, tipo):
            tipos.append(GalhoTipo(tipo, (AusenciaFonte(tipo, papel),)))
    return GalhoPapel(papel, tuple(tipos))


def _combinar(
    oficiais: list[ItemTitulo], inferidos: list[InferenciaTitulo]
) -> list[ItemTitulo]:
    """Combina itens oficiais e inferidos, removendo ausência quando há inferência."""
    if not inferidos:
        return oficiais
    sem_ausencia = [item for item in oficiais if not isinstance(item, AusenciaFonte)]
    return [*sem_ausencia, *inferidos]


def _deve_indicar_ausencia(
    carteira: CarteiraTitulos, papel: PapelTitulo, tipo: TipoTitulo
) -> bool:
    """Indica se o tipo recebe a ausência explícita padrão de fonte."""
    return (
        papel is PapelTitulo.OBRIGACAO
        and carteira.tipo_ativo != "fii"
        and tipo in TIPOS_SEM_FONTE_OBRIGACAO
    )


def _conflita(item: InferenciaTitulo, oficiais: list[ItemTitulo]) -> bool:
    """Indica se o item inferido equivale a um título oficial do mesmo tipo."""
    alvo = _normalizar(item.identificacao or item.descricao)
    if not alvo:
        return False
    for oficial in oficiais:
        if not isinstance(oficial, TituloRendaFixa):
            continue
        candidatos = (oficial.identificacao, *oficial.codigos)
        if any(_equivalente(_normalizar(valor), alvo) for valor in candidatos):
            return True
    return False


def _equivalente(oficial: str, inferido: str) -> bool:
    """Compara identificações normalizadas admitindo descrição mais longa."""
    return bool(oficial) and (oficial in inferido or inferido in oficial)


def _normalizar(valor: object) -> str:
    """Normaliza uma identificação para comparação sem caixa ou pontuação."""
    return re.sub(r"[^a-z0-9]", "", str(valor or "").casefold())


def _ordenar(itens: tuple[ItemTitulo, ...]) -> tuple[ItemTitulo, ...]:
    """Ordena títulos e inferências por nome e mantém agregados/ausências no fim."""
    nomeados = sorted(
        (
            item
            for item in itens
            if isinstance(item, (TituloRendaFixa, InferenciaTitulo))
        ),
        key=lambda item: item.nome_exibicao,
    )
    outros = [
        item
        for item in itens
        if not isinstance(item, (TituloRendaFixa, InferenciaTitulo))
    ]
    return (*nomeados, *outros)
