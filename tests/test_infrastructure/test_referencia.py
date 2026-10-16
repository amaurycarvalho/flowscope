import json
from datetime import date, datetime, timezone

from flowscope.infrastructure.referencia import (
    registrar_last_fundamentals,
    resolver_data_referencia,
)


class TestResolverDataReferencia:
    def test_marcador_presente(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps({"last_fundamentals": {"data": "2026-10-14"}}),
            encoding="utf-8",
        )
        assert resolver_data_referencia(path) == date(2026, 10, 14)

    def test_marcador_tem_prioridade_sobre_last_date(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps(
                {
                    "last_fundamentals": {"data": "2026-10-14"},
                    "last_date": "2020-01-01",
                }
            ),
            encoding="utf-8",
        )
        assert resolver_data_referencia(path) == date(2026, 10, 14)

    def test_fallback_last_date(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"last_date": "2026-08-01"}), encoding="utf-8")
        assert resolver_data_referencia(path) == date(2026, 8, 1)

    def test_sem_data(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"last_tab": "X"}), encoding="utf-8")
        assert resolver_data_referencia(path) is None

    def test_arquivo_ausente(self, tmp_path):
        assert resolver_data_referencia(tmp_path / "nao.json") is None


class TestRegistrarLastFundamentals:
    def test_registra_marcador(self, tmp_path):
        path = tmp_path / "config.json"
        momento = datetime(2026, 10, 14, 9, 30, tzinfo=timezone.utc)
        registrar_last_fundamentals(
            date(2026, 10, 14), fetched_at=momento, path=path
        )
        dados = json.loads(path.read_text(encoding="utf-8"))
        assert dados["last_fundamentals"]["data"] == "2026-10-14"
        assert dados["last_fundamentals"]["fetched_at"] == momento.isoformat()

    def test_preserva_outras_chaves(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps({"last_tickers": ["PETR4"], "llm": {"chat": {}}}),
            encoding="utf-8",
        )
        registrar_last_fundamentals(date(2026, 10, 14), path=path)
        dados = json.loads(path.read_text(encoding="utf-8"))
        assert dados["last_tickers"] == ["PETR4"]
        assert dados["llm"] == {"chat": {}}
        assert dados["last_fundamentals"]["data"] == "2026-10-14"

    def test_nao_sobrescrito_por_mudanca_de_campo_sem_carga(self, tmp_path):
        from flowscope.presentation.composicao import salvar_preferencias

        path = tmp_path / "config.json"
        registrar_last_fundamentals(date(2026, 10, 14), path=path)
        salvar_preferencias(tmp_path, path, {"last_date": "2020-01-01"})
        dados = json.loads(path.read_text(encoding="utf-8"))
        assert dados["last_fundamentals"]["data"] == "2026-10-14"
        assert resolver_data_referencia(path) == date(2026, 10, 14)

    def test_carga_por_cli_e_gui_gravam_o_mesmo_formato(self, tmp_path):
        path = tmp_path / "config.json"
        registrar_last_fundamentals(date(2026, 10, 14), path=path)
        dados = json.loads(path.read_text(encoding="utf-8"))
        assert set(dados["last_fundamentals"]) == {"data", "fetched_at"}
