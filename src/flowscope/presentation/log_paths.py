"""Caminhos compartilhados dos arquivos de log da aplicação."""

from pathlib import Path

#: Caminho do arquivo de log relativo ao diretório home do usuário.
LOG_FILE_RELATIVE_PATH = Path(".flowscope") / "logs" / "flowscope.log"


def log_file_path() -> Path:
    """Retorna o caminho absoluto do arquivo de log da aplicação."""
    return Path.home() / LOG_FILE_RELATIVE_PATH
