"""Leitura da retenção configurável dos arquivos de log.

A preferência vive na chave de topo ``log_retention_days`` de
``~/.flowscope/config.json`` e é lida diretamente pela inicialização do
logging, antes de a GUI carregar as preferências. O leitor é neutro: não
importa apresentação nem LLM.
"""

import json
from pathlib import Path

#: Retenção padrão, em dias, quando a preferência está ausente ou inválida.
DEFAULT_LOG_RETENTION_DAYS = 7

#: Chave de configuração da retenção no ``config.json``.
LOG_RETENTION_KEY = "log_retention_days"

#: Caminho do arquivo de configuração, relativo ao diretório home do usuário.
CONFIG_RELATIVE_PATH = Path(".flowscope") / "config.json"


def _config_path() -> Path:
    """Retorna o caminho absoluto do ``config.json`` do usuário."""
    return Path.home() / CONFIG_RELATIVE_PATH


def _ler_config(path: Path) -> dict:
    """Lê o JSON do arquivo, devolvendo um dicionário vazio em caso de falha."""
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def log_retention_days(config_path: Path | None = None) -> int:
    """Retorna os dias de retenção dos backups, caindo no padrão se inválido.

    Valores ausentes, não inteiros ou menores que ``1`` usam
    :data:`DEFAULT_LOG_RETENTION_DAYS`.
    """
    destino = config_path if config_path is not None else _config_path()
    valor = _ler_config(destino).get(LOG_RETENTION_KEY)
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
        return DEFAULT_LOG_RETENTION_DAYS
    return valor
