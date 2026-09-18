"""Testes da porta de completion do domínio de LLM."""

import inspect

import pytest

from flowscope.domain.llm import LLMPort

pytestmark = pytest.mark.llm


class _FakeProvider:
    """Implementação mínima da porta para o teste de protocolo."""

    def complete(
        self: "_FakeProvider",
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        return f"{len(messages)}:{system_prompt}"


class TestLLMPort:
    def test_assinatura_do_metodo_complete(self):
        parametros = inspect.signature(LLMPort.complete).parameters
        assert list(parametros) == ["self", "messages", "system_prompt"]
        assert parametros["system_prompt"].default is None

    def test_mock_implementa_a_porta(self):
        provedor: LLMPort = _FakeProvider()
        assert provedor.complete([{"role": "user", "content": "oi"}], "seja breve") == (
            "1:seja breve"
        )

    def test_mock_sem_system_prompt(self):
        provedor: LLMPort = _FakeProvider()
        assert provedor.complete([{"role": "user", "content": "hello"}]) == "1:None"
