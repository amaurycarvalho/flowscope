"""Decisão e execução da avaliação de guidance de um documento.

Concentra o portão da categoria ``Relatorio``, a montagem da cascata de fontes
(resumo curto, resumo longo e texto extraído) e a identidade do Relatório
Gerencial (chave de conteúdo). A avaliação é delegada ao caso de uso, que prefere
a IA e recorre à extração determinística quando ela não está disponível. O
extrator determinístico, as estratégias de IA e a resolução da chave são
injetados pelo ponto de composição.
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from hashlib import sha1
from pathlib import Path

from flowscope.application.avaliar_guidance import (
    CATEGORIA_RELATORIO,
    AvaliarGuidanceUseCase,
    ExtratorGuidance,
)
from flowscope.application.fundamental.linhas import formatar_guidance, mes_ano
from flowscope.application.guidance_port import GuidanceStore
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import AvaliacaoGuidance
from flowscope.domain.fii.guidance import METODO_IA, Guidance
from flowscope.domain.llm import LLMPort

#: Resolve a chave de conteúdo (hash) de um documento.
ChaveDocumento = Callable[[DocumentoArquivo], str]


@dataclass(frozen=True)
class EntradaGuidanceArvore:
    """Entrada do ledger com guidance, pronta para a árvore e o chat.

    Carrega o ano/mês derivados da data do relatório, a chave do ledger, a
    identidade do RG (``caminho_pdf``) e o guidance avaliado. É um recorte
    somente-leitura: não avalia nem grava nada.
    """

    ticker: str
    ano: int
    mes: int
    chave: str
    data_relatorio: date
    caminho_pdf: str | None
    guidance: Guidance

    @property
    def texto(self: "EntradaGuidanceArvore") -> str:
        """Texto formatado do guidance, no padrão da coluna de informações."""
        return formatar_guidance(self.guidance)


def rotulo_relatorio_gerencial(
    data_relatorio: date,
    caminho_pdf: str | None,
    documentos: Mapping[Path, DocumentoArquivo] | None = None,
) -> str:
    """Monta o rótulo curado do RG: ``Relatório Gerencial — <mmm/aa> (<arquivo>)``.

    Usa o nome do documento do catálogo quando o caminho do RG é localizável;
    sem o documento, cai para o basename do caminho registrado no ledger.
    """
    nome = _nome_do_documento(caminho_pdf, documentos)
    return f"Relatório Gerencial — {mes_ano(data_relatorio)} ({nome})"


def _nome_do_documento(
    caminho_pdf: str | None,
    documentos: Mapping[Path, DocumentoArquivo] | None,
) -> str:
    """Resolve o nome exibido do RG, do catálogo ou do basename do caminho."""
    if caminho_pdf:
        if documentos:
            documento = documentos.get(Path(caminho_pdf))
            if documento is not None and documento.nome:
                return documento.nome
        return Path(caminho_pdf).name
    return ""


def conteudo_arvore_guidance(
    entrada: EntradaGuidanceArvore,
    documentos: Mapping[Path, DocumentoArquivo] | None = None,
) -> str:
    """Compõe o conteúdo de uma folha de guidance: texto e rótulo do RG."""
    rotulo = rotulo_relatorio_gerencial(
        entrada.data_relatorio, entrada.caminho_pdf, documentos
    )
    return f"{entrada.texto}\n\n{rotulo}"


def _entradas_arvore(
    ticker: str, avaliacoes: Mapping[str, AvaliacaoGuidance]
) -> list[EntradaGuidanceArvore]:
    """Filtra as avaliações com guidance e as ordena por ano/mês decrescentes."""
    entradas: list[EntradaGuidanceArvore] = []
    for chave, avaliacao in avaliacoes.items():
        if avaliacao.guidance is None:
            continue
        data_relatorio = avaliacao.data_relatorio
        entradas.append(
            EntradaGuidanceArvore(
                ticker=ticker,
                ano=data_relatorio.year,
                mes=data_relatorio.month,
                chave=chave,
                data_relatorio=data_relatorio,
                caminho_pdf=avaliacao.caminho_pdf,
                guidance=avaliacao.guidance,
            )
        )
    entradas.sort(key=lambda e: (e.ano, e.mes), reverse=True)
    return entradas


def agrupar_entradas(
    entradas: Iterable[EntradaGuidanceArvore],
) -> list[tuple[int, list[tuple[int, list[EntradaGuidanceArvore]]]]]:
    """Agrupa as entradas de guidance por ano e mês, do mais recente ao antigo."""
    por_ano: dict[int, dict[int, list[EntradaGuidanceArvore]]] = {}
    for entrada in entradas:
        por_ano.setdefault(entrada.ano, {}).setdefault(entrada.mes, []).append(
            entrada
        )
    return [
        (
            ano,
            [
                (mes, itens)
                for mes, itens in sorted(meses.items(), reverse=True)
            ],
        )
        for ano, meses in sorted(por_ano.items(), reverse=True)
    ]


def chave_curta_guidance(chave: str) -> str:
    """Deriva a chave curta e estável de uma folha de guidance."""
    return "g" + sha1(chave.encode("utf-8")).hexdigest()[:10]


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

    def entradas_arvore(
        self: "GuidanceService", ticker: str
    ) -> list[EntradaGuidanceArvore]:
        """Devolve as entradas do ledger com guidance, em somente-leitura.

        Filtra as avaliações cujo resultado é ausência de guidance; não avalia,
        não grava e não reextrai nada.
        """
        try:
            avaliacoes = self._store.avaliacoes(ticker)
        except Exception:
            return []
        return _entradas_arvore(ticker, avaliacoes)

    def estado_arvore(
        self: "GuidanceService",
        ticker: str,
        arquivos: Iterable[DocumentoArquivo],
    ) -> tuple[list[DocumentoArquivo], list[EntradaGuidanceArvore]]:
        """Resolve pendentes e entradas numa única leitura do ledger.

        Combina a filtragem das pendências de IA com as entradas com guidance,
        consultando o ledger do ticker apenas uma vez.
        """
        try:
            avaliacoes = self._store.avaliacoes(ticker)
        except Exception:
            return [], []
        return (
            self._pendentes_de(arquivos, avaliacoes),
            _entradas_arvore(ticker, avaliacoes),
        )

    def _pendentes_de(
        self: "GuidanceService",
        arquivos: Iterable[DocumentoArquivo],
        avaliacoes: Mapping[str, AvaliacaoGuidance],
    ) -> list[DocumentoArquivo]:
        """Filtra os RGs pendentes de avaliação de IA no recorte de avaliações."""
        if not self.ia_disponivel():
            return []
        pendentes: list[DocumentoArquivo] = []
        for arquivo in arquivos:
            if arquivo.categoria != CATEGORIA_RELATORIO:
                continue
            if _data_do_arquivo(arquivo) is None:
                continue
            avaliacao = avaliacoes.get(self._chave_rg(arquivo))
            if avaliacao is None or avaliacao.metodo != METODO_IA:
                pendentes.append(arquivo)
        return pendentes

    def caminho_ledger(self: "GuidanceService", ticker: str) -> Path | None:
        """Devolve o caminho do arquivo de ledger do ticker, se exposto."""
        caminho = getattr(self._store, "caminho", None)
        if not callable(caminho):
            return None
        try:
            return Path(caminho(ticker))
        except Exception:
            return None


def _data_do_arquivo(arquivo: DocumentoArquivo) -> date | None:
    """Monta a data do relatório a partir de ano/mês, ou ``None`` se inválidos."""
    if arquivo.ano < 1 or not 1 <= arquivo.mes <= 12:
        return None
    return date(arquivo.ano, arquivo.mes, 1)
