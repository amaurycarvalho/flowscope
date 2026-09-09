from decimal import Decimal

from flowscope.domain.fii import (
    ClasseCotistas,
    ClassePatrimonio,
    TendenciaFfo,
    classificar_cotistas,
    classificar_patrimonio,
    classificar_tendencia_ffo,
)


class TestClassificarTendenciaFfo:
    def test_forte_alta_em_ou_acima_de_20_porcento(self):
        assert classificar_tendencia_ffo(Decimal("0.20")) is TendenciaFfo.FORTE_ALTA
        assert classificar_tendencia_ffo(Decimal("0.35")) is TendenciaFfo.FORTE_ALTA

    def test_alta_acima_de_5_porcento(self):
        assert classificar_tendencia_ffo(Decimal("0.156")) is TendenciaFfo.ALTA
        assert classificar_tendencia_ffo(Decimal("0.05")) is TendenciaFfo.ALTA

    def test_estavel_dentro_da_banda(self):
        assert classificar_tendencia_ffo(Decimal("0")) is TendenciaFfo.ESTAVEL
        assert classificar_tendencia_ffo(Decimal("0.04")) is TendenciaFfo.ESTAVEL
        assert classificar_tendencia_ffo(Decimal("-0.049")) is TendenciaFfo.ESTAVEL

    def test_queda_entre_20_e_5_porcento_negativo(self):
        assert classificar_tendencia_ffo(Decimal("-0.05")) is TendenciaFfo.QUEDA
        assert classificar_tendencia_ffo(Decimal("-0.20")) is TendenciaFfo.QUEDA

    def test_forte_queda_abaixo_de_20_porcento(self):
        assert classificar_tendencia_ffo(Decimal("-0.2001")) is TendenciaFfo.FORTE_QUEDA
        assert classificar_tendencia_ffo(Decimal("-0.35")) is TendenciaFfo.FORTE_QUEDA


class TestClassificarCotistas:
    def test_micro(self):
        assert classificar_cotistas(1) is ClasseCotistas.MICRO
        assert classificar_cotistas(250) is ClasseCotistas.MICRO

    def test_muito_pequeno(self):
        assert classificar_cotistas(251) is ClasseCotistas.MUITO_PEQUENO
        assert classificar_cotistas(1000) is ClasseCotistas.MUITO_PEQUENO

    def test_pequeno(self):
        assert classificar_cotistas(1001) is ClasseCotistas.PEQUENO
        assert classificar_cotistas(5000) is ClasseCotistas.PEQUENO

    def test_medio_entre_5001_e_35000(self):
        assert classificar_cotistas(5001) is ClasseCotistas.MEDIO
        assert classificar_cotistas(35000) is ClasseCotistas.MEDIO

    def test_grande(self):
        assert classificar_cotistas(35001) is ClasseCotistas.GRANDE
        assert classificar_cotistas(65000) is ClasseCotistas.GRANDE

    def test_muito_grande(self):
        assert classificar_cotistas(65001) is ClasseCotistas.MUITO_GRANDE
        assert classificar_cotistas(100000) is ClasseCotistas.MUITO_GRANDE

    def test_gigante(self):
        assert classificar_cotistas(100001) is ClasseCotistas.GIGANTE


class TestClassificarPatrimonio:
    def test_micro(self):
        assert classificar_patrimonio(Decimal("49000000")) is ClassePatrimonio.MICRO

    def test_pequeno(self):
        assert classificar_patrimonio(Decimal("50000000")) is ClassePatrimonio.PEQUENO
        assert classificar_patrimonio(Decimal("100000000")) is ClassePatrimonio.PEQUENO

    def test_medio(self):
        assert classificar_patrimonio(Decimal("100000001")) is ClassePatrimonio.MEDIO
        assert classificar_patrimonio(Decimal("250000000")) is ClassePatrimonio.MEDIO

    def test_grande_entre_250_e_500_milhoes(self):
        assert classificar_patrimonio(Decimal("250000001")) is ClassePatrimonio.GRANDE
        assert classificar_patrimonio(Decimal("500000000")) is ClassePatrimonio.GRANDE

    def test_muito_grande(self):
        assert classificar_patrimonio(Decimal("500000001")) is ClassePatrimonio.MUITO_GRANDE
        assert classificar_patrimonio(Decimal("1000000000")) is ClassePatrimonio.MUITO_GRANDE

    def test_gigante(self):
        assert classificar_patrimonio(Decimal("1000000001")) is ClassePatrimonio.GIGANTE
