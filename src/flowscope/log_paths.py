"""Configuração compartilhada de logging da aplicação (caminhos e formato)."""

from pathlib import Path

#: Caminho do arquivo de log relativo ao diretório home do usuário.
LOG_FILE_RELATIVE_PATH = Path(".flowscope") / "logs" / "flowscope.log"

#: Formato da linha de log, compartilhado por todos os handlers da aplicação.
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

#: Formato de data/hora do log, compartilhado por todos os handlers da aplicação.
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S,%f"


def log_file_path() -> Path:
    """Retorna o caminho absoluto do arquivo de log da aplicação."""
    return Path.home() / LOG_FILE_RELATIVE_PATH
