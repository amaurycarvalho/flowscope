"""Testes puros da preparação de dados e resumo dos quadrantes."""

from datetime import date

import pytest

from flowscope.application.quadrant import (
    PontoQuadrante,
    build_trajectories,
    compute_scatter_data,
    count_quadrants,
    generate_summary,
    max_trajectory_qty,
    pick_interpretation,
    point_size,
)

D1 = date(2025, 1, 1)
D2 = date(2025, 1, 2)


def _info(
    clv: dict,
    vwap_distance: dict,
    datas: tuple[date, ...] = (D1, D2),
    qty: int = 10,
) -> dict:
    return {
        "daily_data": [
            {"date": dt, "fin_instr_qty": qty} for dt in datas
        ],
        "all_indicators": {
            "clv": clv,
            "vwap_distance": vwap_distance,
        },
    }


class TestBuildTrajectories:
    def test_ordena_por_data_e_escala_o_desvio(self):
        data = {
            "PETR4": _info(
                clv={D1: 0.1, D2: 0.2},
                vwap_distance={D1: 0.5, D2: -0.25},
                datas=(D2, D1),
                qty=10,
            )
        }
        trajectories = build_trajectories(data)
        assert len(trajectories) == 1
        pontos = trajectories[0]
        assert [(p.date, p.clv, p.vwap_dist) for p in pontos] == [
            (D1, 0.1, 50.0),
            (D2, 0.2, -25.0),
        ]
        assert [p.ticker for p in pontos] == ["PETR4", "PETR4"]

    def test_ignora_ticker_sem_dados_diarios(self):
        assert build_trajectories({"X": {"daily_data": []}}) == []

    def test_ignora_registros_sem_indicadores(self):
        data = {
            "PETR4": _info(
                clv={D1: 0.1},
                vwap_distance={D1: 0.5},
            )
        }
        trajectories = build_trajectories(data)
        assert len(trajectories) == 1
        assert len(trajectories[0]) == 1
        assert trajectories[0][0].date == D1

    def test_ticker_sem_pontos_validos_e_descartado(self):
        data = {
            "PETR4": _info(clv={}, vwap_distance={}),
            "VALE3": _info(clv={D1: 0.1}, vwap_distance={D1: 0.5}),
        }
        trajectories = build_trajectories(data)
        assert len(trajectories) == 1
        assert trajectories[0][0].ticker == "VALE3"

    def test_sem_indicadores_retorna_vazio(self):
        assert build_trajectories({}) == []
        assert build_trajectories({"X": {"daily_data": [{"date": D1}]}}) == []


class TestMaxTrajectoryQty:
    def test_maior_quantidade_entre_trajetorias(self):
        trajectories = [
            [
                PontoQuadrante("A", D1, 0.1, 0.5, 10),
                PontoQuadrante("A", D2, 0.2, 0.6, 100),
            ],
            [PontoQuadrante("B", D1, -0.1, -0.5, 50)],
        ]
        assert max_trajectory_qty(trajectories) == 100


class TestPointSize:
    def test_escala_pela_raiz_da_quantidade(self):
        assert point_size(PontoQuadrante("A", D1, 0.0, 0.0, 100), 100) == 200.0
        assert point_size(PontoQuadrante("A", D1, 0.0, 0.0, 25), 100) == 100.0

    def test_tamanho_minimo(self):
        assert point_size(PontoQuadrante("A", D1, 0.0, 0.0, 0), 100) == 10.0

    def test_sem_referencia_usa_minimo_relativo(self):
        assert point_size(PontoQuadrante("A", D1, 0.0, 0.0, 5), 0) == 20.0


class TestComputeScatterData:
    def test_coordenadas_dos_pontos_finais(self):
        trajectories = [
            [
                PontoQuadrante("A", D1, 0.1, 0.5, 10),
                PontoQuadrante("A", D2, 0.2, -0.5, 100),
            ],
            [PontoQuadrante("B", D1, -0.1, 0.25, 50)],
        ]
        last_x, last_y, last_sizes, last_colors, all_y, last_points = (
            compute_scatter_data(trajectories)
        )
        assert last_x == [0.2, -0.1]
        assert last_y == [-0.5, 0.25]
        assert last_colors == [0.2, -0.1]
        assert last_sizes[0] == 200.0
        assert last_sizes[1] == pytest.approx(50.0 ** 0.5 / 100 ** 0.5 * 200)
        assert all_y == [0.5, -0.5, 0.25]
        assert last_points == [trajectories[0][-1], trajectories[1][-1]]


class TestCountQuadrants:
    def test_conta_por_quadrante_e_ignora_eixos(self):
        trajectories = [
            [PontoQuadrante("A", D1, 0.1, 0.5, 1)],
            [PontoQuadrante("B", D1, -0.1, 0.5, 1)],
            [PontoQuadrante("C", D1, -0.1, -0.5, 1)],
            [PontoQuadrante("D", D1, 0.1, -0.5, 1)],
            [PontoQuadrante("E", D1, 0.0, 0.5, 1)],
        ]
        assert count_quadrants(trajectories) == {
            "Q1": 1, "Q2": 1, "Q3": 1, "Q4": 1,
        }

    def test_sem_pontos_zera(self):
        assert count_quadrants([]) == {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}


class TestPickInterpretation:
    def test_vazio(self):
        assert pick_interpretation({"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}) == ""

    def test_predominancia_q1(self):
        texto = pick_interpretation({"Q1": 3, "Q2": 0, "Q3": 1, "Q4": 0})
        assert "amplamente construtivo" in texto

    def test_predominancia_q3(self):
        texto = pick_interpretation({"Q1": 0, "Q2": 0, "Q3": 3, "Q4": 1})
        assert "distribuição" in texto

    def test_enfraquecimento_q2(self):
        texto = pick_interpretation({"Q1": 0, "Q2": 1, "Q3": 0, "Q4": 0})
        assert "realização de lucros" in texto

    def test_recuperacao_q4(self):
        texto = pick_interpretation({"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 1})
        assert "início de recuperação" in texto

    def test_equilibrio(self):
        texto = pick_interpretation({"Q1": 1, "Q2": 1, "Q3": 1, "Q4": 1})
        assert "equilibrada" in texto


class TestGenerateSummary:
    def test_sem_pontos_retorna_vazio(self):
        assert generate_summary([]) == ""

    def test_distribuicao_e_interpretacao(self):
        trajectories = [[PontoQuadrante("A", D1, 0.1, 0.5, 1)]]
        resumo = generate_summary(trajectories)
        assert resumo.startswith(
            "Distribuição: Q1=1, Q2=0, Q3=0, Q4=0 (total: 1)\n\n"
        )
        assert "amplamente construtivo" in resumo
