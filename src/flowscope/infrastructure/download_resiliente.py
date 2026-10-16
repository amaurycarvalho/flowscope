"""Download resiliente compartilhado de arquivos (PDF e HTML).

Centraliza a aquisição de arquivos de hosts externos (FNET e rad.cvm.gov.br)
encapsulando: sessão HTTP, resolução de URL (direta ou ``visualizarDocumento``
→ ``iframe``), override de status por ponto de chamada, validação de conteúdo e
um orçamento total por item (deadline). O download de um item nunca interrompe
os demais: ao esgotar o orçamento ou obter conteúdo inválido, a função devolve
``None``.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from flowscope.infrastructure.http_retry import (
    ConteudoInvalido,
    executar_com_retry,
)

logger = logging.getLogger("flowscope")

#: Timeout padrão de cada requisição (segundos).
TIMEOUT = 30

#: Orçamento total padrão (segundos) por item de download.
DOWNLOAD_TIMEOUT_S = 90.0

#: Número de tentativas por item (o FNET responde de forma intermitente).
TENTATIVAS = 3

#: Espera base (segundos) entre tentativas, multiplicada pela tentativa.
ESPERA = 0.5

#: Trecho do ``iframe`` do FNET que serve o PDF do documento.
_IFRAME_FNET = "exibirDocumento"

#: Cabeçalho padrão das requisições.
_USER_AGENT = "Mozilla/5.0"

#: Motivo do aborto quando o orçamento total do item se esgota.
_MOTIVO_ORCAMENTO = "orçamento de download do item esgotado"


class OrcamentoEsgotado(Exception):
    """O orçamento total do item de download se esgotou."""


class PaginaRejeitada(Exception):
    """A página do visualizador não é utilizável (ex.: captcha habilitado)."""


class _Prazo:
    """Orçamento total (deadline) compartilhado pelas etapas do download.

    Quando ``timeout_total`` é ``None``, o prazo é ilimitado e cada requisição
    usa o ``timeout`` próprio, preservando o comportamento anterior. Quando
    informado, cada etapa consome o restante do orçamento e é abortada ao
    esgotá-lo.
    """

    def __init__(self: _Prazo, timeout_total: float | None) -> None:
        """Inicializa o prazo a partir de um orçamento total opcional."""
        self._limite = (
            None
            if timeout_total is None
            else time.monotonic() + float(timeout_total)
        )

    def esgotado(self: _Prazo) -> bool:
        """Indica se o orçamento total já se esgotou."""
        return self._limite is not None and time.monotonic() >= self._limite

    def efetivo(self: _Prazo, timeout: float) -> float:
        """Retorna o timeout da etapa limitado ao restante do orçamento."""
        if self._limite is None:
            return timeout
        return max(0.0, min(timeout, self._limite - time.monotonic()))


def validar_pdf(resposta: requests.Response) -> bool:
    """Indica se a resposta contém um PDF (assinatura ``%PDF``)."""
    return resposta.content.lstrip()[:4] == b"%PDF"


def validar_html(resposta: requests.Response) -> bool:
    """Indica se o conteúdo é um HTML minimamente reconhecível."""
    bruto = resposta.content.lstrip()
    return bruto[:1] == b"<" and (
        b"<html" in bruto.lower() or b"<body" in bruto.lower()
    )


def _delays() -> tuple[float, ...]:
    """Sequência de esperas entre tentativas, derivada de ``ESPERA``."""
    return tuple(ESPERA * tentativa for tentativa in range(TENTATIVAS)) or (0.0,)


def _checador(
    prazo: _Prazo, cancelar: Callable[[], None] | None
) -> Callable[[], None]:
    """Monta o gancho de cancelamento que também aborta o orçamento esgotado."""

    def _checar() -> None:
        if cancelar is not None:
            cancelar()
        if prazo.esgotado():
            raise OrcamentoEsgotado(_MOTIVO_ORCAMENTO)

    return _checar


def _cabecalhos(base: Mapping[str, str] | None) -> dict[str, str]:
    """Combina os cabeçalhos informados com o ``User-Agent`` padrão."""
    return {"User-Agent": _USER_AGENT, **dict(base or {})}


def _get(
    sessao: requests.Session,
    url: str,
    timeout: float,
    prazo: _Prazo,
    headers: Mapping[str, str],
) -> requests.Response:
    """Executa um GET sob o orçamento, sinalizando o esgotamento."""
    if prazo.esgotado():
        raise OrcamentoEsgotado(_MOTIVO_ORCAMENTO)
    resposta = sessao.get(url, timeout=prazo.efetivo(timeout), headers=dict(headers))
    resposta.raise_for_status()
    return resposta


def _url_do_iframe(resposta: requests.Response) -> str | None:
    """Extrai a URL absoluta do ``iframe`` que serve o documento do FNET."""
    soup = BeautifulSoup(resposta.text, "html.parser")
    for iframe in soup.find_all("iframe", src=True):
        origem = str(iframe.get("src", ""))
        if _IFRAME_FNET in origem:
            return urljoin(resposta.url, origem)
    return None


def baixar_conteudo(
    url: str,
    *,
    sessao: requests.Session | None = None,
    timeout: float = TIMEOUT,
    timeout_total: float | None = DOWNLOAD_TIMEOUT_S,
    prazo: _Prazo | None = None,
    validar: Callable[[requests.Response], bool] | None = None,
    transitorios_extra: frozenset[int] = frozenset(),
    seguir_iframe: bool = False,
    headers: Mapping[str, str] | None = None,
    cancelar: Callable[[], None] | None = None,
) -> requests.Response | None:
    """Baixa ``url`` com validação de conteúdo e orçamento total por item.

    Quando ``seguir_iframe`` é verdadeiro e a resposta não passa em ``validar``,
    segue o ``iframe`` (``exibirDocumento``) com ``Referer`` antes de nova
    tentativa. ``transitorios_extra`` declara códigos normalmente permanentes
    como repetíveis (ex.: ``403`` do FNET). Retorna ``None`` em falha de rede,
    conteúdo inválido, cancelamento ou orçamento esgotado.
    """
    sessao = sessao or requests.Session()
    prazo = prazo or _Prazo(timeout_total)
    cabecalhos = _cabecalhos(headers)
    valida = validar or (lambda _resposta: True)

    def _tentativa() -> requests.Response:
        resposta = _get(sessao, url, timeout, prazo, cabecalhos)
        if not seguir_iframe or valida(resposta):
            return resposta
        alvo = _url_do_iframe(resposta)
        if alvo is None:
            return resposta
        return _get(
            sessao, alvo, timeout, prazo, {**cabecalhos, "Referer": url}
        )

    try:
        return executar_com_retry(
            _tentativa,
            metodo="GET",
            transitorios_extra=transitorios_extra,
            delays=_delays(),
            cancelar=_checador(prazo, cancelar),
            validar=valida,
        )
    except OrcamentoEsgotado:
        logger.warning("Orçamento esgotado ao baixar %s", url)
        return None
    except requests.RequestException as exc:
        logger.warning("Falha ao baixar %s: %r", url, exc)
        return None
    except ConteudoInvalido as exc:
        logger.warning("Conteúdo inválido ao baixar %s: %s", url, exc)
        return None


def post_renovando_sessao(
    url_pagina: str,
    url_post: str,
    corpo: str,
    *,
    sessao: requests.Session | None = None,
    timeout: float = TIMEOUT,
    timeout_total: float | None = DOWNLOAD_TIMEOUT_S,
    prazo: _Prazo | None = None,
    validar: Callable[[requests.Response], bool] | None = None,
    inspectar_pagina: Callable[[requests.Response], bool] | None = None,
    transitorios_extra: frozenset[int] = frozenset(),
    headers: Mapping[str, str] | None = None,
    cancelar: Callable[[], None] | None = None,
) -> requests.Response | None:
    """Resolve um documento do visualizador da CVM RAD com renovação de sessão.

    Faz o GET da página (origem do token/sessão) e o POST ``ExibirPDF``. A cada
    falha do POST, refaz o GET antes de repetir, tudo sob o orçamento do item.
    ``inspectar_pagina``, quando informado, valida cada página obtida; retornar
    ``False`` aborta a resolução (ex.: captcha habilitado). Retorna ``None`` em
    falha de rede, conteúdo inválido, cancelamento ou orçamento esgotado.
    """
    sessao = sessao or requests.Session()
    prazo = prazo or _Prazo(timeout_total)
    cabecalhos = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Requested-With": "XMLHttpRequest",
        **_cabecalhos(headers),
    }
    valida = validar or (lambda _resposta: True)

    def _renovar_pagina() -> None:
        pagina = _get(sessao, url_pagina, timeout, prazo, _cabecalhos(headers))
        if inspectar_pagina is not None and not inspectar_pagina(pagina):
            raise PaginaRejeitada("página do visualizador rejeitada")

    def _tentativa() -> requests.Response:
        _renovar_pagina()
        if prazo.esgotado():
            raise OrcamentoEsgotado(_MOTIVO_ORCAMENTO)
        resposta = sessao.post(
            url_post,
            data=corpo,
            timeout=prazo.efetivo(timeout),
            headers={**cabecalhos, "Referer": url_pagina},
        )
        resposta.raise_for_status()
        return resposta

    try:
        return executar_com_retry(
            _tentativa,
            metodo="POST",
            repetivel=True,
            transitorios_extra=transitorios_extra,
            delays=_delays(),
            cancelar=_checador(prazo, cancelar),
            validar=valida,
        )
    except PaginaRejeitada:
        logger.info("Página do visualizador da CVM rejeitada: %s", url_pagina)
        return None
    except OrcamentoEsgotado:
        logger.warning("Orçamento esgotado ao resolver PDF da CVM em %s", url_post)
        return None
    except requests.RequestException as exc:
        logger.warning("Falha ao resolver PDF da CVM em %s: %r", url_post, exc)
        return None
    except ConteudoInvalido as exc:
        logger.warning("Conteúdo inválido da CVM em %s: %s", url_post, exc)
        return None


__all__ = [
    "DOWNLOAD_TIMEOUT_S",
    "ESPERA",
    "TENTATIVAS",
    "TIMEOUT",
    "OrcamentoEsgotado",
    "PaginaRejeitada",
    "_Prazo",
    "baixar_conteudo",
    "post_renovando_sessao",
    "validar_html",
    "validar_pdf",
]
