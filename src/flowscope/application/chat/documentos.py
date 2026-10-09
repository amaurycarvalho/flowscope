"""Ramo ``/documentos`` da árvore de conhecimento sobre o cache local.

O ramo é estritamente somente-leitura de cache: lê os resumos curtos e longos do
catálogo de documentos e o texto integral já extraído e em cache. Cada ticker
expõe um índice compacto e um nó por documento recuperável, com as folhas
``curto``, ``longo`` e ``texto`` do próprio documento. Documentos pendentes de
resumo ou de extração são omitidos em silêncio — nenhum resumo é gerado e nenhum
texto é extraído durante o chat.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from hashlib import sha1
from pathlib import Path

from flowscope.application.chat.arvore import No, no_folha, no_interno
from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.catalogo import (
    CatalogoDocumentos,
    chave_documento,
)
from flowscope.application.fundamental.linhas import mes_ano
from flowscope.domain.documents import CatalogoTicker, DocumentoArquivo

logger = logging.getLogger("flowscope")

#: Teto de caracteres do índice compacto de documentos por ticker.
TETO_INDICE = 6000

#: Tamanho do trecho do resumo embutido em cada linha do índice.
TAMANHO_TRECHO_INDICE = 140

#: Raízes de cache onde vivem os catálogos por ticker.
_RAIZES = ("bdr", "informe-mensal", "documentos-relevantes")


@dataclass(frozen=True)
class DocumentoEscopo:
    """Documento do escopo do chat com a sua chave estável e resumos."""

    ticker: str
    nome: str
    categoria: str
    ano: int
    mes: int
    chave: str
    caminho: Path
    short_summary: str | None = None
    long_summary: str | None = None


def _achatar(catalogo: CatalogoTicker) -> list[DocumentoArquivo]:
    """Percorre a hierarquia do catálogo devolvendo os arquivos em ordem."""
    arquivos: list[DocumentoArquivo] = []
    for ano in catalogo.anos:
        for mes in ano.meses:
            for categoria in mes.categorias:
                arquivos.extend(categoria.arquivos)
    return arquivos


def chave_curta_documento(chave: str) -> str:
    """Deriva a chave curta e estável do nó de um documento."""
    return "d" + sha1(chave.encode("utf-8")).hexdigest()[:10]


def _trecho(texto: str | None, limite: int = TAMANHO_TRECHO_INDICE) -> str:
    """Extrai um trecho curto do resumo, cortado em fim de frase ou palavra.

    O índice embute este trecho para a LLM distinguir os documentos pelo
    conteúdo (ex.: um RG mensal de uma carta da gestora) sem um segundo salto.
    """
    if not texto:
        return ""
    limpo = " ".join(texto.split())
    if len(limpo) <= limite:
        return limpo
    corte = limpo[:limite]
    for separador in (". ", "; ", "! ", "? "):
        pos = corte.rfind(separador)
        if pos > limite // 2:
            return corte[: pos + 1].strip()
    pos = corte.rfind(" ")
    if pos > limite // 2:
        return corte[:pos].strip()
    return corte.strip()


class FonteDocumentos:
    """Provedor do ramo ``/documentos`` a partir do catálogo em cache."""

    def __init__(
        self: FonteDocumentos,
        catalog: CatalogoDocumentos | None = None,
        rg_chaves: Callable[[str], set[str]] | None = None,
    ) -> None:
        """Guarda o catálogo e o resolvedor de RGs.

        ``rg_chaves`` devolve, por ticker, as chaves dos documentos que são
        Relatórios Gerenciais mensais avaliados (fonte: ledger de guidance). A
        categoria de cache não distingue um RG mensal de cartas/comunicados.
        """
        self._catalog = catalog
        self._rg_chaves = rg_chaves

    def construir(self: FonteDocumentos) -> No:
        """Constrói o ramo ``/documentos`` com os documentos recuperáveis."""
        raiz = no_interno("/documentos", "documentos")
        tickers_no = no_interno("/documentos/tickers", "tickers")
        raiz.filho(tickers_no)
        for ticker in self._tickers_em_cache():
            no_ticker = self._construir_ticker(ticker)
            if no_ticker.folha:
                continue
            raiz.filho(no_ticker)
            tickers_no.filho(
                no_folha(
                    f"/documentos/tickers/{ticker}",
                    ticker,
                    conteudo=ticker,
                    campos={"ticker": ticker},
                )
            )
        return raiz

    def _construir_ticker(self: FonteDocumentos, ticker: str) -> No:
        """Constrói ``/documentos/<ticker>`` com índice e nó por documento.

        Só entram os documentos recuperáveis (resumo ou texto em cache); o texto
        integral é lido do cache uma única vez por ticker e devolvido sob demanda
        por ``obter``. Um ticker sem documentos recuperáveis fica como folha e é
        omitido por ``construir``.
        """
        escopos = self._escopo_ticker(ticker)
        no_ticker = no_interno(f"/documentos/{ticker}", ticker)
        base = f"/documentos/{ticker}"
        textos = self._mapa_textos(self._text_store, ticker)
        recuperaveis = [e for e in escopos if self._recuperavel(e, textos)]
        if not recuperaveis:
            return no_ticker
        indice = self._indice(recuperaveis, textos, self._rgs(ticker))
        no_ticker.filho(
            no_folha(
                f"{base}/indice",
                "indice",
                conteudo=indice,
                campos={"indice": indice},
            )
        )
        for escopo in recuperaveis:
            no_ticker.filho(self._documento(base, escopo, textos))
        return no_ticker

    def _documento(
        self: FonteDocumentos,
        base: str,
        escopo: DocumentoEscopo,
        textos: dict[str, str],
    ) -> No:
        """Monta o nó de um documento com metadados e as folhas com conteúdo."""
        chave = chave_curta_documento(escopo.chave)
        no_doc = no_interno(
            f"{base}/{chave}", escopo.nome, metadado=self._rotulo(escopo)
        )
        no_doc.campos.update(
            {
                "categoria": escopo.categoria,
                "periodo": self._periodo(escopo),
                "nome": escopo.nome,
            }
        )
        if escopo.short_summary:
            no_doc.filho(self._folha_resumo(base, chave, "curto", escopo.short_summary))
        if escopo.long_summary:
            no_doc.filho(self._folha_resumo(base, chave, "longo", escopo.long_summary))
        texto = textos.get(escopo.chave) or ""
        if texto:
            no_doc.filho(
                no_folha(
                    f"{base}/{chave}/texto",
                    "texto",
                    metadado="texto integral",
                    carregar=lambda t=texto: t,
                    campo_pesado="texto",
                )
            )
        return no_doc

    @staticmethod
    def _folha_resumo(base: str, chave: str, segmento: str, conteudo: str) -> No:
        """Monta a folha de resumo de um documento, com rótulo legível."""
        rotulo = "resumo longo" if segmento == "longo" else "resumo curto"
        return no_folha(
            f"{base}/{chave}/{segmento}",
            segmento,
            conteudo=conteudo,
            metadado=rotulo,
            campos={"resumo": conteudo},
        )

    def _rgs(self: FonteDocumentos, ticker: str) -> set[str]:
        """Resolve as chaves dos RGs mensais avaliados do ticker, tolerando falha."""
        if self._rg_chaves is None:
            return set()
        try:
            return set(self._rg_chaves(ticker))
        except Exception:
            logger.warning(
                "Falha ao resolver os RGs mensais de %s", ticker, exc_info=True
            )
            return set()

    def _indice(
        self: FonteDocumentos,
        escopos: list[DocumentoEscopo],
        textos: dict[str, str],
        rg_chaves: set[str],
    ) -> str:
        """Monta o índice compacto dos documentos, do mais recente ao antigo.

        Cada linha traz um trecho do resumo (para distinguir RG de carta) e o
        tipo ``RG mensal``/``documento``; quando há mais de um documento no mesmo
        mês e categoria, sinaliza a posição.
        """
        grupos: dict[tuple[int, int, str], int] = {}
        for escopo in escopos:
            chave_grupo = (escopo.ano, escopo.mes, escopo.categoria)
            grupos[chave_grupo] = grupos.get(chave_grupo, 0) + 1
        vistos: dict[tuple[int, int, str], int] = {}
        linhas: list[str] = []
        total = 0
        for escopo in escopos:
            chave_grupo = (escopo.ano, escopo.mes, escopo.categoria)
            vistos[chave_grupo] = vistos.get(chave_grupo, 0) + 1
            linha = self._linha_indice(
                escopo,
                textos,
                rg_chaves,
                vistos[chave_grupo],
                grupos[chave_grupo],
            )
            if linhas and total + len(linha) + 1 > TETO_INDICE:
                break
            linhas.append(linha)
            total += len(linha) + 1
        return "\n".join(linhas)[:TETO_INDICE]

    @staticmethod
    def _linha_indice(
        escopo: DocumentoEscopo,
        textos: dict[str, str],
        rg_chaves: set[str],
        posicao: int,
        total_grupo: int,
    ) -> str:
        """Formata uma linha do índice com tipo, conteúdo, chave e trecho."""
        tipo = "RG mensal" if escopo.chave in rg_chaves else "documento"
        marcadores: list[str] = []
        if escopo.short_summary or escopo.long_summary:
            marcadores.append("resumo")
        if textos.get(escopo.chave):
            marcadores.append("texto")
        sufixo = "+".join(marcadores) or "-"
        duplicados = f"; {posicao}/{total_grupo}" if total_grupo > 1 else ""
        linha = (
            f"{escopo.ano:04d}/{escopo.mes:02d} — {escopo.categoria} — "
            f"{escopo.nome} (chave: {chave_curta_documento(escopo.chave)}; "
            f"{tipo}; {sufixo}{duplicados})"
        )
        trecho = _trecho(escopo.short_summary or escopo.long_summary)
        if trecho:
            linha += f' — prévia: "{trecho}"'
        return linha

    @staticmethod
    def _recuperavel(escopo: DocumentoEscopo, textos: dict[str, str]) -> bool:
        """Indica se o documento tem resumo ou texto em cache."""
        return bool(
            escopo.short_summary
            or escopo.long_summary
            or textos.get(escopo.chave)
        )

    @staticmethod
    def _periodo(escopo: DocumentoEscopo) -> str:
        """Formata o período do documento como ``AAAA/MM``."""
        return f"{escopo.ano:04d}/{escopo.mes:02d}"

    def _rotulo(self: FonteDocumentos, escopo: DocumentoEscopo) -> str:
        """Monta o rótulo legível do documento: categoria, período e nome."""
        if 1 <= escopo.mes <= 12 and escopo.ano > 0:
            periodo = mes_ano(date(escopo.ano, escopo.mes, 1))
        else:
            periodo = self._periodo(escopo)
        return f"{escopo.categoria} — {periodo} — {escopo.nome}"

    def _escopo_ticker(self: FonteDocumentos, ticker: str) -> list[DocumentoEscopo]:
        """Monta os documentos do escopo a partir do catálogo de um ticker."""
        if self._catalog is None:
            return []
        return [
            DocumentoEscopo(
                ticker=arquivo.ticker,
                nome=arquivo.nome,
                categoria=arquivo.categoria,
                ano=arquivo.ano,
                mes=arquivo.mes,
                chave=chave_documento(arquivo.caminho, self._catalog.base_dir),
                caminho=arquivo.caminho,
                short_summary=arquivo.short_summary,
                long_summary=arquivo.long_summary,
            )
            for arquivo in _achatar(self._catalog.catalogo(ticker))
        ]

    @staticmethod
    def _mapa_textos(store: DocumentTextStore | None, ticker: str) -> dict[str, str]:
        """Obtém o mapa de textos do ticker lendo o cache no máximo uma vez."""
        if store is None:
            return {}
        obter_mapa = getattr(store, "textos", None)
        if callable(obter_mapa):
            try:
                return dict(obter_mapa(ticker))
            except Exception:
                logger.warning("Falha ao ler os textos de %s", ticker, exc_info=True)
                return {}
        return {}

    def _tickers_em_cache(self: FonteDocumentos) -> list[str]:
        """Lista os tickers com catálogo de documentos em cache."""
        if self._catalog is None:
            return []
        base = self._catalog.base_dir
        tickers: set[str] = set()
        for raiz in _RAIZES:
            pasta = base / raiz
            if pasta.is_dir():
                tickers.update(item.name for item in pasta.iterdir() if item.is_dir())
        return sorted(tickers)

    @property
    def _text_store(self: FonteDocumentos) -> DocumentTextStore | None:
        """Store de textos associado ao catálogo."""
        return self._catalog.text_store if self._catalog is not None else None
