"""Resumo em lote headless dos documentos e das notícias pendentes.

Constrói uma fachada headless mínima (sem Tk) sobre o núcleo de lote da
aplicação e resolve os itens pendentes a partir do catálogo local. É reusado
pelos subcomandos ``flowscope resumir ...`` e pela preparação do ``mcp``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from flowscope.application.document_preview import (
    SELETOR_CONTEUDO_DETALHE,
    ExtracaoTexto,
    tem_texto,
)
from flowscope.application.documentos.lote_execucao import executar_resumos
from flowscope.application.documentos.preparacao import PreparacaoTexto
from flowscope.application.extracao_orcada import extrair_arquivo_com_orcamento
from flowscope.application.noticias.lote import pendentes_ordenados
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.noticias import SECAO_GERAL

logger = logging.getLogger("flowscope")


class AcaoError(Exception):
    """Erro de domínio recuperável de um subcomando de ação."""

    def __init__(self: AcaoError, motivo: str, detalhe: str = "") -> None:
        """Guarda o motivo canônico e um detalhe legível."""
        super().__init__(motivo, detalhe)
        self.motivo = motivo
        self.detalhe = detalhe


def last_tickers() -> list[str]:
    """Lê a watchlist carregada (``last_tickers``) do ``config.json``."""
    from flowscope.infrastructure.referencia import carregar_config

    tickers = carregar_config().get("last_tickers")
    if not isinstance(tickers, list):
        return []
    return [t for t in tickers if isinstance(t, str) and t.strip()]


def progresso_stderr(mensagem: str) -> None:
    """Publica uma mensagem de progresso em ``stderr``."""
    import sys

    print(mensagem, file=sys.stderr)


class _ContextoHeadless:
    """Contexto mínimo de progresso/cancelamento para o lote headless."""

    def __init__(self: _ContextoHeadless) -> None:
        """Acumula os erros publicados durante o lote."""
        self.erros: list[BaseException] = []

    def raise_if_cancelled(self: _ContextoHeadless) -> None:
        """Não há cancelamento interativo no modo headless."""

    def descrever(self: _ContextoHeadless, texto: str) -> None:
        """Publica a descrição do item corrente em ``stderr``."""
        progresso_stderr(texto)

    def progress(
        self: _ContextoHeadless,
        detalhe: str = "",
        atual: int | None = None,
        total: int | None = None,
        dados: object = None,
    ) -> None:
        """Publica o progresso do lote em ``stderr``."""
        sufixo = f" ({atual}/{total})" if atual is not None else ""
        if detalhe:
            progresso_stderr(f"{detalhe}{sufixo}")

    def erro(
        self: _ContextoHeadless, excecao: BaseException, dados: object = None
    ) -> None:
        """Acumula e publica a falha do item em ``stderr``."""
        self.erros.append(excecao)
        progresso_stderr(f"ERRO: {excecao}")

    def resultado(
        self: _ContextoHeadless, valor: object, dados: object = None
    ) -> None:
        """Ignora o resultado por item (a contagem é derivada do desfecho)."""


class _PainelHeadless:
    """Fachada headless mínima para o lote de resumos."""

    def __init__(
        self: _PainelHeadless,
        summary: object,
        text_store: object,
        guidance: object | None = None,
        seletor: str | None = None,
        baixar_vinculo: Callable | None = None,
        resolver_vinculo: bool = False,
    ) -> None:
        """Guarda os serviços de resumo, texto, guidance e extração."""
        self._summary = summary
        self._text_store = text_store
        self._guidance = guidance
        self._seletor = seletor
        self._baixar_vinculo = baixar_vinculo
        self._resolver_vinculo = resolver_vinculo

    def chave(self: _PainelHeadless, arquivo: DocumentoArquivo) -> str:
        """Chave de texto/resumo do documento."""
        return self._summary.chave(arquivo)

    def texto_cacheado(
        self: _PainelHeadless, arquivo: DocumentoArquivo
    ) -> str | None:
        """Texto persistido do documento, se houver."""
        return self._text_store.obter(arquivo.ticker, self.chave(arquivo))

    def preparar_texto(
        self: _PainelHeadless, arquivo: DocumentoArquivo, senha: str | None = None
    ) -> ExtracaoTexto:
        """Extrai e persiste o texto do documento (resultado definitivo)."""
        return PreparacaoTexto(
            ler_cache=self.texto_cacheado,
            extrair=self._extrair,
            chave=self.chave,
            salvar=self._text_store.salvar,
        ).preparar(arquivo, senha)

    def _extrair(
        self: _PainelHeadless, arquivo: DocumentoArquivo, senha: str | None
    ) -> ExtracaoTexto:
        """Extrai o texto e, quando aplicável, resolve o documento vinculado."""
        resultado = extrair_arquivo_com_orcamento(
            arquivo.caminho, self._seletor, senha=senha
        )
        if self._resolver_vinculo:
            return self._resolver(arquivo, resultado, senha)
        return resultado

    def _resolver(
        self: _PainelHeadless,
        arquivo: DocumentoArquivo,
        resultado: ExtracaoTexto,
        senha: str | None,
    ) -> ExtracaoTexto:
        """Resolve o documento vinculado da notícia "Geral" (CVM RAD/FNET)."""
        if getattr(arquivo, "secao", "") != SECAO_GERAL or self._baixar_vinculo is None:
            return resultado
        try:
            vinculo = self._baixar_vinculo(resultado.texto, senha)
        except Exception:
            logger.warning(
                "Falha ao resolver o vínculo de %s", arquivo.caminho, exc_info=True
            )
            return resultado
        if vinculo is None or not tem_texto(vinculo.texto):
            return resultado
        return vinculo

    def persistir_no_lote(self: _PainelHeadless) -> bool:
        """Grava cada resumo na thread de trabalho."""
        return True

    def gerar_e_persistir(
        self: _PainelHeadless, arquivo: DocumentoArquivo, texto: str
    ) -> object:
        """Gera o resumo e o persiste."""
        return self._summary.gerar_e_persistir(arquivo, texto)

    def gerar_resumo_estrito(
        self: _PainelHeadless, arquivo: DocumentoArquivo, texto: str
    ) -> object:
        """Gera o resumo propagando falhas, sem gravar."""
        return self._summary.gerar_estrito(arquivo, texto)

    def avaliar_guidance(
        self: _PainelHeadless,
        arquivo: DocumentoArquivo,
        texto: str,
        resumo: object = None,
    ) -> object:
        """Avalia o guidance do documento, quando há serviço."""
        if self._guidance is None:
            return None
        return self._guidance.avaliar(arquivo, texto, resumo)


def _exigir_llm(disponivel: bool) -> None:
    """Falha com erro estruturado quando a LLM não está configurada."""
    if not disponivel:
        raise AcaoError(
            "llm_nao_configurada",
            "nenhum provedor de LLM configurado; configure antes de resumir",
        )


def _pendentes_documentos(nucleo: object, ticker: str) -> list[DocumentoArquivo]:
    """Resolve os documentos pendentes (resumo e guidance) de um ticker."""
    textos = _textos_do_ticker(nucleo, ticker)
    arquivos = _arquivos_do_ticker(nucleo, ticker)
    pendentes = [
        arquivo
        for arquivo in arquivos
        if nucleo.documentos.summary_service.precisa_resumo_ausente(
            arquivo, sem_texto=_sem_texto(textos, nucleo, arquivo)
        )
    ]
    pendentes.extend(_rgs_pendentes(nucleo, ticker, arquivos))
    return pendentes


def _arquivos_do_ticker(nucleo: object, ticker: str) -> list[DocumentoArquivo]:
    """Achata o catálogo do ticker na lista de arquivos."""
    catalogo = nucleo.documentos.catalogo_use_case.executar(ticker)
    return [
        arquivo
        for ano in catalogo.anos
        for mes in ano.meses
        for categoria in mes.categorias
        for arquivo in categoria.arquivos
    ]


def _textos_do_ticker(nucleo: object, ticker: str) -> dict:
    """Lê os textos persistidos do ticker, quando o store em massa suportar."""
    store = nucleo.documentos.text_store
    bulk = getattr(store, "textos", None)
    if not callable(bulk):
        return {}
    try:
        return bulk(ticker) or {}
    except Exception:
        return {}


def _sem_texto(textos: dict, nucleo: object, arquivo: DocumentoArquivo) -> bool:
    """Indica se o texto do documento é marcador de ausência ou branco."""
    chave = nucleo.documentos.summary_service.chave(arquivo)
    texto = textos.get(chave)
    return texto is not None and not tem_texto(texto)


def _rgs_pendentes(
    nucleo: object, ticker: str, arquivos: list[DocumentoArquivo]
) -> list[DocumentoArquivo]:
    """Resolve os RGs já resumidos pendentes de avaliação de guidance."""
    servico = nucleo.documentos.guidance_service
    com_resumo = [a for a in arquivos if a.long_summary is not None]
    try:
        pendentes, _ = servico.estado_arvore(ticker, com_resumo)
    except Exception:
        return []
    caminhos = {a.caminho for a in pendentes}
    return [a for a in arquivos if a.caminho in caminhos]


def _erro_resumo(excecao: BaseException) -> dict:
    """Serializa a falha de um ticker no lote de resumos."""
    return {"erro": {"motivo": "falha_resumo", "detalhe": str(excecao)}}


def _processar_ticker(
    nucleo: object, painel: _PainelHeadless, ticker: str
) -> tuple[dict, bool]:
    """Processa os pendentes do ticker e devolve ``(desfecho, falhou)``."""
    contexto = _ContextoHeadless()
    progresso_stderr(f"Resumos de {ticker}...")
    try:
        pendentes = _pendentes_documentos(nucleo, ticker)
        resultado = executar_resumos(contexto, painel, pendentes)
    except Exception as exc:
        logger.warning("Falha ao resumir documentos de %s", ticker, exc_info=True)
        return _erro_resumo(exc), True
    if contexto.erros:
        return _erro_resumo(contexto.erros[0]), True
    return _resumo_json(resultado, len(pendentes)), False


def _normalizar_tickers(tickers: list[str]) -> list[str]:
    """Normaliza e deduplica os tickers preservando a ordem."""
    return list(dict.fromkeys(t.strip().upper() for t in tickers if t.strip()))


def resumir_documentos(ticker: str | None = None) -> dict:
    """Processa os pendentes de um ticker ou de toda a watchlist.

    Com ``ticker``, valida contra ``last_tickers`` e preserva o formato
    agregado. Sem ``ticker``, percorre a watchlist uma única vez, captura a
    falha de cada ticker sem abortar o lote e devolve ``resultados`` e
    ``falha``.
    """
    watchlist = last_tickers()
    if ticker is not None:
        alvo = ticker.strip().upper()
        if alvo not in watchlist:
            raise AcaoError("ticker_fora_watchlist", alvo)
        alvos = [alvo]
    else:
        alvos = _normalizar_tickers(watchlist)
        if not alvos:
            raise AcaoError("watchlist_ausente", "last_tickers vazio ou ausente")
    from flowscope.presentation.composicao import montar_nucleo

    nucleo = montar_nucleo()
    _exigir_llm(nucleo.documentos.llm_available())
    painel = _PainelHeadless(
        nucleo.documentos.summary_service,
        nucleo.documentos.text_store,
        nucleo.documentos.guidance_service,
    )
    if ticker is not None:
        pendentes = _pendentes_documentos(nucleo, alvos[0])
        resultado = executar_resumos(_ContextoHeadless(), painel, pendentes)
        return _resumo_json(resultado, len(pendentes))
    desfechos = {alvo: _processar_ticker(nucleo, painel, alvo) for alvo in alvos}
    return {
        "resultados": {alvo: desfecho for alvo, (desfecho, _) in desfechos.items()},
        "falha": any(falhou for _, falhou in desfechos.values()),
    }


def resumir_noticias() -> dict:
    """Processa as notícias pendentes de resumo em lote."""
    from flowscope.presentation.composicao import montar_nucleo

    nucleo = montar_nucleo()
    _exigir_llm(nucleo.noticias.llm_available())
    arquivos = list(nucleo.noticias.catalogo.arquivos())
    textos = _textos_noticias(nucleo)
    pendentes = pendentes_ordenados(
        arquivos,
        precisa=lambda arquivo: _precisa_noticia(nucleo, arquivo, textos),
    )
    painel = _PainelHeadless(
        nucleo.noticias.summary_service,
        nucleo.noticias.text_store,
        seletor=SELETOR_CONTEUDO_DETALHE,
        baixar_vinculo=nucleo.noticias.baixar_vinculo,
        resolver_vinculo=True,
    )
    resultado = executar_resumos(_ContextoHeadless(), painel, pendentes)
    return _resumo_json(resultado, len(pendentes))


def _textos_noticias(nucleo: object) -> dict:
    """Lê os textos de notícias em massa, quando suportado."""
    bulk = getattr(nucleo.noticias.text_store, "textos", None)
    if not callable(bulk):
        return {}
    try:
        return bulk("noticias") or {}
    except Exception:
        return {}


def _precisa_noticia(nucleo: object, arquivo: DocumentoArquivo, textos: dict) -> bool:
    """Indica se a notícia precisa de resumo e não tem ausência definitiva."""
    chave = nucleo.noticias.summary_service.chave(arquivo)
    texto = textos.get(chave)
    sem_texto = texto is not None and not tem_texto(texto)
    return nucleo.noticias.summary_service.precisa_resumo_ausente(
        arquivo, sem_texto=sem_texto
    )


def _resumo_json(resultado: object, total: int) -> dict:
    """Serializa o desfecho do lote de resumos."""
    return {
        "pendentes": total,
        "sem_texto": resultado.sem_texto,
        "nao_conclusivos": len(resultado.nao_conclusivos),
        "apontadores": len(resultado.apontadores),
    }
