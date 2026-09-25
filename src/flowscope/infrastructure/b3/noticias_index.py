"""Índice de metadados das notícias em cache.

O caminho do HTML cacheado (``noticias/<AAAA>/<MM>/<hash>.html``) não carrega
título, seção, categoria, data nem URL. Para que a sub-aba "Notícias" e o
contexto do chat montem a árvore lendo apenas o cache local — sem consultar a
B3 — a aquisição registra esses metadados neste índice, indexados pelo caminho
relativo do HTML. A leitura tolera ausência e corrupção e a gravação é atômica.
"""

import json
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

#: Nome do arquivo de índice dentro da subpasta de notícias.
NOME_ARQUIVO_INDICE = "index.json"

#: Subpasta das notícias dentro da raiz de cache.
PASTA_NOTICIAS = "noticias"

#: Versão do schema persistido.
SCHEMA_VERSION_INDICE = 1

#: Chave da data mais antiga já processada da "Geral".
CHAVE_GERAL_MAIS_ANTIGA = "geral_mais_antiga"

#: Chave da data de referência da última carga concluída da "Geral".
CHAVE_GERAL_REFERENCIA = "geral_referencia"


@dataclass(frozen=True)
class NoticiaMeta:
    """Metadados de exibição de uma notícia cacheada."""

    secao: str
    titulo: str
    data_publicacao: str
    categoria: str
    url: str | None = None


class NoticiasIndexStore:
    """Persiste os metadados das notícias cacheadas em um JSON por raiz."""

    def __init__(self: "NoticiasIndexStore", cache_dir: Path | None = None) -> None:
        """Inicializa o índice na raiz informada ou na raiz padrão do FlowScope."""
        base = cache_dir if cache_dir is not None else CacheManager().get_cache_dir()
        self._base = Path(base)
        self._path = self._base / PASTA_NOTICIAS / NOME_ARQUIVO_INDICE

    @property
    def path(self: "NoticiasIndexStore") -> Path:
        """Retorna o caminho do arquivo de índice."""
        return self._path

    def registrar(self: "NoticiasIndexStore", caminho: Path, meta: NoticiaMeta) -> None:
        """Registra os metadados de uma notícia cacheada."""
        self.registrar_muitos([(caminho, meta)])

    def registrar_muitos(
        self: "NoticiasIndexStore", registros: list[tuple[Path, NoticiaMeta]]
    ) -> None:
        """Registra em lote os metadados das notícias cacheadas."""
        self.registrar_lote(registros)

    def registrar_lote(
        self: "NoticiasIndexStore",
        registros: list[tuple[Path, NoticiaMeta]],
        *,
        geral_mais_antiga: date | None = None,
        geral_referencia: date | None = None,
    ) -> None:
        """Registra metadados e marcadores da "Geral" em uma única gravação.

        Concentra a leitura e a escrita do índice para evitar regravar o arquivo
        a cada item; os marcadores informados são aplicados na mesma passagem.
        """
        doc = self._carregar_doc()
        itens = _itens_do_doc(doc)
        for caminho, meta in registros:
            itens[self._relativo(caminho)] = _serializar(meta)
        doc["itens"] = itens
        if geral_mais_antiga is not None:
            atual = _data_iso(doc.get(CHAVE_GERAL_MAIS_ANTIGA))
            if atual is None or geral_mais_antiga < atual:
                doc[CHAVE_GERAL_MAIS_ANTIGA] = geral_mais_antiga.isoformat()
        if geral_referencia is not None:
            doc[CHAVE_GERAL_REFERENCIA] = geral_referencia.isoformat()
        self._gravar(doc)

    def itens(self: "NoticiasIndexStore") -> dict[str, NoticiaMeta]:
        """Retorna os metadados indexados pelo caminho relativo do HTML."""
        resultado: dict[str, NoticiaMeta] = {}
        for relativo, dados in _itens_do_doc(self._carregar_doc()).items():
            meta = _desserializar(dados)
            if meta is not None:
                resultado[relativo] = meta
        return resultado

    def geral_processada(self: "NoticiasIndexStore") -> tuple[date | None, date | None]:
        """Retorna ``(data_mais_antiga, referência)`` já processadas da "Geral"."""
        doc = self._carregar_doc()
        return (
            _data_iso(doc.get(CHAVE_GERAL_MAIS_ANTIGA)),
            _data_iso(doc.get(CHAVE_GERAL_REFERENCIA)),
        )

    def registrar_geral_mais_antiga(
        self: "NoticiasIndexStore", data_ref: date
    ) -> None:
        """Registra a data mais antiga processada, mantendo a menor."""
        doc = self._carregar_doc()
        atual = _data_iso(doc.get(CHAVE_GERAL_MAIS_ANTIGA))
        if atual is not None and atual <= data_ref:
            return
        doc[CHAVE_GERAL_MAIS_ANTIGA] = data_ref.isoformat()
        self._gravar(doc)

    def registrar_geral_referencia(
        self: "NoticiasIndexStore", data_ref: date
    ) -> None:
        """Registra a data de referência da última carga concluída da "Geral"."""
        doc = self._carregar_doc()
        doc[CHAVE_GERAL_REFERENCIA] = data_ref.isoformat()
        self._gravar(doc)

    def _relativo(self: "NoticiasIndexStore", caminho: Path) -> str:
        """Deriva a chave relativa do HTML em relação à raiz de cache."""
        try:
            return Path(caminho).relative_to(self._base).as_posix()
        except ValueError:
            return Path(caminho).name

    def _carregar_doc(self: "NoticiasIndexStore") -> dict:
        """Carrega o documento do índice, tolerando ausência e corrupção."""
        caminho = self._path
        if not caminho.exists():
            return {}
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Índice de notícias corrompido: %s", caminho)
            return {}
        return dados if isinstance(dados, dict) else {}

    def _gravar(self: "NoticiasIndexStore", doc: dict) -> None:
        """Grava o índice de forma atômica."""
        doc["schema_version"] = SCHEMA_VERSION_INDICE
        payload = json.dumps(doc, ensure_ascii=False, default=str).encode("utf-8")
        _atomic_write_bytes(self._path, payload)


def _itens_do_doc(doc: dict) -> dict:
    """Retorna o mapa de itens do documento, tolerando formato inválido."""
    itens = doc.get("itens")
    return itens if isinstance(itens, dict) else {}


def _data_iso(valor: object) -> date | None:
    """Interpreta uma data ISO persistida, tolerando ausência e formato."""
    if not isinstance(valor, str):
        return None
    try:
        return date.fromisoformat(valor[:10])
    except ValueError:
        return None


def _serializar(meta: NoticiaMeta) -> dict:
    """Serializa os metadados para o formato persistido."""
    return {
        "secao": meta.secao,
        "titulo": meta.titulo,
        "data_publicacao": meta.data_publicacao,
        "categoria": meta.categoria,
        "url": meta.url,
    }


def _desserializar(dados: object) -> NoticiaMeta | None:
    """Reconstrói os metadados de um registro persistido, ou ``None``."""
    if not isinstance(dados, dict):
        return None
    return NoticiaMeta(
        secao=_texto(dados.get("secao")),
        titulo=_texto(dados.get("titulo")),
        data_publicacao=_texto(dados.get("data_publicacao")),
        categoria=_texto(dados.get("categoria")),
        url=_texto_ou_none(dados.get("url")),
    )


def _texto(valor: object) -> str:
    """Normaliza um valor persistido para string, tolerando tipos inválidos."""
    return valor if isinstance(valor, str) else ""


def _texto_ou_none(valor: object) -> str | None:
    """Normaliza um valor opcional persistido, devolvendo ``None`` se vazio."""
    return valor if isinstance(valor, str) and valor else None
