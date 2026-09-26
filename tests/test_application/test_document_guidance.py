"""Testes do portão e da execução da avaliação de guidance ao ler um documento."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from flowscope.application.avaliar_guidance import AvaliarGuidanceUseCase
from flowscope.application.documentos.document_guidance import GuidanceService
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.documents.texto import SEM_TEXTO
from flowscope.domain.fii import Guidance
from flowscope.infrastructure.llm.config import guidance_llm_disponivel

GUIDANCE = Guidance(
    valor_min=Decimal("0.74"),
    valor_max=Decimal("0.78"),
    periodo="restante do ano de 2026",
    data_relatorio=date(2026, 8, 1),
)


class _StoreFake:
    def __init__(self, guidance: Guidance | None = None) -> None:
        self.guidance = guidance
        self.salvos: list[tuple[str, Guidance]] = []

    def obter(self, ticker):
        return self.guidance

    def salvar(self, ticker, guidance):
        self.guidance = guidance
        self.salvos.append((ticker, guidance))


class _ExtratorFake:
    def __init__(self, resultado: Guidance | None = None) -> None:
        self.resultado = resultado
        self.chamadas = 0

    def __call__(self, texto, data_relatorio, caminho_pdf):
        self.chamadas += 1
        return self.resultado


class _LLMFake:
    def __init__(self, resposta: str = "") -> None:
        self.resposta = resposta
        self.chamadas: list[list[dict]] = []

    def complete(self, messages, system_prompt=None):
        self.chamadas.append(messages)
        return self.resposta


def _arquivo(
    categoria: str = "Relatorio",
    ano: int = 2026,
    mes: int = 8,
) -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="HGBS11",
        ano=ano,
        mes=mes,
        categoria=categoria,
        nome="10.pdf",
        tipo="pdf",
        caminho=Path("/cache/relatorio/10.pdf"),
    )


def _servico(store, extrator) -> GuidanceService:
    return GuidanceService(
        store, avaliador=AvaliarGuidanceUseCase(store, extrator)
    )


class TestPrecisa:
    def test_outra_categoria_nao_dispara(self):
        servico = _servico(_StoreFake(), _ExtratorFake())
        assert servico.precisa(_arquivo(categoria="Assembleia")) is False

    def test_cache_vazio_dispara(self):
        servico = _servico(_StoreFake(None), _ExtratorFake())
        assert servico.precisa(_arquivo()) is True

    def test_relatorio_mais_recente_dispara(self):
        servico = _servico(_StoreFake(GUIDANCE), _ExtratorFake())
        assert servico.precisa(_arquivo(ano=2026, mes=9)) is True

    def test_relatorio_nao_mais_recente_nao_dispara(self):
        servico = _servico(_StoreFake(GUIDANCE), _ExtratorFake())
        assert servico.precisa(_arquivo(ano=2026, mes=7)) is False


class TestAvaliar:
    def test_sem_texto_extraivel_e_ignorado(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        assert servico.avaliar(_arquivo(), SEM_TEXTO) is None
        assert servico.avaliar(_arquivo(), "") is None
        assert extrator.chamadas == 0

    def test_relatorio_avalia_e_grava(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        resultado = servico.avaliar(_arquivo(), "texto do relatório")
        assert resultado == GUIDANCE
        assert store.salvos == [("HGBS11", GUIDANCE)]

    def test_outra_categoria_nao_grava(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        assert servico.avaliar(_arquivo(categoria="Comunicado"), "texto") is None
        assert store.salvos == []


def _mock_flag(monkeypatch, habilitado: bool, provider: bool) -> None:
    monkeypatch.setattr(
        "flowscope.infrastructure.llm.config.load_guidance_llm_enabled",
        lambda: habilitado,
    )
    monkeypatch.setattr(
        "flowscope.infrastructure.llm.config.llm_configurada",
        lambda: provider,
    )


class TestFlagLLM:
    def test_flag_desabilitado_nao_usa_llm(self, monkeypatch):
        _mock_flag(monkeypatch, habilitado=False, provider=True)
        assert guidance_llm_disponivel() is False

    def test_flag_habilitado_com_provider(self, monkeypatch):
        _mock_flag(monkeypatch, habilitado=True, provider=True)
        assert guidance_llm_disponivel() is True

    def test_flag_habilitado_sem_provider(self, monkeypatch):
        _mock_flag(monkeypatch, habilitado=True, provider=False)
        assert guidance_llm_disponivel() is False

    def test_desabilitado_usa_apenas_deterministico(self, monkeypatch):
        _mock_flag(monkeypatch, habilitado=False, provider=True)
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        llm = _LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,99")
        servico = GuidanceService(
            store,
            extrator=extrator,
            llm_factory=lambda: llm,
            llm_available=guidance_llm_disponivel,
        )
        assert servico.avaliar(_arquivo(), "texto") == GUIDANCE
        assert llm.chamadas == []
        assert extrator.chamadas == 1

    def test_habilitado_prefere_a_llm(self, monkeypatch):
        _mock_flag(monkeypatch, habilitado=True, provider=True)
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        llm = _LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,99\nVALOR_MAX: 0,99")
        servico = GuidanceService(
            store,
            extrator=extrator,
            llm_factory=lambda: llm,
            llm_available=guidance_llm_disponivel,
        )
        resultado = servico.avaliar(_arquivo(), "texto")
        assert resultado is not None
        assert resultado.valor_min == Decimal("0.99")
        assert len(llm.chamadas) == 1
        assert extrator.chamadas == 0
