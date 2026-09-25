"""Portas da camada de aplicação para acesso a proventos estruturados."""

from collections.abc import Callable
from datetime import date
from typing import Protocol

from flowscope.domain.structured import (
    CategoriaMaterialFact,
    CensuraPublica,
    CondicaoExcepcional,
    DocumentoMaterialFact,
    DocumentoProvento,
    NoticiaB3,
    ProgramaAquisicao,
)


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


class RegulacaoRepository(Protocol):
    """Contrato para acesso a dados regulatórios e de mercado da B3."""

    def resolver_code_cvm(self: "RegulacaoRepository", ticker: str) -> str | None:
        """Retorna o codeCVM do ticker informado, ou ``None`` quando não listado."""
        ...

    def listar_fatos_relevantes(
        self: "RegulacaoRepository",
        code_cvm: str,
        categoria: CategoriaMaterialFact | str,
        data_inicio: date,
        data_fim: date,
        ticker: str = "",
    ) -> list[DocumentoMaterialFact]:
        """Lista os documentos do ``GetMaterialFacts`` da categoria e período."""
        ...

    def listar_noticias(
        self: "RegulacaoRepository",
        agencia: str = "18",
        data_inicio: date | None = None,
        data_fim: date | None = None,
        palavra: str | None = None,
    ) -> list[NoticiaB3]:
        """Lista as notícias do Plantão B3 no período e com o filtro informado."""
        ...

    def listar_censuras(self: "RegulacaoRepository") -> list[CensuraPublica]:
        """Lista as censuras públicas da B3."""
        ...

    def listar_condicoes_excepcionais(
        self: "RegulacaoRepository",
    ) -> list[CondicaoExcepcional]:
        """Lista as condições excepcionais da B3."""
        ...

    def listar_programas_aquisicao(
        self: "RegulacaoRepository", reference_date: date | None = None
    ) -> list[ProgramaAquisicao]:
        """Lista os programas de aquisição de ações em andamento da B3."""
        ...


ProgressCallback = Callable[[str, bool], None]
