"""Testes do ledger de avaliações de guidance em JSON por FII."""

import json
import threading
from datetime import date
from decimal import Decimal

from flowscope.domain.fii import (
    METODO_DETERMINISTICO,
    METODO_IA,
    AvaliacaoGuidance,
    Guidance,
)
from flowscope.infrastructure.guidance_store import JsonGuidanceStore

GUIDANCE = Guidance(
    valor_min=Decimal("0.74"),
    valor_max=Decimal("0.78"),
    periodo="restante do ano de 2026",
    data_relatorio=date(2026, 8, 1),
    caminho_pdf="/cache/documentos-relevantes/ALZR11/2026/08/relatorio/10.pdf",
)

AVALIACAO_IA = AvaliacaoGuidance(
    metodo=METODO_IA,
    data_relatorio=date(2026, 8, 1),
    caminho_pdf="/cache/documentos-relevantes/ALZR11/2026/08/relatorio/10.pdf",
    guidance=GUIDANCE,
)

AVALIACAO_AUSENTE = AvaliacaoGuidance(
    metodo=METODO_DETERMINISTICO,
    data_relatorio=date(2026, 9, 1),
    caminho_pdf="/cache/documentos-relevantes/ALZR11/2026/09/relatorio/11.pdf",
    guidance=None,
)


def _escrever(tmp_path, payload) -> None:
    pasta = tmp_path / "guidance"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "ALZR11.json").write_text(json.dumps(payload), encoding="utf-8")


class TestRoundTrip:
    def test_ausente_retorna_sem_guidance(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None
        assert store.obter_avaliacao("ALZR11", "a1b2") is None

    def test_salva_e_recupera_a_avaliacao(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        store.salvar_avaliacao("ALZR11", "a1b2", AVALIACAO_IA)
        assert store.obter_avaliacao("ALZR11", "a1b2") == AVALIACAO_IA
        assert store.obter("ALZR11") == GUIDANCE

    def test_arquivo_fica_no_subdiretorio_do_ticker(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        store.salvar_avaliacao("alzr11", "a1b2", AVALIACAO_IA)
        assert (tmp_path / "guidance" / "ALZR11.json").exists()

    def test_salvar_mesma_chave_substitui(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        store.salvar_avaliacao("ALZR11", "a1b2", AVALIACAO_IA)
        novo = AvaliacaoGuidance(
            metodo=METODO_IA,
            data_relatorio=date(2026, 8, 1),
            guidance=Guidance(
                valor_min=Decimal("0.85"),
                valor_max=Decimal("0.85"),
                periodo="2S26",
                data_relatorio=date(2026, 8, 1),
            ),
        )
        store.salvar_avaliacao("ALZR11", "a1b2", novo)
        assert store.obter_avaliacao("ALZR11", "a1b2") == novo

    def test_persiste_no_schema_v2(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        store.salvar_avaliacao("ALZR11", "a1b2", AVALIACAO_IA)
        dados = json.loads(
            (tmp_path / "guidance" / "ALZR11.json").read_text(encoding="utf-8")
        )
        assert dados["schema_version"] == 2
        assert "a1b2" in dados["avaliacoes"]


class TestDerivacao:
    def test_guidance_corrente_e_o_de_maior_data(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        julho = AvaliacaoGuidance(
            metodo=METODO_DETERMINISTICO,
            data_relatorio=date(2026, 7, 1),
            guidance=Guidance(
                valor_min=Decimal("0.70"),
                valor_max=Decimal("0.70"),
                periodo="jul",
                data_relatorio=date(2026, 7, 1),
            ),
        )
        store.salvar_avaliacao("ALZR11", "h1", julho)
        store.salvar_avaliacao("ALZR11", "a1b2", AVALIACAO_IA)
        assert store.obter("ALZR11") == GUIDANCE

    def test_ausencia_recente_nao_apaga_guidance_anterior(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        store.salvar_avaliacao("ALZR11", "a1b2", AVALIACAO_IA)
        store.salvar_avaliacao("ALZR11", "c3d4", AVALIACAO_AUSENTE)
        assert store.obter("ALZR11") == GUIDANCE

    def test_sem_guidance_derivado_e_ausencia(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        store.salvar_avaliacao("ALZR11", "c3d4", AVALIACAO_AUSENTE)
        assert store.obter("ALZR11") is None


class TestMigracaoV1:
    def test_v1_vira_entrada_deterministica(self, tmp_path):
        _escrever(
            tmp_path,
            {
                "schema_version": 1,
                "guidance": {
                    "valor_min": "0.74",
                    "valor_max": "0.78",
                    "periodo": "restante do ano de 2026",
                    "data_relatorio": "2026-08-01",
                    "caminho_pdf": GUIDANCE.caminho_pdf,
                },
            },
        )
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") == GUIDANCE
        entrada = store.obter_avaliacao("ALZR11", "legacy")
        assert entrada is not None
        assert entrada.metodo == METODO_DETERMINISTICO

    def test_v1_sem_schema_tambem_migra(self, tmp_path):
        _escrever(
            tmp_path,
            {
                "guidance": {
                    "valor_min": "0.74",
                    "valor_max": "0.78",
                    "periodo": "",
                    "data_relatorio": "2026-08-01",
                }
            },
        )
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is not None

    def test_regrava_em_v2_apos_avaliar(self, tmp_path):
        _escrever(
            tmp_path,
            {
                "schema_version": 1,
                "guidance": {
                    "valor_min": "0.74",
                    "valor_max": "0.78",
                    "periodo": "",
                    "data_relatorio": "2026-08-01",
                },
            },
        )
        store = JsonGuidanceStore(cache_dir=tmp_path)
        store.salvar_avaliacao("ALZR11", "a1b2", AVALIACAO_IA)
        dados = json.loads(
            (tmp_path / "guidance" / "ALZR11.json").read_text(encoding="utf-8")
        )
        assert dados["schema_version"] == 2


class TestTolerancia:
    def test_json_corrompido_e_ausencia(self, tmp_path):
        pasta = tmp_path / "guidance"
        pasta.mkdir(parents=True)
        (pasta / "ALZR11.json").write_text("{nao e json", encoding="utf-8")
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None

    def test_payload_nao_dicionario_e_ausencia(self, tmp_path):
        _escrever(tmp_path, ["lista"])
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None

    def test_avaliacoes_nao_dicionario_e_ausencia(self, tmp_path):
        _escrever(tmp_path, {"schema_version": 2, "avaliacoes": ["x"]})
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None

    def test_entrada_com_valor_invalido_e_descartada(self, tmp_path):
        _escrever(
            tmp_path,
            {
                "schema_version": 2,
                "avaliacoes": {
                    "a1b2": {
                        "metodo": "deterministico",
                        "data_relatorio": "2026-08-01",
                        "guidance": {
                            "valor_min": "x",
                            "valor_max": "0,78",
                            "periodo": "2S26",
                        },
                    }
                },
            },
        )
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11") is None

    def test_entrada_sem_data_e_descartada(self, tmp_path):
        _escrever(
            tmp_path,
            {
                "schema_version": 2,
                "avaliacoes": {"a1b2": {"metodo": "ia", "guidance": None}},
            },
        )
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter_avaliacao("ALZR11", "a1b2") is None

    def test_periodo_nao_textual_e_normalizado(self, tmp_path):
        _escrever(
            tmp_path,
            {
                "schema_version": 2,
                "avaliacoes": {
                    "a1b2": {
                        "metodo": "ia",
                        "data_relatorio": "2026-08-01",
                        "guidance": {
                            "valor_min": "0.74",
                            "valor_max": "0.78",
                            "periodo": 42,
                        },
                    }
                },
            },
        )
        store = JsonGuidanceStore(cache_dir=tmp_path)
        assert store.obter("ALZR11").periodo == ""


class TestConcorrencia:
    def test_gravacoes_concorrentes_preservam_ambas(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        barreira = threading.Barrier(2)

        def gravar(chave, avaliacao):
            barreira.wait()
            store.salvar_avaliacao("ALZR11", chave, avaliacao)

        t1 = threading.Thread(target=gravar, args=("a1b2", AVALIACAO_IA))
        t2 = threading.Thread(target=gravar, args=("c3d4", AVALIACAO_AUSENTE))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert store.obter_avaliacao("ALZR11", "a1b2") == AVALIACAO_IA
        assert store.obter_avaliacao("ALZR11", "c3d4") == AVALIACAO_AUSENTE
