"""Cliente HTTP do Plantão de Notícias da B3 e do visualizador da CVM.

Consulta as notícias mês a mês, resolve o documento na página ``Detail`` e
baixa o PDF via POST ``ExibirPDF`` (JSON com base64), validando a assinatura
``%PDF``.
"""

import logging
from datetime import date

import requests

from flowscope.infrastructure.b3.bdr.constants import (
    AGENCIA,
    DETAIL_URL,
    NOTICIAS_URL,
)
from flowscope.infrastructure.b3.bdr.documents import (
    id_protocolo,
    resolver_url_documento,
)
from flowscope.infrastructure.b3.bdr.news import itens_de_noticias
from flowscope.infrastructure.cvm.pdf import baixar_pdf_cvm
from flowscope.infrastructure.http_retry import executar_com_retry

logger = logging.getLogger(__name__)

_TIMEOUT = 30


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
        resposta = executar_com_retry(
            lambda: self._get(NOTICIAS_URL, params=parametros),
            metodo="GET",
        )
        return itens_de_noticias(resposta.json())

    def buscar_detalhe(
        self: "BdrClient", id_noticia: str, data_noticia: date
    ) -> str:
        """Baixa a página ``Detail`` da notícia informada."""
        resposta = executar_com_retry(
            lambda: self._get(
                DETAIL_URL,
                params={
                    "agencia": AGENCIA,
                    "idNoticia": id_noticia,
                    "dataNoticia": data_noticia.isoformat(),
                },
            ),
            metodo="GET",
        )
        return resposta.text

    def _get(self: "BdrClient", url: str, **kwargs: object) -> requests.Response:
        """Executa um GET na sessão, propagando o erro HTTP para o motor."""
        resposta = self._session.get(url, timeout=self._timeout, **kwargs)
        resposta.raise_for_status()
        return resposta

    def baixar_pdf(self: "BdrClient", numero_protocolo: str) -> bytes | None:
        """Baixa e decodifica o PDF do documento, ou ``None`` quando inválido."""
        return baixar_pdf_cvm(
            numero_protocolo, session=self._session, timeout=self._timeout
        )

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
