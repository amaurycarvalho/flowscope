"""Aquisição e cache do corpo das notícias do Plantão B3.

Lista as notícias do último ano via ``RegulacaoRepository``, dia a dia, mantém
apenas os casos excepcionais (eventos de mercado fora da curva, ver
``noticias_tipos``), baixa o HTML de cada artigo a partir da URL e grava um
cache próprio em ``noticias/<AAAA>/<MM>/<hash>.html``. A chave é estável
(``sha1`` da URL ou, sem URL, de data, agência e título). A carga da "Geral" é
incremental: o dia mais recente é sempre recarregado e marcadores no índice
evitam reler os dias já processados. A falha de listagem é tolerada com lista
vazia e a falha por item não interrompe os demais.
"""

import hashlib
import html
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import requests

from flowscope.application.structured_ports import RegulacaoRepository
from flowscope.domain.noticias import (
    ESCOPO_NOTICIAS,
    SECAO_CENSURAS,
    SECAO_CONDICOES,
    SECAO_GERAL,
    SECAO_PROGRAMAS,
    SECOES_ORDEM,
    classificar_tipo,
    noticia_excepcional,
)
from flowscope.domain.structured import (
    CensuraPublica,
    CondicaoExcepcional,
    NoticiaB3,
    ProgramaAquisicao,
)
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes
from flowscope.infrastructure.fii.fundamentus.normalizers import para_data

logger = logging.getLogger("flowscope")

#: Constantes e regras de domínio reexportadas para compatibilidade de imports.
__all__ = [
    "ESCOPO_NOTICIAS",
    "SECAO_CENSURAS",
    "SECAO_CONDICOES",
    "SECAO_GERAL",
    "SECAO_PROGRAMAS",
    "SECOES_ORDEM",
    "classificar_tipo",
    "noticia_excepcional",
]


#: Subpasta do cache de notícias sob o diretório de cache.
PASTA_NOTICIAS = "noticias"

#: Granularidade (em dias) da carga da "Geral": um dia por vez.
DIAS_LOTE = 1

#: Itens acumulados antes de gravar o índice, reduzindo as regravações.
_LOTE_INDICE = 25

#: Período (em dias) de retrocesso da carga da "Geral" (aproximadamente 1 ano).
DIAS_PERIODO = 365

#: Timeout padrão do download do corpo do artigo.
_TIMEOUT = 30

_UM_DIA = timedelta(days=1)


@dataclass(frozen=True)
class ItemNoticia:
    """Item da sub-aba "Notícias" unificado entre as quatro fontes.

    ``url`` é preenchida apenas para as notícias do Plantão B3; sem URL, o
    próprio item é o conteúdo (``conteudo``). ``chave_base`` é a identidade
    estável usada para a chave de cache quando não há URL.
    """

    secao: str
    chave_base: str
    titulo: str
    data_publicacao: str
    categoria: str
    url: str | None = None
    conteudo: str | None = None


def item_de_noticia(noticia: NoticiaB3) -> ItemNoticia:
    """Monta um item da sub-aba a partir de uma notícia do Plantão B3.

    A ``categoria`` da "Geral" é o tipo típico da notícia (ano → mês → tipo na
    árvore), e não a agência; títulos fora dos tipos conhecidos caem em "Outros".
    """
    titulo = noticia.titulo or ""
    return ItemNoticia(
        secao=SECAO_GERAL,
        chave_base="|".join(
            [
                SECAO_GERAL,
                noticia.data_publicacao or "",
                noticia.agencia or "",
                titulo,
            ]
        ),
        titulo=titulo,
        data_publicacao=noticia.data_publicacao,
        categoria=classificar_tipo(titulo),
        url=noticia.url,
    )


def item_de_censura(censura: CensuraPublica) -> ItemNoticia:
    """Monta um item da sub-aba a partir de uma censura pública."""
    titulo = censura.titulo or "Censura pública"
    if censura.ticker and f"({censura.ticker})" not in titulo:
        titulo = f"{titulo} ({censura.ticker})"
    return ItemNoticia(
        secao=SECAO_CENSURAS,
        chave_base="|".join(
            [
                SECAO_CENSURAS,
                censura.data or "",
                censura.ticker or "",
                censura.titulo or "",
            ]
        ),
        titulo=titulo,
        data_publicacao=censura.data,
        categoria=censura.ticker or "—",
        conteudo=censura.to_text(),
    )


def item_de_condicao(condicao: CondicaoExcepcional) -> ItemNoticia:
    """Monta um item da sub-aba a partir de uma condição excepcional."""
    return ItemNoticia(
        secao=SECAO_CONDICOES,
        chave_base="|".join(
            [
                SECAO_CONDICOES,
                condicao.companhia or "",
                condicao.data_concessao or "",
                condicao.condicao or "",
            ]
        ),
        titulo=condicao.companhia or "Condição excepcional",
        data_publicacao=condicao.data_concessao or "",
        categoria=condicao.segmento or "—",
        conteudo=condicao.to_text(),
    )


def item_de_programa(programa: ProgramaAquisicao) -> ItemNoticia:
    """Monta um item da sub-aba a partir de um programa de aquisição."""
    titulo = programa.empresa or "Programa de aquisição"
    if programa.quantidade:
        titulo = f"{titulo} — {programa.quantidade}"
    return ItemNoticia(
        secao=SECAO_PROGRAMAS,
        chave_base="|".join(
            [
                SECAO_PROGRAMAS,
                programa.empresa or "",
                programa.data_inicio or "",
                programa.data_fim or "",
                programa.quantidade or "",
            ]
        ),
        titulo=titulo,
        data_publicacao=programa.data_inicio or programa.data_aprovacao or "",
        categoria=programa.empresa or "—",
        conteudo=programa.to_text(),
    )


def chave_item(item: ItemNoticia) -> str:
    """Deriva a chave estável do item a partir da URL ou da identidade base."""
    url = (item.url or "").strip()
    base = url or item.chave_base
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def fontes_noticias(
    repository: RegulacaoRepository,
    reference_date: date,
    palavra: str | None = None,
) -> list[tuple[str, Callable[[], list[ItemNoticia]]]]:
    """Retorna as fontes na ordem de exibição, cada uma como carga preguiçosa.

    A listagem de cada fonte é adiada para o momento do consumo, permitindo
    anunciar o status da carga antes de consultar a B3. As fontes regulatórias
    são leves (poucas requisições, sem download por item); a "Geral" é a carga
    pesada e por isso vem por último.
    """
    return [
        (
            SECAO_CENSURAS,
            lambda: _itens_de_fonte(repository, "listar_censuras", item_de_censura),
        ),
        (
            SECAO_CONDICOES,
            lambda: _itens_de_fonte(
                repository, "listar_condicoes_excepcionais", item_de_condicao
            ),
        ),
        (
            SECAO_PROGRAMAS,
            lambda: _itens_de_fonte(
                repository,
                "listar_programas_aquisicao",
                item_de_programa,
                reference_date,
            ),
        ),
        (
            SECAO_GERAL,
            lambda: [
                item_de_noticia(noticia)
                for noticia in listar_periodo(repository, reference_date, palavra)
            ],
        ),
    ]


def listar_itens(
    repository: RegulacaoRepository,
    reference_date: date,
    palavra: str | None = None,
) -> list[ItemNoticia]:
    """Lista os itens das quatro fontes, deixando a "Geral" por último."""
    return [
        item
        for _secao, listar in fontes_noticias(repository, reference_date, palavra)
        for item in listar()
    ]


def _itens_de_fonte(
    repository: RegulacaoRepository,
    metodo: str,
    converter: Callable[[object], ItemNoticia],
    *args: object,
) -> list[ItemNoticia]:
    """Lista e converte uma fonte, tolerando ausência do método e falhas."""
    funcao = getattr(repository, metodo, None)
    if funcao is None:
        return []
    try:
        return [converter(objeto) for objeto in funcao(*args)]
    except Exception:  # indisponibilidade de uma fonte não interrompe as demais
        logger.warning("Falha ao listar %s", metodo, exc_info=True)
        return []


def html_do_item(item: ItemNoticia) -> bytes:
    """Monta o HTML mínimo de um item sem URL, usando o próprio item."""
    titulo = html.escape(item.titulo or "")
    corpo = html.escape(item.conteudo or item.titulo or "")
    return (
        "<html><body>"
        f"<h1>{titulo}</h1><pre>{corpo}</pre>"
        "</body></html>"
    ).encode()


def chave_noticia(noticia: NoticiaB3) -> str:
    """Deriva a chave estável da notícia a partir da URL ou dos metadados."""
    url = (noticia.url or "").strip()
    if url:
        base = url
    else:
        base = "|".join(
            [
                noticia.data_publicacao or "",
                noticia.agencia or "",
                noticia.titulo or "",
            ]
        )
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def data_noticia(texto: object, fallback: date) -> date:
    """Interpreta a data de publicação da notícia, ou usa o fallback."""
    if texto:
        iso = _data_iso(texto)
        if iso is not None:
            return iso
        convertida = para_data(str(texto))
        if convertida is not None:
            return convertida
    return fallback


def listar_periodo(
    repository: RegulacaoRepository,
    reference_date: date,
    palavra: str | None = None,
) -> list[NoticiaB3]:
    """Lista as notícias excepcionais do último ano, dia a dia.

    A leitura é feita um dia por vez e os resultados são acumulados e
    deduplicados pela chave estável; apenas eventos excepcionais são mantidos.
    """
    resultado: list[NoticiaB3] = []
    vistos: set[str] = set()
    for inicio, fim in janelas_geral(reference_date):
        for noticia in _listar_janela(repository, inicio, fim, palavra):
            if not noticia_excepcional(noticia.titulo):
                continue
            chave = chave_noticia(noticia)
            if chave in vistos:
                continue
            vistos.add(chave)
            resultado.append(noticia)
    return resultado


def janelas_geral(
    reference_date: date,
    mais_antiga: date | None = None,
    referencia: date | None = None,
) -> list[tuple[date, date]]:
    """Dias cobrindo o último ano, do mais recente ao mais antigo.

    O dia mais recente é sempre incluído. Em seguida, preenche a eventual
    lacuna entre a referência da carga anterior (``referencia``) e o dia mais
    recente; por fim, retrocede a partir da data mais antiga já processada
    (``mais_antiga``) até o limite de um ano, permitindo retomar uma carga
    interrompida. Os dias já processados são pulados.
    """
    limite = reference_date - timedelta(days=DIAS_PERIODO - 1)
    primeiro_inicio = max(limite, reference_date - timedelta(days=DIAS_LOTE - 1))
    janelas: list[tuple[date, date]] = [(primeiro_inicio, reference_date)]

    fim = reference_date - timedelta(days=DIAS_LOTE)
    piso = (referencia + _UM_DIA) if referencia is not None else limite
    while fim >= max(limite, piso):
        inicio = max(limite, piso, fim - timedelta(days=DIAS_LOTE - 1))
        janelas.append((inicio, fim))
        fim = inicio - _UM_DIA

    if mais_antiga is not None and mais_antiga > limite:
        fim = mais_antiga - _UM_DIA
        while fim >= limite:
            inicio = max(limite, fim - timedelta(days=DIAS_LOTE - 1))
            janelas.append((inicio, fim))
            fim = inicio - _UM_DIA
    return janelas


def _listar_janela(
    repository: RegulacaoRepository,
    inicio: date,
    fim: date,
    palavra: str | None,
) -> Iterable[NoticiaB3]:
    """Lista um dia, tolerando indisponibilidade com lista vazia."""
    try:
        return list(
            repository.listar_noticias(
                data_inicio=inicio, data_fim=fim, palavra=palavra
            )
        )
    except Exception:  # indisponibilidade não deve interromper a interface
        logger.warning(
            "Falha ao listar notícias de %s a %s", inicio, fim, exc_info=True
        )
        return []


def itens_de_janela(
    repository: RegulacaoRepository,
    inicio: date,
    fim: date,
    palavra: str | None = None,
) -> list[ItemNoticia] | None:
    """Lista e converte os itens excepcionais de um lote, sem duplicatas.

    Retorna ``None`` quando a listagem do lote falha, para que a aquisição não
    marque o lote como processado e possa retomá-lo depois.
    """
    try:
        noticias = list(
            repository.listar_noticias(
                data_inicio=inicio, data_fim=fim, palavra=palavra
            )
        )
    except Exception:  # indisponibilidade não marca o lote como processado
        logger.warning(
            "Falha ao listar notícias de %s a %s", inicio, fim, exc_info=True
        )
        return None
    itens: list[ItemNoticia] = []
    vistos: set[str] = set()
    for noticia in noticias:
        if not noticia_excepcional(noticia.titulo):
            continue
        chave = chave_noticia(noticia)
        if chave in vistos:
            continue
        vistos.add(chave)
        itens.append(item_de_noticia(noticia))
    return itens


def baixar_noticia(url: str, *, timeout: int = _TIMEOUT) -> bytes | None:
    """Baixa o HTML do artigo, devolvendo ``None`` em qualquer falha."""
    try:
        resposta = requests.get(
            url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}
        )
        resposta.raise_for_status()
    except requests.RequestException:
        logger.warning("Falha ao baixar notícia %s", url, exc_info=True)
        return None
    return resposta.content or None


class NoticiasCache:
    """Cache próprio do HTML das notícias, sem sobrescrever conteúdo existente."""

    def __init__(
        self: "NoticiasCache", cache_dir: Path | None = None
    ) -> None:
        """Inicializa o cache na raiz informada ou na raiz padrão do FlowScope."""
        base = cache_dir if cache_dir is not None else CacheManager().get_cache_dir()
        self._base = Path(base)

    @property
    def base_dir(self: "NoticiasCache") -> Path:
        """Retorna a raiz de cache usada para compor as chaves das stores."""
        return self._base

    def caminho(self: "NoticiasCache", chave: str, data: date) -> Path:
        """Resolve o caminho ``noticias/<AAAA>/<MM>/<chave>.html``."""
        return (
            self._base
            / PASTA_NOTICIAS
            / f"{data.year:04d}"
            / f"{data.month:02d}"
            / f"{chave}.html"
        )

    def existe(self: "NoticiasCache", chave: str, data: date) -> bool:
        """Indica se já há conteúdo cacheado para a chave e data."""
        return self.caminho(chave, data).is_file()

    def gravar(
        self: "NoticiasCache", chave: str, data: date, conteudo: bytes
    ) -> None:
        """Grava o HTML do artigo de forma atômica, se ainda não existir."""
        caminho = self.caminho(chave, data)
        if caminho.is_file():
            return
        _atomic_write_bytes(caminho, conteudo)

    def ler(self: "NoticiasCache", chave: str, data: date) -> bytes | None:
        """Lê o HTML cacheado, tolerando ausência e falha de leitura."""
        try:
            return self.caminho(chave, data).read_bytes()
        except OSError:
            return None


def _data_iso(valor: object) -> date | None:
    """Interpreta uma data ISO (com ou sem horário) como ``date``."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None
