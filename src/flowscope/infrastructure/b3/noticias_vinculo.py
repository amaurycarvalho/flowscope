"""Download do conteúdo apontado por uma URL embutida na notícia "Geral".

Algumas notícias não trazem o conteúdo no corpo: o ``#conteudoDetalhe`` é apenas
um apontador em texto puro para o documento. Casos típicos são "Esclarecimentos
de questionamentos CVM/B3" (visualizador da CVM RAD) e esclarecimentos/avisos de
oferta de FIIs (visualizador do FNET). Como o corpo é somente um apontador, o
conteúdo real é baixado sob demanda — ao selecionar a notícia ou ao gerar os
resumos pendentes.

A resolução usa o download resiliente compartilhado
(``download-conteudo-resiliente``): valida o conteúdo (PDF), segue o ``iframe``
do FNET e, no visualizador da CVM RAD, renova a sessão refazendo o GET antes de
repetir o POST, tudo sob o orçamento total por item. Captcha habilitado, falha de
rede ou formato inesperado resultam em ``None``, mantendo o corpo original. Um
PDF protegido por senha devolve o estado ``PROTEGIDO`` para que a apresentação
possa solicitar a senha.
"""

import base64
import json
import logging
from urllib.parse import parse_qs, urlparse

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
from flowscope.infrastructure.download_resiliente import (
    _Prazo,
    baixar_conteudo,
    post_renovando_sessao,
    validar_pdf,
)

logger = logging.getLogger("flowscope")

#: Timeout das requisições ao documento vinculado.
TIMEOUT = 30

__all__ = [
    "apontador_pendente",
    "baixar_conteudo_vinculado",
    "extrair_url_vinculada",
]


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


def _baixar_fnet(
    sessao: requests.Session,
    url: str,
    timeout: int,
    senha: str | None,
    prazo: _Prazo,
) -> ExtracaoTexto | None:
    """Resolve o documento do visualizador do FNET pelo helper resiliente.

    Segue o ``iframe`` que aponta para o PDF (``exibirDocumento``) quando o
    visualizador não serve o documento direto.
    """
    resposta = baixar_conteudo(
        url,
        sessao=sessao,
        timeout=timeout,
        prazo=prazo,
        validar=validar_pdf,
        seguir_iframe=True,
        transitorios_extra=frozenset({403}),
    )
    if resposta is None:
        return None
    return _texto_do_documento(resposta.content, senha, prazo)


def _baixar_cvm_rad(
    sessao: requests.Session,
    url: str,
    timeout: int,
    senha: str | None,
    prazo: _Prazo,
) -> ExtracaoTexto | None:
    """Resolve o documento do visualizador da CVM RAD com renovação de sessão."""
    partes = urlparse(url)
    parametros = parse_qs(partes.query)
    protocolo = _primeiro(parametros, "ID", "NumeroProtocoloEntrega")
    if not protocolo:
        return None
    codigo = "2" if parametros.get("ID") else "1"
    corpo = json.dumps(
        {
            "codigoInstituicao": codigo,
            "numeroProtocolo": protocolo,
            "token": "",
            "versaoCaptcha": "",
        }
    )
    url_post = f"{partes.scheme}://{partes.netloc}{partes.path}/ExibirPDF"
    resp = post_renovando_sessao(
        url,
        url_post,
        corpo,
        sessao=sessao,
        timeout=timeout,
        prazo=prazo,
        validar=_payload_tem_pdf,
        inspectar_pagina=_sem_captcha,
    )
    if resp is None:
        return None
    return _texto_da_resposta(resp.json(), senha, prazo)


def _sem_captcha(resposta: requests.Response) -> bool:
    """Indica se a página do visualizador da CVM não exige captcha."""
    soup = BeautifulSoup(resposta.text, "html.parser")
    if _campo(soup, "hdnHabilitaCaptcha") == "S":
        logger.info("Documento CVM exige captcha; download ignorado.")
        return False
    return True


def _payload_tem_pdf(resposta: requests.Response) -> bool:
    """Indica se o payload JSON do WebMethod contém um PDF válido."""
    try:
        payload = resposta.json()
    except ValueError:
        return False
    dados = payload.get("d") if isinstance(payload, dict) else None
    if not isinstance(dados, str) or dados.startswith(":ERRO:") or dados == "V2":
        return False
    try:
        bruto = base64.b64decode(dados)
    except ValueError:
        return False
    return bruto.lstrip()[:4] == b"%PDF"


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
