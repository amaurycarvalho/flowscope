"""Download de PDF no visualizador de arquivos externos da CVM.

O documento é obtido por POST ``ExibirPDF``, que devolve JSON com o conteúdo
em base64. O sistema valida que o conteúdo decodificado começa com ``%PDF``.
"""

import base64
import json
import logging

import requests

logger = logging.getLogger("flowscope")

#: Endpoint do visualizador de arquivos externos da CVM.
CVM_PDF_URL = (
    "https://www.rad.cvm.gov.br/ENETWEB/"
    "frmExibirArquivoIPEExterno.aspx/ExibirPDF"
)

#: Código de instituição usado ao consultar o PDF pelo ``ID`` do documento.
CODIGO_INSTITUICAO = "2"

_HEADERS_JSON = {"Content-Type": "application/json; charset=utf-8"}


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


def baixar_pdf_cvm(
    numero_protocolo: str,
    *,
    session: requests.Session | None = None,
    timeout: int = 30,
) -> bytes | None:
    """Baixa e decodifica o PDF do documento pelo protocolo da CVM.

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
    try:
        resposta = (session or requests).post(
            CVM_PDF_URL,
            data=corpo,
            headers=_HEADERS_JSON,
            timeout=timeout,
        )
        resposta.raise_for_status()
        payload = resposta.json()
    except (requests.RequestException, ValueError):
        logger.warning("Falha ao baixar PDF da CVM", exc_info=True)
        return None
    return decodificar_pdf(payload)
