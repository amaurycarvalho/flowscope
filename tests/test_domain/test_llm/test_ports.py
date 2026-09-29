"""Testes da porta de completion do domínio de LLM."""

import inspect

import pytest

from flowscope.domain.llm import LLMPort, LLMResposta, LLMUsage

pytestmark = pytest.mark.llm


class _FakeProvider:
    """Implementação mínima da porta para o teste de protocolo."""

    def complete(
        self: "_FakeProvider",
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> LLMResposta:
        return LLMResposta(texto=f"{len(messages)}:{system_prompt}")


class TestLLMPort:
    def test_assinatura_do_metodo_complete(self):
        parametros = inspect.signature(LLMPort.complete).parameters
        assert list(parametros) == ["self", "messages", "system_prompt"]
        assert parametros["system_prompt"].default is None

    def test_mock_implementa_a_porta(self):
        provedor: LLMPort = _FakeProvider()
        assert provedor.complete(
            [{"role": "user", "content": "oi"}], "seja breve"
        ).texto == "1:seja breve"

    def test_mock_sem_system_prompt(self):
        provedor: LLMPort = _FakeProvider()
        assert provedor.complete([{"role": "user", "content": "hello"}]).texto == (
            "1:None"
        )


class TestUsoDeTokens:
    def test_resposta_expoe_texto_e_uso(self):
        resposta = LLMResposta(
            texto="ok", uso=LLMUsage(entrada=10, saida=5)
        )
        assert resposta.texto == "ok"
        assert resposta.uso.entrada == 10
        assert resposta.uso.saida == 5

    def test_uso_padrao_e_zero(self):
        resposta = LLMResposta(texto="ok")
        assert resposta.uso.entrada == 0
        assert resposta.uso.saida == 0
        assert resposta.uso.entrada_cache == 0
        assert resposta.uso.cache_write == 0

    def test_uso_com_cache(self):
        resposta = LLMResposta(
            texto="ok",
            uso=LLMUsage(entrada=100, saida=10, entrada_cache=40, cache_write=5),
        )
        assert resposta.uso.entrada_cache == 40
        assert resposta.uso.cache_write == 5
