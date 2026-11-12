"""Avaliação do guidance de distribuição de um Relatório Gerencial.

Cada RG é avaliado no máximo uma vez por método e por versão de avaliação.
Quando o provedor de chat está configurado, submete cada fonte da cascata
(resumo curto, resumo longo e texto extraído) a uma avaliação pela IA, que
prevalece sobre o determinístico; se a IA falha ou devolve uma resposta
incompleta, recorre à extração determinística. Em nenhum caso a ausência de
extração apaga a avaliação de outro RG.
"""

import logging
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from flowscope.application.guidance_port import GuidanceStore
from flowscope.domain.fii.guidance import (
    METODO_DETERMINISTICO,
    METODO_IA,
    AvaliacaoGuidance,
    Guidance,
)
from flowscope.domain.llm import LLMError, LLMPort
from flowscope.domain.structured.documentos_relevantes import nome_categoria

logger = logging.getLogger("flowscope")

#: Extrator determinístico injetado (texto, data, caminho) -> guidance/ausência.
ExtratorGuidance = Callable[[str, date, str | None], "Guidance | None"]

#: Categoria de exibição dos Relatórios Gerenciais na sub-aba "Documentos".
CATEGORIA_RELATORIO = nome_categoria(7)

#: Versão do prompt de avaliação, gravada no ledger para permitir reavaliação.
PROMPT_VERSION = "1"

#: Instruções estáveis de avaliação, enviadas como prefixo de sistema.
SYSTEM_PROMPT = (
    "Você recebe um trecho de um Relatório Gerencial de um fundo "
    "imobiliário (FII). Determine se ele contém guidance de distribuição "
    "de rendimentos: uma projeção, orientação ou faixa de valor por cota "
    "para um período futuro.\n"
    "Ignore definições de glossário e referências macroeconômicas "
    "(forward guidance).\n"
    "Responda no formato exato, em quatro linhas:\n"
    "GUIDANCE: SIM ou NAO\n"
    "VALOR_MIN: <valor numérico por cota, ou vazio>\n"
    "VALOR_MAX: <valor numérico por cota, ou vazio>\n"
    "PERIODO: <período de validade, ou vazio>\n"
    "Com GUIDANCE: NAO, deixe VALOR_MIN, VALOR_MAX e PERIODO vazios. Um valor "
    "único preenche VALOR_MIN e VALOR_MAX com o mesmo número. Use o ponto como "
    "separador decimal e não inclua símbolo de moeda. Na dúvida, responda NAO."
)

_GUIDANCE = re.compile(
    r"GUIDANCE\s*:\s*(SIM|S[ÍI]M|NAO|N[ÃA]O)", re.IGNORECASE
)
_VALOR_MIN = re.compile(r"VALOR_M[ÍI]N\s*:\s*(.*)", re.IGNORECASE)
_VALOR_MAX = re.compile(r"VALOR_M[ÁA]X\s*:\s*(.*)", re.IGNORECASE)
_PERIODO = re.compile(r"PER[ÍI]ODO\s*:\s*(.*)", re.IGNORECASE)
_NUMERO = re.compile(r"\d[\d.,]*")

_SIM = frozenset({"SIM", "SÍM"})
_NAO = frozenset({"NAO", "NÃO"})
_PERIODOS_VAGOS = frozenset(
    {
        "",
        "-",
        "n/a",
        "na",
        "não especificado",
        "nao especificado",
        "sem período",
        "sem periodo",
        "não informado",
        "nao informado",
    }
)
_NAO_DEFINIDO = object()


@dataclass(frozen=True)
class _Interpretacao:
    """Interpretação da resposta da IA: guidance, ausência ou inválida."""

    guidance: Guidance | None
    valida: bool


class AvaliarGuidanceUseCase:
    """Avalia o guidance de um RG e registra o resultado no ledger."""

    def __init__(
        self: "AvaliarGuidanceUseCase",
        store: GuidanceStore,
        extrator: ExtratorGuidance,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
    ) -> None:
        """Guarda o store, o extrator determinístico e a estratégia de IA."""
        self._store = store
        self._extrator = extrator
        self._llm_factory = llm_factory
        self._llm_available = llm_available
        self._modelo_cache: object = _NAO_DEFINIDO

    def avaliar_rg(
        self: "AvaliarGuidanceUseCase",
        ticker: str,
        chave: str,
        data_relatorio: date,
        caminho_pdf: str | None,
        fontes: Sequence[str | None],
    ) -> AvaliacaoGuidance | None:
        """Avalia o RG aplicando o controle por método/versão e a cascata.

        Devolve a avaliação registrada, ou ``None`` quando nada foi avaliado
        (RG já coberto pela versão atual ou sem fontes utilizáveis).
        """
        existente = self._store.obter_avaliacao(ticker, chave)
        ia_disponivel = self.ia_disponivel()
        llm = self._obter_llm() if ia_disponivel else None
        if self._manter_existente(existente, ia_disponivel, llm):
            return existente
        resultado = self._avaliar_com_ia(
            ticker,
            chave,
            data_relatorio,
            caminho_pdf,
            fontes,
            ia_disponivel,
            llm,
        )
        if resultado is not None:
            return resultado
        if existente is not None:
            return existente
        resultado = self._cascata_deterministica(
            data_relatorio, caminho_pdf, fontes
        )
        self._store.salvar_avaliacao(ticker, chave, resultado)
        return resultado

    def _manter_existente(
        self: "AvaliarGuidanceUseCase",
        existente: AvaliacaoGuidance | None,
        ia_disponivel: bool,
        llm: LLMPort | None,
    ) -> bool:
        """Indica se a entrada existente já satisfaz a versão/método atuais."""
        if existente is None:
            return False
        if existente.metodo == METODO_IA:
            return not self.precisa_reavaliar(existente, llm)
        if existente.metodo == METODO_DETERMINISTICO:
            return not ia_disponivel
        return False

    def _avaliar_com_ia(
        self: "AvaliarGuidanceUseCase",
        ticker: str,
        chave: str,
        data_relatorio: date,
        caminho_pdf: str | None,
        fontes: Sequence[str | None],
        ia_disponivel: bool,
        llm: LLMPort | None,
    ) -> AvaliacaoGuidance | None:
        """Executa a cascata de IA e grava o resultado, quando aplicável."""
        if not ia_disponivel or llm is None:
            return None
        resultado = self._cascata_ia(data_relatorio, caminho_pdf, fontes, llm)
        if resultado is None:
            return None
        if resultado.guidance is None:
            self._registrar_conflito(
                ticker, data_relatorio, caminho_pdf, fontes
            )
        self._store.salvar_avaliacao(ticker, chave, resultado)
        return resultado

    def ia_disponivel(self: "AvaliarGuidanceUseCase") -> bool:
        """Indica se a avaliação pela IA está disponível e funcional."""
        if self._llm_available is not None:
            try:
                return bool(self._llm_available())
            except Exception:  # configuração ilegível equivale a indisponível
                return False
        return self._llm_factory is not None

    def precisa_reavaliar(
        self: "AvaliarGuidanceUseCase",
        avaliacao: AvaliacaoGuidance,
        llm: LLMPort | None = None,
    ) -> bool:
        """Indica se uma avaliação por IA precisa ser refeita na versão atual."""
        if avaliacao.metodo != METODO_IA:
            return False
        if avaliacao.prompt_version != PROMPT_VERSION:
            return True
        modelo = _modelo_de(llm) if llm is not None else self.modelo_atual()
        return bool(modelo and avaliacao.modelo != modelo)

    def avaliacao_atual(
        self: "AvaliarGuidanceUseCase", avaliacao: AvaliacaoGuidance
    ) -> bool:
        """Indica se a avaliação por IA está na versão atual do prompt/modelo."""
        return not self.precisa_reavaliar(avaliacao)

    def modelo_atual(self: "AvaliarGuidanceUseCase") -> str | None:
        """Retorna o modelo atual da IA, com cache por instância."""
        if not self.ia_disponivel():
            return None
        if self._modelo_cache is _NAO_DEFINIDO:
            self._modelo_cache = _modelo_de(self._obter_llm())
        return (
            self._modelo_cache
            if isinstance(self._modelo_cache, str)
            else None
        )

    def limpar_cache_modelo(self: "AvaliarGuidanceUseCase") -> None:
        """Invalida o modelo em cache após reconfiguração da IA."""
        self._modelo_cache = _NAO_DEFINIDO

    def _obter_llm(self: "AvaliarGuidanceUseCase") -> LLMPort | None:
        """Cria a LLM a partir da fábrica, tolerando indisponibilidade."""
        if self._llm_factory is None:
            return None
        try:
            return self._llm_factory()
        except LLMError:
            return None
        except Exception:  # configuração inesperadamente inválida
            return None

    def _avaliacao_ia(
        self: "AvaliarGuidanceUseCase",
        data_relatorio: date,
        caminho_pdf: str | None,
        guidance: Guidance | None,
        momento: datetime,
        modelo: str | None,
    ) -> AvaliacaoGuidance:
        """Monta uma avaliação por IA com a proveniência da versão atual."""
        return AvaliacaoGuidance(
            metodo=METODO_IA,
            data_relatorio=data_relatorio,
            caminho_pdf=caminho_pdf,
            guidance=guidance,
            avaliado_em=momento,
            prompt_version=PROMPT_VERSION,
            modelo=modelo,
        )

    def _cascata_ia(
        self: "AvaliarGuidanceUseCase",
        data_relatorio: date,
        caminho_pdf: str | None,
        fontes: Sequence[str | None],
        llm: LLMPort,
    ) -> AvaliacaoGuidance | None:
        """Avalia as fontes pela IA em ordem.

        ``None`` apenas quando a IA falha ou devolve resposta inválida antes de
        produzir qualquer avaliação. Uma avaliação válida já obtida de uma fonte
        anterior NÃO é descartada por uma falha em fonte posterior.
        """
        obteve = False
        momento = datetime.now(timezone.utc)
        modelo = _modelo_de(llm)
        for fonte in fontes:
            if not _utilizavel(fonte):
                continue
            funcional, interpretacao = self._tentar_llm(
                llm, fonte, data_relatorio, caminho_pdf
            )
            if not funcional or not interpretacao.valida:
                if obteve:
                    break
                return None
            obteve = True
            if interpretacao.guidance is not None:
                return self._avaliacao_ia(
                    data_relatorio,
                    caminho_pdf,
                    interpretacao.guidance,
                    momento,
                    modelo,
                )
        return self._avaliacao_ia(
            data_relatorio, caminho_pdf, None, momento, modelo
        )

    def _cascata_deterministica(
        self: "AvaliarGuidanceUseCase",
        data_relatorio: date,
        caminho_pdf: str | None,
        fontes: Sequence[str | None],
    ) -> AvaliacaoGuidance:
        """Avalia as fontes pelo extrator determinístico, em ordem."""
        momento = datetime.now(timezone.utc)
        for fonte in fontes:
            if not _utilizavel(fonte):
                continue
            guidance = self._extrator(fonte, data_relatorio, caminho_pdf)
            if guidance is not None:
                return AvaliacaoGuidance(
                    metodo=METODO_DETERMINISTICO,
                    data_relatorio=data_relatorio,
                    caminho_pdf=caminho_pdf,
                    guidance=guidance,
                    avaliado_em=momento,
                )
        return AvaliacaoGuidance(
            metodo=METODO_DETERMINISTICO,
            data_relatorio=data_relatorio,
            caminho_pdf=caminho_pdf,
            guidance=None,
            avaliado_em=momento,
        )

    def _registrar_conflito(
        self: "AvaliarGuidanceUseCase",
        ticker: str,
        data_relatorio: date,
        caminho_pdf: str | None,
        fontes: Sequence[str | None],
    ) -> None:
        """Registra divergência em que o determinístico acha guidance e a IA não."""
        for fonte in fontes:
            if not _utilizavel(fonte):
                continue
            try:
                guidance = self._extrator(fonte, data_relatorio, caminho_pdf)
            except Exception:  # diagnóstico não interrompe a avaliação
                logger.warning(
                    "Falha no diagnóstico determinístico de guidance de %s",
                    ticker,
                    exc_info=True,
                )
                continue
            if guidance is not None:
                logger.warning(
                    "Conflito de guidance em %s (%s): IA concluiu ausência, "
                    "determinístico encontrou %s a %s (%s)",
                    ticker,
                    data_relatorio.isoformat(),
                    guidance.valor_min,
                    guidance.valor_max,
                    guidance.periodo,
                )
                return

    def _tentar_llm(
        self: "AvaliarGuidanceUseCase",
        llm: LLMPort,
        texto: str,
        data_relatorio: date,
        caminho_pdf: str | None,
    ) -> tuple[bool, _Interpretacao]:
        """Tenta avaliar pela LLM; informa se o recurso se mostrou funcional."""
        try:
            resposta = llm.complete(
                [{"role": "user", "content": texto}],
                system_prompt=SYSTEM_PROMPT,
            )
        except LLMError:
            return False, _Interpretacao(None, False)
        except Exception:  # falha inesperada equivale a LLM não funcional
            return False, _Interpretacao(None, False)
        return True, self._interpretar(
            resposta.texto, data_relatorio, caminho_pdf
        )

    @staticmethod
    def _interpretar(
        resposta: str,
        data_relatorio: date,
        caminho_pdf: str | None,
    ) -> _Interpretacao:
        """Interpreta a resposta da LLM, tolerando formatos inesperados."""
        if not isinstance(resposta, str) or not resposta.strip():
            return _Interpretacao(None, False)
        menciona = _GUIDANCE.search(resposta)
        if menciona is None:
            return _Interpretacao(None, False)
        decisao = menciona.group(1).strip().upper()
        if decisao in _NAO:
            return _Interpretacao(None, True)
        if decisao not in _SIM:
            return _Interpretacao(None, False)
        valores = _valores_da_resposta(resposta)
        if not valores:
            return _Interpretacao(None, False)
        return _Interpretacao(
            Guidance(
                valor_min=min(valores),
                valor_max=max(valores),
                periodo=_periodo(resposta),
                data_relatorio=data_relatorio,
                caminho_pdf=caminho_pdf,
            ),
            True,
        )


def _utilizavel(fonte: str | None) -> bool:
    """Indica se a fonte tem conteúdo avaliável."""
    return bool(fonte) and bool(fonte.strip())


def _valores_da_resposta(resposta: str) -> list[Decimal]:
    """Extrai os valores das linhas ``VALOR_MIN``/``VALOR_MAX``."""
    valores: list[Decimal] = []
    for padrao in (_VALOR_MIN, _VALOR_MAX):
        encontrado = padrao.search(resposta)
        if encontrado is None:
            continue
        for token in _NUMERO.findall(encontrado.group(1)):
            valor = _decimal(token)
            if valor is not None:
                valores.append(valor)
    return valores


def _periodo(resposta: str) -> str:
    """Extrai e normaliza o período de validade da resposta."""
    encontrado = _PERIODO.search(resposta)
    if encontrado is None:
        return ""
    return _normalizar_periodo(encontrado.group(1))


def _normalizar_periodo(valor: str) -> str:
    """Retorna o período normalizado, convertendo rótulos vagos em ausência."""
    texto = valor.strip()
    if not texto:
        return ""
    chave = texto.lower()
    if chave in _PERIODOS_VAGOS:
        return ""
    if chave.startswith(
        ("não especificado", "nao especificado", "sem período", "sem periodo")
    ):
        return ""
    return texto


def _decimal(valor: str) -> Decimal | None:
    """Retorna o ``Decimal`` de um número, tolerando moeda e separadores."""
    texto = valor.strip().strip(".,")
    if not texto:
        return None
    if "," in texto:
        normalizado = texto.replace(".", "").replace(",", ".")
    elif texto.count(".") > 1:
        normalizado = texto.replace(".", "")
    else:
        normalizado = texto
    try:
        return Decimal(normalizado)
    except InvalidOperation:
        return None


def _modelo_de(llm: LLMPort | None) -> str | None:
    """Lê o modelo exposto pelo adaptador, quando disponível."""
    if llm is None:
        return None
    for atributo in ("modelo", "model"):
        valor = getattr(llm, atributo, None)
        if isinstance(valor, str) and valor.strip():
            return valor
    return None
