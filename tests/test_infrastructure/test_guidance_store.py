"""Testes do store de guidance de distribuição em JSON por FII."""

import json
from datetime import date
from decimal import Decimal

from flowscope.domain.fii import Guidance
from flowscope.infrastructure.guidance_store import JsonGuidanceStore

GUIDANCE = Guidance(
    valor_min=Decimal("0.74"),
    valor_max=Decimal("0.78"),
    periodo="restante do ano de 2026",
    data_relatorio=date(2026, 8, 1),
    caminho_pdf="/cache/documentos-relevantes/ALZR11/2026/08/relatorio/10.pdf",
)


def _salvar_json(tmp_path, payload) -> None:
    pasta = tmp_path / "guidance"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "ALZR11.json").write_text(json.dumps(payload), encoding="utf-8")


class TestRoundTrip:
    def test_ausente_retorna_sem_guidance(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None

    def test_salva_e_recupera_a_proveniencia(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        store.salvar("ALZR11", GUIDANCE)
        assert store.obter("ALZR11") == GUIDANCE

    def test_arquivo_fica_no_subdiretorio_do_ticker(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        store.salvar("alzr11", GUIDANCE)
        assert (tmp_path / "guidance" / "ALZR11.json").exists()

    def test_salvar_substitui_o_guidance_anterior(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        store.salvar("ALZR11", GUIDANCE)
        novo = Guidance(
            valor_min=Decimal("0.85"),
            valor_max=Decimal("0.85"),
            periodo="2S26",
            data_relatorio=date(2026, 9, 1),
        )
        store.salvar("ALZR11", novo)
        assert store.obter("ALZR11") == novo


class TestTolerancia:
    def test_json_corrompido_e_ausencia(self, tmp_path):
        pasta = tmp_path / "guidance"
        pasta.mkdir(parents=True)
        (pasta / "ALZR11.json").write_text("{nao e json", encoding="utf-8")
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None

    def test_payload_nao_dicionario_e_ausencia(self, tmp_path):
        _salvar_json(tmp_path, ["lista"])
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None

    def test_payload_sem_guidance_e_ausencia(self, tmp_path):
        _salvar_json(tmp_path, {"schema_version": 1})
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None

    def test_guidance_com_valor_invalido_e_descartado(self, tmp_path):
        _salvar_json(
            tmp_path,
            {
                "guidance": {
                    "valor_min": "x",
                    "valor_max": "0,78",
                    "periodo": "2S26",
                    "data_relatorio": "2026-08-01",
                }
            },
        )
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None

    def test_guidance_sem_data_e_descartado(self, tmp_path):
        _salvar_json(
            tmp_path,
            {
                "guidance": {
                    "valor_min": "0.74",
                    "valor_max": "0.78",
                    "periodo": "2S26",
                }
            },
        )
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None

    def test_campos_textuais_invalidos_sao_normalizados(self, tmp_path):
        _salvar_json(
            tmp_path,
            {
                "guidance": {
                    "valor_min": "0.74",
                    "valor_max": "0.78",
                    "periodo": 42,
                    "data_relatorio": "2026-08-01",
                    "caminho_pdf": 7,
                }
            },
        )
        store = JsonGuidanceStore(cache_dir=tmp_path)
        guidance = store.obter("ALZR11")
        assert guidance is not None
        assert guidance.periodo == ""
        assert guidance.caminho_pdf is None
