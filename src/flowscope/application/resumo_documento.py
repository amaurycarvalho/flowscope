"""Serviço de resumo de documentos apoiado na porta ``LLMPort``.

Produz um resumo curto (até 280 caracteres) e um longo (até 1500 caracteres) a
partir do texto integral de um documento. A fórmula XYZ orienta os dois
resumos, pedidos em uma única chamada de completion. O parsing é tolerante:
quando o formato delimitado não é identificável, a resposta inteira vira o
resumo longo e um trecho inicial em fronteira o resumo curto.
"""

import re
from dataclasses import dataclass

from flowscope.domain.llm import LLMPort

#: Limite de caracteres do resumo curto.
LIMITE_CURTO = 280

#: Limite de caracteres do resumo longo.
LIMITE_LONGO = 1500

#: Orçamento máximo de caracteres do texto enviado à LLM.
ORCAMENTO_ENTRADA = 12000

#: Separadores de fim de frase usados no truncamento em fronteira.
_FRONTEIRAS_FRASE = (". ", "; ", "! ", "? ")

#: Pontuações que encerram um resumo íntegro (não truncado).
_PONTUACAO_FINAL = (".", "!", "?", ";", ":", "…")

#: Delimitador do resumo curto na resposta, até o delimitador longo.
_MARCADOR_CURTO = re.compile(r"CURTO\s*:\s*(.*?)(?=LONGO\s*:|$)", re.DOTALL | re.IGNORECASE)

#: Delimitador do resumo longo na resposta.
_MARCADOR_LONGO = re.compile(r"LONGO\s*:\s*(.*)", re.DOTALL | re.IGNORECASE)


def _truncar_em_fronteira(texto: str, limite: int) -> str:
    """Trunca preservando fronteira de frase e, na falta, de palavra.

    Corta no último fim de frase dentro do limite; sem frase, no último espaço;
    só corta duro quando não há nenhuma fronteira no trecho.
    """
    if len(texto) <= limite:
        return texto
    corte = texto[:limite]
    for separador in _FRONTEIRAS_FRASE:
        pos = corte.rfind(separador)
        if pos >= 0:
            return corte[: pos + 1].strip()
    pos = corte.rfind(" ")
    if pos > 0:
        return corte[:pos].strip()
    return corte.strip()


def resumo_integro(resumo: str | None) -> bool:
    """Indica se um resumo persistido termina em pontuação final.

    Um resumo sem pontuação final foi truncado no meio da palavra/frase e deve
    ser considerado desatualizado, passível de regeneração.
    """
    if not resumo:
        return False
    texto = " ".join(resumo.split())
    return bool(texto) and texto.endswith(_PONTUACAO_FINAL)


@dataclass(frozen=True)
class ResumoDocumento:
    """Par de resumos de um documento, curto e longo."""

    short_summary: str = ""
    long_summary: str = ""


class ResumirDocumentoUseCase:
    """Gera os resumos curto e longo de um documento consumindo ``LLMPort``."""

    def __init__(self: "ResumirDocumentoUseCase", llm: LLMPort) -> None:
        """Guarda a porta de completion usada nas chamadas."""
        self._llm = llm

    def resumir(self: "ResumirDocumentoUseCase", texto: str) -> ResumoDocumento:
        """Resume o texto em um par curto/longo, propagando falhas da LLM."""
        if not texto or not texto.strip():
            return ResumoDocumento()
        entrada = texto[:ORCAMENTO_ENTRADA]
        resposta = self._llm.complete(
            [{"role": "user", "content": self._montar_prompt(entrada)}]
        )
        curto, longo = self._interpretar(resposta.texto)
        return ResumoDocumento(
            short_summary=_truncar_em_fronteira(curto, LIMITE_CURTO),
            long_summary=_truncar_em_fronteira(longo, LIMITE_LONGO),
        )

    @staticmethod
    def _montar_prompt(texto: str) -> str:
        """Monta o prompt com a fórmula XYZ e os limites dos resumos."""
        return (
            "Resuma o documento a seguir em português do Brasil, aplicando a "
            "fórmula XYZ (X: o que o texto diz; Y: por que isso importa; "
            "Z: o que se conclui) tanto no resumo curto quanto no longo.\n"
            "Responda em uma única mensagem, no formato exato:\n"
            "CURTO: <resumo em 1 a 2 frases, de até 280 caracteres>\n"
            "LONGO: <resumo em parágrafos, de até 1500 caracteres>\n\n"
            f"Documento:\n{texto}"
        )

    @staticmethod
    def _interpretar(resposta: str) -> tuple[str, str]:
        """Extrai os resumos da resposta, com fallback para a resposta inteira."""
        curto = _MARCADOR_CURTO.search(resposta)
        longo = _MARCADOR_LONGO.search(resposta)
        if curto is not None and longo is not None:
            return curto.group(1).strip(), longo.group(1).strip()
        inteira = resposta.strip()
        return _truncar_em_fronteira(inteira, LIMITE_CURTO), inteira
