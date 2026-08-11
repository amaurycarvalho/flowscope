"""Funções auxiliares de texto e arquivo para a lista de tickers.

Concentra a normalização de listas de tickers e a leitura e gravação
desses arquivos, isolando a lógica de persistência do widget de
interface gráfica.
"""

from pathlib import Path


def normalize_tickers(content: str) -> list[str]:
    """Normaliza o conteúdo textual em uma lista de tickers válidos.

    Cada linha não vazia é convertida para maiúsculas e limpa de
    espaços em branco antes de ser retornada.
    """
    return [t.strip().upper() for t in content.splitlines() if t.strip()]


def load_tickers(path: Path) -> list[str]:
    """Lê um arquivo de tickers e devolve a lista normalizada de ativos."""
    content = path.read_text(encoding="utf-8")
    return normalize_tickers(content)


def save_tickers(path: Path, tickers: list[str]) -> None:
    """Grava a lista de tickers em um arquivo de texto, um por linha."""
    path.write_text("\n".join(tickers), encoding="utf-8")
