"""Decisão e execução da avaliação de guidance de um documento.

Concentra o portão da categoria ``Relatorio``, a montagem da cascata de fontes
(resumo curto, resumo longo e texto extraído) e a identidade do Relatório
Gerencial (chave de conteúdo). A avaliação é delegada ao caso de uso, que prefere
a IA e recorre à extração determinística quando ela não está disponível. O
extrator determinístico, as estratégias de IA e a resolução da chave são
injetados pelo ponto de composição.
"""

from collections.abc import Callable, Iterable, Mapping
from datetime import date

from flowscope.application.avaliar_guidance import (
    CATEGORIA_RELATORIO,
    AvaliarGuidanceUseCase,
    ExtratorGuidance,
)
from flowscope.application.guidance_port import GuidanceStore
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import AvaliacaoGuidance
from flowscope.domain.fii.guidance import METODO_IA
from flowscope.domain.llm import LLMPort

#: Resolve a chave de conteúdo (hash) de um documento.
ChaveDocumento = Callable[[DocumentoArquivo], str]


def _chave_padrao(arquivo: DocumentoArquivo) -> str:
    """Fallback da chave quando nenhum resolvedor é injetado."""
    return arquivo.nome


class GuidanceService:
    """Decide e executa a avaliação de guidance de um documento."""

    def __init__(
        self: "GuidanceService",
        store: GuidanceStore,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
        avaliador: AvaliarGuidanceUseCase | None = None,
        extrator: ExtratorGuidance | None = None,
        chave_rg: ChaveDocumento | None = None,
    ) -> None:
        """Guarda o store, a estratégia de avaliação e a chave do documento."""
        self._store = store
        self._chave_rg = chave_rg if chave_rg is not None else _chave_padrao
        if avaliador is not None:
            self._avaliador = avaliador
        elif extrator is not None:
            self._avaliador = AvaliarGuidanceUseCase(
                store,
                extrator,
                llm_factory=llm_factory,
                llm_available=llm_available,
            )
        else:
            raise ValueError(
                "GuidanceService exige 'avaliador' ou 'extrator'."
            )

    def precisa(self: "GuidanceService", arquivo: DocumentoArquivo) -> bool:
        """Indica se o documento deve ser considerado para avaliação de guidance."""
        return arquivo.categoria == CATEGORIA_RELATORIO

    def avaliar(
        self: "GuidanceService",
        arquivo: DocumentoArquivo,
        texto: str | None,
        resumo: ResumoDocumento | None = None,
    ) -> AvaliacaoGuidance | None:
        """Avalia a cascata de fontes do documento, tolerando entradas vazias."""
        if arquivo.categoria != CATEGORIA_RELATORIO:
            return None
        data_relatorio = _data_do_arquivo(arquivo)
        if data_relatorio is None:
            return None
        curto = resumo.short_summary if resumo is not None else arquivo.short_summary
        longo = resumo.long_summary if resumo is not None else arquivo.long_summary
        fontes = (curto, longo, texto)
        if not any(fonte and fonte.strip() for fonte in fontes):
            return None
        return self._avaliador.avaliar_rg(
            arquivo.ticker,
            self._chave_rg(arquivo),
            data_relatorio,
            str(arquivo.caminho),
            fontes,
        )

    def ia_disponivel(self: "GuidanceService") -> bool:
        """Indica se a avaliação de guidance pela IA está disponível."""
        return self._avaliador.ia_disponivel()

    def pendente(self: "GuidanceService", arquivo: DocumentoArquivo) -> bool:
        """Indica se o RG carece de avaliação de guidance pela IA.

        Um RG é pendente quando a IA está disponível e sua entrada no ledger
        está ausente ou não foi marcada como `ia`. Não avalia nem grava.
        """
        return bool(self.pendentes([arquivo]))

    def pendentes(
        self: "GuidanceService", arquivos: Iterable[DocumentoArquivo]
    ) -> list[DocumentoArquivo]:
        """Filtra os RGs pendentes de avaliação de guidance pela IA.

        Lê o ledger no máximo uma vez por ticker; devolve ``[]`` quando a IA
        não está disponível. Não avalia nem altera o ledger.
        """
        if not self.ia_disponivel():
            return []
        candidatos = [
            arquivo
            for arquivo in arquivos
            if arquivo.categoria == CATEGORIA_RELATORIO
            and _data_do_arquivo(arquivo) is not None
        ]
        entradas: dict[str, Mapping[str, AvaliacaoGuidance]] = {}
        pendentes: list[DocumentoArquivo] = []
        for arquivo in candidatos:
            if arquivo.ticker not in entradas:
                entradas[arquivo.ticker] = self._store.avaliacoes(arquivo.ticker)
            avaliacao = entradas[arquivo.ticker].get(self._chave_rg(arquivo))
            if avaliacao is None or avaliacao.metodo != METODO_IA:
                pendentes.append(arquivo)
        return pendentes


def _data_do_arquivo(arquivo: DocumentoArquivo) -> date | None:
    """Monta a data do relatório a partir de ano/mês, ou ``None`` se inválidos."""
    if arquivo.ano < 1 or not 1 <= arquivo.mes <= 12:
        return None
    return date(arquivo.ano, arquivo.mes, 1)
