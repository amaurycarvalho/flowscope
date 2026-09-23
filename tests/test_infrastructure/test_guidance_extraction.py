"""Testes da extração determinística do guidance de Relatórios Gerenciais."""

from datetime import date
from decimal import Decimal

from flowscope.infrastructure.fii.guidance_extraction import (
    extrair_guidance,
    extrair_guidance_de_pdf,
    normalizar_texto,
)

DATA = date(2026, 8, 1)


def _periodo(texto: str) -> str:
    guidance = extrair_guidance(texto, DATA)
    assert guidance is not None
    return guidance.periodo


class TestNormalizacao:
    def test_colapsa_espacos(self):
        assert normalizar_texto("  Guidance \n\n 2S26  ") == "Guidance 2S26"

    def test_texto_vazio_ou_none(self):
        assert normalizar_texto("") == ""
        assert normalizar_texto(None) == ""

    def test_junta_letras_espacadas(self):
        assert normalizar_texto("G u i d a n c e") == "Guidance"

    def test_preserva_palavras_normais(self):
        assert normalizar_texto("restante do ano") == "restante do ano"


class TestValor:
    def test_valor_unico_tem_minimo_igual_ao_maximo(self):
        guidance = extrair_guidance("Guidance 2S26: R$ 0,85/cota", DATA)
        assert guidance is not None
        assert guidance.valor_min == guidance.valor_max == Decimal("0.85")

    def test_faixa_entre(self):
        guidance = extrair_guidance(
            "Guidance: entre R$ 0,74 e R$ 0,78 por cota", DATA
        )
        assert guidance is not None
        assert (guidance.valor_min, guidance.valor_max) == (
            Decimal("0.74"),
            Decimal("0.78"),
        )

    def test_banda_superior_e_inferior(self):
        texto = (
            "Guidance. Banda Superior R$ 0,10. Banda Inferior R$ 0,08."
        )
        guidance = extrair_guidance(texto, DATA)
        assert guidance is not None
        assert (guidance.valor_min, guidance.valor_max) == (
            Decimal("0.08"),
            Decimal("0.10"),
        )

    def test_faixa_em_ingles(self):
        guidance = extrair_guidance(
            "Guidance for the next 3 months: R$ 0.10 to R$ 0.11/unit", DATA
        )
        assert guidance is not None
        assert (guidance.valor_min, guidance.valor_max) == (
            Decimal("0.10"),
            Decimal("0.11"),
        )

    def test_multiplos_valores_usa_minimo_e_maximo(self):
        guidance = extrair_guidance(
            "Guidance 2S26: R$ 0,80 e R$ 0,90 por cota", DATA
        )
        assert guidance is not None
        assert (guidance.valor_min, guidance.valor_max) == (
            Decimal("0.80"),
            Decimal("0.90"),
        )

    def test_valor_sem_prazo_reconhecido(self):
        assert extrair_guidance("Guidance: R$ 0,85/cota", DATA) is not None


class TestPeriodo:
    def test_semestre(self):
        assert _periodo("Guidance 2S26: R$ 0,85/cota") == "2S26"

    def test_trimestre(self):
        assert _periodo("Guidance 3T26: R$ 0,85/cota") == "3T26"

    def test_restante_do_ano(self):
        assert (
            _periodo(
                "Guidance: R$ 0,85/cota para o restante do ano de 2026"
            )
            == "restante do ano de 2026"
        )

    def test_ate_o_fim_do_ano(self):
        assert (
            _periodo("Guidance: R$ 0,85/cota até o fim do ano de 2026")
            == "até o fim do ano de 2026"
        )

    def test_proximos_meses(self):
        assert (
            _periodo("Guidance: R$ 0,85/cota nos próximos 6 meses")
            == "próximos 6 meses"
        )

    def test_intervalo_de_meses(self):
        assert (
            _periodo("Guidance jul/26 a dez/26: R$ 0,85/cota")
            == "jul/26 a dez/26"
        )

    def test_ingles_next_months(self):
        assert (
            _periodo("Guidance for the next 3 months: R$ 0,10 to R$ 0,11/unit")
            == "next 3 months"
        )

    def test_segundo_semestre(self):
        assert (
            _periodo("Guidance no segundo semestre de 2026: R$ 0,85/cota")
            == "segundo semestre de 2026"
        )


class TestFalsosPositivos:
    def test_glossario_nao_e_guidance(self):
        texto = "Guidance: Projeção em relação ao desempenho financeiro futuro"
        assert extrair_guidance(texto, DATA) is None

    def test_definicao_de_glossario(self):
        texto = "Guidance: Definição aplicável a projeções futuras"
        assert extrair_guidance(texto, DATA) is None

    def test_forward_guidance_macroeconomico(self):
        texto = "O banco central não deu forward guidance sobre os juros"
        assert extrair_guidance(texto, DATA) is None

    def test_sem_mencao_retorna_none(self):
        assert extrair_guidance("Relatório sem a palavra-chave", DATA) is None

    def test_texto_vazio_retorna_none(self):
        assert extrair_guidance("", DATA) is None


class TestPdf:
    def test_pdf_invalido_preserva_ausencia(self, tmp_path):
        caminho = tmp_path / "relatorio.pdf"
        caminho.write_bytes(b"isto nao e um pdf")
        assert extrair_guidance_de_pdf(caminho, DATA) is None

    def test_arquivo_inexistente_retorna_none(self, tmp_path):
        assert extrair_guidance_de_pdf(tmp_path / "nao.pdf", DATA) is None


class TestProveniencia:
    def test_caminho_pdf_e_preservado(self):
        guidance = extrair_guidance(
            "Guidance 2S26: R$ 0,85/cota", DATA, "/cache/10.pdf"
        )
        assert guidance is not None
        assert guidance.caminho_pdf == "/cache/10.pdf"
        assert guidance.data_relatorio == DATA
