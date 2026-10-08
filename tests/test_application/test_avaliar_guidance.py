"""Testes da avaliação do guidance de um Relatório Gerencial."""

from datetime import date
from decimal import Decimal

from flowscope.application.avaliar_guidance import AvaliarGuidanceUseCase
from flowscope.domain.fii import (
    METODO_DETERMINISTICO,
    METODO_IA,
    AvaliacaoGuidance,
    Guidance,
)
from flowscope.domain.llm import (
    LLMCommunicationError,
    LLMResposta,
    LLMUnavailableError,
)

DATA = date(2026, 8, 1)
CAMINHO = "/x.pdf"

EXISTENTE_IA = AvaliacaoGuidance(
    metodo=METODO_IA,
    data_relatorio=DATA,
    caminho_pdf=CAMINHO,
    guidance=Guidance(
        valor_min=Decimal("0.85"),
        valor_max=Decimal("0.85"),
        periodo="2S26",
        data_relatorio=DATA,
        caminho_pdf=CAMINHO,
    ),
)

EXISTENTE_DET = AvaliacaoGuidance(
    metodo=METODO_DETERMINISTICO,
    data_relatorio=DATA,
    caminho_pdf=CAMINHO,
    guidance=Guidance(
        valor_min=Decimal("0.70"),
        valor_max=Decimal("0.70"),
        periodo="2S26",
        data_relatorio=DATA,
        caminho_pdf=CAMINHO,
    ),
)

EXTRAIDO = Guidance(
    valor_min=Decimal("0.74"),
    valor_max=Decimal("0.78"),
    periodo="restante do ano de 2026",
    data_relatorio=DATA,
    caminho_pdf=CAMINHO,
)


class _LLMFake:
    def __init__(self, resposta: str = "", erro: Exception | None = None) -> None:
        self.resposta = resposta
        self.erro = erro
        self.chamadas: list[str] = []

    def complete(self, messages, system_prompt=None):
        self.chamadas.append(messages[0]["content"])
        if self.erro is not None:
            raise self.erro
        return LLMResposta(texto=self.resposta)


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


def _factory(llm=None, erro: Exception | None = None):
    def criar():
        if erro is not None:
            raise erro
        return llm

    return criar


def _caso(store, extrator, llm=None, erro=None, disponivel=None):
    disponibilidade = (lambda: disponivel) if disponivel is not None else None
    if disponivel is None and erro is None and llm is None:
        return AvaliarGuidanceUseCase(store, extrator)
    return AvaliarGuidanceUseCase(
        store,
        extrator,
        llm_factory=_factory(llm, erro),
        llm_available=disponibilidade,
    )


class TestCascataIA:
    def test_resumo_curto_interrompe_a_cascata(self):
        llm = _LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,74\nVALOR_MAX: 0,78")
        extrator = _ExtratorFake(EXTRAIDO)
        store = _StoreFake()
        caso = _caso(store, extrator, llm=llm)
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("curto", "longo", "texto")
        )
        assert resultado.metodo == METODO_IA
        assert resultado.guidance.valor_min == Decimal("0.74")
        assert len(llm.chamadas) == 1
        assert store.salvos[0][0] == "ALZR11"

    def test_resumo_longo_usado_quando_curto_nao_tem(self):
        llm = _LLMFake("GUIDANCE: NAO")
        extrator = _ExtratorFake(EXTRAIDO)
        caso = _caso(_StoreFake(), extrator, llm=llm)
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("curto", "longo", "texto")
        )
        assert resultado.metodo == METODO_IA
        assert resultado.guidance is None
        assert len(llm.chamadas) == 3


class TestFalhaIA:
    def test_falha_recorre_ao_deterministico(self):
        extrator = _ExtratorFake(EXTRAIDO)
        store = _StoreFake()
        caso = _caso(
            store,
            extrator,
            llm=_LLMFake(erro=LLMCommunicationError("timeout")),
        )
        resultado = caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("texto",))
        assert resultado.metodo == METODO_DETERMINISTICO
        assert resultado.guidance == EXTRAIDO
        assert store.salvos[-1][1] == "k1"

    def test_factory_indisponivel_usa_deterministico(self):
        extrator = _ExtratorFake(EXTRAIDO)
        caso = _caso(_StoreFake(), extrator, erro=LLMUnavailableError("x"))
        resultado = caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("texto",))
        assert resultado.metodo == METODO_DETERMINISTICO

    def test_ia_indisponivel_por_flag_usa_deterministico(self):
        extrator = _ExtratorFake(EXTRAIDO)
        store = _StoreFake()
        caso = _caso(
            store,
            extrator,
            llm=_LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,99"),
            disponivel=False,
        )
        resultado = caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("texto",))
        assert resultado.metodo == METODO_DETERMINISTICO
        assert extrator.chamadas == ["texto"]


class TestControlePorMetodo:
    def test_ja_avaliado_por_ia_nao_refaz(self):
        store = _StoreFake({("ALZR11", "k1"): EXISTENTE_IA})
        extrator = _ExtratorFake(EXTRAIDO)
        caso = _caso(store, extrator, llm=_LLMFake("GUIDANCE: NAO"))
        resultado = caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("texto",))
        assert resultado == EXISTENTE_IA
        assert store.salvos == []
        assert extrator.chamadas == []

    def test_deterministico_com_ia_disponivel_e_substituido(self):
        store = _StoreFake({("ALZR11", "k1"): EXISTENTE_DET})
        extrator = _ExtratorFake(EXTRAIDO)
        llm = _LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,99\nVALOR_MAX: 0,99")
        caso = _caso(store, extrator, llm=llm)
        resultado = caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("texto",))
        assert resultado.metodo == METODO_IA
        assert resultado.guidance.valor_min == Decimal("0.99")
        assert extrator.chamadas == []

    def test_deterministico_sem_ia_nao_refaz(self):
        store = _StoreFake({("ALZR11", "k1"): EXISTENTE_DET})
        extrator = _ExtratorFake(EXTRAIDO)
        caso = _caso(store, extrator, disponivel=False)
        resultado = caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("texto",))
        assert resultado == EXISTENTE_DET
        assert store.salvos == []
        assert extrator.chamadas == []

    def test_deterministico_com_falha_da_ia_preserva_entrada(self):
        store = _StoreFake({("ALZR11", "k1"): EXISTENTE_DET})
        extrator = _ExtratorFake(EXTRAIDO)
        caso = _caso(
            store, extrator, llm=_LLMFake(erro=LLMCommunicationError("x"))
        )
        resultado = caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("texto",))
        assert resultado == EXISTENTE_DET
        assert store.salvos == []
        assert extrator.chamadas == []

    def test_ausencia_ia_registrada_sem_apagar_outros(self):
        store = _StoreFake({("ALZR11", "k1"): EXISTENTE_IA})
        llm = _LLMFake("GUIDANCE: NAO")
        caso = _caso(store, _ExtratorFake(), llm=llm)
        resultado = caso.avaliar_rg("ALZR11", "k2", DATA, CAMINHO, ("texto",))
        assert resultado.metodo == METODO_IA
        assert resultado.guidance is None
        assert store.obter("ALZR11") == EXISTENTE_IA.guidance


class TestPrompt:
    def test_prompt_inclui_a_fonte(self):
        llm = _LLMFake("GUIDANCE: NAO")
        caso = _caso(_StoreFake(), _ExtratorFake(), llm=llm)
        caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("conteudo unico",))
        assert "conteudo unico" in llm.chamadas[0]
        assert "GUIDANCE:" in llm.chamadas[0]

    def test_fontes_vazias_sao_puladas(self):
        llm = _LLMFake("GUIDANCE: NAO")
        caso = _caso(_StoreFake(), _ExtratorFake(), llm=llm)
        caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, (None, "   ", "texto"))
        assert len(llm.chamadas) == 1
