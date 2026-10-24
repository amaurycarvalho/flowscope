"""Ramo ``/direitos-obrigacoes`` da árvore de conhecimento.

O ramo é montado exclusivamente a partir do cache normalizado por ticker. Sem
cache, mantém os sub-ramos navegáveis com a mensagem de ausência de dados.
Cada título individual expõe ``geral``, ``adicionais``, ``ltv`` e ``documentos``;
agregados expõem ``agregado/resumo`` e ausências expõem ``sem-fonte``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from flowscope.application.chat.arvore import No, no_folha, no_interno
from flowscope.application.documentos.mensagens import mensagem_placeholder
from flowscope.application.renda_fixa import (
    ConsultarTitulosUseCase,
    InferenciasRepository,
    render_adicionais,
    render_agregado,
    render_ausencia,
    render_data_referencia,
    render_documentos,
    render_geral,
    render_inferencia_documento,
    render_inferencia_geral,
    render_inferencia_proveniencia,
    render_ltv_titulo,
)
from flowscope.domain.renda_fixa import (
    ArvoreTitulos,
    AusenciaFonte,
    CarteiraInferencias,
    CarteiraTitulos,
    GalhoPapel,
    GalhoTipo,
    InferenciaTitulo,
    PapelTitulo,
    TituloAgregado,
    TituloRendaFixa,
    montar_arvore,
)

logger = logging.getLogger("flowscope")

#: Sub-ramos de papel na ordem canônica.
_PAPEIS = (PapelTitulo.OBRIGACAO, PapelTitulo.DIREITO)


@dataclass(frozen=True)
class _EntradaTicker:
    """Carteira oficial e inferências de um ticker prontas para a árvore."""

    carteira: CarteiraTitulos
    inferencias: tuple[InferenciaTitulo, ...] = ()


class FonteDireitosObrigacoes:
    """Provedor do ramo ``/direitos-obrigacoes`` a partir do cache por ticker."""

    def __init__(
        self: FonteDireitosObrigacoes,
        consultar: ConsultarTitulosUseCase | None = None,
        watchlist: list[str] | None = None,
        inferencias: InferenciasRepository | None = None,
    ) -> None:
        """Guarda a consulta oficial, a watchlist e o cache de inferências."""
        self._consultar = consultar
        self._watchlist = [ticker.strip().upper() for ticker in watchlist or ()]
        self._inferencias = inferencias

    def construir(self: FonteDireitosObrigacoes) -> No:
        """Constrói o ramo com títulos individuais, agregados e ausências."""
        raiz = no_interno("/direitos-obrigacoes", "direitos e obrigacoes")
        entradas = self._entradas()
        if not entradas:
            return _placeholder(raiz)
        raiz.filho(_no_data_referencia([entrada.carteira for entrada in entradas]))
        for papel in _PAPEIS:
            raiz.filho(_no_papel(_agregar(entradas, papel), papel))
        return raiz

    def _entradas(self: FonteDireitosObrigacoes) -> list[_EntradaTicker]:
        """Lê do cache os tickers da watchlist, omitindo os totalmente vazios."""
        entradas: list[_EntradaTicker] = []
        for ticker in self._watchlist:
            carteira = self._carteira_de(ticker)
            inferencias = self._inferencias_de(ticker)
            if carteira is None and not inferencias:
                continue
            entradas.append(
                _EntradaTicker(
                    carteira or CarteiraTitulos(ticker=ticker),
                    inferencias,
                )
            )
        return entradas

    def _carteira_de(
        self: FonteDireitosObrigacoes, ticker: str
    ) -> CarteiraTitulos | None:
        """Lê a carteira oficial do ticker, tolerando cache ilegível."""
        if self._consultar is None:
            return None
        try:
            return self._consultar.executar(ticker)
        except Exception:  # cache ilegível não derruba o ramo
            logger.warning("Falha ao ler títulos de %s", ticker, exc_info=True)
            return None

    def _inferencias_de(
        self: FonteDireitosObrigacoes, ticker: str
    ) -> tuple[InferenciaTitulo, ...]:
        """Lê as inferências do ticker, tolerando cache ilegível."""
        if self._inferencias is None:
            return ()
        try:
            cache = self._inferencias.ler(ticker)
        except Exception:  # cache ilegível não derruba o ramo
            logger.warning(
                "Falha ao ler inferências de %s", ticker, exc_info=True
            )
            return ()
        if not isinstance(cache, CarteiraInferencias):
            return ()
        return cache.itens


def _placeholder(raiz: No) -> No:
    """Monta os sub-ramos de ausência de dados, preservando os caminhos."""
    for papel in (PapelTitulo.DIREITO, PapelTitulo.OBRIGACAO):
        conteudo = mensagem_placeholder(papel.segmento)
        raiz.filho(
            no_folha(
                f"/direitos-obrigacoes/{papel.segmento}",
                papel.segmento,
                conteudo=conteudo,
                campos={"situacao": conteudo},
            )
        )
    return raiz


def _agregar(
    entradas: list[_EntradaTicker], papel: PapelTitulo
) -> GalhoPapel:
    """Combina os galhos de várias entradas, agrupando por tipo."""
    por_tipo: dict[object, list] = {}
    for entrada in entradas:
        arvore = montar_arvore(entrada.carteira, entrada.inferencias)
        galho = _galho_de(arvore, papel)
        for tipo in galho.tipos:
            por_tipo.setdefault(tipo.tipo, []).extend(tipo.itens)
    return GalhoPapel(
        papel,
        tuple(
            GalhoTipo(tipo, tuple(itens))
            for tipo, itens in por_tipo.items()
        ),
    )


def _galho_de(arvore: ArvoreTitulos, papel: PapelTitulo) -> GalhoPapel:
    """Seleciona o galho do papel na árvore normalizada."""
    return (
        arvore.obrigacoes
        if papel is PapelTitulo.OBRIGACAO
        else arvore.direitos
    )


def _no_papel(galho: GalhoPapel, papel: PapelTitulo) -> No:
    """Monta o sub-ramo de um papel, com o nó ``titulos`` quando há dados."""
    caminho = f"/direitos-obrigacoes/{papel.segmento}"
    if not galho.tipos:
        conteudo = mensagem_placeholder(papel.segmento)
        return no_folha(
            caminho,
            papel.segmento,
            conteudo=conteudo,
            campos={"situacao": conteudo},
        )
    no = no_interno(caminho, papel.segmento)
    titulos = no_interno(f"{caminho}/titulos", "titulos")
    for tipo in galho.tipos:
        titulos.filho(_no_tipo(tipo, f"{caminho}/titulos/{tipo.tipo.segmento}"))
    no.filho(titulos)
    return no


def _no_tipo(tipo: GalhoTipo, caminho: str) -> No:
    """Monta o nó do tipo com títulos, agregado ou ausência."""
    no = no_interno(caminho, tipo.tipo.rotulo)
    for item in tipo.itens:
        no.filho(_no_item(item, caminho))
    return no


def _no_item(item: object, caminho: str) -> No:
    """Monta o nó do título individual, inferido, agregado ou ausência."""
    if isinstance(item, TituloRendaFixa):
        return _no_titulo(item, f"{caminho}/{item.id}")
    if isinstance(item, InferenciaTitulo):
        return _no_inferencia(item, f"{caminho}/{item.id}")
    if isinstance(item, TituloAgregado):
        return no_folha(
            f"{caminho}/agregado/resumo",
            "agregado",
            conteudo=render_agregado(item),
            campos=_campos(item),
        )
    if isinstance(item, AusenciaFonte):
        return no_folha(
            f"{caminho}/sem-fonte",
            "sem-fonte",
            conteudo=render_ausencia(item),
            campos={"motivo": item.motivo, "tipo": item.tipo.rotulo},
        )
    raise TypeError(f"item de título inesperado: {item!r}")


def _no_titulo(titulo: TituloRendaFixa, caminho: str) -> No:
    """Monta o nó interno do título com as quatro folhas canônicas."""
    no = no_interno(caminho, titulo.nome_exibicao, metadado=titulo.tipo.rotulo)
    campos = _campos(titulo)
    for sufixo, conteudo in (
        ("geral", render_geral(titulo)),
        ("adicionais", render_adicionais(titulo)),
        ("ltv", render_ltv_titulo(titulo)),
        ("documentos", render_documentos(titulo)),
    ):
        no.filho(
            no_folha(f"{caminho}/{sufixo}", sufixo, conteudo=conteudo, campos=campos)
        )
    return no


def _no_inferencia(item: InferenciaTitulo, caminho: str) -> No:
    """Monta o nó do item inferido com os caminhos canônicos de proveniência."""
    no = no_interno(
        caminho,
        f"{item.nome_exibicao} (inferido pela IA)",
        metadado="inferido pela IA",
    )
    campos = _campos(item)
    for sufixo, conteudo in (
        ("geral", render_inferencia_geral(item)),
        ("adicionais", render_inferencia_proveniencia(item)),
        ("documentos", render_inferencia_documento(item)),
    ):
        no.filho(
            no_folha(f"{caminho}/{sufixo}", sufixo, conteudo=conteudo, campos=campos)
        )
    return no


def _campos(item: object) -> dict[str, str]:
    """Monta os campos pesquisáveis de um item de título."""
    return {
        "rotulo": str(getattr(item, "rotulo", "")),
        "tipo": getattr(getattr(item, "tipo", None), "rotulo", ""),
        "emissor": str(getattr(item, "emissor_legal", "") or ""),
        "devedor": str(getattr(item, "devedor", "") or ""),
        "fonte": str(getattr(item, "fonte", "") or ""),
        "data_referencia": str(getattr(item, "data_referencia", "") or ""),
        "documento": str(getattr(item, "documento", "") or ""),
        "trecho": str(getattr(item, "trecho", "") or ""),
        "inferido": "sim" if getattr(item, "inferido", False) else "",
    }


def _no_data_referencia(carteiras: list[CarteiraTitulos]) -> No:
    """Monta o nó ``/direitos-obrigacoes/data-referencia`` com as fontes."""
    fontes: dict = {}
    datas = []
    adquiridos = []
    for carteira in carteiras:
        for nome, fonte in carteira.fontes.items():
            fontes[f"{carteira.ticker}/{nome}"] = fonte
        if carteira.data_referencia is not None:
            datas.append(carteira.data_referencia)
        if carteira.adquirido_em:
            adquiridos.append(carteira.adquirido_em)
    data = max(datas) if datas else None
    conteudo = render_data_referencia(
        data, fontes, max(adquiridos) if adquiridos else ""
    )
    return no_folha(
        "/direitos-obrigacoes/data-referencia",
        "data-referencia",
        conteudo=conteudo,
        campos={"data": data.isoformat() if data else ""},
    )
