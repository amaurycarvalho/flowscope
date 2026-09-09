"""Portas da camada de aplicação para acesso a proventos estruturados."""

from collections.abc import Callable
from datetime import date
from typing import Protocol

from flowscope.domain.structured import DocumentoProvento


class ProventosRepository(Protocol):
    """Contrato para obtenção de proventos estruturados de documentos da B3."""

    def resolver_ticker(self: "ProventosRepository", ticker: str) -> str | None:
        """Retorna o idFNET do ticker informado, ou ``None`` quando não houver dados."""
        ...

    def listar_documentos(
        self: "ProventosRepository",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        tipo: int,
    ) -> list[dict]:
        """Lista os documentos estruturados do idFNET no período informado."""
        ...

    def extrair_detalhes(
        self: "ProventosRepository", documento: dict
    ) -> DocumentoProvento:
        """Extrai os detalhes do documento listado como uma entidade de provento.

        O dicionário recebido é um item retornado por ``listar_documentos`` e
        pode conter metadados adicionais (ticker, idFNET) anexados pelo caso de
        uso para compor o documento extraído.
        """
        ...


ProgressCallback = Callable[[str, bool], None]
