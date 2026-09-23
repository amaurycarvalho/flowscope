"""Testes da avaliação do guidance de um Relatório Gerencial."""

from datetime import date
from decimal import Decimal

from flowscope.application.avaliar_guidance import AvaliarGuidanceUseCase
from flowscope.domain.fii import Guidance
from flowscope.domain.llm import (
    LLMCommunicationError,
    LLMUnavailableError,
)

CACHE = Guidance(
    valor_min=Decimal("0.85"),
    valor_max=Decimal("0.85"),
    periodo="2S26",
    data_relatorio=date(2026, 7, 1),
)

EXTRAIDO = Guidance(
    valor_min=Decimal("0.74"),
    valor_max=Decimal("0.78"),
    periodo="restante do ano de 2026",
    data_relatorio=date(2026, 8, 1),
)


class _LLMFake:
    def __init__(self, resposta: str = "", erro: Exception | None = None) -> None:
        self.resposta = resposta
        self.erro = erro
        self.chamadas: list[tuple[list[dict], str | None]] = []

    def complete(self, messages, system_prompt=None):
        self.chamadas.append((messages, system_prompt))
        if self.erro is not None:
            raise self.erro
        return self.resposta


class _StoreFake:
    def __init__(self, inicial: dict | None = None) -> None:
        self._dados = dict(inicial or {})
        self.salvos: list[tuple[str, Guidance]] = []

    def obter(self, ticker):
        return self._dados.get(ticker)

    def salvar(self, ticker, guidance):
        self._dados[ticker] = guidance
        self.salvos.append((ticker, guidance))


class _ExtratorFake:
    def __init__(self, resultado: Guidance | None = None) -> None:
        self.resultado = resultado
        self.chamadas: list[tuple[str, date, str | None]] = []

    def __call__(self, texto, data_relatorio, caminho_pdf):
        self.chamadas.append((texto, data_relatorio, caminho_pdf))
        return self.resultado


def _factory(llm=None, erro: Exception | None = None):
    def criar():
        if erro is not None:
            raise erro
        return llm

    return criar


class TestCaminhoLLM:
    def test_llm_funcional_encontra_guidance(self):
        llm = _LLMFake(
            "GUIDANCE: SIM\nVALOR_MIN: 0,74\nVALOR_MAX: 0,78\n"
            "PERIODO: restante do ano de 2026"
        )
        extrator = _ExtratorFake(EXTRAIDO)
        store = _StoreFake()
        caso = AvaliarGuidanceUseCase(store, extrator, llm_factory=_factory(llm))
        guidance = caso.avaliar("ALZR11", "texto", date(2026, 8, 1), "/x.pdf")
        assert guidance == Guidance(
            valor_min=Decimal("0.74"),
            valor_max=Decimal("0.78"),
            periodo="restante do ano de 2026",
            data_relatorio=date(2026, 8, 1),
            caminho_pdf="/x.pdf",
        )
        assert extrator.chamadas == []
        assert store.salvos == [("ALZR11", guidance)]

    def test_prompt_inclui_o_texto(self):
        llm = _LLMFake("GUIDANCE: NAO")
        _ = AvaliarGuidanceUseCase(
            _StoreFake(), _ExtratorFake(), llm_factory=_factory(llm)
        ).avaliar("ALZR11", "conteudo unico", date(2026, 8, 1))
        prompt = llm.chamadas[0][0][0]["content"]
        assert "conteudo unico" in prompt
        assert "GUIDANCE:" in prompt

    def test_llm_funcional_sem_guidance_preserva_cache(self):
        extrator = _ExtratorFake(EXTRAIDO)
        store = _StoreFake()
        caso = AvaliarGuidanceUseCase(
            store, extrator, llm_factory=_factory(_LLMFake("GUIDANCE: NAO"))
        )
        assert caso.avaliar("ALZR11", "texto", date(2026, 8, 1)) is None
        assert extrator.chamadas == []
        assert store.salvos == []

    def test_llm_so_com_minimo_usa_valor_unico(self):
        llm = _LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,85")
        guidance = AvaliarGuidanceUseCase(
            _StoreFake(), _ExtratorFake(), llm_factory=_factory(llm)
        ).avaliar("ALZR11", "texto", date(2026, 8, 1))
        assert guidance is not None
        assert guidance.valor_min == guidance.valor_max == Decimal("0.85")

    def test_llm_sim_sem_valores_nao_extrai(self):
        llm = _LLMFake("GUIDANCE: SIM\nPERIODO: 2S26")
        guidance = AvaliarGuidanceUseCase(
            _StoreFake(), _ExtratorFake(), llm_factory=_factory(llm)
        ).avaliar("ALZR11", "texto", date(2026, 8, 1))
        assert guidance is None

    def test_llm_generico_nao_e_guidance(self):
        llm = _LLMFake("resposta fora do formato")
        guidance = AvaliarGuidanceUseCase(
            _StoreFake(), _ExtratorFake(), llm_factory=_factory(llm)
        ).avaliar("ALZR11", "texto", date(2026, 8, 1))
        assert guidance is None

    def test_llm_available_falso_usa_extrator(self):
        extrator = _ExtratorFake(EXTRAIDO)
        caso = AvaliarGuidanceUseCase(
            _StoreFake(),
            extrator,
            llm_factory=_factory(_LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,85")),
            llm_available=lambda: False,
        )
        assert caso.avaliar("ALZR11", "texto", date(2026, 8, 1)) == EXTRAIDO
        assert extrator.chamadas != []


class TestFallbackDeterministico:
    def test_factory_indisponivel_usa_extrator(self):
        extrator = _ExtratorFake(EXTRAIDO)
        store = _StoreFake()
        caso = AvaliarGuidanceUseCase(
            store, extrator, llm_factory=_factory(erro=LLMUnavailableError("x"))
        )
        guidance = caso.avaliar("ALZR11", "texto", date(2026, 8, 1), "/x.pdf")
        assert guidance == EXTRAIDO
        assert store.salvos == [("ALZR11", EXTRAIDO)]

    def test_chamada_llm_falha_usa_extrator(self):
        extrator = _ExtratorFake(EXTRAIDO)
        llm = _LLMFake(erro=LLMCommunicationError("timeout"))
        caso = AvaliarGuidanceUseCase(_StoreFake(), extrator, llm_factory=_factory(llm))
        assert caso.avaliar("ALZR11", "texto", date(2026, 8, 1)) == EXTRAIDO
        assert extrator.chamadas != []

    def test_sem_factory_usa_extrator(self):
        extrator = _ExtratorFake(EXTRAIDO)
        caso = AvaliarGuidanceUseCase(_StoreFake(), extrator)
        assert caso.avaliar("ALZR11", "texto", date(2026, 8, 1)) == EXTRAIDO

    def test_resultado_obsoleto_nao_sobrescreve_cache_mais_novo(self):
        store = _StoreFake({"ALZR11": CACHE})
        caso = AvaliarGuidanceUseCase(
            store,
            _ExtratorFake(EXTRAIDO),
            llm_factory=_factory(erro=LLMUnavailableError("x")),
        )
        resultado = caso.avaliar("ALZR11", "texto", date(2026, 6, 1))
        assert resultado is not None
        assert store.salvos == []

    def test_ausencia_de_extracao_preserva_cache(self):
        store = _StoreFake({"ALZR11": CACHE})
        caso = AvaliarGuidanceUseCase(store, _ExtratorFake(None))
        assert caso.avaliar("ALZR11", "texto", date(2026, 8, 1)) is None
        assert store.salvos == []
        assert store.obter("ALZR11") == CACHE


class TestDeveAvaliar:
    def test_cache_vazio_dispara(self):
        caso = AvaliarGuidanceUseCase(_StoreFake(), _ExtratorFake())
        assert caso.deve_avaliar(2026, 8, None) is True

    def test_relatorio_mais_recente_dispara(self):
        caso = AvaliarGuidanceUseCase(_StoreFake(), _ExtratorFake())
        assert caso.deve_avaliar(2026, 8, CACHE) is True

    def test_mesmo_mes_nao_dispara(self):
        caso = AvaliarGuidanceUseCase(_StoreFake(), _ExtratorFake())
        assert caso.deve_avaliar(2026, 7, CACHE) is False

    def test_relatorio_anterior_nao_dispara(self):
        caso = AvaliarGuidanceUseCase(_StoreFake(), _ExtratorFake())
        assert caso.deve_avaliar(2026, 6, CACHE) is False


class TestPortoesDoDocumento:
    def test_outra_categoria_nao_avalia(self):
        extrator = _ExtratorFake(EXTRAIDO)
        store = _StoreFake()
        caso = AvaliarGuidanceUseCase(store, extrator)
        assert caso.avaliar_documento(
            "ALZR11", "Assembleia", 2026, 8, "texto", "/x.pdf"
        ) is None
        assert extrator.chamadas == []
        assert store.salvos == []

    def test_sem_texto_nao_avalia(self):
        extrator = _ExtratorFake(EXTRAIDO)
        caso = AvaliarGuidanceUseCase(_StoreFake(), extrator)
        assert caso.avaliar_documento(
            "ALZR11", "Relatorio", 2026, 8, "   ", "/x.pdf"
        ) is None
        assert extrator.chamadas == []

    def test_relatorio_nao_mais_recente_nao_avalia(self):
        extrator = _ExtratorFake(EXTRAIDO)
        store = _StoreFake({"ALZR11": CACHE})
        caso = AvaliarGuidanceUseCase(store, extrator)
        assert caso.avaliar_documento(
            "ALZR11", "Relatorio", 2026, 7, "texto", "/x.pdf"
        ) is None
        assert extrator.chamadas == []

    def test_gatilho_completo_avalia_e_grava(self):
        extrator = _ExtratorFake(EXTRAIDO)
        store = _StoreFake()
        caso = AvaliarGuidanceUseCase(store, extrator)
        guidance = caso.avaliar_documento(
            "ALZR11", "Relatorio", 2026, 8, "texto", "/x.pdf"
        )
        assert guidance == EXTRAIDO
        assert extrator.chamadas == [
            ("texto", date(2026, 8, 1), "/x.pdf")
        ]
        assert store.salvos == [("ALZR11", EXTRAIDO)]
