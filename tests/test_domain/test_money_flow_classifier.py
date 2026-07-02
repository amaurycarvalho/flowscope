from flowscope.domain.strategies.classifiers import (
    MoneyFlowClassification,
    classify_money_flow,
)


class TestClassifyMoneyFlow:
    def test_muito_forte_vendedor(self):
        cls = classify_money_flow(-0.20)
        assert cls.label == "Fluxo Muito Forte (Vendedor)"
        assert cls.short_label == "Muito Forte"
        assert cls.score == -4

    def test_muito_forte_vendedor_boundary_neg_inf(self):
        cls = classify_money_flow(-999.0)
        assert cls.label == "Fluxo Muito Forte (Vendedor)"
        assert cls.score == -4

    def test_forte_vendedor(self):
        cls = classify_money_flow(-0.12)
        assert cls.label == "Fluxo Forte (Vendedor)"
        assert cls.score == -3

    def test_forte_vendedor_boundary_neg_0_15(self):
        cls = classify_money_flow(-0.15)
        assert cls.label == "Fluxo Forte (Vendedor)"
        assert cls.score == -3

    def test_forte_vendedor_upper_boundary(self):
        cls = classify_money_flow(-0.08)
        assert cls.label == "Fluxo Moderado (Vendedor)"
        assert cls.score == -2

    def test_moderado_vendedor(self):
        cls = classify_money_flow(-0.05)
        assert cls.label == "Fluxo Moderado (Vendedor)"
        assert cls.score == -2

    def test_moderado_vendedor_upper_boundary(self):
        cls = classify_money_flow(-0.03)
        assert cls.label == "Fluxo Fraco (Vendedor)"
        assert cls.score == -1

    def test_fraco_vendedor(self):
        cls = classify_money_flow(-0.02)
        assert cls.label == "Fluxo Fraco (Vendedor)"
        assert cls.score == -1

    def test_fraco_vendedor_upper_boundary(self):
        cls = classify_money_flow(-0.01)
        assert cls.label == "Neutro"
        assert cls.score == 0

    def test_neutro_zero(self):
        cls = classify_money_flow(0.0)
        assert cls.label == "Neutro"
        assert cls.score == 0

    def test_neutro_positivo(self):
        cls = classify_money_flow(0.005)
        assert cls.label == "Neutro"
        assert cls.score == 0

    def test_neutro_upper_boundary(self):
        cls = classify_money_flow(0.01)
        assert cls.label == "Fluxo Fraco (Comprador)"
        assert cls.score == 1

    def test_fraco_comprador(self):
        cls = classify_money_flow(0.02)
        assert cls.label == "Fluxo Fraco (Comprador)"
        assert cls.score == 1

    def test_fraco_comprador_upper_boundary(self):
        cls = classify_money_flow(0.03)
        assert cls.label == "Fluxo Moderado (Comprador)"
        assert cls.score == 2

    def test_moderado_comprador(self):
        cls = classify_money_flow(0.05)
        assert cls.label == "Fluxo Moderado (Comprador)"
        assert cls.score == 2

    def test_moderado_comprador_upper_boundary(self):
        cls = classify_money_flow(0.08)
        assert cls.label == "Fluxo Forte (Comprador)"
        assert cls.score == 3

    def test_forte_comprador(self):
        cls = classify_money_flow(0.12)
        assert cls.label == "Fluxo Forte (Comprador)"
        assert cls.score == 3

    def test_forte_comprador_upper_boundary(self):
        cls = classify_money_flow(0.15)
        assert cls.label == "Fluxo Muito Forte (Comprador)"
        assert cls.score == 4

    def test_muito_forte_comprador(self):
        cls = classify_money_flow(0.30)
        assert cls.label == "Fluxo Muito Forte (Comprador)"
        assert cls.score == 4

    def test_muito_forte_comprador_boundary_pos_inf(self):
        cls = classify_money_flow(999.0)
        assert cls.label == "Fluxo Muito Forte (Comprador)"
        assert cls.score == 4

    def test_returns_dataclass(self):
        cls = classify_money_flow(0.12)
        assert isinstance(cls, MoneyFlowClassification)
        assert cls.color == "#388E3C"
        assert cls.short_label == "Forte"
