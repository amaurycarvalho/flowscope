import argparse
import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from flowscope.presentation import cli_consultas
from flowscope.presentation.cli import build_parser

_PATH = "flowscope.application.structured_use_cases.ExtrairDadosRegulatoriosUseCase"


def _use_case(resultado):
    use_case = MagicMock()
    use_case.execute.return_value = resultado
    return use_case


def _consultar(recurso, **kwargs):
    base = dict(comando="consultar", recurso=recurso, saida=None)
    base.update(kwargs)
    return argparse.Namespace(**base)


class TestParserEscopo:
    def test_fatos_aceita_ticker_categoria_e_datas(self):
        args = build_parser().parse_args(
            ["consultar", "fatos", "PETR4", "--categoria", "4",
             "--data-inicio", "2026-01-01", "--data-fim", "2026-06-30"]
        )
        assert args.recurso == "fatos"
        assert args.ticker == "PETR4"
        assert args.categoria == "4"
        assert args.data_inicio == date(2026, 1, 1)
        assert args.data_fim == date(2026, 6, 30)

    def test_noticias_aceita_palavra_e_datas(self):
        args = build_parser().parse_args(
            ["consultar", "noticias", "--palavra", "PETROBRAS",
             "--data-inicio", "2026-01-01", "--data-fim", "2026-12-31"]
        )
        assert args.recurso == "noticias"
        assert args.palavra == "PETROBRAS"
        assert args.data_inicio == date(2026, 1, 1)

    def test_regulacao_sem_parametros_contextuais(self):
        args = build_parser().parse_args(["consultar", "regulacao"])
        assert args.recurso == "regulacao"
        assert args.saida is None

    def test_proventos_exige_datas(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["consultar", "proventos", "ALZR11"])

    def test_categoria_fora_de_fatos_e_rejeitada(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(
                ["consultar", "noticias", "--categoria", "4"]
            )

    def test_palavra_fora_de_noticias_e_rejeitada(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(
                ["consultar", "fatos", "PETR4", "--palavra", "X"]
            )

    def test_datas_fora_de_consultar_sao_rejeitadas(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(
                ["consultar", "regulacao", "--data-inicio", "2026-01-01"]
            )


class TestConsultarFatos:
    def test_imprime_json_com_company_name_e_code_cvm(self, capsys):
        resultado = {
            "tipo": "fatos_relevantes",
            "metadados": {"codeCVM": "9512", "empresa": "PETROBRAS", "ticker": "PETR4"},
            "documentos": [{"ticker": "PETR4", "companyName": "PETROBRAS"}],
        }
        with patch(_PATH, return_value=_use_case(resultado)) as classe:
            cli_consultas.executar_consultar(
                _consultar("fatos", ticker="PETR4", categoria=None,
                           data_inicio=date(2026, 1, 1), data_fim=date(2026, 6, 30))
            )
        payload = json.loads(capsys.readouterr().out)
        assert payload["metadados"]["ticker"] == "PETR4"
        chamada = classe.return_value.execute.call_args
        assert chamada.args[0] == "fatos"
        assert chamada.kwargs["ticker"] == "PETR4"

    def test_categoria_especifica_repassada(self, capsys):
        resultado = {"tipo": "fatos_relevantes", "documentos": []}
        with patch(_PATH, return_value=_use_case(resultado)) as classe:
            cli_consultas.executar_consultar(
                _consultar("fatos", ticker="petr4", categoria="4",
                           data_inicio=None, data_fim=None)
            )
        chamada = classe.return_value.execute.call_args
        assert chamada.kwargs["categoria"] == "4"
        assert chamada.kwargs["ticker"] == "PETR4"


class TestConsultarNoticias:
    def test_imprime_json_com_periodo(self, capsys):
        resultado = {"tipo": "noticias", "noticias": []}
        with patch(_PATH, return_value=_use_case(resultado)) as classe:
            cli_consultas.executar_consultar(
                _consultar("noticias", palavra=None,
                           data_inicio=date(2026, 7, 1), data_fim=date(2026, 7, 29))
            )
        payload = json.loads(capsys.readouterr().out)
        assert payload["tipo"] == "noticias"
        chamada = classe.return_value.execute.call_args
        assert chamada.args[0] == "noticias"
        assert chamada.kwargs["data_inicio"] == date(2026, 7, 1)

    def test_palavra_repassada(self):
        resultado = {"tipo": "noticias", "noticias": []}
        with patch(_PATH, return_value=_use_case(resultado)) as classe:
            cli_consultas.executar_consultar(
                _consultar("noticias", palavra="PETROBRAS",
                           data_inicio=None, data_fim=None)
            )
        assert classe.return_value.execute.call_args.kwargs["palavra"] == "PETROBRAS"


class TestConsultarRegulacao:
    def test_imprime_json_com_censuras_e_condicoes(self, capsys):
        resultado = {
            "tipo": "regulacao",
            "censuras": [{"titulo": "FII TORDE EI (TORD)", "ticker": "TORD"}],
            "condicoes": [],
        }
        with patch(_PATH, return_value=_use_case(resultado)) as classe:
            cli_consultas.executar_consultar(_consultar("regulacao"))
        payload = json.loads(capsys.readouterr().out)
        assert payload["censuras"][0]["ticker"] == "TORD"
        assert classe.return_value.execute.call_args.args[0] == "regulacao"

    def test_saida_grava_arquivo_json(self, tmp_path, capsys):
        resultado = {"tipo": "regulacao", "censuras": [], "condicoes": []}
        destino = tmp_path / "regulacao.json"
        with patch(_PATH, return_value=_use_case(resultado)):
            cli_consultas.executar_consultar(
                _consultar("regulacao", saida=str(destino))
            )
        assert json.loads(destino.read_text(encoding="utf-8"))["tipo"] == "regulacao"
        assert capsys.readouterr().out == ""


class TestCenarioSemDados:
    def test_ticker_sem_code_cvm_imprime_json_vazio_sem_crash(self, capsys):
        resultado = {
            "tipo": "fatos_relevantes",
            "metadados": {"codeCVM": None, "empresa": None, "ticker": "SEM_CVM"},
            "documentos": [],
        }
        with patch(_PATH, return_value=_use_case(resultado)):
            cli_consultas.executar_consultar(
                _consultar("fatos", ticker="SEM_CVM", categoria=None,
                           data_inicio=None, data_fim=None)
            )
        payload = json.loads(capsys.readouterr().out)
        assert payload["documentos"] == []
        assert payload["metadados"]["codeCVM"] is None
