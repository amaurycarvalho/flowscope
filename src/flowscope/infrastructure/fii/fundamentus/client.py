"""Cliente HTTP do Fundamentus com rate-limit e respeito ao robots.txt."""

import time
import urllib.robotparser
from collections.abc import Callable
from typing import Any

import requests

from .errors import NetworkError, TickerNotFound

BASE_URL = "https://www.fundamentus.com.br/detalhes.php"
ROBOTS_URL = "https://www.fundamentus.com.br/robots.txt"
USER_AGENT = "FlowScope/1.0"
DEFAULT_TIMEOUT = 15.0
DEFAULT_RATE_LIMIT_S = 1.0

_PISTAS_NAO_ENCONTRADO = ("nenhum papel encontrado", "não encontrado")


class FundamentusClient:
    """Baixa páginas do Fundamentus respeitando rate-limit e robots.txt."""

    def __init__(
        self: "FundamentusClient",
        timeout: float = DEFAULT_TIMEOUT,
        rate_limit_s: float = DEFAULT_RATE_LIMIT_S,
        session: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
        robot_parser: urllib.robotparser.RobotFileParser | None = None,
        respect_robots: bool = True,
    ) -> None:
        """Inicializa o cliente com timeout, rate-limit e política de robots."""
        self._timeout = timeout
        self._rate_limit_s = rate_limit_s
        self._session = session or requests.Session()
        self._sleep = sleep
        self._robot_parser = robot_parser
        self._respect_robots = respect_robots
        self._ultima_requisicao = 0.0

    def fetch(self: "FundamentusClient", ticker: str) -> str:
        """Baixa a página de detalhes do ticker, sinalizando erros tipados."""
        return self.fetch_response(ticker).text

    def fetch_response(
        self: "FundamentusClient",
        ticker: str,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> requests.Response:
        """Baixa a página, opcionalmente condicional, devolvendo a resposta HTTP.

        Quando ``etag``/``last_modified`` são informados, envia os cabeçalhos
        condicionais e não trata ``304 Not Modified`` como erro.
        """
        if self._respect_robots and not self._pode_acessar(BASE_URL):
            raise NetworkError("Acesso bloqueado pelo robots.txt do Fundamentus")
        self._respeitar_limite()
        headers = {"User-Agent": USER_AGENT}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        try:
            resposta = self._session.get(
                BASE_URL,
                params={"papel": ticker.strip().upper()},
                timeout=self._timeout,
                headers=headers,
            )
            if resposta.status_code != 304:
                resposta.raise_for_status()
        except requests.RequestException as erro:
            raise NetworkError(str(erro)) from erro
        self._ultima_requisicao = time.monotonic()
        if resposta.status_code != 304:
            texto = resposta.text
            if any(pista in texto.lower() for pista in _PISTAS_NAO_ENCONTRADO):
                raise TickerNotFound(f"Ticker '{ticker}' não encontrado no Fundamentus")
        return resposta

    def _respeitar_limite(self: "FundamentusClient") -> None:
        """Aguarda o intervalo mínimo entre requisições, se necessário."""
        if self._rate_limit_s <= 0:
            return
        decorrido = time.monotonic() - self._ultima_requisicao
        if self._ultima_requisicao and decorrido < self._rate_limit_s:
            self._sleep(self._rate_limit_s - decorrido)

    def _pode_acessar(self: "FundamentusClient", url: str) -> bool:
        """Verifica o robots.txt, liberando o acesso quando indisponível."""
        parser = self._obter_robot_parser()
        if parser is None:
            return True
        return parser.can_fetch(USER_AGENT, url)

    def _obter_robot_parser(
        self: "FundamentusClient",
    ) -> urllib.robotparser.RobotFileParser | None:
        """Carrega e memoriza o robots.txt, tolerando indisponibilidade."""
        if self._robot_parser is not None:
            return self._robot_parser
        parser = urllib.robotparser.RobotFileParser()
        try:
            resposta = self._session.get(
                ROBOTS_URL, timeout=self._timeout, headers={"User-Agent": USER_AGENT}
            )
            resposta.raise_for_status()
        except requests.RequestException:
            self._robot_parser = None
            return None
        parser.parse(resposta.text.splitlines())
        self._robot_parser = parser
        return parser
