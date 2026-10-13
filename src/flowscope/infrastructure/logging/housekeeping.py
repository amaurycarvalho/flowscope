"""Housekeeping diário dos arquivos de log da aplicação.

Cada dia corresponde a um arquivo: o ativo ``flowscope.log`` e os arquivos
arquivados ``flowscope-YYYY-MM-DD.log``. Aqui vivem a limpeza por idade e a
rolagem do arquivo obsoleto na inicialização, fora da apresentação.
"""

import logging
from datetime import date, datetime, timedelta
from pathlib import Path

logger = logging.getLogger("flowscope")

#: Prefixo dos arquivos de log arquivados por data.
BACKUP_PREFIX = "flowscope-"

#: Sufixo dos arquivos de log arquivados por data.
BACKUP_SUFFIX = ".log"

#: Formato da data embutida no nome dos arquivos arquivados.
BACKUP_DATE_FORMAT = "%Y-%m-%d"

#: Prefixo do nome padrão gerado pelo ``TimedRotatingFileHandler``.
_HANDLER_BACKUP_PREFIX = "flowscope.log."


def nome_backup(data: date) -> str:
    """Retorna o nome do arquivo arquivado para uma data (``flowscope-<data>.log``)."""
    return f"{BACKUP_PREFIX}{data.strftime(BACKUP_DATE_FORMAT)}{BACKUP_SUFFIX}"


def _data_do_backup(nome: str) -> date | None:
    """Extrai a data de um nome de arquivo arquivado, ou ``None`` se fora do padrão."""
    if not nome.startswith(BACKUP_PREFIX) or not nome.endswith(BACKUP_SUFFIX):
        return None
    meio = nome[len(BACKUP_PREFIX):-len(BACKUP_SUFFIX)]
    try:
        return datetime.strptime(meio, BACKUP_DATE_FORMAT).date()
    except ValueError:
        return None


def renomear_backup(default_name: str) -> str:
    """Reescreve o nome padrão do handler para o formato ``flowscope-<data>.log``.

    O ``TimedRotatingFileHandler`` nomeia o arquivo rotacionado como
    ``flowscope.log.YYYY-MM-DD``; o ``namer`` do handler usa esta função para
    gravar ``flowscope-YYYY-MM-DD.log``. Nomes fora desse padrão são devolvidos
    sem alteração.
    """
    caminho = Path(default_name)
    nome = caminho.name
    if not nome.startswith(_HANDLER_BACKUP_PREFIX):
        return default_name
    data = nome[len(_HANDLER_BACKUP_PREFIX):]
    return str(caminho.with_name(f"{BACKUP_PREFIX}{data}{BACKUP_SUFFIX}"))


def limpar_backups_antigos(
    diretorio: Path,
    hoje: date,
    retencao_dias: int,
) -> None:
    """Apaga os arquivos arquivados anteriores a ``hoje - retencao_dias``.

    Preserva o dia corrente e os ``retencao_dias`` dias anteriores. O arquivo
    ativo e arquivos fora do padrão datado são ignorados; falhas de ``OSError``
    são toleradas sem interromper a inicialização.
    """
    try:
        if not diretorio.is_dir():
            return
        limite = hoje - timedelta(days=retencao_dias)
        for caminho in diretorio.iterdir():
            data = _data_do_backup(caminho.name)
            if data is None or data >= limite:
                continue
            try:
                caminho.unlink()
            except OSError:
                logger.warning(
                    "Falha ao remover log antigo %s", caminho, exc_info=True
                )
    except OSError:
        logger.warning(
            "Falha ao limpar logs antigos em %s", diretorio, exc_info=True
        )


def rotacionar_log_obsoleto(log_path: Path, hoje: date) -> None:
    """Renomeia o log ativo de um dia anterior para o arquivo arquivado datado.

    Usa a data da última modificação do arquivo. Quando o destino já existir, o
    conteúdo do ativo é concatenado ao destino antes de removê-lo. Nada é feito
    quando o ativo não existe, já pertence ao dia corrente ou é de um dia
    posterior a ``hoje``. Falhas de ``OSError`` são toleradas.
    """
    try:
        if not log_path.is_file():
            return
        modificado = datetime.fromtimestamp(log_path.stat().st_mtime)
        if modificado.date() >= hoje:
            return
        destino = log_path.with_name(nome_backup(modificado.date()))
        if destino.exists():
            with destino.open("ab") as saida, log_path.open("rb") as origem:
                saida.write(origem.read())
            log_path.unlink()
        else:
            log_path.rename(destino)
    except OSError:
        logger.warning(
            "Falha ao rotacionar o log obsoleto %s", log_path, exc_info=True
        )
