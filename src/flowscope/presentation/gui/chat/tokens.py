"""Contador e formatação de tokens da sessão do chat.

Os totais acumulados são exibidos na barra de status em milhares com uma casa
decimal (``5540`` → ``5.5K``). O contador e a formatação são puros e
independentes do widget, para serem testáveis sem ``DISPLAY``.
"""

from dataclasses import dataclass

from flowscope.domain.llm import LLMUsage


def formatar_k(valor: int) -> str:
    """Formata um total de tokens em milhares com uma casa decimal."""
    return f"{valor / 1000:.1f}K"


def formatar_tokens(entrada: int, saida: int) -> str:
    """Formata os totais de entrada e saída para o rótulo persistente."""
    return f"Tokens: {formatar_k(entrada)} entrada · {formatar_k(saida)} saída"


@dataclass
class ContadorTokens:
    """Acumula, por sessão, os tokens de entrada e saída das completions."""

    entrada: int = 0
    saida: int = 0

    def acumular(self: "ContadorTokens", uso: LLMUsage) -> None:
        """Soma o uso reportado por uma completion ao total da sessão."""
        self.entrada += uso.entrada
        self.saida += uso.saida

    def zerar(self: "ContadorTokens") -> None:
        """Reinicia o total acumulado da sessão."""
        self.entrada = 0
        self.saida = 0

    def texto(self: "ContadorTokens") -> str:
        """Formata o total acumulado para o rótulo da barra de status."""
        return formatar_tokens(self.entrada, self.saida)
