from datetime import date
from unittest.mock import MagicMock

import pytest

from flowscope.application.structured_use_cases import ExtrairDadosRegulatoriosUseCase
from flowscope.domain.structured import (
    CensuraPublica,
    CondicaoExcepcional,
    FatoRelevante,
    NoticiaB3,
)


def _fato() -> FatoRelevante:
    return FatoRelevante(
        code_cvm="9512",
        empresa="PETROLEO BRASILEIRO S.A. PETROBRAS",
        ticker="PETR4",
        data_referencia="16/04/2026 14:16",
        data_entrega="28/04/2026 19:19:42",
        categoria="Fatos Relevantes",
        tipo=None,
        especie=None,
        status="Ativo",
        assunto="Tomada de Contas",
        url_documento="https://rad.cvm.gov.br/x",
        url_download="https://rad.cvm.gov.br/y",
    )


def _noticia() -> NoticiaB3:
    return NoticiaB3(
        titulo="PETROBRAS anuncia dividendos",
        data_publicacao="2026-07-28 10:00:00",
        url="https://x",
        agencia="18",
    )


def _censura() -> CensuraPublica:
    return CensuraPublica(
        titulo="FII TORDE EI (TORD)",
        ticker="TORD",
        data="25/02/2026",
        conteudo="Censura aplicada.",
    )


def _condicao() -> CondicaoExcepcional:
    return CondicaoExcepcional(
        companhia="Bradsaúde S.A.",
        segmento="Novo Mercado",
        condicao="Ações abaixo do mínimo",
        data_concessao="19/05/2026",
        prazo="30/10/2027",
    )


@pytest.fixture
def repositorio() -> MagicMock:
    return MagicMock()


class TestExtrairDadosRegulatoriosUseCase:
    def test_fatos_percorre_todas_as_categorias(self, repositorio):
        repositorio.resolver_code_cvm.return_value = "9512"
        repositorio.listar_fatos_relevantes.side_effect = [
            [],
            [],
            [_fato()],
            [],
            [],
        ]
        use_case = ExtrairDadosRegulatoriosUseCase(repositorio)
        resultado = use_case.execute(
            "fatos",
            ticker="PETR4",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 6, 30),
        )
        assert repositorio.listar_fatos_relevantes.call_count == 5
        assert resultado["tipo"] == "fatos_relevantes"
        assert resultado["metadados"]["ticker"] == "PETR4"
        assert resultado["metadados"]["codeCVM"] == "9512"
        assert resultado["metadados"]["empresa"] == "PETROLEO BRASILEIRO S.A. PETROBRAS"
        assert len(resultado["documentos"]) == 1
        documento = resultado["documentos"][0]
        assert documento["companyName"].startswith("PETROLEO")
        assert documento["codeCVM"] == "9512"

    def test_fatos_com_categoria_especifica(self, repositorio):
        repositorio.resolver_code_cvm.return_value = "9512"
        repositorio.listar_fatos_relevantes.return_value = [_fato()]
        use_case = ExtrairDadosRegulatoriosUseCase(repositorio)
        resultado = use_case.execute("fatos", ticker="PETR4", categoria="4")
        assert repositorio.listar_fatos_relevantes.call_count == 1
        chamada = repositorio.listar_fatos_relevantes.call_args
        assert chamada.args[1] == "4"
        assert len(resultado["documentos"]) == 1

    def test_fatos_com_categoria_invalida_levanta(self, repositorio):
        use_case = ExtrairDadosRegulatoriosUseCase(repositorio)
        with pytest.raises(ValueError):
            use_case.execute("fatos", ticker="PETR4", categoria="99")

    def test_ticker_sem_code_cvm_retorna_lista_vazia(self, repositorio):
        repositorio.resolver_code_cvm.return_value = None
        use_case = ExtrairDadosRegulatoriosUseCase(repositorio)
        resultado = use_case.execute("fatos", ticker="TICKER_SEM_CVM")
        assert resultado["documentos"] == []
        assert resultado["metadados"]["codeCVM"] is None
        repositorio.listar_fatos_relevantes.assert_not_called()

    def test_falha_em_categoria_individual_loga_e_continua(self, repositorio, caplog):
        repositorio.resolver_code_cvm.return_value = "9512"
        repositorio.listar_fatos_relevantes.side_effect = [
            RuntimeError("API indisponível"),
            [_fato()],
            [_fato()],
            [_fato()],
            [_fato()],
        ]
        use_case = ExtrairDadosRegulatoriosUseCase(repositorio)
        with caplog.at_level("WARNING", logger="flowscope.application.structured_use_cases"):
            resultado = use_case.execute("fatos", ticker="PETR4")
        assert len(resultado["documentos"]) == 4
        assert any("Erro ao listar categoria" in record.getMessage() for record in caplog.records)

    def test_sem_ticker_levanta(self, repositorio):
        use_case = ExtrairDadosRegulatoriosUseCase(repositorio)
        with pytest.raises(ValueError):
            use_case.execute("fatos")

    def test_noticias(self, repositorio):
        repositorio.listar_noticias.return_value = [_noticia()]
        use_case = ExtrairDadosRegulatoriosUseCase(repositorio)
        resultado = use_case.execute(
            "noticias",
            palavra="PETROBRAS",
            data_inicio=date(2026, 7, 1),
            data_fim=date(2026, 7, 29),
        )
        assert resultado["tipo"] == "noticias"
        assert len(resultado["noticias"]) == 1
        chamada = repositorio.listar_noticias.call_args
        assert chamada.kwargs["palavra"] == "PETROBRAS"

    def test_regulacao(self, repositorio):
        repositorio.listar_censuras.return_value = [_censura()]
        repositorio.listar_condicoes_excepcionais.return_value = [_condicao()]
        use_case = ExtrairDadosRegulatoriosUseCase(repositorio)
        resultado = use_case.execute("regulacao")
        assert resultado["tipo"] == "regulacao"
        assert len(resultado["censuras"]) == 1
        assert len(resultado["condicoes"]) == 1
        assert resultado["censuras"][0]["ticker"] == "TORD"
        assert resultado["condicoes"][0]["dataConcessao"] == "19/05/2026"

    def test_tipo_invalido_levanta(self, repositorio):
        use_case = ExtrairDadosRegulatoriosUseCase(repositorio)
        with pytest.raises(ValueError):
            use_case.execute("outro")
