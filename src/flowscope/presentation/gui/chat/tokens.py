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


#: Teto padrão da cota de navegação, em tokens.
TETO_NAVEGACAO = 32000


def formatar_tokens(
    entrada: int,
    saida: int,
    bruto: int = 0,
    contexto_pct: float | None = None,
    navegacao: int = 0,
    teto_navegacao: int = TETO_NAVEGACAO,
) -> str:
    """Formata entrada, saída, contexto e a cota de navegação.

    O terceiro segmento é o ``prompt_tokens`` bruto da completion mais recente
    (base do percentual), rotulado ``contexto``; o quarto é a cota de navegação
    acumulada sobre o seu teto (``nav: W/32K``).
    """
    janela = f"{formatar_k(bruto)} contexto"
    if contexto_pct is not None:
        janela += f" ({round(contexto_pct)}%)"
    nav = f"nav: {formatar_k(navegacao)}/{teto_navegacao // 1000}K"
    return (
        f"Tokens: {formatar_k(entrada)} entrada / "
        f"{formatar_k(saida)} saída / {janela} · {nav}"
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
    navegacao: int = 0

    def acumular(self: "ContadorTokens", uso: LLMUsage) -> None:
        """Soma o uso reportado por uma completion ao total da sessão."""
        self.entrada += max(0, uso.entrada - uso.entrada_cache)
        self.saida += uso.saida
        self.ultimo_prompt = uso.entrada

    def acumular_navegacao(self: "ContadorTokens", tokens: int) -> None:
        """Define a cota de navegação acumulada da sessão."""
        self.navegacao = max(0, int(tokens))

    def zerar(self: "ContadorTokens") -> None:
        """Reinicia o total acumulado da sessão."""
        self.entrada = 0
        self.saida = 0
        self.ultimo_prompt = 0
        self.navegacao = 0

    def percentual(self: "ContadorTokens", context_window: int | None) -> float | None:
        """Calcula o percentual da janela ocupado pela completion mais recente."""
        if not context_window or context_window <= 0:
            return None
        return self.ultimo_prompt * 100 / context_window

    def texto(self: "ContadorTokens", context_window: int | None = None) -> str:
        """Formata o total acumulado, o prompt bruto e a cota de navegação."""
        return formatar_tokens(
            self.entrada,
            self.saida,
            self.ultimo_prompt,
            self.percentual(context_window),
            self.navegacao,
        )
