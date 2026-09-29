"""Testes de integração da contabilidade de tokens do chat.

Combinam a porta de completion, a estimativa de cache do caso de uso e o
contador da barra de status para verificar o total de entrada ajustado e o
percentual da janela de contexto.
"""

from types import SimpleNamespace

from flowscope.application.chat import ConsultarChatUseCase, ContextoChat
from flowscope.domain.llm import LLMResposta, LLMUsage
from flowscope.infrastructure.llm import presets as presets_module
from flowscope.infrastructure.llm.presets import resolve_context_window
from flowscope.presentation.gui.chat.tokens import ContadorTokens


class _LLMComUso:
    """Porta de teste que devolve sempre o mesmo uso."""

    def __init__(self, resposta: str, uso: LLMUsage) -> None:
        self._resposta = resposta
        self._uso = uso
        self.chamadas = 0

    def complete(
        self, messages: list[dict], system_prompt: str | None = None
    ) -> LLMResposta:
        self.chamadas += 1
        return LLMResposta(texto=self._resposta, uso=self._uso)


class TestFluxoContabilidade:
    def test_provedor_reporta_cache_desconta_e_rotula(self):
        llm = _LLMComUso(
            '{"resposta": "ok", "documentos": []}',
            LLMUsage(entrada=1000, saida=100, entrada_cache=300),
        )
        contador = ContadorTokens()
        ConsultarChatUseCase(llm).consultar(
            "p",
            ContextoChat(bloco_estavel="E"),
            ao_uso=contador.acumular,
        )
        assert contador.entrada == 700
        assert contador.texto(7000) == (
            "Tokens: 0.7K entrada / 0.1K saída / 1.0K (14%)"
        )

    def test_provedor_sem_cache_usa_estimativa(self):
        llm = _LLMComUso(
            '{"resposta": "ok", "documentos": []}',
            LLMUsage(entrada=1000, saida=100),
        )
        contador = ContadorTokens()
        usecase = ConsultarChatUseCase(
            llm, contar_tokens=lambda texto: 250, cache_suportado=True
        )
        usecase.consultar(
            "p",
            ContextoChat(bloco_estavel="E", prefixo_repetido=True),
            ao_uso=contador.acumular,
        )
        assert contador.entrada == 750


class TestPercentualJanela:
    def test_percentual_com_janela_de_preset(self, monkeypatch):
        monkeypatch.setattr(presets_module, "_janela_litellm", lambda model: 0)
        janela = resolve_context_window("openai", "gpt-4o-mini")
        assert janela == 128000
        contador = ContadorTokens()
        contador.acumular(LLMUsage(entrada=3232, saida=10))
        assert contador.texto(janela).endswith("(3%)")

    def test_percentual_com_janela_enriquecida(self, monkeypatch):
        monkeypatch.setattr(
            presets_module, "_janela_litellm", lambda model: 100000
        )
        janela = resolve_context_window("custom", "gpt-4o-mini")
        assert janela == 100000
        contador = ContadorTokens()
        contador.acumular(LLMUsage(entrada=550, saida=10))
        assert contador.texto(janela).endswith("(1%)")

    def test_percentual_sem_janela(self):
        contador = ContadorTokens()
        contador.acumular(LLMUsage(entrada=550, saida=10))
        assert contador.texto(0) == contador.texto()
        assert "(" not in contador.texto()

    def test_uso_como_objeto_do_adapter(self):
        contador = ContadorTokens()
        contador.acumular(SimpleNamespace(entrada=100, saida=1, entrada_cache=0))
        assert contador.entrada == 100
