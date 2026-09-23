"""Testes da tradução de erros de LLM para mensagens exibíveis na interface."""

from flowscope.domain.llm import (
    LLMCommunicationError,
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMUnavailableError,
)
from flowscope.presentation.gui.llm.mensagens import mensagem_erro_llm


class TestMensagensPorTipo:
    def test_servico_indisponivel(self):
        mensagem = mensagem_erro_llm(
            LLMServiceUnavailableError("Error code: 503 - high demand")
        )
        assert "temporariamente indisponível" in mensagem
        assert "Tente novamente em instantes" in mensagem
        assert "503" not in mensagem

    def test_limite_de_uso(self):
        mensagem = mensagem_erro_llm(LLMRateLimitError("Error code: 429"))
        assert "Limite de uso da I.A." in mensagem

    def test_falha_de_comunicacao(self):
        mensagem = mensagem_erro_llm(LLMCommunicationError("timeout"))
        assert "conectar ao serviço de I.A." in mensagem

    def test_configuracao_invalida(self):
        mensagem = mensagem_erro_llm(
            LLMConfigurationError("Provedor custom incompleto")
        )
        assert "Configuração de I.A. inválida" in mensagem

    def test_provedor_generico(self):
        mensagem = mensagem_erro_llm(LLMProviderError("401 unauthorized"))
        assert "provedor de I.A. retornou um erro" in mensagem
        assert "Consulte o log" in mensagem


class TestFallbacks:
    def test_llm_indisponivel_preserva_str(self):
        erro = LLMUnavailableError("Dependências de LLM ausentes.")
        assert mensagem_erro_llm(erro) == str(erro)

    def test_excecao_nao_llm_preserva_str(self):
        erro = RuntimeError("conversão falhou")
        assert mensagem_erro_llm(erro) == "conversão falhou"
