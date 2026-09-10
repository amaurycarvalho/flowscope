"""Heurísticas de identificação de fundos da B3."""


def _fund_root(ticker: str) -> str:
    """Remove o sufixo numérico do ticker, devolvendo o código do fundo."""
    ticker = ticker.strip().upper()
    raiz = ticker.rstrip("0123456789")
    return raiz or ticker


def _selecionar_fund(candidatos: list[dict]) -> dict | None:
    """Seleciona o registro cujo ``id`` é usado nas consultas de relatórios.

    Prefere o registro com ``idMain`` não nulo (RFC-008 §3); sem ele, recorre à
    heurística legada de ignorar o registro cujo ``tradingName`` começa com
    ``Fundo:``.
    """
    derivados = [item for item in candidatos if item.get("idMain") is not None]
    if derivados:
        return derivados[0]
    for item in candidatos:
        if "Fundo:" in str(item.get("tradingName", "")):
            continue
        if item.get("id"):
            return item
    return candidatos[0] if candidatos else None
