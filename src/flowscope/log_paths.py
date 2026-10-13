"""Configuração compartilhada de logging da aplicação (caminhos e formato)."""

from pathlib import Path

#: Caminho do diretório de logs relativo ao diretório home do usuário.
LOG_DIR_RELATIVE_PATH = Path(".flowscope") / "logs"

#: Nome do arquivo de log ativo, dentro do diretório de logs.
LOG_FILE_NAME = "flowscope.log"

#: Formato da linha de log, compartilhado por todos os handlers da aplicação.
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

#: Formato de data/hora do log, compartilhado por todos os handlers da aplicação.
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S,%f"


def log_dir() -> Path:
    """Retorna o caminho absoluto do diretório de logs da aplicação."""
    return Path.home() / LOG_DIR_RELATIVE_PATH


def log_file_path() -> Path:
    """Retorna o caminho absoluto do arquivo de log ativo da aplicação."""
    return log_dir() / LOG_FILE_NAME
