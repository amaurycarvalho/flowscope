"""Testes da classificação de quadrantes CLV x desvio do VWAP."""

from flowscope.domain.strategies.classifiers import QUADRANTES, classify_quadrant


class TestClassifyQuadrant:
    def test_q1_comprador_acima_do_vwap(self):
        assert classify_quadrant(0.3, 0.5) == "Q1"

    def test_q2_vendedor_acima_do_vwap(self):
        assert classify_quadrant(-0.3, 0.5) == "Q2"

    def test_q3_vendedor_abaixo_do_vwap(self):
        assert classify_quadrant(-0.3, -0.5) == "Q3"

    def test_q4_comprador_abaixo_do_vwap(self):
        assert classify_quadrant(0.3, -0.5) == "Q4"

    def test_pontos_sobre_os_eixos_nao_tem_quadrante(self):
        assert classify_quadrant(0.0, 0.5) is None
        assert classify_quadrant(0.5, 0.0) is None
        assert classify_quadrant(0.0, 0.0) is None

    def test_quadrantes_na_ordem_de_exibicao(self):
        assert QUADRANTES == ("Q1", "Q2", "Q3", "Q4")
