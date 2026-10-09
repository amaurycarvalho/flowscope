"""Presets de provedores de LLM e resolução de modelo, API URL e janela.

Cada preset adota endpoints OpenAI-compatible, de modo que o adaptador envia
sempre ``custom_llm_provider="openai"``. O preset ``custom`` deixa modelo e API
URL em branco para preenchimento manual pelo usuário. Além do modelo e da API
URL, cada preset declara a janela de contexto padrão (``context_window``) e se o
provedor suporta cache de prompt (``cache_prompt``).
"""

from collections.abc import Callable

from flowscope.domain.llm import LLMConfigurationError

#: Provedores suportados com seus defaults de modelo, API URL, janela e cache.
PROVIDER_PRESETS: dict[str, dict[str, object]] = {
    "none": {
        "model": "",
        "api_url": "",
        "context_window": 0,
        "cache_prompt": False,
    },
    "openai": {
        "model": "gpt-4o-mini",
        "api_url": "https://api.openai.com/v1",
        "context_window": 1048576,
        "cache_prompt": True,
    },
    "gemini": {
        "model": "gemini-3.1-flash-lite",
        "api_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "context_window": 1048576,
        "cache_prompt": True,
    },
    "copilot": {
        "model": "gpt-4o",
        "api_url": "https://models.inference.ai.azure.com",
        "context_window": 1048576,
        "cache_prompt": True,
    },
    "claude": {
        "model": "claude-sonnet-4-20250514",
        "api_url": "https://api.anthropic.com/v1",
        "context_window": 1048576,
        "cache_prompt": True,
    },
    "deepseek": {
        "model": "deepseek-chat",
        "api_url": "https://api.deepseek.com/v1",
        "context_window": 1048576,
        "cache_prompt": True,
    },
    "ollama": {
        "model": "llama3.2",
        "api_url": "http://localhost:11434/v1",
        "context_window": 131072,
        "cache_prompt": False,
    },
    "custom": {
        "model": "",
        "api_url": "",
        "context_window": 131072,
        "cache_prompt": False,
    },
}

#: Contadores de tokens memoizados por modelo, compartilhados entre turnos.
_CONTADORES: dict[str, Callable[[str], int]] = {}


def _inteiro(valor: object) -> int:
    """Retorna o valor numérico convertido em inteiro não negativo."""
    try:
        return max(0, int(valor))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def resolve_provider(
    provider: str,
    model: str | None = None,
    api_url: str | None = None,
) -> tuple[str, str]:
    """Resolve o modelo e a API URL de um provedor, aplicando defaults do preset.

    Lança ``LLMConfigurationError`` para provedor desconhecido ou para o
    provedor ``custom`` sem modelo/API URL informados.
    """
    if provider not in PROVIDER_PRESETS:
        raise LLMConfigurationError(f"Provedor de LLM desconhecido: {provider}")
    preset = PROVIDER_PRESETS[provider]
    resolved_model = model or str(preset["model"])
    resolved_url = api_url or str(preset["api_url"])
    if not resolved_model or not resolved_url:
        raise LLMConfigurationError(
            f"Provedor {provider} requer model e api_url configurados"
        )
    return resolved_model, resolved_url


def _import_litellm() -> object | None:
    """Importa o liteLLM desabilitando o banner de provedores, ou ``None``.

    O liteLLM imprime um banner na saída padrão quando não infere o provedor a
    partir do nome do modelo (ex.: ``deepseek-chat`` sem o prefixo do provedor).
    O flag ``suppress_debug_info`` silencia esse banner nas consultas de janela e
    contagem, que não fazem chamadas de rede.
    """
    try:
        import litellm
    except ImportError:
        return None
    litellm.suppress_debug_info = True
    return litellm


def _janela_litellm(model: str) -> int:
    """Consulta a janela de entrada do liteLLM, devolvendo zero se indisponível."""
    litellm = _import_litellm()
    if litellm is None:
        return 0
    try:
        info = litellm.get_model_info(model)
    except Exception:
        return 0
    if isinstance(info, dict):
        return _inteiro(info.get("max_input_tokens"))
    return 0


def resolve_context_window(provider: str, model: str | None = None) -> int:
    """Resolve a janela de contexto do modelo, preferindo a informação do liteLLM.

    Sem a informação do liteLLM (dependência opcional ausente ou modelo fora do
    registro), cai no ``context_window`` do preset. Devolve zero quando a janela
    não é conhecida.
    """
    if model:
        janela = _janela_litellm(model)
        if janela > 0:
            return janela
    preset = PROVIDER_PRESETS.get(provider, {})
    return _inteiro(preset.get("context_window"))


def cache_suportado(provider: str) -> bool:
    """Indica se o provedor declara suporte a cache de prompt no preset."""
    preset = PROVIDER_PRESETS.get(provider, {})
    return bool(preset.get("cache_prompt", False))


def _contar_litellm(model: str, texto: str) -> int:
    """Conta tokens pelo liteLLM, caindo em heurística de caracteres."""
    if not texto:
        return 0
    litellm = _import_litellm()
    if litellm is None:
        return max(1, len(texto) // 4)
    try:
        return max(0, int(litellm.token_counter(model=model, text=texto)))
    except Exception:
        return max(1, len(texto) // 4)


def _montar_contador(model: str) -> Callable[[str], int]:
    """Monta um contador de tokens memoizado por texto para um modelo."""
    cache_local: dict[str, int] = {}

    def contar(texto: str) -> int:
        if texto in cache_local:
            return cache_local[texto]
        total = _contar_litellm(model, texto)
        cache_local[texto] = total
        return total

    return contar


def token_counter_for(model: str) -> Callable[[str], int]:
    """Devolve o contador de tokens memoizado do modelo, criando-o se preciso."""
    contador = _CONTADORES.get(model)
    if contador is None:
        contador = _montar_contador(model)
        _CONTADORES[model] = contador
    return contador
