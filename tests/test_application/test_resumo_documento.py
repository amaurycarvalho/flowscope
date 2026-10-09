"""Testes do serviço de resumo de documentos."""

import pytest

from flowscope.application.resumo_documento import (
    LIMITE_CURTO,
    LIMITE_LONGO,
    ORCAMENTO_ENTRADA,
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


def _prompt(llm: _LLMFake) -> str:
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
    def test_contem_formula_xyz_e_limites(self):
        llm = _LLMFake("CURTO: c\nLONGO: l")
        ResumirDocumentoUseCase(llm).resumir("documento")
        prompt = _prompt(llm)
        assert "XYZ" in prompt
        assert "280" in prompt
        assert "1500" in prompt

    def test_pede_frases_e_paragrafos(self):
        llm = _LLMFake("CURTO: c\nLONGO: l")
        ResumirDocumentoUseCase(llm).resumir("documento")
        prompt = _prompt(llm)
        assert "1 a 2 frases" in prompt
        assert "parágrafos" in prompt


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
        llm = _LLMFake("CURTO: " + "x" * 250 + ". " + "y" * 100)
        resumo = ResumirDocumentoUseCase(llm).resumir("documento")
        assert resumo.short_summary.endswith(".")
        assert "y" not in resumo.short_summary

    def test_trunca_no_ultimo_espaco(self):
        texto = "palavra " * 60
        esperado = texto[:LIMITE_CURTO].rstrip()
        assert _truncar_em_fronteira(texto, LIMITE_CURTO) == esperado
        assert not _truncar_em_fronteira(texto, LIMITE_CURTO).endswith("palavr")

    def test_sem_fronteira_corta_duro(self):
        assert _truncar_em_fronteira("z" * 400, LIMITE_CURTO) == "z" * LIMITE_CURTO
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
            "CURTO: " + "a" * 400 + "\nLONGO: " + "b" * 2000
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
        prompt = _prompt(llm)
        assert "a" * 100 in prompt
        assert excedente not in prompt


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
