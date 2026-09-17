"""Abertura de documentos em cache no aplicativo padrão do sistema."""

import os
import platform
import subprocess
from pathlib import Path


def abrir_no_aplicativo(caminho: Path) -> None:
    """Abre o arquivo no aplicativo padrão do sistema operacional.

    PDFs são encaminhados ao leitor padrão e HTML ao navegador padrão,
    conforme a associação do sistema para cada extensão.
    """
    destino = str(caminho)
    sistema = platform.system()
    if sistema == "Windows":
        os.startfile(destino)  # type: ignore[attr-defined]
    elif sistema == "Darwin":
        subprocess.run(["open", destino], check=False)
    else:
        subprocess.run(["xdg-open", destino], check=False)
