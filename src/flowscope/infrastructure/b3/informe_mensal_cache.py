"""Cache em disco do HTML do Informe Mensal Estruturado da B3.

Os documentos históricos não mudam, então o cache não expira. A árvore
``<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`` é organizada por
ticker, ano e mês de referência para permitir inspeção manual e reuso entre
execuções, sem alterar as entidades de leitura já existentes.
"""

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.fii.fundamentus.normalizers import para_data

logger = logging.getLogger("flowscope")

#: Subpasta do cache de informes mensais sob o diretório de cache.
PASTA_CACHE = "informe-mensal"


@dataclass(frozen=True)
class InformeMensalArquivo:
    """Documento de informe mensal persistido em disco."""

    ticker: str
    document_id: int
    referencia: date
    caminho: Path


class InformeMensalCache:
    """Armazena e recupera o HTML dos informes em uma árvore por ticker/ano/mês."""

    def __init__(self: "InformeMensalCache", base_dir: Path) -> None:
        """Inicializa o cache com o diretório raiz informado."""
        self._base = Path(base_dir)

    @property
    def base_dir(self: "InformeMensalCache") -> Path:
        """Retorna o diretório raiz do cache de informes mensais."""
        return self._base

    def pasta_ticker(self: "InformeMensalCache", ticker: str) -> Path:
        """Retorna a pasta de cache do ticker."""
        return self._base / ticker.strip().upper()

    def caminho(
        self: "InformeMensalCache",
        ticker: str,
        referencia: date,
        id_documento: int | str,
    ) -> Path:
        """Monta o caminho do HTML do informe mensal."""
        return (
            self.pasta_ticker(ticker)
            / f"{referencia.year:04d}"
            / f"{referencia.month:02d}"
            / f"{id_documento}.html"
        )

    def existe(
        self: "InformeMensalCache",
        ticker: str,
        referencia: date,
        id_documento: int | str,
    ) -> bool:
        """Indica se o HTML do informe já está em cache."""
        return self.caminho(ticker, referencia, id_documento).is_file()

    def ler(
        self: "InformeMensalCache",
        ticker: str,
        referencia: date,
        id_documento: int | str,
    ) -> str | None:
        """Lê o HTML do informe em cache, ou ``None`` quando ausente/corrompido."""
        caminho = self.caminho(ticker, referencia, id_documento)
        try:
            return caminho.read_text(encoding="utf-8")
        except OSError:
            return None

    def gravar(
        self: "InformeMensalCache",
        ticker: str,
        referencia: date,
        id_documento: int | str,
        html: str,
    ) -> Path:
        """Grava o HTML do informe de forma atômica e retorna o caminho."""
        caminho = self.caminho(ticker, referencia, id_documento)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        tmp = caminho.with_suffix(".tmp")
        tmp.write_text(html, encoding="utf-8")
        tmp.rename(caminho)
        return caminho

    def listar(self: "InformeMensalCache", ticker: str) -> list[InformeMensalArquivo]:
        """Lista os informes em cache do ticker, do mais recente ao mais antigo."""
        pasta = self.pasta_ticker(ticker)
        arquivos: list[InformeMensalArquivo] = []
        for caminho in pasta.glob("*/*/*.html"):
            arquivo = _para_arquivo(pasta, caminho)
            if arquivo is not None:
                arquivos.append(arquivo)
        arquivos.sort(
            key=lambda arquivo: (arquivo.referencia, arquivo.document_id),
            reverse=True,
        )
        return arquivos


class InformeMensalArquivoProvider:
    """Baixa e persiste o HTML dos informes mensais, reutilizando o cache."""

    def __init__(
        self: "InformeMensalArquivoProvider",
        client: B3FundosClient | None = None,
        cache_dir: Path | None = None,
        cache: CacheManager | None = None,
    ) -> None:
        """Inicializa o provider com o cliente, o cache JSON e a árvore de arquivos."""
        self._client = client or B3FundosClient()
        base = (
            Path(cache_dir)
            if cache_dir is not None
            else (cache or CacheManager()).get_cache_dir() / PASTA_CACHE
        )
        self._arquivos = InformeMensalCache(base)

    @property
    def cache(self: "InformeMensalArquivoProvider") -> InformeMensalCache:
        """Retorna a árvore de arquivos de informes mensais."""
        return self._arquivos

    def persistir(
        self: "InformeMensalArquivoProvider", ticker: str, documento: dict
    ) -> InformeMensalArquivo | None:
        """Grava o HTML do documento em disco, ou ``None`` em falha/sem identificador.

        Um arquivo já existente é reutilizado sem novo download. Uma falha de
        download é sinalizada com ``None``, sem criar arquivo e sem propagar a
        exceção para não interromper o processamento de outros documentos.
        """
        id_documento = _id_da_url(str(documento.get("urlViewerFundosNet") or ""))
        if id_documento is None:
            return None
        referencia = resolver_data_referencia(documento)
        if self._arquivos.existe(ticker, referencia, id_documento):
            caminho = self._arquivos.caminho(ticker, referencia, id_documento)
            return InformeMensalArquivo(
                ticker=ticker.strip().upper(),
                document_id=id_documento,
                referencia=referencia,
                caminho=caminho,
            )
        try:
            html = self._client.buscar_html_documento(str(id_documento))
        except Exception:  # falha de rede isolada por documento
            logger.warning(
                "Falha ao baixar informe mensal %s de %s",
                id_documento,
                ticker,
                exc_info=True,
            )
            return None
        if not html:
            return None
        caminho = self._arquivos.gravar(ticker, referencia, id_documento, html)
        return InformeMensalArquivo(
            ticker=ticker.strip().upper(),
            document_id=id_documento,
            referencia=referencia,
            caminho=caminho,
        )

    def persistir_todos(
        self: "InformeMensalArquivoProvider",
        ticker: str,
        documentos: Iterable[dict],
    ) -> list[InformeMensalArquivo]:
        """Grava os documentos do ticker, tolerando falhas individuais."""
        arquivos: list[InformeMensalArquivo] = []
        for documento in documentos:
            arquivo = self.persistir(ticker, documento)
            if arquivo is not None:
                arquivos.append(arquivo)
        return arquivos


def resolver_data_referencia(documento: dict) -> date:
    """Deriva a data do informe: referência, entrega e, por fim, a data corrente."""
    referencia = _data_iso(documento.get("referenceDate"))
    if referencia is not None:
        return referencia
    entrega = para_data(_texto(documento.get("deliveryDateFormat")))
    if entrega is not None:
        return entrega
    return datetime.now(timezone.utc).date()


def _para_arquivo(pasta: Path, caminho: Path) -> InformeMensalArquivo | None:
    """Monta a referência de um arquivo em cache, ignorando caminhos inválidos."""
    if not caminho.is_file():
        return None
    try:
        ano, mes, _ = caminho.relative_to(pasta).parts
        referencia = date(int(ano), int(mes), 1)
        document_id = int(caminho.stem)
    except (ValueError, IndexError):
        return None
    return InformeMensalArquivo(
        ticker=pasta.name,
        document_id=document_id,
        referencia=referencia,
        caminho=caminho,
    )


def _id_da_url(url: str) -> int | None:
    """Extrai o identificador numérico do documento a partir da URL."""
    valores = parse_qs(urlparse(url).query).get("id")
    if not valores:
        return None
    try:
        return int(valores[0])
    except ValueError:
        return None


def _data_iso(valor: object) -> date | None:
    """Interpreta uma data ISO (com ou sem horário) como ``date``."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _texto(valor: object) -> str | None:
    """Retorna o texto limpo de um valor, ou ``None`` quando vazio."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None
