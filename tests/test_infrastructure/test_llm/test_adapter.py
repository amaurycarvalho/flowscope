"""Testes do adaptador liteLLM, do mapeamento de erros e do rate limit."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from flowscope.domain.llm import (
    LLMCommunicationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMUnavailableError,
)
from flowscope.infrastructure.llm import adapter as adapter_module
from flowscope.infrastructure.llm.adapter import LiteLLMChatAdapter
from flowscope.infrastructure.llm.rate_limiter import RateLimiter

pytestmark = pytest.mark.llm


class _Timeout(Exception):
    pass


class _APIConnectionError(Exception):
    pass


class _RateLimitError(Exception):
    pass


class _AuthenticationError(Exception):
    pass


class _BadRequestError(Exception):
    pass


class _APIError(Exception):
    pass


class _ServiceUnavailableError(Exception):
    pass


class _InternalServerError(Exception):
    pass


def _resposta(conteudo: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=conteudo))]
    )


def _litellm_falso(conteudo: str = "ok") -> SimpleNamespace:
    return SimpleNamespace(
        Timeout=_Timeout,
        APIConnectionError=_APIConnectionError,
        RateLimitError=_RateLimitError,
        AuthenticationError=_AuthenticationError,
        BadRequestError=_BadRequestError,
        APIError=_APIError,
        ServiceUnavailableError=_ServiceUnavailableError,
        InternalServerError=_InternalServerError,
        completion=MagicMock(return_value=_resposta(conteudo)),
    )


class _LimiterNoop:
    def __init__(self: "_LimiterNoop") -> None:
        self.chamadas = 0

    def acquire(self: "_LimiterNoop") -> None:
        self.chamadas += 1


class TestChamada:
    def test_argumentos_enviados(self, monkeypatch):
        falso = _litellm_falso()
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        limiter = _LimiterNoop()
        adapter = LiteLLMChatAdapter(
            model="gpt-4o-mini",
            api_key="sk-1",
            api_url="https://api.openai.com/v1",
            rate_limiter=limiter,
        )
        resultado = adapter.complete([{"role": "user", "content": "oi"}])
        assert resultado == "ok"
        falso.completion.assert_called_once_with(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "oi"}],
            api_key="sk-1",
            api_base="https://api.openai.com/v1",
            custom_llm_provider="openai",
        )
        assert limiter.chamadas == 1

    def test_sem_api_url_nao_envia_base(self, monkeypatch):
        falso = _litellm_falso()
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        adapter = LiteLLMChatAdapter(
            model="llama3.2", rate_limiter=_LimiterNoop()
        )
        adapter.complete([{"role": "user", "content": "oi"}])
        _, kwargs = falso.completion.call_args
        assert "api_base" not in kwargs
        assert "custom_llm_provider" not in kwargs

    def test_system_prompt_prefixa_mensagem(self, monkeypatch):
        falso = _litellm_falso()
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        adapter = LiteLLMChatAdapter(model="m", rate_limiter=_LimiterNoop())
        adapter.complete(
            [{"role": "user", "content": "oi"}], system_prompt="seja breve"
        )
        _, kwargs = falso.completion.call_args
        assert kwargs["messages"] == [
            {"role": "system", "content": "seja breve"},
            {"role": "user", "content": "oi"},
        ]

    def test_sem_system_prompt_nao_prefixa(self, monkeypatch):
        falso = _litellm_falso()
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        adapter = LiteLLMChatAdapter(model="m", rate_limiter=_LimiterNoop())
        adapter.complete([{"role": "user", "content": "oi"}])
        _, kwargs = falso.completion.call_args
        assert kwargs["messages"] == [{"role": "user", "content": "oi"}]


class TestMapeamentoExcecoes:
    @pytest.mark.parametrize(
        ("erro", "esperado"),
        [
            (_Timeout("t"), LLMCommunicationError),
            (_APIConnectionError("c"), LLMCommunicationError),
            (_RateLimitError("429"), LLMRateLimitError),
            (_AuthenticationError("auth"), LLMProviderError),
            (_BadRequestError("bad"), LLMProviderError),
            (_APIError("api"), LLMProviderError),
            (_ServiceUnavailableError("503"), LLMServiceUnavailableError),
            (_InternalServerError("500"), LLMServiceUnavailableError),
            (RuntimeError("desconhecido"), LLMProviderError),
        ],
    )
    def test_traducao(self, monkeypatch, erro, esperado):
        falso = _litellm_falso()
        falso.completion.side_effect = erro
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        adapter = LiteLLMChatAdapter(model="m", rate_limiter=_LimiterNoop())
        with pytest.raises(esperado):
            adapter.complete([{"role": "user", "content": "oi"}])

    def test_import_error_vira_unavailable(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "litellm", None)
        adapter = LiteLLMChatAdapter(model="m", rate_limiter=_LimiterNoop())
        with pytest.raises(LLMUnavailableError):
            adapter.complete([{"role": "user", "content": "oi"}])


class TestSilenciarDebugLiteLLM:
    def test_import_liga_suppress_debug_info(self):
        litellm = adapter_module._import_litellm()
        assert litellm.suppress_debug_info is True

    def test_mapeamento_nao_imprime_banner(self, capsys):
        adapter_module._import_litellm()
        from litellm.litellm_core_utils import exception_mapping_utils as emu

        try:
            emu.exception_type(
                model="gpt-4o-mini",
                original_exception=RuntimeError("boom"),
                custom_llm_provider="openai",
            )
        except Exception:
            pass

        capturado = capsys.readouterr()
        assert "Give Feedback" not in capturado.out
        assert "LiteLLM.Info" not in capturado.out


class TestRateLimitIntegrado:
    def test_chamadas_sao_desaceleradas(self, monkeypatch):
        class _FakeClock:
            def __init__(self):
                self.t = 0.0
                self.sonos: list[float] = []

            def now(self):
                return self.t

            def sleep(self, segundos):
                self.sonos.append(segundos)
                self.t += segundos

        relogio = _FakeClock()
        limiter = RateLimiter(1, clock=relogio.now, sleeper=relogio.sleep)
        falso = _litellm_falso()
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        adapter = LiteLLMChatAdapter(model="m", rate_limiter=limiter)
        adapter.complete([{"role": "user", "content": "1"}])
        adapter.complete([{"role": "user", "content": "2"}])
        assert relogio.t == 60.0
        assert falso.completion.call_count == 2
