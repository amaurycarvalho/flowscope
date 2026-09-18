"""Serviço de resumo de documentos apoiado na porta ``LLMPort``.

Produz um resumo curto (até 280 caracteres) e um longo (até 1500 caracteres) a
partir do texto integral de um documento. A fórmula XYZ orienta os dois
resumos, pedidos em uma única chamada de completion. O parsing é tolerante:
quando o formato delimitado não é identificável, a resposta inteira vira o
resumo longo e seus primeiros 280 caracteres o resumo curto.
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

#: Delimitador do resumo curto na resposta, até o delimitador longo.
_MARCADOR_CURTO = re.compile(r"CURTO\s*:\s*(.*?)(?=LONGO\s*:|$)", re.DOTALL | re.IGNORECASE)

#: Delimitador do resumo longo na resposta.
_MARCADOR_LONGO = re.compile(r"LONGO\s*:\s*(.*)", re.DOTALL | re.IGNORECASE)


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
        curto, longo = self._interpretar(resposta)
        return ResumoDocumento(
            short_summary=curto[:LIMITE_CURTO],
            long_summary=longo[:LIMITE_LONGO],
        )

    @staticmethod
    def _montar_prompt(texto: str) -> str:
        """Monta o prompt com a fórmula XYZ e os limites dos resumos."""
        return (
            "Resuma o documento a seguir em português do Brasil, aplicando a "
            "fórmula XYZ (X: o que o texto diz; Y: por que isso importa; "
            "Z: o que se conclui) tanto no resumo curto quanto no longo.\n"
            "Responda em uma única mensagem, no formato exato:\n"
            "CURTO: <resumo de até 280 caracteres>\n"
            "LONGO: <resumo de até 1500 caracteres>\n\n"
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
        return inteira[:LIMITE_CURTO], inteira
