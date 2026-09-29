"""Contador e formatação de tokens da sessão do chat.

Os totais acumulados são exibidos na barra de status em milhares com uma casa
decimal (``5540`` → ``5.5K``). A entrada acumulada desconta os tokens servidos
por cache de prompt, e o rótulo acrescenta o percentual inteiro de ocupação da
janela de contexto da completion mais recente. O contador e a formatação são
puros e independentes do widget, para serem testáveis sem ``DISPLAY``.
"""

from dataclasses import dataclass

from flowscope.domain.llm import LLMUsage


def formatar_k(valor: int) -> str:
    """Formata um total de tokens em milhares com uma casa decimal."""
    return f"{valor / 1000:.1f}K"


def formatar_tokens(
    entrada: int,
    saida: int,
    bruto: int = 0,
    contexto_pct: float | None = None,
) -> str:
    """Formata entrada, saída e o prompt bruto da janela, separados por ``/``.

    O último segmento é o ``prompt_tokens`` bruto da completion mais recente
    (base do percentual), seguido do percentual da janela entre parênteses
    quando conhecido.
    """
    janela = formatar_k(bruto)
    if contexto_pct is not None:
        janela += f" ({round(contexto_pct)}%)"
    return (
        f"Tokens: {formatar_k(entrada)} entrada / "
        f"{formatar_k(saida)} saída / {janela}"
    )


@dataclass
class ContadorTokens:
    """Acumula, por sessão, os tokens de entrada e saída das completions.

    ``entrada`` soma apenas os tokens novos (``entrada - entrada_cache``);
    ``ultimo_prompt`` guarda o ``prompt_tokens`` bruto da completion mais recente
    para o percentual da janela de contexto.
    """

    entrada: int = 0
    saida: int = 0
    ultimo_prompt: int = 0

    def acumular(self: "ContadorTokens", uso: LLMUsage) -> None:
        """Soma o uso reportado por uma completion ao total da sessão."""
        self.entrada += max(0, uso.entrada - uso.entrada_cache)
        self.saida += uso.saida
        self.ultimo_prompt = uso.entrada

    def zerar(self: "ContadorTokens") -> None:
        """Reinicia o total acumulado da sessão."""
        self.entrada = 0
        self.saida = 0
        self.ultimo_prompt = 0

    def percentual(self: "ContadorTokens", context_window: int | None) -> float | None:
        """Calcula o percentual da janela ocupado pela completion mais recente."""
        if not context_window or context_window <= 0:
            return None
        return self.ultimo_prompt * 100 / context_window

    def texto(self: "ContadorTokens", context_window: int | None = None) -> str:
        """Formata o total acumulado, o prompt bruto e a janela para a barra."""
        return formatar_tokens(
            self.entrada,
            self.saida,
            self.ultimo_prompt,
            self.percentual(context_window),
        )
