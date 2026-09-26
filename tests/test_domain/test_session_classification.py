"""Testes puros da classificação de pregão (amplitude x eficiência)."""

from flowscope.domain.strategies.classifiers import (
    classify_session,
    classify_trend,
    median_value,
)


class TestClassifyTrend:
    def test_lateral_quando_amplitude_baixa_e_eficiencia_baixa(self):
        assert classify_trend(0.1, 0.2, 0.2) == "Pregão Lateral"

    def test_lateral_no_limite_de_eficiencia_0_30(self):
        assert classify_trend(0.1, 0.2, 0.30) == "Pregão Lateral"

    def test_lateral_quando_amplitude_igual_a_mediana(self):
        assert classify_trend(0.2, 0.2, 0.1) == "Pregão Lateral"

    def test_volatilidade_sem_direcao_com_amplitude_alta(self):
        assert classify_trend(0.3, 0.2, 0.2) == "Volatilidade sem Direção"

    def test_volatilidade_no_limite_de_eficiencia_0_30(self):
        assert classify_trend(0.3, 0.2, 0.30) == "Volatilidade sem Direção"

    def test_consistente_quando_amplitude_baixa_e_eficiencia_alta(self):
        assert classify_trend(0.1, 0.2, 0.31) == "Movimento Consistente"

    def test_consistente_quando_amplitude_igual_a_mediana(self):
        assert classify_trend(0.2, 0.2, 0.5) == "Movimento Consistente"

    def test_direcional_forte_quando_amplitude_alta_e_eficiencia_alta(self):
        assert classify_trend(0.3, 0.2, 0.31) == "Movimento Direcional Forte"


class TestMedianValue:
    def test_lista_impar_retorna_elemento_central(self):
        assert median_value([3.0, 1.0, 2.0]) == 2.0

    def test_lista_par_retorna_media_dos_centrais(self):
        assert median_value([1.0, 2.0, 3.0, 4.0]) == 2.5

    def test_lista_com_um_elemento_retorna_o_proprio(self):
        assert median_value([5.0]) == 5.0

    def test_lista_nao_ordenada_e_ordenada_antes(self):
        assert median_value([9.0, 1.0, 5.0, 3.0]) == 4.0


class TestClassifySession:
    def test_usa_a_ultima_data_informada(self):
        range_pct = {"d1": 0.1, "d2": 0.2, "d3": 0.3}
        eff = {"d1": 0.1, "d2": 0.1, "d3": 0.2}
        assert classify_session("d3", range_pct, eff) == (
            "Volatilidade sem Direção"
        )

    def test_paridade_com_classify_trend_e_median_value(self):
        range_pct = {"d1": 0.1, "d2": 0.4}
        eff = {"d1": 0.5, "d2": 0.5}
        esperado = classify_trend(
            0.4, median_value([0.1, 0.4]), 0.5
        )
        assert classify_session("d2", range_pct, eff) == esperado

    def test_retorna_none_sem_data(self):
        assert classify_session(None, {"d1": 0.1}, {"d1": 0.1}) is None

    def test_retorna_none_sem_amplitudes(self):
        assert classify_session("d1", {}, {"d1": 0.1}) is None

    def test_retorna_none_sem_eficiencias(self):
        assert classify_session("d1", {"d1": 0.1}, {}) is None

    def test_retorna_none_sem_percentuais_validos(self):
        assert classify_session("d1", {"d1": None}, {"d1": 0.1}) is None

    def test_retorna_none_quando_ultima_data_ausente_na_amplitude(self):
        assert classify_session("d2", {"d1": 0.1}, {"d2": 0.1}) is None

    def test_retorna_none_quando_ultima_data_ausente_na_eficiencia(self):
        assert classify_session("d2", {"d2": 0.1}, {"d1": 0.1}) is None
