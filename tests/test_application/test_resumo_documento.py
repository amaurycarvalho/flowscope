"""Testes do serviço de resumo de documentos."""

import pytest

from flowscope.application.resumo_documento import (
    LIMITE_CURTO,
    LIMITE_LONGO,
    ORCAMENTO_CURTO,
    ORCAMENTO_ENTRADA,
    ORCAMENTO_LONGO,
    SYSTEM_PROMPT,
    ResumirDocumentoUseCase,
    ResumoDocumento,
    _truncar_em_fronteira,
    resumo_integro,
)
from flowscope.domain.llm import LLMCommunicationError, LLMResposta, LLMUnavailableError


class _LLMFake:
    """Porta de LLM mínima que registra as chamadas recebidas."""

    def __init__(self, resposta: str = "") -> None:
        self.resposta = resposta
        self.chamadas: list[tuple[list[dict], str | None]] = []

    def complete(
        self, messages: list[dict], system_prompt: str | None = None
    ) -> LLMResposta:
        self.chamadas.append((messages, system_prompt))
        return LLMResposta(texto=self.resposta)


def _system(llm: _LLMFake) -> str:
    return llm.chamadas[0][1]


def _user(llm: _LLMFake) -> str:
    return llm.chamadas[0][0][0]["content"]


class TestResumir:
    def test_uma_chamada_e_dois_resumos(self):
        llm = _LLMFake("CURTO: resumo curto\nLONGO: resumo longo")
        resumo = ResumirDocumentoUseCase(llm).resumir("texto do documento")
        assert resumo == ResumoDocumento("resumo curto", "resumo longo")
        assert len(llm.chamadas) == 1

    def test_texto_vazio_nao_chama_a_llm(self):
        llm = _LLMFake("CURTO: x\nLONGO: y")
        servico = ResumirDocumentoUseCase(llm)
        assert servico.resumir("") == ResumoDocumento("", "")
        assert servico.resumir("   ") == ResumoDocumento("", "")
        assert llm.chamadas == []

    def test_formato_inesperado_usa_resposta_inteira(self):
        resposta = "x" * 400
        llm = _LLMFake(resposta)
        resumo = ResumirDocumentoUseCase(llm).resumir("documento")
        assert resumo.long_summary == resposta
        assert resumo.short_summary == resposta[:LIMITE_CURTO]


class TestPrompt:
    def test_system_prompt_contem_formula_xyz_e_limites(self):
        llm = _LLMFake("CURTO: c\nLONGO: l")
        ResumirDocumentoUseCase(llm).resumir("documento")
        system = _system(llm)
        assert system == SYSTEM_PROMPT
        assert "XYZ" in system
        assert str(ORCAMENTO_CURTO) in system
        assert str(ORCAMENTO_LONGO) in system

    def test_orcamento_cabe_no_teto(self):
        assert ORCAMENTO_CURTO < LIMITE_CURTO
        assert ORCAMENTO_LONGO < LIMITE_LONGO

    def test_system_prompt_orca_o_xyz(self):
        llm = _LLMFake("CURTO: c\nLONGO: l")
        ResumirDocumentoUseCase(llm).resumir("documento")
        system = _system(llm)
        assert "Planeje X, Y e Z" in system
        assert "nunca omita a conclusão (Z)" in system

    def test_system_prompt_pede_frases_e_paragrafos(self):
        llm = _LLMFake("CURTO: c\nLONGO: l")
        ResumirDocumentoUseCase(llm).resumir("documento")
        system = _system(llm)
        assert "1 a 2 frases" in system
        assert "parágrafos" in system

    def test_system_prompt_restringe_formato(self):
        llm = _LLMFake("CURTO: c\nLONGO: l")
        ResumirDocumentoUseCase(llm).resumir("documento")
        system = _system(llm)
        assert "markdown" in system
        assert "listas" in system
        assert "CURTO:" in system
        assert "documento fornecido" in system

    def test_user_contem_apenas_o_documento(self):
        llm = _LLMFake("CURTO: c\nLONGO: l")
        ResumirDocumentoUseCase(llm).resumir("texto do documento")
        assert llm.chamadas[0][0] == [
            {"role": "user", "content": "texto do documento"}
        ]
        assert len(llm.chamadas[0][0]) == 1


class TestFronteira:
    def test_resumo_curto_nao_corta_palavra(self):
        llm = _LLMFake("CURTO: " + "palavra " * 60 + "\nLONGO: longo.")
        resumo = ResumirDocumentoUseCase(llm).resumir("documento")
        assert len(resumo.short_summary) <= LIMITE_CURTO
        assert resumo.short_summary.endswith("palavra")

    def test_resumo_longo_nao_corta_palavra(self):
        llm = _LLMFake("CURTO: c.\nLONGO: " + "palavra " * 400)
        resumo = ResumirDocumentoUseCase(llm).resumir("documento")
        assert len(resumo.long_summary) <= LIMITE_LONGO
        assert resumo.long_summary.endswith("palavra")

    def test_prefere_fim_de_frase(self):
        llm = _LLMFake(
            "CURTO: " + "x" * (LIMITE_CURTO - 20) + ". " + "y" * 100
        )
        resumo = ResumirDocumentoUseCase(llm).resumir("documento")
        assert resumo.short_summary.endswith(".")
        assert "y" not in resumo.short_summary

    def test_trunca_no_ultimo_espaco(self):
        texto = "palavra " * 100
        cortado = _truncar_em_fronteira(texto, LIMITE_CURTO)
        assert len(cortado) <= LIMITE_CURTO
        assert cortado.endswith("palavra")

    def test_sem_fronteira_corta_duro(self):
        assert _truncar_em_fronteira("z" * (LIMITE_CURTO + 100), LIMITE_CURTO) == (
            "z" * LIMITE_CURTO
        )
        assert _truncar_em_fronteira("z" * LIMITE_CURTO, LIMITE_CURTO) == (
            "z" * LIMITE_CURTO
        )

    def test_resumo_integro_por_pontuacao_final(self):
        assert resumo_integro("conclusão.") is True
        assert resumo_integro("sério!") is True
        assert resumo_integro("e então?") is True
        assert resumo_integro("lista;") is True
        assert resumo_integro("assim:") is True
        assert resumo_integro("continua…") is True
        assert resumo_integro("cortado no meio da pa") is False
        assert resumo_integro("") is False
        assert resumo_integro(None) is False




class TestLimites:
    def test_trunca_resumo_curto_e_longo(self):
        resposta = (
            "CURTO: " + "a" * (LIMITE_CURTO + 100) + "\nLONGO: "
            + "b" * (LIMITE_LONGO + 100)
        )
        llm = _LLMFake(resposta)
        resumo = ResumirDocumentoUseCase(llm).resumir("documento")
        assert len(resumo.short_summary) == LIMITE_CURTO
        assert len(resumo.long_summary) == LIMITE_LONGO

    def test_limita_entrada_ao_orcamento(self):
        excedente = "EXCEDENTE"
        texto = "a" * ORCAMENTO_ENTRADA + excedente
        llm = _LLMFake("CURTO: c\nLONGO: l")
        ResumirDocumentoUseCase(llm).resumir(texto)
        user = _user(llm)
        assert "a" * 100 in user
        assert excedente not in user


class TestExcecoes:
    def test_llm_indisponivel_propaga(self):
        class _Falha(_LLMFake):
            def complete(self, messages, system_prompt=None):
                raise LLMUnavailableError("sem provedor")

        with pytest.raises(LLMUnavailableError):
            ResumirDocumentoUseCase(_Falha()).resumir("documento")

    def test_falha_de_comunicacao_propaga(self):
        class _Falha(_LLMFake):
            def complete(self, messages, system_prompt=None):
                raise LLMCommunicationError("timeout")

        with pytest.raises(LLMCommunicationError):
            ResumirDocumentoUseCase(_Falha()).resumir("documento")
