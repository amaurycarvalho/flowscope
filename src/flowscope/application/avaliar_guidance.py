"""Avaliação do guidance de distribuição de um Relatório Gerencial.

Quando há LLM disponível e funcional, submete o texto a uma avaliação específica
e usa o resultado (havendo guidance, substitui o cache; não havendo, preserva).
Quando a LLM está indisponível ou a chamada falha, recorre a uma extração
determinística injetada. Em nenhum caso a ausência de extração apaga o cache.
"""

import logging
import re
from collections.abc import Callable
from datetime import date
from decimal import Decimal, InvalidOperation

from flowscope.application.guidance_port import GuidanceStore
from flowscope.domain.fii.guidance import Guidance
from flowscope.domain.llm import LLMError, LLMPort
from flowscope.domain.structured.documentos_relevantes import nome_categoria

logger = logging.getLogger("flowscope")

#: Extrator determinístico injetado (texto, data, caminho) -> guidance/ausência.
ExtratorGuidance = Callable[[str, date, str | None], "Guidance | None"]

#: Categoria de exibição dos Relatórios Gerenciais na sub-aba "Documentos".
CATEGORIA_RELATORIO = nome_categoria(7)

_GUIDANCE_SIM = re.compile(r"GUIDANCE\s*:\s*(SIM|S[ÍI]M)", re.IGNORECASE)
_VALOR_MIN = re.compile(r"VALOR_M[ÍI]N\s*:\s*([\d.,]+)", re.IGNORECASE)
_VALOR_MAX = re.compile(r"VALOR_M[ÁA]X\s*:\s*([\d.,]+)", re.IGNORECASE)
_PERIODO = re.compile(r"PER[ÍI]ODO\s*:\s*(.*)", re.IGNORECASE)


class AvaliarGuidanceUseCase:
    """Avalia o guidance de um relatório e o persiste quando encontrado."""

    def __init__(
        self: "AvaliarGuidanceUseCase",
        store: GuidanceStore,
        extrator: ExtratorGuidance,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
    ) -> None:
        """Guarda o store, o extrator determinístico e a estratégia de LLM."""
        self._store = store
        self._extrator = extrator
        self._llm_factory = llm_factory
        self._llm_available = llm_available

    def deve_avaliar(
        self: "AvaliarGuidanceUseCase",
        ano: int,
        mes: int,
        guidance_cache: Guidance | None,
    ) -> bool:
        """Indica se o relatório é mais recente que o guidance em cache."""
        if guidance_cache is None:
            return True
        referencia = guidance_cache.data_relatorio
        return (ano, mes) > (referencia.year, referencia.month)

    def avaliar_documento(
        self: "AvaliarGuidanceUseCase",
        ticker: str,
        categoria: str,
        ano: int,
        mes: int,
        texto: str,
        caminho_pdf: str | None,
    ) -> Guidance | None:
        """Avalia o documento aplicando categoria, texto e data como portões."""
        if categoria != CATEGORIA_RELATORIO:
            return None
        if not texto or not texto.strip():
            return None
        cache = self._store.obter(ticker)
        if not self.deve_avaliar(ano, mes, cache):
            return None
        return self.avaliar(ticker, texto, date(ano, mes, 1), caminho_pdf)

    def avaliar(
        self: "AvaliarGuidanceUseCase",
        ticker: str,
        texto: str,
        data_relatorio: date,
        caminho_pdf: str | None = None,
    ) -> Guidance | None:
        """Avalia o texto pela LLM ou pelo extrator e grava se houver guidance."""
        funcional, guidance = self._tentar_llm(texto, data_relatorio, caminho_pdf)
        if not funcional:
            guidance = self._extrator(texto, data_relatorio, caminho_pdf)
        if guidance is not None and self._pode_substituir(ticker, data_relatorio):
            self._store.salvar(ticker, guidance)
        return guidance

    def _pode_substituir(
        self: "AvaliarGuidanceUseCase", ticker: str, data_relatorio: date
    ) -> bool:
        """Evita que um resultado obsoleto sobrescreva um guidance mais recente."""
        atual = self._store.obter(ticker)
        return self.deve_avaliar(
            data_relatorio.year, data_relatorio.month, atual
        )

    def _tentar_llm(
        self: "AvaliarGuidanceUseCase",
        texto: str,
        data_relatorio: date,
        caminho_pdf: str | None,
    ) -> tuple[bool, Guidance | None]:
        """Tenta avaliar pela LLM; informa se o recurso se mostrou funcional."""
        if self._llm_available is not None and not self._llm_available():
            return False, None
        if self._llm_factory is None:
            return False, None
        try:
            llm = self._llm_factory()
        except LLMError:
            return False, None
        except Exception:  # configuração inesperadamente inválida
            return False, None
        try:
            resposta = llm.complete(
                [{"role": "user", "content": self._montar_prompt(texto)}]
            )
        except LLMError:
            return False, None
        except Exception:  # falha inesperada equivale a LLM não funcional
            return False, None
        return True, self._interpretar(resposta, data_relatorio, caminho_pdf)

    @staticmethod
    def _montar_prompt(texto: str) -> str:
        """Monta o prompt que pergunta se o relatório contém guidance."""
        return (
            "Você recebe o texto de um Relatório Gerencial de um fundo "
            "imobiliário (FII). Determine se ele contém guidance de distribuição "
            "de rendimentos: uma projeção, orientação ou faixa de valor por cota "
            "para um período futuro.\n"
            "Ignore definições de glossário e referências macroeconômicas "
            "(forward guidance).\n"
            "Responda no formato exato:\n"
            "GUIDANCE: SIM ou NAO\n"
            "VALOR_MIN: <valor numérico por cota, ou vazio>\n"
            "VALOR_MAX: <valor numérico por cota, ou vazio>\n"
            "PERIODO: <período de validade, ou vazio>\n\n"
            f"Documento:\n{texto}"
        )

    @staticmethod
    def _interpretar(
        resposta: str,
        data_relatorio: date,
        caminho_pdf: str | None,
    ) -> Guidance | None:
        """Interpreta a resposta da LLM, tolerando formatos inesperados."""
        if not isinstance(resposta, str) or _GUIDANCE_SIM.search(resposta) is None:
            return None
        minimo = _valor(resposta, _VALOR_MIN)
        maximo = _valor(resposta, _VALOR_MAX)
        if minimo is None and maximo is None:
            return None
        valor_min = minimo if minimo is not None else maximo
        valor_max = maximo if maximo is not None else minimo
        if valor_min is None or valor_max is None:
            return None
        return Guidance(
            valor_min=min(valor_min, valor_max),
            valor_max=max(valor_min, valor_max),
            periodo=_periodo(resposta),
            data_relatorio=data_relatorio,
            caminho_pdf=caminho_pdf,
        )


def _valor(resposta: str, padrao: re.Pattern) -> Decimal | None:
    """Extrai um valor decimal da resposta, ou ``None``."""
    encontrado = padrao.search(resposta)
    if encontrado is None:
        return None
    return _decimal(encontrado.group(1))


def _periodo(resposta: str) -> str:
    """Extrai o período de validade da resposta, ou string vazia."""
    encontrado = _PERIODO.search(resposta)
    return encontrado.group(1).strip() if encontrado is not None else ""


def _decimal(valor: str) -> Decimal | None:
    """Retorna o ``Decimal`` de um número com vírgula ou ponto."""
    try:
        if "," in valor:
            return Decimal(valor.replace(".", "").replace(",", "."))
        return Decimal(valor)
    except InvalidOperation:
        return None
