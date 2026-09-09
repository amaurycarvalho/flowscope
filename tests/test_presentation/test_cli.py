import json
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from flowscope.domain.structured import (
    CNPJ,
    DocumentoProvento,
    Entidade,
    ISIN,
    Provento,
    ValorProvento,
)
from flowscope.presentation.cli import (
    _load_tickers,
    _parse_data,
    build_parser,
    export_vwap_csv,
    run_structured_earnings,
)


def _documento() -> DocumentoProvento:
    return DocumentoProvento(
        ticker="ALZR11",
        id_fnet="20294",
        id_documento="1224160",
        url_documento="https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=1224160",
        data_extracao="2026-07-29T14:30:00-03:00",
        entidade=Entidade(
            nome="ALIANZA TRUST FUNDO",
            cnpj=CNPJ("28.737.771/0001-85"),
            nome_administrador="BTG PACTUAL DTVM",
            cnpj_administrador=CNPJ("59.281.253/0001-23"),
            responsavel="Leandro Pereira",
            telefone="(11) 3383-3102",
        ),
        provento=Provento(
            codigo_isin=ISIN("BRALZRCTF006"),
            codigo_negociacao="ALZR11",
            tipo="Rendimento",
            data_base=date(2026, 6, 18),
            valor_por_unidade=ValorProvento(Decimal("0.08355")),
            data_pagamento=date(2026, 6, 25),
            periodo_referencia="Maio-2026",
            isento_ir=True,
        ),
    )


class TestBuildParser:
    def test_parser_has_gui_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--gui"])
        assert args.gui

    def test_parser_has_version_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--version"])
        assert args.version

    def test_parser_has_vwap_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--vwap"])
        assert args.vwap

    def test_parser_tem_structured_earnings(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "--structured-earnings",
                "ALZR11",
                "--data-inicio",
                "2026-01-01",
                "--data-fim",
                "2026-07-29",
            ]
        )
        assert args.structured_earnings == "ALZR11"
        assert args.data_inicio == date(2026, 1, 1)
        assert args.data_fim == date(2026, 7, 29)

    def test_parser_aceita_output(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "--structured-earnings",
                "ALZR11",
                "--data-inicio",
                "2026-01-01",
                "--data-fim",
                "2026-07-29",
                "--output",
                "proventos.json",
            ]
        )
        assert args.output == "proventos.json"

    def test_parser_default_no_args(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert not args.gui
        assert not args.version
        assert args.structured_earnings is None


class TestLoadTickers:
    def test_load_valid_file(self, tmp_path):
        f = tmp_path / "tickers.txt"
        f.write_text("PETR4\nVALE3\nITUB4\n")
        result = _load_tickers(str(f))
        assert result == ["PETR4", "VALE3", "ITUB4"]

    def test_normalizes_lines(self, tmp_path):
        f = tmp_path / "tickers.txt"
        f.write_text(" petr4 \nVale3\n\n", encoding="utf-8")
        result = _load_tickers(str(f))
        assert result == ["PETR4", "VALE3"]

    def test_file_not_found(self):
        with pytest.raises(SystemExit):
            _load_tickers("/nonexistent/tickers.txt")

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        with pytest.raises(SystemExit):
            _load_tickers(str(f))

    def test_file_not_found_exits_with_code_1(self, tmp_path, capsys):
        from unittest.mock import patch

        from flowscope.presentation import cli

        with patch.object(cli.sys, "exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                cli._load_tickers(str(tmp_path / "missing.txt"))
        mock_exit.assert_called_once_with(1)
        assert "não encontrado" in capsys.readouterr().err

    def test_empty_file_exits_with_code_1(self, tmp_path, capsys):
        from unittest.mock import patch

        from flowscope.presentation import cli

        f = tmp_path / "tickers.txt"
        f.write_text("   ", encoding="utf-8")
        with patch.object(cli.sys, "exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                cli._load_tickers(str(f))
        mock_exit.assert_called_once_with(1)
        assert "está vazio" in capsys.readouterr().err


class TestExportVwapCsv:
    def test_genera_cabecalho_e_linhas_com_vwap(self):
        metrics = {
            "PETR4": {"vwap": {"period_vwap": 28.8}},
            "VALE3": {"vwap": {"period_vwap": 62.8}},
            "ITUB4": {},
        }
        content = export_vwap_csv(["PETR4", "VALE3", "ITUB4"], metrics)
        assert "Ticker;VWAP_Periodo" in content
        assert "PETR4;28.8" in content
        assert "VALE3;62.8" in content
        assert "ITUB4" not in content

    def test_sem_vwap_gera_apenas_cabecalho(self):
        content = export_vwap_csv(["PETR4"], {"PETR4": {}})
        assert content == "Ticker;VWAP_Periodo"

    def test_grava_arquivo_quando_output_path_informado(self, tmp_path):
        output = tmp_path / "vwap.csv"
        metrics = {"PETR4": {"vwap": {"period_vwap": 28.8}}}
        content = export_vwap_csv(["PETR4"], metrics, str(output))
        assert output.read_text(encoding="utf-8") == content

    def test_missing_ticker_is_skipped(self):
        metrics = {"PETR4": {"vwap": {"period_vwap": 28.8}}}
        content = export_vwap_csv(["PETR4", "MISSING"], metrics)
        assert content == "Ticker;VWAP_Periodo\nPETR4;28.8"

    def test_exact_content_newlines(self):
        metrics = {
            "PETR4": {"vwap": {"period_vwap": 28.8}},
            "VALE3": {"vwap": {"period_vwap": 62.8}},
        }
        content = export_vwap_csv(["PETR4", "VALE3"], metrics)
        assert content == "Ticker;VWAP_Periodo\nPETR4;28.8\nVALE3;62.8"


class TestParseData:
    def test_data_valida(self):
        assert _parse_data("2026-07-29") == date(2026, 7, 29)

    def test_data_invalida_levanta(self):
        from argparse import ArgumentTypeError

        with pytest.raises(ArgumentTypeError):
            _parse_data("29/07/2026")


class TestRunStructuredEarnings:
    def test_imprime_json_no_stdout_com_documentos(self, capsys):
        use_case = _mock_use_case([_documento()])
        with patch(
            "flowscope.application.structured_use_cases.ExtrairProventosUseCase", return_value=use_case
        ):
            import argparse

            args = argparse.Namespace(
                structured_earnings="ALZR11",
                data_inicio=date(2026, 1, 1),
                data_fim=date(2026, 7, 29),
                output=None,
            )
            run_structured_earnings(args)
        saida = capsys.readouterr().out
        payload = json.loads(saida)
        assert payload[0]["ticker"] == "ALZR11"
        assert payload[0]["dadosFundos"]["nomeFundo"] == "ALIANZA TRUST FUNDO"

    def test_sem_dados_exibe_mensagem_sem_erro(self, capsys):
        use_case = _mock_use_case([])
        with patch(
            "flowscope.application.structured_use_cases.ExtrairProventosUseCase", return_value=use_case
        ):
            import argparse

            args = argparse.Namespace(
                structured_earnings="PETR4",
                data_inicio=date(2026, 1, 1),
                data_fim=date(2026, 7, 29),
                output=None,
            )
            run_structured_earnings(args)
        saida = capsys.readouterr().out
        assert "Nenhum dado disponível para PETR4" in saida

    def test_output_grava_arquivo_json(self, tmp_path, capsys):
        use_case = MagicMock()
        use_case.execute.return_value = [_documento()]
        destino = tmp_path / "proventos.json"
        with patch(
            "flowscope.application.structured_use_cases.ExtrairProventosUseCase", return_value=use_case
        ):
            import argparse

            args = argparse.Namespace(
                structured_earnings="ALZR11",
                data_inicio=date(2026, 1, 1),
                data_fim=date(2026, 7, 29),
                output=str(destino),
            )
            run_structured_earnings(args)
        payload = json.loads(destino.read_text(encoding="utf-8"))
        assert payload[0]["dadosProvento"]["valorPorUnidade"] == "0.08355"
        assert "Extra" in capsys.readouterr().out


def _mock_use_case(documentos):
    use_case = MagicMock()
    use_case.execute.return_value = documentos
    return use_case
