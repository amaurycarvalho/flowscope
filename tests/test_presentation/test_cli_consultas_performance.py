"""Testes do subcomando ``flowscope exportar performance``."""

import argparse
import json
import logging

import pytest

from flowscope.presentation import cli_consultas


def _snapshot() -> dict:
    return {
        "schema_version": 1,
        "source": "headless",
        "ref_date": "2026-11-07",
        "period_days": 30,
        "sampling_method": "fibonacci",
        "cached_at": "2026-11-07T18:30:00+00:00",
        "benchmarks": ["IFIX", "IBOV"],
        "default": "IFIX",
        "ticker_types": {"HGLG11": "FII", "PETR4": "ACAO"},
        "results": {
            "IFIX": {
                "benchmark": "IFIX",
                "index_available": True,
                "return_basis": "total",
                "tickers": [
                    {
                        "ticker": "HGLG11",
                        "ticker_return": 0.12,
                        "index_return": 0.05,
                        "excess_pp": 7.0,
                        "observations": 20,
                        "suspicious_event": False,
                    }
                ],
            },
            "IBOV": {
                "benchmark": "IBOV",
                "index_available": True,
                "return_basis": "price",
                "tickers": [
                    {
                        "ticker": "PETR4",
                        "ticker_return": 0.03,
                        "index_return": 0.04,
                        "excess_pp": -1.0,
                        "observations": 21,
                        "suspicious_event": True,
                    }
                ],
            },
        },
    }


def _args(**kwargs) -> argparse.Namespace:
    base = {
        "comando": "exportar",
        "recurso": "performance",
        "formato": "csv",
        "benchmark": None,
        "saida": None,
    }
    base.update(kwargs)
    return argparse.Namespace(**base)


@pytest.fixture
def store(monkeypatch):
    estado = {"snapshot": _snapshot()}

    class _Store:
        def __init__(self, cache_dir=None):
            pass

        def ler(self):
            return estado["snapshot"]

    monkeypatch.setattr(
        "flowscope.infrastructure.performance.JsonPerformanceSnapshotStore",
        _Store,
    )
    return estado


class TestExportarPerformance:
    def test_csv_usa_ponto_e_virgula_e_contexto(self, store, capsys):
        cli_consultas.executar_exportar(_args(formato="csv"))
        saida = capsys.readouterr().out
        linhas = saida.strip().splitlines()
        assert linhas[0].split(";")[:5] == [
            "ref_date",
            "period_days",
            "sampling_method",
            "return_basis",
            "index_available",
        ]
        assert "2026-11-07;30;fibonacci;total;true;IFIX;HGLG11;0.12" in saida
        assert "IBOV;PETR4;0.03" in saida

    def test_json_estruturado(self, store, capsys):
        cli_consultas.executar_exportar(_args(formato="json"))
        payload = json.loads(capsys.readouterr().out)
        assert payload["ref_date"] == "2026-11-07"
        assert set(payload["results"]) == {"IFIX", "IBOV"}

    def test_filtro_por_benchmark(self, store, capsys):
        cli_consultas.executar_exportar(_args(formato="json", benchmark="ifix"))
        payload = json.loads(capsys.readouterr().out)
        assert payload["benchmarks"] == ["IFIX"]
        assert set(payload["results"]) == {"IFIX"}

    def test_saida_em_arquivo(self, store, capsys, tmp_path):
        destino = tmp_path / "performance.csv"
        cli_consultas.executar_exportar(_args(formato="csv", saida=str(destino)))
        assert capturas_vazias(capsys)
        assert "HGLG11" in destino.read_text(encoding="utf-8")

    def test_snapshot_ausente(self, store, capsys, caplog):
        store["snapshot"] = None
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            with pytest.raises(SystemExit) as exc:
                cli_consultas.executar_exportar(_args(formato="json"))
        assert exc.value.code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["erro"]["motivo"] == "performance_ausente"
        assert "atualizar performance" in payload["erro"]["dica"]
        assert "exportação sem snapshot" in caplog.text

    def test_benchmark_ausente(self, store, capsys):
        with pytest.raises(SystemExit) as exc:
            cli_consultas.executar_exportar(
                _args(formato="json", benchmark="IDIV")
            )
        assert exc.value.code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["erro"]["motivo"] == "benchmark_ausente"
        assert "IFIX" in payload["erro"]["detalhe"]

    def test_falha_de_escrita(self, store, capsys, tmp_path, caplog):
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            with pytest.raises(SystemExit) as exc:
                cli_consultas.executar_exportar(
                    _args(formato="json", saida=str(tmp_path))
                )
        assert exc.value.code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["erro"]["motivo"] == "falha_escrita"
        assert "falha ao gravar a exportação" in caplog.text


def capturas_vazias(capsys) -> bool:
    """Indica se ``stdout`` e ``stderr`` estão vazios."""
    capturado = capsys.readouterr()
    return capturado.out == "" and capturado.err == ""


class TestParser:
    def test_formato_invalido_rejeitado(self):
        from flowscope.presentation.cli import build_parser

        with pytest.raises(SystemExit):
            build_parser().parse_args(
                ["exportar", "performance", "--formato", "xml"]
            )

    def test_flags_reconhecidas(self):
        from flowscope.presentation.cli import build_parser

        args = build_parser().parse_args(
            [
                "exportar",
                "performance",
                "--formato",
                "csv",
                "--benchmark",
                "IFIX",
                "--saida",
                "x.csv",
            ]
        )
        assert args.recurso == "performance"
        assert args.formato == "csv"
        assert args.benchmark == "IFIX"
        assert args.saida == "x.csv"
