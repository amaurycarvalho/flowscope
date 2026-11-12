"""Testes da avaliação do guidance de um Relatório Gerencial."""

import logging
from dataclasses import replace
from datetime import date
from decimal import Decimal

from flowscope.application.avaliar_guidance import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    AvaliarGuidanceUseCase,
)
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
    prompt_version=PROMPT_VERSION,
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
    def __init__(
        self,
        resposta: str = "",
        erro: Exception | None = None,
        modelo: str | None = None,
    ) -> None:
        self.resposta = resposta
        self.erro = erro
        self.modelo = modelo
        self.chamadas: list[tuple[list[dict], str | None]] = []

    def complete(self, messages, system_prompt=None):
        self.chamadas.append((messages, system_prompt))
        if self.erro is not None:
            raise self.erro
        return LLMResposta(texto=self.resposta)


def _user(llm: _LLMFake) -> str:
    return llm.chamadas[0][0][0]["content"]


def _system(llm: _LLMFake) -> str:
    return llm.chamadas[0][1]


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
    def test_instrucoes_no_system_e_trecho_no_user(self):
        llm = _LLMFake("GUIDANCE: NAO")
        caso = _caso(_StoreFake(), _ExtratorFake(), llm=llm)
        caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("conteudo unico",))
        assert _system(llm) == SYSTEM_PROMPT
        assert _user(llm) == "conteudo unico"
        assert llm.chamadas[0][0] == [
            {"role": "user", "content": "conteudo unico"}
        ]

    def test_system_prompt_define_formato_e_regras(self):
        llm = _LLMFake("GUIDANCE: NAO")
        caso = _caso(_StoreFake(), _ExtratorFake(), llm=llm)
        caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("trecho",))
        system = _system(llm)
        assert "GUIDANCE: SIM ou NAO" in system
        assert "VALOR_MIN" in system
        assert "VALOR_MAX" in system
        assert "PERIODO" in system
        assert "mesmo número" in system
        assert "ponto como separador decimal" in system
        assert "Na dúvida, responda NAO" in system

    def test_prefixo_identico_entre_fontes(self):
        llm = _LLMFake("GUIDANCE: NAO")
        caso = _caso(_StoreFake(), _ExtratorFake(), llm=llm)
        caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("fonte um", "fonte dois"))
        assert len(llm.chamadas) == 2
        assert _system(llm) == SYSTEM_PROMPT

    def test_fontes_vazias_sao_puladas(self):
        llm = _LLMFake("GUIDANCE: NAO")
        caso = _caso(_StoreFake(), _ExtratorFake(), llm=llm)
        caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, (None, "   ", "texto"))
        assert len(llm.chamadas) == 1


class TestFalhaPosteriorNaoDescarta:
    def test_preserva_avaliacao_ja_obtida(self):
        class _LLMSequencial:
            def __init__(self) -> None:
                self.chamadas = 0

            def complete(self, messages, system_prompt=None):
                self.chamadas += 1
                if self.chamadas == 1:
                    return LLMResposta(texto="GUIDANCE: NAO")
                raise LLMCommunicationError("cota esgotada")

        llm = _LLMSequencial()
        caso = _caso(_StoreFake(), _ExtratorFake(EXTRAIDO), llm=llm)
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("curto", "longo", "texto")
        )
        assert resultado.metodo == METODO_IA
        assert resultado.guidance is None
        assert llm.chamadas == 2

    def test_falha_na_primeira_fonte_recorre_ao_deterministico(self):
        class _LLMSequencial:
            def __init__(self) -> None:
                self.chamadas = 0

            def complete(self, messages, system_prompt=None):
                self.chamadas += 1
                raise LLMCommunicationError("cota esgotada")

        llm = _LLMSequencial()
        extrator = _ExtratorFake(EXTRAIDO)
        caso = _caso(_StoreFake(), extrator, llm=llm)
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("curto", "longo", "texto")
        )
        assert resultado.metodo == METODO_DETERMINISTICO
        assert resultado.guidance == EXTRAIDO
        assert llm.chamadas == 1


class TestInterpretacaoTolerante:
    def _avaliar(self, resposta: str):
        caso = _caso(_StoreFake(), _ExtratorFake(), llm=_LLMFake(resposta))
        return caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("texto",))

    def test_simbolo_de_moeda_e_tolerado(self):
        resultado = self._avaliar(
            "GUIDANCE: SIM\nVALOR_MIN: R$ 0,85\nVALOR_MAX: R$ 0,90"
        )
        assert resultado.metodo == METODO_IA
        assert resultado.guidance.valor_min == Decimal("0.85")
        assert resultado.guidance.valor_max == Decimal("0.90")

    def test_faixa_na_mesma_linha_e_tolerada(self):
        resultado = self._avaliar(
            "GUIDANCE: SIM\nVALOR_MIN: 0,85 a 0,90\nVALOR_MAX:"
        )
        assert resultado.guidance.valor_min == Decimal("0.85")
        assert resultado.guidance.valor_max == Decimal("0.90")

    def test_separador_de_milhar_e_tolerado(self):
        resultado = self._avaliar(
            "GUIDANCE: SIM\nVALOR_MIN: 1.234,56\nVALOR_MAX: 1.234,56"
        )
        assert resultado.guidance.valor_min == Decimal("1234.56")

    def test_periodo_vago_e_normalizado(self):
        resultado = self._avaliar(
            "GUIDANCE: SIM\nVALOR_MIN: 0,85\nVALOR_MAX: 0,85\n"
            "PERIODO: não especificado"
        )
        assert resultado.guidance.periodo == ""

    def test_periodo_reconhecido_e_preservado(self):
        resultado = self._avaliar(
            "GUIDANCE: SIM\nVALOR_MIN: 0,85\nVALOR_MAX: 0,85\n"
            "PERIODO: 2S26"
        )
        assert resultado.guidance.periodo == "2S26"


class TestRespostaInvalida:
    def test_sim_sem_valores_recorre_ao_deterministico(self):
        extrator = _ExtratorFake(EXTRAIDO)
        caso = _caso(
            _StoreFake(),
            extrator,
            llm=_LLMFake("GUIDANCE: SIM\nVALOR_MIN:\nVALOR_MAX:"),
        )
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("texto",)
        )
        assert resultado.metodo == METODO_DETERMINISTICO
        assert resultado.guidance == EXTRAIDO
        assert extrator.chamadas == ["texto"]

    def test_sim_sem_valores_sem_deterministico_nao_registra_ia(self):
        caso = _caso(
            _StoreFake(),
            _ExtratorFake(None),
            llm=_LLMFake("GUIDANCE: SIM\nVALOR_MIN:\nVALOR_MAX:"),
        )
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("texto",)
        )
        assert resultado.metodo == METODO_DETERMINISTICO
        assert resultado.guidance is None


class TestReavaliacaoPorVersao:
    def test_avaliacao_ia_grava_proveniencia(self):
        store = _StoreFake()
        llm = _LLMFake(
            "GUIDANCE: SIM\nVALOR_MIN: 0,99\nVALOR_MAX: 0,99",
            modelo="modelo-x",
        )
        caso = _caso(store, _ExtratorFake(), llm=llm)
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("texto",)
        )
        assert resultado.prompt_version == PROMPT_VERSION
        assert resultado.modelo == "modelo-x"
        assert resultado.avaliado_em is not None

    def test_ia_versao_anterior_e_reavaliada(self):
        antiga = replace(EXISTENTE_IA, prompt_version="0")
        store = _StoreFake({("ALZR11", "k1"): antiga})
        llm = _LLMFake(
            "GUIDANCE: SIM\nVALOR_MIN: 0,99\nVALOR_MAX: 0,99"
        )
        caso = _caso(store, _ExtratorFake(), llm=llm)
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("texto",)
        )
        assert resultado.metodo == METODO_IA
        assert resultado.prompt_version == PROMPT_VERSION
        assert resultado.guidance.valor_min == Decimal("0.99")
        assert store.salvos[-1][1] == "k1"

    def test_ia_sem_versao_e_reavaliada(self):
        antiga = replace(EXISTENTE_IA, prompt_version=None)
        store = _StoreFake({("ALZR11", "k1"): antiga})
        llm = _LLMFake("GUIDANCE: NAO")
        caso = _caso(store, _ExtratorFake(), llm=llm)
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("texto",)
        )
        assert resultado.prompt_version == PROMPT_VERSION
        assert resultado.guidance is None
        assert store.salvos

    def test_modelo_diferente_reavalia(self):
        antiga = replace(EXISTENTE_IA, modelo="modelo-antigo")
        store = _StoreFake({("ALZR11", "k1"): antiga})
        llm = _LLMFake(
            "GUIDANCE: SIM\nVALOR_MIN: 0,99\nVALOR_MAX: 0,99",
            modelo="modelo-novo",
        )
        caso = _caso(store, _ExtratorFake(), llm=llm)
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("texto",)
        )
        assert resultado.modelo == "modelo-novo"
        assert resultado.guidance.valor_min == Decimal("0.99")

    def test_falha_na_reavaliacao_preserva_entrada(self):
        antiga = replace(EXISTENTE_IA, prompt_version="0")
        store = _StoreFake({("ALZR11", "k1"): antiga})
        caso = _caso(
            store,
            _ExtratorFake(),
            llm=_LLMFake(erro=LLMCommunicationError("x")),
        )
        resultado = caso.avaliar_rg(
            "ALZR11", "k1", DATA, CAMINHO, ("texto",)
        )
        assert resultado == antiga
        assert store.salvos == []


class TestConflitoDeterministico:
    def test_conflito_registrado_sem_sobrescrever(self, caplog):
        store = _StoreFake()
        caso = _caso(store, _ExtratorFake(EXTRAIDO), llm=_LLMFake("GUIDANCE: NAO"))
        with caplog.at_level(logging.WARNING):
            resultado = caso.avaliar_rg(
                "ALZR11", "k1", DATA, CAMINHO, ("texto",)
            )
        assert resultado.metodo == METODO_IA
        assert resultado.guidance is None
        assert any(
            "Conflito de guidance" in registro.message
            for registro in caplog.records
        )
        assert store.salvos[-1][2].guidance is None

    def test_sem_conflito_nao_registra_warning(self, caplog):
        caso = _caso(
            _StoreFake(), _ExtratorFake(None), llm=_LLMFake("GUIDANCE: NAO")
        )
        with caplog.at_level(logging.WARNING):
            caso.avaliar_rg("ALZR11", "k1", DATA, CAMINHO, ("texto",))
        assert not any(
            "Conflito de guidance" in registro.message
            for registro in caplog.records
        )
