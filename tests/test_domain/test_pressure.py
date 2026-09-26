"""Testes puros da normalização das pressões de compra e venda."""

import pytest

from flowscope.domain.strategies import pressure_percentages


class TestPressurePercentages:
    def test_reparte_conforme_a_pressao(self):
        bp_pct, sp_pct = pressure_percentages(1.0, 3.0)
        assert bp_pct == pytest.approx(25.0)
        assert sp_pct == pytest.approx(75.0)

    def test_pressoes_iguais_metade_cada(self):
        assert pressure_percentages(2.0, 2.0) == (50.0, 50.0)

    def test_sem_pressao_metade_cada(self):
        assert pressure_percentages(0.0, 0.0) == (50.0, 50.0)

    def test_apenas_compra(self):
        assert pressure_percentages(0.5, 0.0) == (100.0, 0.0)

    def test_soma_nao_positiva_metade_cada(self):
        assert pressure_percentages(-1.0, -1.0) == (50.0, 50.0)
