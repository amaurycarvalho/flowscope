import argparse
import json
from datetime import date
from unittest.mock import MagicMock, patch

from flowscope.presentation.cli import (
    build_parser,
    run_fatos_relevantes,
    run_noticias,
    run_regulacao,
)

_PATH = "flowscope.application.structured_use_cases.ExtrairDadosRegulatoriosUseCase"


def _use_case(resultado):
    use_case = MagicMock()
    use_case.execute.return_value = resultado
    return use_case


class TestParserRegulatorio:
    def test_parser_tem_fatos_relevantes(self):
        args = build_parser().parse_args(["--fatos-relevantes", "PETR4"])
        assert args.fatos_relevantes == "PETR4"

    def test_parser_tem_noticias(self):
        args = build_parser().parse_args(["--noticias"])
        assert args.noticias is True

    def test_parser_tem_regulacao(self):
        args = build_parser().parse_args(["--regulacao"])
        assert args.regulacao is True

    def test_parser_tem_categoria(self):
        args = build_parser().parse_args(
            ["--fatos-relevantes", "PETR4", "--categoria", "4"]
        )
        assert args.categoria == "4"

    def test_parser_tem_palavra(self):
        args = build_parser().parse_args(["--noticias", "--palavra", "PETROBRAS"])
        assert args.palavra == "PETROBRAS"

    def test_parser_reutiliza_datas(self):
        args = build_parser().parse_args(
            [
                "--fatos-relevantes",
                "PETR4",
                "--data-inicio",
                "2026-01-01",
                "--data-fim",
                "2026-06-30",
            ]
        )
        assert args.data_inicio == date(2026, 1, 1)
        assert args.data_fim == date(2026, 6, 30)

    def test_parser_flags_padrao_none(self):
        args = build_parser().parse_args([])
        assert args.fatos_relevantes is None
        assert args.noticias is False
        assert args.regulacao is False
        assert args.categoria is None
        assert args.palavra is None


class TestRunFatosRelevantes:
    def test_imprime_json_com_company_name_e_code_cvm(self, capsys):
        resultado = {
            "tipo": "fatos_relevantes",
            "dataExtracao": "2026-07-29T14:30:00",
            "metadados": {
                "codeCVM": "9512",
                "empresa": "PETROLEO BRASILEIRO S.A. PETROBRAS",
                "ticker": "PETR4",
            },
            "documentos": [
                {
                    "codeCVM": "9512",
                    "companyName": "PETROLEO BRASILEIRO S.A. PETROBRAS",
                    "ticker": "PETR4",
                    "dataReferencia": "16/04/2026 14:16",
                    "categoria": "Fatos Relevantes",
                    "assunto": "Tomada de Contas",
                }
            ],
        }
        with patch(_PATH, return_value=_use_case(resultado)) as classe:
            args = argparse.Namespace(
                fatos_relevantes="PETR4",
                categoria=None,
                data_inicio=date(2026, 1, 1),
                data_fim=date(2026, 6, 30),
            )
            run_fatos_relevantes(args)
        payload = json.loads(capsys.readouterr().out)
        assert payload["metadados"]["ticker"] == "PETR4"
        assert payload["metadados"]["codeCVM"] == "9512"
        assert payload["documentos"][0]["companyName"].startswith("PETROLEO")
        chamada = classe.return_value.execute.call_args
        assert chamada.args[0] == "fatos"
        assert chamada.kwargs["ticker"] == "PETR4"

    def test_categoria_especifica_repassada(self, capsys):
        resultado = {
            "tipo": "fatos_relevantes",
            "metadados": {"codeCVM": "9512", "empresa": None, "ticker": "PETR4"},
            "documentos": [],
        }
        with patch(_PATH, return_value=_use_case(resultado)) as classe:
            args = argparse.Namespace(
                fatos_relevantes="petr4",
                categoria="4",
                data_inicio=None,
                data_fim=None,
            )
            run_fatos_relevantes(args)
        payload = json.loads(capsys.readouterr().out)
        assert payload["metadados"]["ticker"] == "PETR4"
        chamada = classe.return_value.execute.call_args
        assert chamada.kwargs["categoria"] == "4"
        assert chamada.kwargs["ticker"] == "PETR4"


class TestRunNoticias:
    def test_imprime_json_com_periodo(self, capsys):
        resultado = {
            "tipo": "noticias",
            "dataExtracao": "2026-07-29T14:30:00",
            "noticias": [],
        }
        with patch(_PATH, return_value=_use_case(resultado)) as classe:
            args = argparse.Namespace(
                palavra=None,
                data_inicio=date(2026, 7, 1),
                data_fim=date(2026, 7, 29),
            )
            run_noticias(args)
        payload = json.loads(capsys.readouterr().out)
        assert payload["tipo"] == "noticias"
        chamada = classe.return_value.execute.call_args
        assert chamada.args[0] == "noticias"
        assert chamada.kwargs["data_inicio"] == date(2026, 7, 1)
        assert chamada.kwargs["data_fim"] == date(2026, 7, 29)

    def test_palavra_repassada(self):
        resultado = {
            "tipo": "noticias",
            "noticias": [
                {
                    "titulo": "PETROBRAS anuncia dividendos",
                    "dataPublicacao": "2026-07-28",
                    "url": "https://x",
                    "agencia": "18",
                }
            ],
        }
        with patch(_PATH, return_value=_use_case(resultado)) as classe:
            args = argparse.Namespace(palavra="PETROBRAS", data_inicio=None, data_fim=None)
            run_noticias(args)
        chamada = classe.return_value.execute.call_args
        assert chamada.kwargs["palavra"] == "PETROBRAS"


class TestRunRegulacao:
    def test_imprime_json_com_censuras_e_condicoes(self, capsys):
        resultado = {
            "tipo": "regulacao",
            "dataExtracao": "2026-07-29T14:30:00",
            "censuras": [
                {"titulo": "FII TORDE EI (TORD)", "ticker": "TORD", "data": "25/02/2026"}
            ],
            "condicoes": [],
        }
        with patch(_PATH, return_value=_use_case(resultado)) as classe:
            run_regulacao(argparse.Namespace())
        payload = json.loads(capsys.readouterr().out)
        assert payload["censuras"][0]["ticker"] == "TORD"
        assert "condicoes" in payload
        assert classe.return_value.execute.call_args.args[0] == "regulacao"


class TestCenarioSemDados:
    def test_ticker_sem_code_cvm_imprime_json_vazio_sem_crash(self, capsys):
        resultado = {
            "tipo": "fatos_relevantes",
            "metadados": {"codeCVM": None, "empresa": None, "ticker": "SEM_CVM"},
            "documentos": [],
        }
        with patch(_PATH, return_value=_use_case(resultado)):
            args = argparse.Namespace(
                fatos_relevantes="SEM_CVM",
                categoria=None,
                data_inicio=None,
                data_fim=None,
            )
            run_fatos_relevantes(args)
        payload = json.loads(capsys.readouterr().out)
        assert payload["documentos"] == []
        assert payload["metadados"]["codeCVM"] is None
