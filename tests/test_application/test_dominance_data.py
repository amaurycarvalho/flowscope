"""Testes puros da preparação de dados dos gráficos de dominância."""

from datetime import date
from decimal import Decimal

import pytest

from flowscope.application.dominance.hastes import (
    bar_colors,
    compute_stems,
    stem_length,
)
from flowscope.application.dominance.ranking import (
    RankingRow,
    build_rows,
    stem_lengths,
)
from flowscope.application.dominance.timeline import (
    TimelineRow,
    build_rows as build_timeline_rows,
    direction_balance,
)
from flowscope.domain.strategies.classifiers import classify_dominance

D1 = date(2025, 1, 1)
D2 = date(2025, 1, 2)
D3 = date(2025, 1, 3)


class TestBuildRankingRows:
    def test_extrai_ultimo_clv_e_fluxo(self):
        data = {
            "PETR4": {
                "all_indicators": {"clv": {D1: 0.2, D3: 0.5}},
                "money_flow_volume": Decimal("1000"),
            },
        }
        rows = build_rows(data)
        assert rows == [RankingRow("PETR4", 0.5, 1000.0, D3)]

    def test_fluxo_ausente_vira_zero(self):
        data = {"PETR4": {"all_indicators": {"clv": {D1: 0.1}}}}
        rows = build_rows(data)
        assert rows[0].mfv == 0.0

    def test_ignora_sem_indicadores_ou_clv(self):
        assert build_rows({}) == []
        assert build_rows({"X": {}}) == []
        assert build_rows({"X": {"all_indicators": {}}}) == []

    def test_ignora_clv_nulo_na_ultima_data(self):
        data = {"X": {"all_indicators": {"clv": {D1: 0.3, D2: None}}}}
        assert build_rows(data) == []

    def test_preserva_ordem_de_entrada(self):
        data = {
            "A": {"all_indicators": {"clv": {D1: 0.1}}},
            "B": {"all_indicators": {"clv": {D1: -0.1}}},
        }
        assert [r.ticker for r in build_rows(data)] == ["A", "B"]

    def test_stem_lengths_por_fluxo(self):
        assert stem_lengths([0.0, 5.0], max_val=5.0) == [0.0, 0.1]


class TestBuildTimelineRows:
    def test_ordem_cronologica_decrescente(self):
        info = {
            "all_indicators": {
                "clv": {D1: 0.1, D2: 0.2, D3: None},
                "daily_efficiency": {D1: Decimal("0.5")},
                "daily_money_flow": {D2: Decimal("200")},
            },
        }
        rows = build_timeline_rows(info)
        assert [r.date for r in rows] == [D2, D1]
        assert rows[0] == TimelineRow(D2, 0.2, 0.0, 200.0)
        assert rows[1] == TimelineRow(D1, 0.1, 0.5, 0.0)

    def test_sem_indicadores_retorna_vazio(self):
        assert build_timeline_rows({}) == []
        assert build_timeline_rows({"all_indicators": {}}) == []

    def test_direction_balance_conta_compradores_e_vendedores(self):
        rows = [
            TimelineRow(D1, 0.2, 0.0, 0.0),
            TimelineRow(D2, -0.1, 0.0, 0.0),
            TimelineRow(D3, 0.0, 0.0, 0.0),
        ]
        assert direction_balance(rows) == (1, 1)

    def test_direction_balance_sem_direcao(self):
        assert direction_balance([]) == (0, 0)


class TestStemLength:
    def test_valor_nulo(self):
        assert stem_length(0.0, 10.0, 0.10) == 0.0

    def test_normalizado_pela_raiz(self):
        assert stem_length(4.0, 16.0, 0.10) == pytest.approx(0.05)

    def test_negativo_usa_modulo(self):
        assert stem_length(-4.0, 16.0, 0.10) == pytest.approx(0.05)

    def test_garante_comprimento_minimo(self):
        assert stem_length(0.001, 1000.0, 0.10) == 0.015

    def test_sem_escala_retorna_minimo(self):
        assert stem_length(5.0, 0.0, 0.10) == 0.015


class TestComputeStems:
    def test_hastes_positiva_e_negativa(self):
        ys, xmins, xmaxs, _ = compute_stems(
            values=[10.0, 10.0],
            clvs=[0.5, -0.5],
            y_pos=[0, 1],
            max_val=10.0,
            scale=0.1,
        )
        assert ys == [0, 1]
        assert xmins == [0.0, pytest.approx(-0.6)]
        assert xmaxs == [pytest.approx(0.6), 0.0]

    def test_ignora_valor_zero_ou_clv_pequeno(self):
        ys, _, _, _ = compute_stems(
            values=[10.0, 10.0, 10.0],
            clvs=[0.5, 0.0, 0.01],
            y_pos=[0, 1, 2],
            max_val=10.0,
        )
        assert ys == [0]

    def test_cores_por_intensidade(self):
        _, _, _, colors = compute_stems(
            values=[10.0, 10.0, 10.0, 10.0],
            clvs=[0.05, 0.2, 0.5, 0.9],
            y_pos=[0, 1, 2, 3],
            max_val=10.0,
        )
        assert colors == ["#C0C0C0", "#555555", "#222222", "#0A0A0A"]

    def test_sem_hastes_retorna_listas_vazias(self):
        ys, xmins, xmaxs, colors = compute_stems(
            values=[0.0], clvs=[0.5], y_pos=[0], max_val=10.0,
        )
        assert ys == xmins == xmaxs == colors == []


class TestBarColors:
    def test_cor_por_clv(self):
        clvs = [-0.9, 0.0, 0.5]
        assert bar_colors(clvs) == [classify_dominance(c).color for c in clvs]

    def test_lista_vazia(self):
        assert bar_colors([]) == []
