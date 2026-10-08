"""Erros de domínio relacionados a ativos de FII e papel."""


class TickerNaoEncontrado(Exception):
    """Ticker sem dados de papel na fonte consultada.

    Sinaliza o caso esperado de ausência de dados (ticker inexistente ou sem
    cobertura), distinguindo-o de falhas de layout ou de rede que exigem
    atenção.
    """
