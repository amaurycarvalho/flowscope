"""Download do conteúdo apontado por uma URL embutida na notícia "Geral".

Algumas notícias não trazem o conteúdo no corpo: o ``#conteudoDetalhe`` é apenas
um apontador em texto puro para o documento. Casos típicos são "Esclarecimentos
de questionamentos CVM/B3" (visualizador da CVM RAD) e esclarecimentos/avisos de
oferta de FIIs (visualizador do FNET). Como o corpo é somente um apontador, o
conteúdo real é baixado sob demanda — ao selecionar a notícia ou ao gerar os
resumos pendentes.

Cada host usa uma estratégia própria: o visualizador da CVM RAD devolve uma
página cujo PDF é obtido por um POST AJAX (``ExibirPDF``) em base64; o FNET
devolve uma página com um ``iframe`` (``exibirDocumento``) que serve o PDF.
Captcha habilitado, falha de rede ou formato inesperado resultam em ``None`` (ou
texto vazio), sem erro, mantendo o corpo original.
"""

import base64
import json
import logging
import re
import time
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from flowscope.infrastructure.b3.bdr.text import extrair_texto as extrair_texto_pdf

logger = logging.getLogger("flowscope")

#: Timeout das requisições ao documento vinculado.
TIMEOUT = 30

#: Número de tentativas das requisições (o FNET responde de forma intermitente).
TENTATIVAS = 3

#: Espera base (em segundos) entre tentativas, multiplicada pela tentativa.
ESPERA = 0.5

#: Regex de uma URL absoluta no corpo da notícia.
_URL = re.compile(r"https?://[^\s<>\"']+")

#: Trechos que identificam o visualizador de documentos da CVM (RAD).
_HOST_CVM_RAD = "rad.cvm.gov.br"
_PAGINA_CVM_RAD = "frmExibirArquivoIPEExterno.aspx"

#: Trechos que identificam o visualizador de documentos do FNET.
_HOST_FNET = "fnet.bmfbovespa.com.br"
_PAGINA_FNET = "visualizarDocumento"

#: Trecho do ``iframe`` do FNET que serve o PDF do documento.
_IFRAME_FNET = "exibirDocumento"

#: Cabeçalho padrão das requisições.
_USER_AGENT = "Mozilla/5.0"


def extrair_url_vinculada(texto: str) -> str | None:
    """Retorna a primeira URL suportada (CVM RAD ou FNET) embutida no corpo."""
    if not texto:
        return None
    for bruta in _URL.findall(texto):
        url = bruta.rstrip(".,;)")
        if _host_suportado(url) is not None:
            return url
    return None


def apontador_pendente(texto: str, corpo: str) -> bool:
    """Indica se ``texto`` ainda é o apontador não resolvido do ``corpo``.

    Vale quando o texto contém uma URL suportada e é idêntico ao corpo atual do
    ``#conteudoDetalhe`` (ou seja, o download do documento vinculado não
    concluiu). A comparação evita tratar como pendente um documento já resolvido
    que porventura cite uma URL suportada.
    """
    return bool(corpo) and texto == corpo and extrair_url_vinculada(texto) is not None


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
    host = _host_suportado(url)
    if host is None:
        return None
    sessao = sessao or requests.Session()
    try:
        if host == "fnet":
            return _baixar_fnet(sessao, url, timeout)
        return _baixar_cvm_rad(sessao, url, timeout)
    except Exception:  # falha isolada não pode interromper a pré-visualização
        logger.warning("Falha ao baixar documento vinculado %s", url, exc_info=True)
        return None


def _host_suportado(url: str) -> str | None:
    """Identifica o resolvedor aplicável à URL, ou ``None``."""
    if _HOST_CVM_RAD in url and _PAGINA_CVM_RAD in url:
        return "cvm"
    if _HOST_FNET in url and _PAGINA_FNET in url:
        return "fnet"
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
    resposta = _obter(sessao, url, timeout)
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
            "User-Agent": _USER_AGENT,
        },
    )
    resp.raise_for_status()
    return _texto_da_resposta(resp.json())


def _baixar_fnet(sessao: requests.Session, url: str, timeout: int) -> str | None:
    """Resolve o documento do visualizador do FNET.

    Se o visualizador já servir o PDF, extrai-o direto; caso contrário, segue o
    ``iframe`` que aponta para o PDF (``exibirDocumento``).
    """
    resposta = _obter(sessao, url, timeout)
    if _e_pdf(resposta):
        return _texto_do_documento(resposta.content)
    alvo = _url_do_pdf_fnet(resposta)
    if alvo is None:
        return None
    documento = _obter(sessao, alvo, timeout, referer=url)
    return _texto_do_documento(documento.content)


def _url_do_pdf_fnet(resposta: requests.Response) -> str | None:
    """Extrai a URL absoluta do ``iframe`` que serve o PDF do FNET."""
    soup = BeautifulSoup(resposta.text, "html.parser")
    for iframe in soup.find_all("iframe", src=True):
        origem = str(iframe.get("src", ""))
        if _IFRAME_FNET in origem:
            return urljoin(resposta.url, origem)
    return None


def _obter(
    sessao: requests.Session,
    url: str,
    timeout: int,
    *,
    referer: str | None = None,
) -> requests.Response:
    """Faz o GET com algumas tentativas, para tolerar a instabilidade do host."""
    headers = {"User-Agent": _USER_AGENT}
    if referer:
        headers["Referer"] = referer
    ultimo: Exception | None = None
    for tentativa in range(TENTATIVAS):
        try:
            resposta = sessao.get(url, timeout=timeout, headers=headers)
            resposta.raise_for_status()
            return resposta
        except requests.RequestException as exc:
            ultimo = exc
            if tentativa + 1 < TENTATIVAS:
                time.sleep(ESPERA * (tentativa + 1))
    if ultimo is not None:
        raise ultimo
    raise RuntimeError(url)


def _e_pdf(resposta: requests.Response) -> bool:
    """Indica se a resposta já é o próprio PDF."""
    if "application/pdf" in resposta.headers.get("Content-Type", "").lower():
        return True
    return resposta.content.lstrip()[:4] == b"%PDF"


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
    return _texto_do_documento(bruto) or None


def _texto_do_documento(bruto: bytes) -> str:
    """Extrai o texto do documento (PDF) ou do HTML devolvido."""
    if bruto.lstrip()[:4] == b"%PDF":
        return extrair_texto_pdf(bruto)
    return BeautifulSoup(
        bruto.decode("utf-8", errors="replace"), "html.parser"
    ).get_text("\n", strip=True)
