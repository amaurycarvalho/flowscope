"""Testes da leitura e escrita atômica do snapshot de performance."""

import json
import logging
from datetime import date, datetime, timezone
from unittest.mock import patch

from flowscope.application.performance import (
    SCHEMA_VERSION_SNAPSHOT,
    montar_payload,
    montar_snapshot,
)
from flowscope.infrastructure.performance import JsonPerformanceSnapshotStore


def _snapshot() -> dict:
    return montar_snapshot(
        montar_payload({}, {}, [], []),
        ref_date=date(2026, 11, 7),
        period_days=30,
        sampling_method="fibonacci",
        source="headless",
        cached_at=datetime(2026, 11, 7, 18, 30, tzinfo=timezone.utc),
    )


class TestJsonPerformanceSnapshotStore:
    def test_caminho_padrao(self, tmp_path):
        store = JsonPerformanceSnapshotStore(cache_dir=tmp_path)
        assert store.caminho == tmp_path / "performance" / "latest.json"

    def test_grava_e_le_roundtrip(self, tmp_path):
        store = JsonPerformanceSnapshotStore(cache_dir=tmp_path)
        assert store.gravar(_snapshot()) is True
        assert store.ler() == _snapshot()

    def test_ausente_retorna_none(self, tmp_path):
        assert JsonPerformanceSnapshotStore(cache_dir=tmp_path).ler() is None

    def test_json_invalido_retorna_none_e_loga(self, tmp_path, caplog):
        store = JsonPerformanceSnapshotStore(cache_dir=tmp_path)
        store.caminho.parent.mkdir(parents=True, exist_ok=True)
        store.caminho.write_text("nao-json", encoding="utf-8")
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            assert store.ler() is None
        assert "snapshot ilegível" in caplog.text

    def test_resultado_nao_dicionario_retorna_none(self, tmp_path, caplog):
        store = JsonPerformanceSnapshotStore(cache_dir=tmp_path)
        store.caminho.parent.mkdir(parents=True, exist_ok=True)
        store.caminho.write_text(
            json.dumps({"schema_version": SCHEMA_VERSION_SNAPSHOT, "results": []}),
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            assert store.ler() is None
        assert "sem objeto de resultados" in caplog.text

    def test_schema_divergente_retorna_none(self, tmp_path, caplog):
        store = JsonPerformanceSnapshotStore(cache_dir=tmp_path)
        store.caminho.parent.mkdir(parents=True, exist_ok=True)
        store.caminho.write_text(
            json.dumps(
                {
                    "schema_version": 99,
                    "results": {},
                    "ref_date": "2026-11-07",
                    "period_days": 30,
                    "sampling_method": "fibonacci",
                    "cached_at": "2026-11-07T00:00:00+00:00",
                    "benchmarks": [],
                    "ticker_types": {},
                }
            ),
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            assert store.ler() is None
        assert "schema divergente" in caplog.text

    def test_falha_de_escrita_nao_propaga(self, tmp_path, caplog):
        store = JsonPerformanceSnapshotStore(cache_dir=tmp_path)
        with patch(
            "flowscope.infrastructure.performance.snapshot_store._atomic_write_bytes",
            side_effect=OSError("sem espaço"),
        ):
            with caplog.at_level(logging.WARNING, logger="flowscope"):
                assert store.gravar(_snapshot()) is False
        assert "falha ao gravar o snapshot" in caplog.text
