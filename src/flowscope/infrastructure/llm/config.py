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


def load_llm_config(path: Path | None = None) -> dict:
    """Carrega o bloco ``llm.chat`` preenchendo os campos ausentes com defaults."""
    data = _read_json(path or CONFIG_PATH)
    llm = data.get("llm")
    chat = llm.get("chat") if isinstance(llm, dict) else None
    if not isinstance(chat, dict):
        chat = {}
    config = dict(DEFAULT_LLM_CONFIG)
    for chave in DEFAULT_LLM_CONFIG:
        if chave in chat and chat[chave] is not None:
            config[chave] = chat[chave]
    try:
        config["rpm"] = int(config["rpm"])
    except (TypeError, ValueError):
        config["rpm"] = DEFAULT_LLM_CONFIG["rpm"]
    return config


def save_llm_config(config: dict, path: Path | None = None) -> None:
    """Grava ``llm.chat`` preservando as demais chaves do arquivo."""
    destino = path or CONFIG_PATH
    data = _read_json(destino)
    llm = data.get("llm")
    if not isinstance(llm, dict):
        llm = {}
    llm["chat"] = {
        chave: config.get(chave, DEFAULT_LLM_CONFIG[chave])
        for chave in DEFAULT_LLM_CONFIG
    }
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
