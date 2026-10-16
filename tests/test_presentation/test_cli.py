import argparse
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
from flowscope.presentation import cli_consultas
from flowscope.presentation.cli import _load_tickers, _parse_data, build_parser


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


def _mock_use_case(documentos):
    use_case = MagicMock()
    use_case.execute.return_value = documentos
    return use_case


class TestBuildParser:
    def test_parser_has_gui_flag(self):
        args = build_parser().parse_args(["--gui"])
        assert args.gui

    def test_parser_has_version_flag(self):
        args = build_parser().parse_args(["--version"])
        assert args.version

    def test_parser_registra_exportar(self):
        args = build_parser().parse_args(["exportar", "vwap"])
        assert args.comando == "exportar"
        assert args.recurso == "vwap"

    def test_parser_registra_consultar(self):
        args = build_parser().parse_args(
            ["consultar", "proventos", "ALZR11", "--data-inicio", "2026-01-01",
             "--data-fim", "2026-07-29"]
        )
        assert args.comando == "consultar"
        assert args.recurso == "proventos"
        assert args.ticker == "ALZR11"
        assert args.data_inicio == date(2026, 1, 1)
        assert args.data_fim == date(2026, 7, 29)

    def test_flags_planas_removidas(self):
        parser = build_parser()
        for argv in (["--vwap"], ["--structured-earnings", "ALZR11"],
                     ["--fatos-relevantes", "PETR4"], ["--noticias"],
                     ["--regulacao"], ["--tickers", "t.txt"], ["--mcp"]):
            with pytest.raises(SystemExit):
                parser.parse_args(argv)

    def test_parser_default_no_args(self):
        args = build_parser().parse_args([])
        assert not args.gui
        assert not args.version
        assert args.comando is None


class TestLoadTickers:
    def test_load_valid_file(self, tmp_path):
        f = tmp_path / "tickers.txt"
        f.write_text("PETR4\nVALE3\nITUB4\n")
        assert _load_tickers(str(f)) == ["PETR4", "VALE3", "ITUB4"]

    def test_normalizes_lines(self, tmp_path):
        f = tmp_path / "tickers.txt"
        f.write_text(" petr4 \nVale3\n\n", encoding="utf-8")
        assert _load_tickers(str(f)) == ["PETR4", "VALE3"]

    def test_file_not_found(self):
        with pytest.raises(SystemExit):
            _load_tickers("/nonexistent/tickers.txt")

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        with pytest.raises(SystemExit):
            _load_tickers(str(f))

    def test_file_not_found_exits_with_code_1(self, tmp_path, capsys):
        from flowscope.presentation import cli

        with patch.object(cli.sys, "exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                cli._load_tickers(str(tmp_path / "missing.txt"))
        mock_exit.assert_called_once_with(1)
        assert "não encontrado" in capsys.readouterr().err

    def test_empty_file_exits_with_code_1(self, tmp_path, capsys):
        from flowscope.presentation import cli

        f = tmp_path / "tickers.txt"
        f.write_text("   ", encoding="utf-8")
        with patch.object(cli.sys, "exit", side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                cli._load_tickers(str(f))
        mock_exit.assert_called_once_with(1)
        assert "está vazio" in capsys.readouterr().err


class TestParseData:
    def test_data_valida(self):
        assert _parse_data("2026-07-29") == date(2026, 7, 29)

    def test_data_invalida_levanta(self):
        from argparse import ArgumentTypeError

        with pytest.raises(ArgumentTypeError):
            _parse_data("29/07/2026")


class TestExportarVwap:
    def _args(self, **kwargs):
        base = dict(comando="exportar", recurso="vwap", tickers=None, saida=None)
        base.update(kwargs)
        return argparse.Namespace(**base)

    def test_grava_arquivo_padrao_com_data(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        use_case = MagicMock()
        use_case.execute.return_value = "Ticker;VWAP_Periodo"
        with patch(
            "flowscope.application.use_cases.ExportVWAPUseCase", return_value=use_case
        ):
            cli_consultas.executar_exportar(self._args())
        arquivos = list(tmp_path.glob("vwap_*.csv"))
        assert len(arquivos) == 1
        assert arquivos[0].read_text(encoding="utf-8") == "Ticker;VWAP_Periodo"

    def test_saida_customizada_sobrescreve_nome(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        destino = tmp_path / "relatorio.csv"
        use_case = MagicMock()
        use_case.execute.return_value = "conteudo"
        with patch(
            "flowscope.application.use_cases.ExportVWAPUseCase", return_value=use_case
        ):
            cli_consultas.executar_exportar(self._args(saida=str(destino)))
        assert destino.read_text(encoding="utf-8") == "conteudo"
        assert list(tmp_path.glob("vwap_*.csv")) == []

    def test_tickers_filtra_exportacao(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        use_case = MagicMock()
        use_case.execute.return_value = "x"
        with (
            patch(
                "flowscope.application.use_cases.ExportVWAPUseCase",
                return_value=use_case,
            ),
            patch.object(cli_consultas, "_load_tickers", return_value=["PETR4"]),
        ):
            cli_consultas.executar_exportar(self._args(tickers="meus.txt"))
        assert use_case.execute.call_args.kwargs["ticker_filter"] == ["PETR4"]


class TestConsultarProventos:
    def _args(self, **kwargs):
        base = dict(
            comando="consultar",
            recurso="proventos",
            ticker="ALZR11",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 7, 29),
            saida=None,
        )
        base.update(kwargs)
        return argparse.Namespace(**base)

    def test_imprime_json_no_stdout_com_documentos(self, capsys):
        use_case = _mock_use_case([_documento()])
        with patch(
            "flowscope.application.structured_use_cases.ExtrairProventosUseCase",
            return_value=use_case,
        ):
            cli_consultas.executar_consultar(self._args())
        payload = json.loads(capsys.readouterr().out)
        assert payload[0]["ticker"] == "ALZR11"
        assert payload[0]["dadosFundos"]["nomeFundo"] == "ALIANZA TRUST FUNDO"

    def test_sem_dados_exibe_mensagem_sem_erro(self, capsys):
        use_case = _mock_use_case([])
        with patch(
            "flowscope.application.structured_use_cases.ExtrairProventosUseCase",
            return_value=use_case,
        ):
            cli_consultas.executar_consultar(self._args(ticker="PETR4"))
        assert "Nenhum dado disponível para PETR4" in capsys.readouterr().out

    def test_saida_grava_arquivo_json(self, tmp_path, capsys):
        use_case = _mock_use_case([_documento()])
        destino = tmp_path / "proventos.json"
        with patch(
            "flowscope.application.structured_use_cases.ExtrairProventosUseCase",
            return_value=use_case,
        ):
            cli_consultas.executar_consultar(self._args(saida=str(destino)))
        payload = json.loads(destino.read_text(encoding="utf-8"))
        assert payload[0]["dadosProvento"]["valorPorUnidade"] == "0.08355"
        assert "Extra" in capsys.readouterr().out
