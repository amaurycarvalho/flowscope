"""Cache e aquisição dos PDFs de documentos relevantes da B3.

Os documentos históricos não mudam, então o cache não expira. A árvore
``<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`` é
organizada por ticker, ano, mês e categoria para permitir inspeção manual e
reuso entre execuções, sem alterar as entidades de leitura existentes.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from flowscope.domain.structured import (
    DocumentoRelevante,
    nome_categoria,
    nome_por_slug,
    slug_categoria,
)
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.fii.fundamentus.normalizers import para_data

logger = logging.getLogger("flowscope")

#: Subpasta do cache de documentos relevantes sob o diretório de cache.
PASTA_CACHE = "documentos-relevantes"


@dataclass(frozen=True)
class DocumentoRelevanteArquivo:
    """PDF de documento relevante persistido em disco."""

    ticker: str
    document_id: str
    categoria: str
    referencia: date
    caminho: Path


class DocumentosRelevantesCache:
    """Armazena e recupera PDFs em uma árvore por ticker/ano/mês/categoria."""

    def __init__(
        self: "DocumentosRelevantesCache", base_dir: Path
    ) -> None:
        """Inicializa o cache com o diretório raiz informado."""
        self._base = Path(base_dir)

    @property
    def base_dir(self: "DocumentosRelevantesCache") -> Path:
        """Retorna o diretório raiz do cache de documentos relevantes."""
        return self._base

    def pasta_ticker(self: "DocumentosRelevantesCache", ticker: str) -> Path:
        """Retorna a pasta de cache do ticker."""
        return self._base / ticker.strip().upper()

    def caminho(
        self: "DocumentosRelevantesCache",
        ticker: str,
        referencia: date,
        categoria: str,
        id_documento: str,
    ) -> Path:
        """Monta o caminho do PDF a partir do slug da categoria."""
        return (
            self.pasta_ticker(ticker)
            / f"{referencia.year:04d}"
            / f"{referencia.month:02d}"
            / categoria
            / f"{id_documento}.pdf"
        )

    def existe(
        self: "DocumentosRelevantesCache",
        ticker: str,
        referencia: date,
        categoria: str,
        id_documento: str,
    ) -> bool:
        """Indica se o PDF do documento já está em cache."""
        return self.caminho(ticker, referencia, categoria, id_documento).is_file()

    def ler(
        self: "DocumentosRelevantesCache",
        ticker: str,
        referencia: date,
        categoria: str,
        id_documento: str,
    ) -> bytes | None:
        """Lê o PDF em cache, ou ``None`` quando ausente/corrompido."""
        caminho = self.caminho(ticker, referencia, categoria, id_documento)
        try:
            return caminho.read_bytes()
        except OSError:
            return None

    def gravar(
        self: "DocumentosRelevantesCache",
        ticker: str,
        referencia: date,
        categoria: str,
        id_documento: str,
        conteudo: bytes,
    ) -> Path:
        """Grava o PDF de forma atômica e retorna o caminho."""
        caminho = self.caminho(ticker, referencia, categoria, id_documento)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        tmp = caminho.with_suffix(".tmp")
        tmp.write_bytes(conteudo)
        tmp.rename(caminho)
        return caminho

    def listar(
        self: "DocumentosRelevantesCache", ticker: str
    ) -> list[DocumentoRelevanteArquivo]:
        """Lista os PDFs em cache do ticker, do mais recente ao mais antigo."""
        pasta = self.pasta_ticker(ticker)
        arquivos: list[DocumentoRelevanteArquivo] = []
        for caminho in pasta.glob("*/*/*/*.pdf"):
            arquivo = _para_arquivo(pasta, caminho)
            if arquivo is not None:
                arquivos.append(arquivo)
        arquivos.sort(
            key=lambda arquivo: (arquivo.referencia, arquivo.document_id),
            reverse=True,
        )
        return arquivos


class DocumentosRelevantesProvider:
    """Lista, baixa e persiste PDFs de documentos relevantes, reutilizando o cache."""

    def __init__(
        self: "DocumentosRelevantesProvider",
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
        self._arquivos = DocumentosRelevantesCache(base)

    @property
    def cache(self: "DocumentosRelevantesProvider") -> DocumentosRelevantesCache:
        """Retorna a árvore de arquivos de documentos relevantes."""
        return self._arquivos

    def sincronizar(
        self: "DocumentosRelevantesProvider",
        ticker: str,
        id_fnet: str | None,
        data_inicio: date,
        data_fim: date,
    ) -> list[DocumentoRelevante]:
        """Lista as 4 categorias, baixa e cacheia os PDFs, tolerando falhas."""
        itens = self._client.listar_todos_documentos_relevantes(
            id_fnet, data_inicio, data_fim
        )
        documentos: list[DocumentoRelevante] = []
        for item in itens:
            documento = self.persistir(ticker, id_fnet, item)
            if documento is not None:
                documentos.append(documento)
        return documentos

    def persistir(
        self: "DocumentosRelevantesProvider",
        ticker: str,
        id_fnet: str | None,
        item: dict,
    ) -> DocumentoRelevante | None:
        """Baixa e cacheia o PDF do item, ou ``None`` em falha/não-PDF.

        Um arquivo já existente é reutilizado sem novo download. Conteúdo sem
        assinatura ``%PDF`` é rejeitado sem criar arquivo e sem propagar a
        exceção para não interromper os demais documentos.
        """
        id_documento = _id_da_url(str(item.get("urlViewerFundosNet") or ""))
        codigo = item.get("category")
        if id_documento is None or codigo is None:
            return None
        referencia = resolver_data_referencia(item)
        slug = slug_categoria(codigo)
        if self._arquivos.existe(ticker, referencia, slug, id_documento):
            tamanho = (
                self._arquivos.caminho(
                    ticker, referencia, slug, id_documento
                ).stat().st_size
            )
        else:
            try:
                conteudo = self._client.baixar_pdf_documento(id_documento)
            except Exception:  # falha de rede isolada por documento
                logger.warning(
                    "Falha ao baixar documento relevante %s de %s",
                    id_documento,
                    ticker,
                    exc_info=True,
                )
                return None
            if not conteudo:
                return None
            self._arquivos.gravar(ticker, referencia, slug, id_documento, conteudo)
            tamanho = len(conteudo)
        return _documento_relevante(
            ticker, id_fnet, item, id_documento, codigo, tamanho
        )


def resolver_data_referencia(documento: dict) -> date:
    """Deriva a data do documento: referência, entrega e, por fim, a corrente."""
    referencia = _data_iso(documento.get("referenceDate"))
    if referencia is not None:
        return referencia
    entrega = para_data(_texto(documento.get("deliveryDateFormat")))
    if entrega is not None:
        return entrega
    return datetime.now(timezone.utc).date()


def _documento_relevante(
    ticker: str,
    id_fnet: str | None,
    item: dict,
    id_documento: str,
    codigo: object,
    tamanho_bytes: int,
) -> DocumentoRelevante:
    """Monta a entidade a partir do item bruto da API e do PDF persistido."""
    return DocumentoRelevante(
        ticker=ticker.strip().upper(),
        id_fnet=id_fnet,
        id_documento=id_documento,
        categoria=nome_categoria(codigo),
        descricao=_descricao(item),
        data_referencia=_data_iso(item.get("referenceDate")),
        data_entrega=_texto(
            item.get("deliveryDateFormat") or item.get("deliveryDate")
        )
        or "",
        url=str(item.get("urlViewerFundosNet") or ""),
        tamanho_bytes=tamanho_bytes,
        data_extracao=datetime.now(timezone.utc),
    )


def _para_arquivo(
    pasta: Path, caminho: Path
) -> DocumentoRelevanteArquivo | None:
    """Monta a referência de um arquivo em cache, ignorando caminhos inválidos."""
    if not caminho.is_file():
        return None
    try:
        ano, mes, slug, _ = caminho.relative_to(pasta).parts
        referencia = date(int(ano), int(mes), 1)
    except (ValueError, IndexError):
        return None
    categoria = nome_por_slug(slug)
    if categoria is None or not caminho.stem:
        return None
    return DocumentoRelevanteArquivo(
        ticker=pasta.name,
        document_id=caminho.stem,
        categoria=categoria,
        referencia=referencia,
        caminho=caminho,
    )


def _descricao(item: dict) -> str:
    """Retorna a descrição do documento, tolerando variações de campo da API."""
    for chave in ("description", "describleKind", "subjects", "describleType"):
        texto = _texto(item.get(chave))
        if texto:
            return texto
    return ""


def _id_da_url(url: str) -> str | None:
    """Extrai o identificador do documento a partir da URL de visualização."""
    valores = parse_qs(urlparse(url).query).get("id")
    return valores[0] if valores else None


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
