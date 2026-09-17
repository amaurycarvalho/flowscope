"""Cliente HTTP do Plantão de Notícias da B3 e do visualizador da CVM.

Consulta as notícias mês a mês, resolve o documento na página ``Detail`` e
baixa o PDF via POST ``ExibirPDF`` (JSON com base64), validando a assinatura
``%PDF``.
"""

import json
import logging
from datetime import date

import requests

from flowscope.infrastructure.b3.bdr.constants import (
    AGENCIA,
    CODIGO_INSTITUICAO,
    CVM_PDF_URL,
    DETAIL_URL,
    NOTICIAS_URL,
)
from flowscope.infrastructure.b3.bdr.documents import (
    decodificar_pdf,
    id_protocolo,
    resolver_url_documento,
)
from flowscope.infrastructure.b3.bdr.news import itens_de_noticias

logger = logging.getLogger("flowscope")

_TIMEOUT = 30

_HEADERS_JSON = {"Content-Type": "application/json; charset=utf-8"}


class BdrClient:
    """Consulta o Plantão B3 e baixa PDFs de avisos aos acionistas de BDR."""

    def __init__(
        self: "BdrClient",
        session: requests.Session | None = None,
        timeout: int = _TIMEOUT,
    ) -> None:
        """Inicializa o cliente com a sessão HTTP e o timeout informados."""
        self._session = session or requests.Session()
        self._timeout = timeout

    def coletar_noticias(
        self: "BdrClient",
        agencia: str,
        palavra: str,
        inicio: date,
        fim: date,
    ) -> list[dict]:
        """Coleta os itens brutos de notícias de uma janela mensal."""
        parametros = {
            "agencia": agencia,
            "palavra": palavra,
            "dataInicial": inicio.isoformat(),
            "dataFinal": fim.isoformat(),
        }
        logger.info("Consultando %s", NOTICIAS_URL)
        resposta = self._session.get(
            NOTICIAS_URL, params=parametros, timeout=self._timeout
        )
        resposta.raise_for_status()
        return itens_de_noticias(resposta.json())

    def buscar_detalhe(
        self: "BdrClient", id_noticia: str, data_noticia: date
    ) -> str:
        """Baixa a página ``Detail`` da notícia informada."""
        resposta = self._session.get(
            DETAIL_URL,
            params={
                "agencia": AGENCIA,
                "idNoticia": id_noticia,
                "dataNoticia": data_noticia.isoformat(),
            },
            timeout=self._timeout,
        )
        resposta.raise_for_status()
        return resposta.text

    def baixar_pdf(self: "BdrClient", numero_protocolo: str) -> bytes | None:
        """Baixa e decodifica o PDF do documento, ou ``None`` quando inválido."""
        corpo = json.dumps(
            {
                "codigoInstituicao": CODIGO_INSTITUICAO,
                "numeroProtocolo": numero_protocolo,
                "token": "",
                "versaoCaptcha": "",
            }
        )
        try:
            resposta = self._session.post(
                CVM_PDF_URL,
                data=corpo,
                headers=_HEADERS_JSON,
                timeout=self._timeout,
            )
            resposta.raise_for_status()
            payload = resposta.json()
        except (requests.RequestException, ValueError):
            logger.warning(
                "Falha ao baixar PDF de aviso de BDR", exc_info=True
            )
            return None
        return decodificar_pdf(payload)

    def obter_pdf_de_aviso(
        self: "BdrClient", id_noticia: str, data_noticia: date
    ) -> bytes | None:
        """Resolve o documento do aviso e baixa o PDF correspondente."""
        try:
            html = self.buscar_detalhe(id_noticia, data_noticia)
        except requests.RequestException:
            logger.warning(
                "Falha ao resolver detalhe do aviso %s", id_noticia, exc_info=True
            )
            return None
        url = resolver_url_documento(html)
        if url is None:
            return None
        protocolo = id_protocolo(url)
        if protocolo is None:
            return None
        return self.baixar_pdf(protocolo)
