"""Cache em disco dos PDFs de avisos aos acionistas de BDR.

Os documentos históricos não mudam, então o cache não expira. A árvore
``<cache>/bdr/<TICKER>/<AAAA>/<MM>/<id>.pdf`` é organizada por ticker, ano e
mês para permitir inspeção manual e reuso entre execuções.
"""

import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger("flowscope")


class PdfCache:
    """Armazena e recupera PDFs de avisos em uma árvore por ticker/ano/mês."""

    def __init__(self: "PdfCache", base_dir: Path) -> None:
        """Inicializa o cache com o diretório raiz informado."""
        self._base = Path(base_dir)

    @property
    def base_dir(self: "PdfCache") -> Path:
        """Retorna o diretório raiz do cache de PDFs de BDR."""
        return self._base

    def pasta_ticker(self: "PdfCache", ticker: str) -> Path:
        """Retorna a pasta de cache do ticker."""
        return self._base / ticker.strip().upper()

    def caminho(
        self: "PdfCache", ticker: str, referencia: date, id_aviso: str
    ) -> Path:
        """Monta o caminho do PDF do aviso."""
        return (
            self.pasta_ticker(ticker)
            / f"{referencia.year:04d}"
            / f"{referencia.month:02d}"
            / f"{id_aviso}.pdf"
        )

    def existe(
        self: "PdfCache", ticker: str, referencia: date, id_aviso: str
    ) -> bool:
        """Indica se o PDF do aviso já está em cache."""
        return self.caminho(ticker, referencia, id_aviso).is_file()

    def ler(
        self: "PdfCache", ticker: str, referencia: date, id_aviso: str
    ) -> bytes | None:
        """Lê o PDF do aviso em cache, ou ``None`` quando ausente/corrompido."""
        caminho = self.caminho(ticker, referencia, id_aviso)
        try:
            return caminho.read_bytes()
        except OSError:
            return None

    def gravar(
        self: "PdfCache",
        ticker: str,
        referencia: date,
        id_aviso: str,
        conteudo: bytes,
    ) -> Path:
        """Grava o PDF do aviso de forma atômica e retorna o caminho."""
        caminho = self.caminho(ticker, referencia, id_aviso)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        tmp = caminho.with_suffix(".tmp")
        tmp.write_bytes(conteudo)
        tmp.rename(caminho)
        return caminho
