"""Download de PDF no visualizador de arquivos externos da CVM.

O documento é obtido pelo fluxo ``GET página → POST ExibirPDF`` (o GET renova a
sessão/token do visualizador), que devolve JSON com o conteúdo em base64. O
sistema valida que o conteúdo decodificado começa com ``%PDF``.
"""

import base64
import json
import logging
from urllib.parse import quote

import requests

from flowscope.infrastructure.download_resiliente import (
    DOWNLOAD_TIMEOUT_S,
    post_renovando_sessao,
)

logger = logging.getLogger("flowscope")

#: Endpoint do visualizador de arquivos externos da CVM (POST ``ExibirPDF``).
CVM_PDF_URL = (
    "https://www.rad.cvm.gov.br/ENETWEB/"
    "frmExibirArquivoIPEExterno.aspx/ExibirPDF"
)

#: Página do visualizador (origem do token/sessão renovados antes do POST).
CVM_PDF_PAGE_URL = CVM_PDF_URL.removesuffix("/ExibirPDF")

#: Código de instituição usado ao consultar o PDF pelo ``ID`` do documento.
CODIGO_INSTITUICAO = "2"


def conteudo_e_pdf(dados: bytes) -> bool:
    """Indica se o conteúdo começa com a assinatura ``%PDF``."""
    return dados.startswith(b"%PDF")


def decodificar_pdf(payload: object) -> bytes | None:
    """Decodifica o PDF de um payload ``{"d": "<base64>"}``.

    Retorna ``None`` quando o payload não contém o campo, quando o base64 é
    inválido ou quando o conteúdo não começa com ``%PDF``.
    """
    conteudo = payload.get("d") if isinstance(payload, dict) else None
    if not isinstance(conteudo, str) or not conteudo:
        return None
    try:
        dados = base64.b64decode(conteudo, validate=True)
    except ValueError:
        logger.warning("Conteúdo base64 inválido no documento da CVM", exc_info=True)
        return None
    if not conteudo_e_pdf(dados):
        return None
    return dados


def _payload_tem_pdf(resposta: requests.Response) -> bool:
    """Valida que a resposta JSON contém um PDF em base64."""
    try:
        payload = resposta.json()
    except ValueError:
        return False
    return decodificar_pdf(payload) is not None


def baixar_pdf_cvm(
    numero_protocolo: str,
    *,
    session: requests.Session | None = None,
    timeout: int = 30,
    timeout_total: float | None = DOWNLOAD_TIMEOUT_S,
) -> bytes | None:
    """Baixa e decodifica o PDF do documento pelo protocolo da CVM.

    Usa o fluxo resiliente com renovação de sessão do visualizador da CVM.
    Retorna ``None`` em falha de rede, payload inválido ou conteúdo que não
    seja PDF, sem propagar a exceção.
    """
    corpo = json.dumps(
        {
            "codigoInstituicao": CODIGO_INSTITUICAO,
            "numeroProtocolo": numero_protocolo,
            "token": "",
            "versaoCaptcha": "",
        }
    )
    pagina = f"{CVM_PDF_PAGE_URL}?ID={quote(str(numero_protocolo))}"
    resposta = post_renovando_sessao(
        pagina,
        CVM_PDF_URL,
        corpo,
        sessao=session,
        timeout=timeout,
        timeout_total=timeout_total,
        validar=_payload_tem_pdf,
    )
    if resposta is None:
        return None
    try:
        payload = resposta.json()
    except ValueError:
        logger.warning("Payload inválido do PDF da CVM", exc_info=True)
        return None
    return decodificar_pdf(payload)
