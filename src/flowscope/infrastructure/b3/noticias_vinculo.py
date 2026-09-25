"""Download do conteúdo apontado por uma URL embutida na notícia "Geral".

Algumas notícias trazem no corpo apenas um link para o documento (por exemplo,
"Esclarecimentos de questionamentos CVM/B3"). Como o corpo é somente um
apontador em texto puro, o conteúdo real é baixado sob demanda — ao selecionar
a notícia ou ao gerar os resumos pendentes.

O visualizador da CVM RAD não serve o arquivo diretamente: devolve uma página
cujo PDF é obtido por um POST AJAX (``ExibirPDF``) em base64. Captcha
habilitado, falha de rede ou formato inesperado resultam em ``None``, sem erro.
"""

import base64
import json
import logging
import re
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from flowscope.infrastructure.b3.bdr.text import extrair_texto as extrair_texto_pdf

logger = logging.getLogger("flowscope")

#: Timeout das requisições ao documento vinculado.
TIMEOUT = 30

#: Regex de uma URL absoluta no corpo da notícia.
_URL = re.compile(r"https?://[^\s<>\"']+")

#: Trechos que identificam o visualizador de documentos da CVM (RAD).
_HOST_CVM_RAD = "rad.cvm.gov.br"
_PAGINA_CVM_RAD = "frmExibirArquivoIPEExterno.aspx"


def extrair_url_vinculada(texto: str) -> str | None:
    """Retorna a primeira URL suportada embutida no corpo da notícia."""
    if not texto:
        return None
    for bruta in _URL.findall(texto):
        url = bruta.rstrip(".,;)")
        if _HOST_CVM_RAD in url and _PAGINA_CVM_RAD in url:
            return url
    return None


def baixar_conteudo_vinculado(
    texto: str,
    *,
    sessao: requests.Session | None = None,
    timeout: int = TIMEOUT,
) -> str | None:
    """Baixa e extrai o texto do documento apontado pela URL embutida.

    Retorna ``None`` quando não há URL suportada, o download falha ou o captcha
    está habilitado; nesses casos a notícia mantém o corpo original.
    """
    url = extrair_url_vinculada(texto)
    if url is None:
        return None
    sessao = sessao or requests.Session()
    try:
        return _baixar_cvm_rad(sessao, url, timeout)
    except Exception:  # falha isolada não pode interromper a pré-visualização
        logger.warning("Falha ao baixar documento vinculado %s", url, exc_info=True)
        return None


def _baixar_cvm_rad(
    sessao: requests.Session, url: str, timeout: int
) -> str | None:
    """Resolve o documento do visualizador da CVM RAD."""
    partes = urlparse(url)
    parametros = parse_qs(partes.query)
    protocolo = _primeiro(parametros, "ID", "NumeroProtocoloEntrega")
    if not protocolo:
        return None
    codigo = "2" if parametros.get("ID") else "1"
    resposta = sessao.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    resposta.raise_for_status()
    soup = BeautifulSoup(resposta.text, "html.parser")
    if _campo(soup, "hdnHabilitaCaptcha") == "S":
        logger.info("Documento CVM %s exige captcha; download ignorado.", protocolo)
        return None
    corpo = json.dumps(
        {
            "codigoInstituicao": codigo,
            "numeroProtocolo": protocolo,
            "token": "",
            "versaoCaptcha": "",
        }
    )
    resp = sessao.post(
        f"{partes.scheme}://{partes.netloc}{partes.path}/ExibirPDF",
        data=corpo,
        timeout=timeout,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": url,
            "User-Agent": "Mozilla/5.0",
        },
    )
    resp.raise_for_status()
    return _texto_da_resposta(resp.json())


def _primeiro(parametros: dict, *chaves: str) -> str | None:
    """Retorna o primeiro valor não vazio entre as chaves informadas."""
    for chave in chaves:
        valores = parametros.get(chave)
        if valores:
            return str(valores[0])
    return None


def _campo(soup: BeautifulSoup, id_: str) -> str | None:
    """Lê o valor de um campo oculto do visualizador, se existir."""
    elemento = soup.find(id=id_)
    valor = elemento.get("value") if elemento is not None else None
    return valor if isinstance(valor, str) else None


def _texto_da_resposta(payload: object) -> str | None:
    """Decodifica o PDF em base64 devolvido pelo WebMethod, ou ``None``."""
    dados = payload.get("d") if isinstance(payload, dict) else None
    if not isinstance(dados, str) or dados.startswith(":ERRO:") or dados == "V2":
        return None
    try:
        bruto = base64.b64decode(dados)
    except ValueError:
        return None
    return _texto_do_documento(bruto)


def _texto_do_documento(bruto: bytes) -> str:
    """Extrai o texto do documento (PDF) ou do HTML devolvido."""
    if bruto.lstrip()[:4] == b"%PDF":
        return extrair_texto_pdf(bruto)
    return BeautifulSoup(
        bruto.decode("utf-8", errors="replace"), "html.parser"
    ).get_text("\n", strip=True)
