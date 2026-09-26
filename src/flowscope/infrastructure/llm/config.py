"""Leitura e gravação da configuração de LLM no ``config.json``.

A configuração de completion vive no bloco ``llm.chat`` de
``~/.flowscope/config.json``. A gravação faz *read-modify-write*: relê o
arquivo e substitui apenas ``llm.chat``, preservando as preferências da GUI e
outros sub-blocos de ``llm`` (como ``embedding``). Nenhuma dependência de
apresentação é importada aqui.
"""

import importlib.util
import json
from pathlib import Path

from flowscope.infrastructure.llm.presets import PROVIDER_PRESETS

#: Diretório e arquivo de configuração do usuário.
CONFIG_DIR = Path.home() / ".flowscope"
CONFIG_PATH = CONFIG_DIR / "config.json"

#: Valores padrão do bloco ``llm.chat``.
DEFAULT_LLM_CONFIG: dict = {
    "provider": "none",
    "api_url": "",
    "model": "",
    "api_key": "",
    "rpm": 5,
}

#: Campos guardados por provedor no mapa ``llm.chat.providers``.
_CHAT_FIELDS = ("api_url", "model", "api_key", "rpm")

#: Valor padrão do flag de análise de guidance via LLM (desabilitado).
DEFAULT_GUIDANCE_ENABLED = False


def _read_json(path: Path) -> dict:
    """Lê o JSON do arquivo, devolvendo um dicionário vazio em caso de falha."""
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _ler_chat(data: dict) -> dict:
    """Devolve o sub-bloco ``llm.chat`` como dicionário (vazio se ausente)."""
    llm = data.get("llm")
    chat = llm.get("chat") if isinstance(llm, dict) else None
    return chat if isinstance(chat, dict) else {}


def _normalizar_provedor(entrada: dict | None) -> dict:
    """Preenche os campos ausentes de uma entrada de provedor com defaults."""
    resultado = {chave: DEFAULT_LLM_CONFIG[chave] for chave in _CHAT_FIELDS}
    if isinstance(entrada, dict):
        for chave in _CHAT_FIELDS:
            if entrada.get(chave) is not None:
                resultado[chave] = entrada[chave]
    try:
        resultado["rpm"] = int(resultado["rpm"])
    except (TypeError, ValueError):
        resultado["rpm"] = DEFAULT_LLM_CONFIG["rpm"]
    return resultado


def _providers_do_chat(chat: dict) -> dict[str, dict]:
    """Normaliza o mapa ``providers``, migrando o formato plano anterior.

    O formato novo guarda um mapa ``providers``; o anterior guardava os campos
    do provedor ativo de forma plana em ``llm.chat``. Quando o mapa está ausente
    ou vazio, os campos planos viram a entrada do provedor ativo.
    """
    providers = chat.get("providers")
    if isinstance(providers, dict) and providers:
        return {
            nome: _normalizar_provedor(entrada)
            for nome, entrada in providers.items()
            if isinstance(nome, str) and nome != "none"
        }
    provider = chat.get("provider")
    if isinstance(provider, str) and provider and provider != "none":
        plano = {chave: chat.get(chave) for chave in _CHAT_FIELDS}
        return {provider: _normalizar_provedor(plano)}
    return {}


def load_provider_configs(path: Path | None = None) -> dict[str, dict]:
    """Carrega o mapa ``llm.chat.providers``, migrando o formato plano anterior."""
    return _providers_do_chat(_ler_chat(_read_json(path or CONFIG_PATH)))


def load_llm_config(path: Path | None = None) -> dict:
    """Carrega o bloco ``llm.chat`` do provedor ativo com defaults preenchidos."""
    chat = _ler_chat(_read_json(path or CONFIG_PATH))
    config = dict(DEFAULT_LLM_CONFIG)
    provider = chat.get("provider")
    if isinstance(provider, str) and provider:
        config["provider"] = provider
    if config["provider"] == "none":
        return config
    entrada = _providers_do_chat(chat).get(config["provider"])
    if entrada is not None:
        config.update(entrada)
    return config


def save_llm_config(config: dict, path: Path | None = None) -> None:
    """Grava ``llm.chat`` preservando os demais provedores e blocos do arquivo."""
    destino = path or CONFIG_PATH
    data = _read_json(destino)
    provider = config.get("provider") or "none"
    providers = _providers_do_chat(_ler_chat(data))
    if provider != "none":
        entrada = {
            chave: config.get(chave, DEFAULT_LLM_CONFIG[chave])
            for chave in _CHAT_FIELDS
        }
        providers[provider] = _normalizar_provedor(entrada)
    llm = data.get("llm")
    if not isinstance(llm, dict):
        llm = {}
    llm["chat"] = {"provider": provider, "providers": providers}
    data["llm"] = llm
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def load_guidance_llm_enabled(path: Path | None = None) -> bool:
    """Indica se a análise de guidance via LLM está habilitada (padrão: não).

    O flag vive no bloco ``llm.guidance.enabled`` e é independente do provedor
    de chat: desabilitado, a avaliação de guidance usa apenas a extração
    determinística.
    """
    data = _read_json(path or CONFIG_PATH)
    llm = data.get("llm")
    guidance = llm.get("guidance") if isinstance(llm, dict) else None
    if not isinstance(guidance, dict):
        return DEFAULT_GUIDANCE_ENABLED
    return bool(guidance.get("enabled", DEFAULT_GUIDANCE_ENABLED))


def save_guidance_llm_enabled(enabled: bool, path: Path | None = None) -> None:
    """Grava o flag ``llm.guidance.enabled`` preservando o bloco ``llm.chat``."""
    destino = path or CONFIG_PATH
    data = _read_json(destino)
    llm = data.get("llm")
    if not isinstance(llm, dict):
        llm = {}
    guidance = llm.get("guidance")
    if not isinstance(guidance, dict):
        guidance = {}
    guidance["enabled"] = bool(enabled)
    llm["guidance"] = guidance
    data["llm"] = llm
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def get_presets() -> dict[str, dict[str, str]]:
    """Retorna os presets de provedores suportados."""
    return PROVIDER_PRESETS


def check_llm_deps() -> bool:
    """Indica se a dependência opcional ``litellm`` está instalada."""
    try:
        return importlib.util.find_spec("litellm") is not None
    except (ImportError, ValueError):
        return False


def llm_configurada() -> bool:
    """Indica se há provedor diferente de ``none`` e dependências presentes."""
    try:
        config = load_llm_config()
        return config.get("provider", "none") != "none" and check_llm_deps()
    except Exception:  # configuração ilegível não deve quebrar a interface
        return False


def guidance_llm_disponivel() -> bool:
    """Indica se a análise de guidance via LLM está habilitada e configurada.

    O flag ``llm.guidance.enabled`` (padrão desabilitado) controla o uso da LLM
    especificamente para guidance; quando desabilitado, roda apenas a extração
    determinística, ainda que o provedor de chat esteja configurado.
    """
    return load_guidance_llm_enabled() and llm_configurada()
