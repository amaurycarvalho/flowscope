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


def _resposta(conteudo: str, usage: object = None) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=conteudo))],
        usage=usage,
    )


def _litellm_falso(conteudo: str = "ok", usage: object = None) -> SimpleNamespace:
    return SimpleNamespace(
        Timeout=_Timeout,
        APIConnectionError=_APIConnectionError,
        RateLimitError=_RateLimitError,
        AuthenticationError=_AuthenticationError,
        BadRequestError=_BadRequestError,
        APIError=_APIError,
        ServiceUnavailableError=_ServiceUnavailableError,
        InternalServerError=_InternalServerError,
        completion=MagicMock(return_value=_resposta(conteudo, usage)),
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
        assert resultado.texto == "ok"
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

    def test_usage_reportado(self, monkeypatch):
        usage = SimpleNamespace(prompt_tokens=12, completion_tokens=7)
        falso = _litellm_falso(usage=usage)
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        adapter = LiteLLMChatAdapter(model="m", rate_limiter=_LimiterNoop())
        resultado = adapter.complete([{"role": "user", "content": "oi"}])
        assert resultado.uso.entrada == 12
        assert resultado.uso.saida == 7

    def test_usage_ausente_vira_zero(self, monkeypatch):
        falso = _litellm_falso(usage=None)
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        adapter = LiteLLMChatAdapter(model="m", rate_limiter=_LimiterNoop())
        resultado = adapter.complete([{"role": "user", "content": "oi"}])
        assert resultado.uso.entrada == 0
        assert resultado.uso.saida == 0

    def test_usage_com_cache_reportado(self, monkeypatch):
        usage = SimpleNamespace(
            prompt_tokens=100,
            completion_tokens=20,
            prompt_tokens_details=SimpleNamespace(
                cached_tokens=40, cache_creation_tokens=5
            ),
        )
        falso = _litellm_falso(usage=usage)
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        adapter = LiteLLMChatAdapter(model="m", rate_limiter=_LimiterNoop())
        resultado = adapter.complete([{"role": "user", "content": "oi"}])
        assert resultado.uso.entrada == 100
        assert resultado.uso.entrada_cache == 40
        assert resultado.uso.cache_write == 5

    def test_usage_com_detalhes_em_dict(self, monkeypatch):
        usage = {
            "prompt_tokens": 50,
            "completion_tokens": 10,
            "prompt_tokens_details": {"cached_tokens": 30},
        }
        falso = _litellm_falso(usage=usage)
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        adapter = LiteLLMChatAdapter(model="m", rate_limiter=_LimiterNoop())
        resultado = adapter.complete([{"role": "user", "content": "oi"}])
        assert resultado.uso.entrada_cache == 30
        assert resultado.uso.cache_write == 0

    def test_usage_sem_detalhes_de_cache(self, monkeypatch):
        usage = SimpleNamespace(prompt_tokens=12, completion_tokens=7)
        falso = _litellm_falso(usage=usage)
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        adapter = LiteLLMChatAdapter(model="m", rate_limiter=_LimiterNoop())
        resultado = adapter.complete([{"role": "user", "content": "oi"}])
        assert resultado.uso.entrada_cache == 0
        assert resultado.uso.cache_write == 0


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
        adapter = LiteLLMChatAdapter(
            model="m", rate_limiter=_LimiterNoop(), retry_delays=()
        )
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


class TestRetryTransitorio:
    def _montar(self, monkeypatch, erros, *, jitter=None):
        falso = _litellm_falso()
        falso.completion.side_effect = erros
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        sonos: list[float] = []
        limiter = _LimiterNoop()
        adapter = LiteLLMChatAdapter(
            model="m",
            rate_limiter=limiter,
            sleeper=sonos.append,
            jitter=(lambda: 0.0) if jitter is None else jitter,
        )
        return falso, adapter, sonos, limiter

    def test_transitorio_com_sucesso_na_segunda_tentativa(self, monkeypatch):
        falso, adapter, sonos, limiter = self._montar(
            monkeypatch,
            [_ServiceUnavailableError("503"), _resposta("ok")],
        )

        resultado = adapter.complete([{"role": "user", "content": "oi"}])

        assert resultado.texto == "ok"
        assert falso.completion.call_count == 2
        assert limiter.chamadas == 2
        assert sonos == [1.0]

    def test_esgotamento_propaga_ultimo_erro(self, monkeypatch):
        falso, adapter, sonos, limiter = self._montar(
            monkeypatch, _ServiceUnavailableError("503")
        )

        with pytest.raises(LLMServiceUnavailableError):
            adapter.complete([{"role": "user", "content": "oi"}])

        assert falso.completion.call_count == 3
        assert limiter.chamadas == 3
        assert sonos == [1.0, 3.0]

    def test_permanente_nao_repete(self, monkeypatch):
        falso, adapter, sonos, limiter = self._montar(
            monkeypatch, _AuthenticationError("auth")
        )

        with pytest.raises(LLMProviderError):
            adapter.complete([{"role": "user", "content": "oi"}])

        assert falso.completion.call_count == 1
        assert limiter.chamadas == 1
        assert sonos == []

    def test_backoff_recebe_jitter(self, monkeypatch):
        _falso, adapter, sonos, _limiter = self._montar(
            monkeypatch,
            _ServiceUnavailableError("503"),
            jitter=lambda: 0.5,
        )

        with pytest.raises(LLMServiceUnavailableError):
            adapter.complete([{"role": "user", "content": "oi"}])

        assert sonos == [1.5, 4.5]

    def test_sem_retry_e_uma_unica_tentativa(self, monkeypatch):
        falso = _litellm_falso()
        falso.completion.side_effect = _ServiceUnavailableError("503")
        monkeypatch.setattr(adapter_module, "_import_litellm", lambda: falso)
        limiter = _LimiterNoop()
        adapter = LiteLLMChatAdapter(
            model="m", rate_limiter=limiter, retry_delays=()
        )

        with pytest.raises(LLMServiceUnavailableError):
            adapter.complete([{"role": "user", "content": "oi"}])

        assert falso.completion.call_count == 1
        assert limiter.chamadas == 1
