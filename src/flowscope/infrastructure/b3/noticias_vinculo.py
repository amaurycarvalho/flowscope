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
Captcha habilitado, falha de rede ou formato inesperado resultam em ``None``,
mantendo o corpo original. Um PDF protegido por senha devolve o estado
``PROTEGIDO`` para que a apresentação possa solicitar a senha.
"""

import base64
import json
import logging
import time
from urllib.parse import SplitResult, parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from flowscope.application.document_preview import (
    ExtracaoTexto,
    StatusExtracao,
)
from flowscope.application.extracao_orcada import (
    EXTRACAO_TIMEOUT_S,
    extrair_pdf_com_orcamento,
)
from flowscope.domain.noticias import (
    apontador_pendente,
    extrair_url_vinculada,
    host_suportado,
)
from flowscope.infrastructure.http_retry import executar_com_retry

logger = logging.getLogger("flowscope")

#: Timeout das requisições ao documento vinculado.
TIMEOUT = 30

#: Número de tentativas das requisições (o FNET responde de forma intermitente).
TENTATIVAS = 3

#: Espera base (em segundos) entre tentativas, multiplicada pela tentativa.
ESPERA = 0.5

#: Motivo do aborto quando o orçamento total de resolução se esgota.
_MOTIVO_ORCAMENTO = "orçamento de resolução do documento vinculado esgotado"

#: Trecho do ``iframe`` do FNET que serve o PDF do documento.
_IFRAME_FNET = "exibirDocumento"

#: Cabeçalho padrão das requisições.
_USER_AGENT = "Mozilla/5.0"

__all__ = [
    "apontador_pendente",
    "baixar_conteudo_vinculado",
    "extrair_url_vinculada",
]


class _Prazo:
    """Orçamento total (deadline) compartilhado pelas etapas da resolução.

    Quando ``timeout_total`` é ``None``, o prazo é ilimitado e cada requisição
    usa o ``timeout`` próprio, preservando o comportamento anterior. Quando
    informado, cada etapa consome o restante do orçamento e é abortada ao
    esgotá-lo.
    """

    def __init__(self: "_Prazo", timeout_total: float | None) -> None:
        self._limite = (
            None
            if timeout_total is None
            else time.monotonic() + float(timeout_total)
        )

    def esgotado(self: "_Prazo") -> bool:
        """Indica se o orçamento total já se esgotou."""
        return self._limite is not None and time.monotonic() >= self._limite

    def efetivo(self: "_Prazo", timeout: float) -> float:
        """Retorna o timeout da etapa limitado ao restante do orçamento."""
        if self._limite is None:
            return timeout
        return max(0.0, min(timeout, self._limite - time.monotonic()))


def baixar_conteudo_vinculado(
    texto: str,
    senha: str | None = None,
    *,
    sessao: requests.Session | None = None,
    timeout: int = TIMEOUT,
    timeout_total: float | None = None,
) -> ExtracaoTexto | None:
    """Baixa e extrai o texto do documento apontado pela URL embutida.

    Retorna ``None`` quando não há URL suportada, o download falha, o captcha
    está habilitado ou o documento não tem texto; nesses casos a notícia mantém
    o corpo original. Um PDF protegido por senha devolve ``PROTEGIDO`` (texto
    possivelmente vazio) para a apresentação solicitar a senha. ``timeout_total``
    limita a duração de toda a resolução (rede + extração), compartilhada entre
    as requisições e o parse do PDF baixado.
    """
    url = extrair_url_vinculada(texto)
    if url is None:
        return None
    host = host_suportado(url)
    if host is None:
        return None
    prazo = _Prazo(timeout_total)
    sessao = sessao or requests.Session()
    try:
        if host == "fnet":
            resultado = _baixar_fnet(sessao, url, timeout, senha, prazo)
        else:
            resultado = _baixar_cvm_rad(sessao, url, timeout, senha, prazo)
    except requests.RequestException as exc:
        logger.warning(
            "Falha de comunicação ao baixar documento vinculado %s: %s: %s. "
            "Mantendo o corpo original.",
            url,
            type(exc).__name__,
            exc,
        )
        return None
    except Exception as exc:  # erro inesperado permanece rastreável
        logger.warning(
            "Falha ao baixar documento vinculado %s: %s",
            url,
            exc,
            exc_info=True,
        )
        return None
    if resultado is not None and resultado.status is StatusExtracao.SEM_TEXTO:
        return None
    return resultado


def _baixar_cvm_rad(
    sessao: requests.Session,
    url: str,
    timeout: int,
    senha: str | None,
    prazo: _Prazo,
) -> ExtracaoTexto | None:
    """Resolve o documento do visualizador da CVM RAD."""
    partes = urlparse(url)
    parametros = parse_qs(partes.query)
    protocolo = _primeiro(parametros, "ID", "NumeroProtocoloEntrega")
    if not protocolo:
        return None
    codigo = "2" if parametros.get("ID") else "1"
    resposta = _obter(sessao, url, timeout, prazo)
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
    resp = executar_com_retry(
        lambda: _post_exibir_pdf(sessao, partes, corpo, timeout, url, prazo),
        metodo="POST",
        repetivel=True,
    )
    return _texto_da_resposta(resp.json(), senha, prazo)


def _post_exibir_pdf(
    sessao: requests.Session,
    partes: SplitResult,
    corpo: str,
    timeout: int,
    referer: str,
    prazo: _Prazo,
) -> requests.Response:
    """Executa o POST ``ExibirPDF`` e valida a resposta HTTP."""
    if prazo.esgotado():
        raise requests.Timeout(_MOTIVO_ORCAMENTO)
    resp = sessao.post(
        f"{partes.scheme}://{partes.netloc}{partes.path}/ExibirPDF",
        data=corpo,
        timeout=prazo.efetivo(timeout),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": referer,
            "User-Agent": _USER_AGENT,
        },
    )
    resp.raise_for_status()
    return resp


def _baixar_fnet(
    sessao: requests.Session,
    url: str,
    timeout: int,
    senha: str | None,
    prazo: _Prazo,
) -> ExtracaoTexto | None:
    """Resolve o documento do visualizador do FNET.

    Se o visualizador já servir o PDF, extrai-o direto; caso contrário, segue o
    ``iframe`` que aponta para o PDF (``exibirDocumento``).
    """
    resposta = _obter(sessao, url, timeout, prazo)
    if _e_pdf(resposta):
        return _texto_do_documento(resposta.content, senha, prazo)
    alvo = _url_do_pdf_fnet(resposta)
    if alvo is None:
        return None
    documento = _obter(sessao, alvo, timeout, prazo, referer=url)
    return _texto_do_documento(documento.content, senha, prazo)


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
    prazo: _Prazo,
    *,
    referer: str | None = None,
) -> requests.Response:
    """Faz o GET com a política central de retry, tolerando host instável."""
    headers = {"User-Agent": _USER_AGENT}
    if referer:
        headers["Referer"] = referer
    delays = tuple(ESPERA * tentativa for tentativa in range(TENTATIVAS))

    def _fazer() -> requests.Response:
        if prazo.esgotado():
            raise requests.Timeout(_MOTIVO_ORCAMENTO)
        resposta = sessao.get(
            url, timeout=prazo.efetivo(timeout), headers=headers
        )
        resposta.raise_for_status()
        return resposta

    return executar_com_retry(_fazer, metodo="GET", delays=delays)


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


def _texto_da_resposta(
    payload: object, senha: str | None, prazo: _Prazo
) -> ExtracaoTexto | None:
    """Decodifica o PDF em base64 devolvido pelo WebMethod, ou ``None``."""
    dados = payload.get("d") if isinstance(payload, dict) else None
    if not isinstance(dados, str) or dados.startswith(":ERRO:") or dados == "V2":
        return None
    try:
        bruto = base64.b64decode(dados)
    except ValueError:
        return None
    return _texto_do_documento(bruto, senha, prazo)


def _texto_do_documento(
    bruto: bytes, senha: str | None, prazo: _Prazo
) -> ExtracaoTexto:
    """Extrai o texto do documento (PDF) ou do HTML devolvido.

    O parse do PDF baixado respeita o restante do orçamento da resolução; o
    HTML baixado NÃO está sujeito ao orçamento, como na extração por arquivo.
    """
    if bruto.lstrip()[:4] == b"%PDF":
        return extrair_pdf_com_orcamento(
            bruto, senha, timeout=prazo.efetivo(EXTRACAO_TIMEOUT_S)
        )
    texto = BeautifulSoup(
        bruto.decode("utf-8", errors="replace"), "html.parser"
    ).get_text("\n", strip=True)
    status = StatusExtracao.OK if texto.strip() else StatusExtracao.SEM_TEXTO
    return ExtracaoTexto(texto, status)
