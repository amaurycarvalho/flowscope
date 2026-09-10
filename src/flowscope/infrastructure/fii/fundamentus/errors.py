"""Erros tipados do provider do Fundamentus (RFC-011 §9)."""


class FundamentusError(Exception):
    """Erro base do provider do Fundamentus."""


class TickerNotFound(FundamentusError):
    """Ticker não encontrado no portal Fundamentus."""


class LayoutChanged(FundamentusError):
    """Layout da página mudou e campos obrigatórios desapareceram."""


class NetworkError(FundamentusError):
    """Falha de rede ou status HTTP de erro ao acessar o Fundamentus."""
