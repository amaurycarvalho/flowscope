"""Testes do portão e da execução da avaliação de guidance de um documento."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from flowscope.application.avaliar_guidance import AvaliarGuidanceUseCase
from flowscope.application.documentos.document_guidance import GuidanceService
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import METODO_IA, AvaliacaoGuidance, Guidance
from flowscope.domain.llm import LLMResposta

GUIDANCE = Guidance(
    valor_min=Decimal("0.74"),
    valor_max=Decimal("0.78"),
    periodo="restante do ano de 2026",
    data_relatorio=date(2026, 8, 1),
)


class _StoreFake:
    def __init__(self, inicial: dict | None = None) -> None:
        self._dados = dict(inicial or {})
        self.salvos: list[tuple] = []

    def obter(self, ticker):
        return next(
            (a.guidance for a in self._dados.values() if a.guidance is not None),
            None,
        )

    def obter_avaliacao(self, ticker, chave):
        return self._dados.get((ticker, chave))

    def salvar_avaliacao(self, ticker, chave, avaliacao):
        self._dados[(ticker, chave)] = avaliacao
        self.salvos.append((ticker, chave, avaliacao))


class _ExtratorFake:
    def __init__(self, resultado: Guidance | None = None) -> None:
        self.resultado = resultado
        self.chamadas: list[str] = []

    def __call__(self, texto, data_relatorio, caminho_pdf):
        self.chamadas.append(texto)
        return self.resultado


class _LLMFake:
    def __init__(self, resposta: str = "") -> None:
        self.resposta = resposta
        self.chamadas: list[str] = []

    def complete(self, messages, system_prompt=None):
        self.chamadas.append(messages[0]["content"])
        return LLMResposta(texto=self.resposta)


def _arquivo(
    categoria: str = "Relatorio",
    ano: int = 2026,
    mes: int = 8,
    short_summary: str | None = None,
    long_summary: str | None = None,
) -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="HGBS11",
        ano=ano,
        mes=mes,
        categoria=categoria,
        nome="10.pdf",
        tipo="pdf",
        caminho=Path("/cache/relatorio/10.pdf"),
        short_summary=short_summary,
        long_summary=long_summary,
    )


def _servico(store, extrator, **kwargs) -> GuidanceService:
    return GuidanceService(
        store, avaliador=AvaliarGuidanceUseCase(store, extrator), **kwargs
    )


class TestPrecisa:
    def test_outra_categoria_nao_dispara(self):
        servico = _servico(_StoreFake(), _ExtratorFake())
        assert servico.precisa(_arquivo(categoria="Assembleia")) is False

    def test_relatorio_dispara(self):
        servico = _servico(_StoreFake(), _ExtratorFake())
        assert servico.precisa(_arquivo()) is True

    def test_relatorio_antigo_ainda_dispara(self):
        servico = _servico(_StoreFake(), _ExtratorFake())
        assert servico.precisa(_arquivo(ano=2020, mes=1)) is True


class TestAvaliar:
    def test_sem_fontes_nao_avalia(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        assert servico.avaliar(_arquivo(), None) is None
        assert servico.avaliar(_arquivo(), "   ") is None
        assert extrator.chamadas == []

    def test_cascata_usa_resumo_curto_primeiro(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        resumo = ResumoDocumento("curto", "longo")
        resultado = servico.avaliar(_arquivo(), "texto integral", resumo)
        assert resultado.guidance == GUIDANCE
        assert extrator.chamadas == ["curto"]

    def test_usa_texto_quando_sem_resumo(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        resultado = servico.avaliar(_arquivo(), "texto integral")
        assert resultado.guidance == GUIDANCE
        assert extrator.chamadas == ["texto integral"]

    def test_outra_categoria_nao_grava(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        assert servico.avaliar(_arquivo(categoria="Comunicado"), "texto") is None
        assert store.salvos == []

    def test_chave_rg_injetada(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(
            store, extrator, chave_rg=lambda arquivo: "hash-abc"
        )
        servico.avaliar(_arquivo(), "texto")
        assert store.salvos[0][1] == "hash-abc"

    def test_data_invalida_nao_avalia(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        assert servico.avaliar(_arquivo(ano=0, mes=0), "texto") is None
        assert store.salvos == []


class TestPreferenciaIA:
    def test_ia_prevalece_em_servico_completo(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        llm = _LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,99\nVALOR_MAX: 0,99")
        servico = GuidanceService(
            store,
            extrator=extrator,
            llm_factory=lambda: llm,
            llm_available=lambda: True,
        )
        resultado = servico.avaliar(_arquivo(), "texto")
        assert resultado.metodo == METODO_IA
        assert resultado.guidance.valor_min == Decimal("0.99")
        assert extrator.chamadas == []

    def test_ia_indisponivel_usa_deterministico(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        llm = _LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,99")
        servico = GuidanceService(
            store,
            extrator=extrator,
            llm_factory=lambda: llm,
            llm_available=lambda: False,
        )
        resultado = servico.avaliar(_arquivo(), "texto")
        assert resultado.guidance == GUIDANCE
        assert extrator.chamadas == ["texto"]
        assert llm.chamadas == []


class TestRecuperacaoDeEntrada:
    def test_ja_avaliado_por_ia_nao_reavalia(self):
        existente = AvaliacaoGuidance(
            metodo=METODO_IA,
            data_relatorio=date(2026, 8, 1),
            guidance=GUIDANCE,
        )
        store = _StoreFake({("HGBS11", "10.pdf"): existente})
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        assert servico.avaliar(_arquivo(), "texto") == existente
        assert store.salvos == []
        assert extrator.chamadas == []
