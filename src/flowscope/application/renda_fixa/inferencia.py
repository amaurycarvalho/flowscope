"""Inferência de direitos e obrigações a partir dos resumos persistidos.

O caso de uso lê o catálogo em cache, seleciona apenas Relatórios Gerenciais e
Informes Mensais de FII já resumidos, chama a LLM com um prompt estável e
persiste os itens validados em um cache separado do oficial. Falhas por
documento são toleradas e o cancelamento é cooperativo.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

from flowscope.application.avaliar_guidance import CATEGORIA_RELATORIO
from flowscope.application.cancellation import CancellationToken, OperacaoCancelada
from flowscope.application.documentos.catalogo import (
    CatalogoRepository,
    chave_documento,
)
from flowscope.application.renda_fixa.inferencia_resposta import (
    SYSTEM_PROMPT,
    interpretar_resposta,
    montar_entrada,
)
from flowscope.application.renda_fixa.portas import (
    InferenciasRepository,
    TitulosRepository,
)
from flowscope.application.renda_fixa.resultados import ResultadoInferencia
from flowscope.application.resumo_documento import resumo_integro
from flowscope.domain.documents import CatalogoTicker, DocumentoArquivo
from flowscope.domain.llm import LLMPort
from flowscope.domain.renda_fixa import (
    PARSER_VERSION_INFERENCIA,
    CarteiraInferencias,
    InferenciaTitulo,
    cobertura_oficial_completa,
)

logger = logging.getLogger("flowscope")

#: Categorias cujo resumo pode originar inferências.
CATEGORIAS_ELEGIVEIS = frozenset({CATEGORIA_RELATORIO, "Informe Mensal"})

ProgressoInferencia = Callable[[int, int, str], None]
CancelarInferencia = Callable[[], None]


class InferirDireitosObrigacoesUseCase:
    """Extrai, valida e persiste direitos e obrigações dos resumos."""

    def __init__(
        self: InferirDireitosObrigacoesUseCase,
        catalogo: CatalogoRepository,
        titulos: TitulosRepository,
        inferencias: InferenciasRepository,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
        flag_habilitada: Callable[[], bool] | None = None,
        base_dir: Path | None = None,
        prompt_version: str = PARSER_VERSION_INFERENCIA,
    ) -> None:
        """Guarda as portas, a fábrica de LLM e a versão do prompt."""
        self._catalogo = catalogo
        self._titulos = titulos
        self._inferencias = inferencias
        self._llm_factory = llm_factory
        self._llm_available = llm_available
        self._flag_habilitada = flag_habilitada or (lambda: True)
        self._base_dir = Path(base_dir) if base_dir is not None else None
        self._prompt_version = prompt_version

    def disponivel(self: InferirDireitosObrigacoesUseCase) -> bool:
        """Indica se a inferência está ligada e há LLM configurada."""
        try:
            habilitada = bool(self._flag_habilitada())
        except Exception:  # configuração ilegível equivale a desligada
            return False
        if not habilitada:
            return False
        if self._llm_available is not None:
            try:
                return bool(self._llm_available())
            except Exception:
                return False
        return self._llm_factory is not None

    def precisa_inferencia(
        self: InferirDireitosObrigacoesUseCase, ticker: str
    ) -> bool:
        """Indica se o ticker tem inferência elegível ainda não persistida."""
        alvo = (ticker or "").strip().upper()
        if not alvo or not self.disponivel():
            return False
        try:
            oficial = self._titulos.ler(alvo)
            if cobertura_oficial_completa(oficial):
                return False
            documentos = self._documentos_elegiveis(alvo)
            if not documentos:
                return False
            cache = self._cache_valido(alvo)
            return any(
                not self._processado(cache, documento) for documento in documentos
            )
        except Exception:  # cache ilegível não deve habilitar a ação
            logger.warning(
                "Falha ao avaliar a inferência pendente de %s", alvo, exc_info=True
            )
            return False

    def executar(
        self: InferirDireitosObrigacoesUseCase,
        ticker: str,
        progress: ProgressoInferencia | None = None,
        cancelar: CancelarInferencia | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> ResultadoInferencia:
        """Executa a inferência dos documentos pendentes do ticker."""
        alvo = (ticker or "").strip().upper()
        checar = self._cancelar(cancelar, cancel_token)
        if not alvo or not self.disponivel():
            return ResultadoInferencia()
        self._checar(checar)
        oficial = self._titulos.ler(alvo)
        if cobertura_oficial_completa(oficial):
            return ResultadoInferencia()
        documentos = self._documentos_elegiveis(alvo)
        cache = self._cache_valido(alvo)
        pendentes = [
            documento for documento in documentos if not self._processado(cache, documento)
        ]
        if not pendentes:
            return ResultadoInferencia()
        return self._processar(alvo, pendentes, cache, progress, checar)

    def _processar(
        self: InferirDireitosObrigacoesUseCase,
        ticker: str,
        pendentes: list[DocumentoArquivo],
        cache: CarteiraInferencias | None,
        progress: ProgressoInferencia | None,
        cancelar: Callable[[], None],
    ) -> ResultadoInferencia:
        """Processa os documentos pendentes, persistindo após cada sucesso."""
        itens = list(cache.itens if cache is not None else ())
        total = len(pendentes)
        novos = 0
        falhas = 0
        for indice, documento in enumerate(pendentes, start=1):
            if self._cancelado(cancelar):
                return ResultadoInferencia(
                    executada=True, itens=novos, falhas=falhas, cancelada=True
                )
            self._publicar(progress, indice - 1, total)
            try:
                extraidos = self._inferir_documento(ticker, documento)
            except OperacaoCancelada:
                return ResultadoInferencia(
                    executada=True, itens=novos, falhas=falhas, cancelada=True
                )
            except Exception:
                falhas += 1
                logger.warning(
                    "Falha ao inferir direitos de %s/%s",
                    ticker,
                    documento.nome,
                    exc_info=True,
                )
                continue
            chave = self._chave(documento)
            itens = [item for item in itens if item.chave_documento != chave]
            itens.extend(self._com_proveniencia(extraidos, documento, chave))
            novos += len(extraidos)
            self._gravar(ticker, itens)
            self._publicar(progress, indice, total)
        return ResultadoInferencia(executada=True, itens=novos, falhas=falhas)

    def _inferir_documento(
        self: InferirDireitosObrigacoesUseCase,
        ticker: str,
        documento: DocumentoArquivo,
    ) -> list[InferenciaTitulo]:
        """Chama a LLM para um documento e valida a resposta estruturada."""
        resumo = documento.long_summary or ""
        entrada = montar_entrada(
            ticker,
            documento.nome,
            resumo,
            self._data_referencia(documento),
        )
        resposta = self._criar_llm().complete(
            [{"role": "user", "content": entrada}],
            system_prompt=SYSTEM_PROMPT,
        )
        return interpretar_resposta(
            resposta.texto,
            documento.nome,
            self._data_referencia(documento),
        )

    def _com_proveniencia(
        self: InferirDireitosObrigacoesUseCase,
        itens: list[InferenciaTitulo],
        documento: DocumentoArquivo,
        chave: str,
    ) -> list[InferenciaTitulo]:
        """Acrescenta a chave documental e o hash do resumo aos itens."""
        digest = self._hash_resumo(documento.long_summary or "")
        return [
            replace(item, chave_documento=chave, hash_resumo=digest)
            for item in itens
        ]

    def _documentos_elegiveis(
        self: InferirDireitosObrigacoesUseCase, ticker: str
    ) -> list[DocumentoArquivo]:
        """Seleciona RGs e Informes Mensais com resumo longo íntegro."""
        catalogo = self._catalogo.catalogo(ticker)
        return [
            documento
            for documento in _documentos(catalogo)
            if _elegivel(documento)
        ]

    def _cache_valido(
        self: InferirDireitosObrigacoesUseCase, ticker: str
    ) -> CarteiraInferencias | None:
        """Lê o cache somente quando a versão do prompt é a corrente."""
        cache = self._inferencias.ler(ticker)
        if cache is None or cache.parser_version != self._prompt_version:
            return None
        return cache

    def _processado(
        self: InferirDireitosObrigacoesUseCase,
        cache: CarteiraInferencias | None,
        documento: DocumentoArquivo,
    ) -> bool:
        """Indica se o documento já tem inferência válida no cache."""
        if cache is None:
            return False
        chave = self._chave(documento)
        digest = self._hash_resumo(documento.long_summary or "")
        return any(
            item.chave_documento == chave and item.hash_resumo == digest
            for item in cache.itens
        )

    def _gravar(
        self: InferirDireitosObrigacoesUseCase,
        ticker: str,
        itens: list[InferenciaTitulo],
    ) -> None:
        """Grava o cache completo do ticker de forma atômica."""
        self._inferencias.gravar(
            CarteiraInferencias(
                ticker=ticker,
                parser_version=self._prompt_version,
                adquirido_em=datetime.now(timezone.utc).isoformat(),
                itens=tuple(itens),
            )
        )

    def _chave(self: InferirDireitosObrigacoesUseCase, documento: DocumentoArquivo) -> str:
        """Resolve a chave estável do documento no cache."""
        if self._base_dir is None:
            return documento.nome
        return chave_documento(documento.caminho, self._base_dir)

    @staticmethod
    def _hash_resumo(resumo: str) -> str:
        """Calcula o hash do resumo usado na idempotência do cache."""
        return hashlib.sha256(resumo.encode("utf-8")).hexdigest()

    @staticmethod
    def _data_referencia(documento: DocumentoArquivo) -> date | None:
        """Deriva a data de referência do ano/mês do documento."""
        try:
            return date(documento.ano, documento.mes, 1)
        except ValueError:
            return None

    def _criar_llm(self: InferirDireitosObrigacoesUseCase) -> LLMPort:
        """Cria a porta de completion a partir da fábrica injetada."""
        if self._llm_factory is None:
            raise RuntimeError("Fábrica de LLM não configurada.")
        return self._llm_factory()

    @staticmethod
    def _cancelar(
        cancelar: CancelarInferencia | None,
        token: CancellationToken | None,
    ) -> Callable[[], None]:
        """Combina o cancelamento por callback e por token."""
        if cancelar is not None:
            return cancelar
        if token is not None:
            return token.raise_if_cancelled
        return lambda: None

    @staticmethod
    def _checar(cancelar: Callable[[], None]) -> None:
        """Verifica o cancelamento antes de iniciar a fase."""
        cancelar()

    @staticmethod
    def _cancelado(cancelar: Callable[[], None]) -> bool:
        """Indica se o cancelamento foi solicitado, sem propagar a exceção."""
        try:
            cancelar()
        except OperacaoCancelada:
            return True
        return False

    @staticmethod
    def _publicar(
        progress: ProgressoInferencia | None, atual: int, total: int
    ) -> None:
        """Publica o progresso da inferência quando houver callback."""
        if progress is not None:
            progress(atual, total, "inferência de direitos e obrigações")


def _documentos(catalogo: CatalogoTicker) -> list[DocumentoArquivo]:
    """Achata a hierarquia do catálogo na lista de arquivos."""
    return [
        documento
        for ano in catalogo.anos
        for mes in ano.meses
        for categoria in mes.categorias
        for documento in categoria.arquivos
    ]


def _elegivel(documento: DocumentoArquivo) -> bool:
    """Indica se o documento tem categoria elegível e resumo longo íntegro."""
    return (
        documento.categoria in CATEGORIAS_ELEGIVEIS
        and resumo_integro(documento.long_summary)
    )
