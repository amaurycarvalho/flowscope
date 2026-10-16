"""Política central de tratamento de erros HTTP e motor de retry comum.

Classifica todo status de resposta em quatro categorias (:class:`Categoria`) e
oferece :func:`executar_com_retry`, o motor único usado pelos acessos de rede
de leitura/download do FlowScope. O motor repete apenas categorias repetíveis
(``THROTTLE``, ``TRANSITORIO``, ``GATEWAY``) e apenas métodos idempotentes — ou
POSTs de leitura explicitamente marcados — honra ``Retry-After`` com teto,
aplica backoff com jitter e oferece um gancho de cancelamento.

Probes de cache condicional (que interpretam 304/403/404 como estado de
validação) e o provedor de LLM NÃO usam este motor.
"""

from __future__ import annotations

import enum
import logging
import random
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import TypeVar

import requests

logger = logging.getLogger(__name__)

#: Intervalos de espera (em segundos) antes de cada tentativa repetível.
RETRY_DELAYS: tuple[float, ...] = (0, 1, 3, 10)

#: Backoff base maior usado pelas respostas ``GATEWAY`` (520–524).
RETRY_DELAYS_GATEWAY: tuple[float, ...] = (0, 2, 6, 18)

#: Teto (em segundos) da espera indicada por ``Retry-After``.
ESPERA_MAXIMA_S = 60.0

#: Métodos HTTP considerados idempotentes e, portanto, repetíveis.
METODOS_IDEMPOTENTES = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})

#: Códigos 4xx transitórios (o restante do 4xx é permanente).
_TRANSITORIOS_4XX = frozenset({408, 425})

#: Códigos 5xx permanentes (o restante do 5xx é transitório).
_PERMANENTES_5XX = frozenset({501, 505, 506, 511})

#: Códigos de erro de origem atrás de Cloudflare, tratados como gateway.
_GATEWAY = frozenset({520, 521, 522, 523, 524})

T = TypeVar("T")


class Categoria(enum.Enum):
    """Categoria de tratamento de um status HTTP."""

    PERMANENTE = "permanente"
    THROTTLE = "throttle"
    TRANSITORIO = "transitorio"
    GATEWAY = "gateway"


class ConteudoInvalido(Exception):
    """Conteúdo baixado não corresponde ao esperado após as tentativas."""

    def __init__(self: ConteudoInvalido, tentativas: int) -> None:
        """Registra o número de tentativas consumidas sem conteúdo válido."""
        super().__init__(
            f"conteúdo inválido após {tentativas} tentativa(s)"
        )
        self.tentativas = tentativas


def _sleep_padrao(segundos: float) -> None:
    """Espera padrão entre tentativas, isolada para injeção nos testes."""
    time.sleep(segundos)


def _header(headers: Mapping[str, str] | None, nome: str) -> str | None:
    """Lê um cabeçalho de forma tolerante a maiúsculas/minúsculas."""
    if not headers:
        return None
    if nome in headers:
        return headers[nome]
    alvo = nome.lower()
    for chave, valor in headers.items():
        if str(chave).lower() == alvo:
            return valor
    return None


def _tem_retry_after(headers: Mapping[str, str] | None) -> bool:
    """Indica se a resposta traz o cabeçalho ``Retry-After``."""
    return _header(headers, "Retry-After") is not None


def classificar(
    status: int, headers: Mapping[str, str] | None = None
) -> Categoria:
    """Classifica um status HTTP em exatamente uma :class:`Categoria`.

    Regra de default: todo ``4xx`` é ``PERMANENTE`` (exceto 408/425 e 429) e
    todo ``5xx`` é ``TRANSITORIO`` (exceto 501/505/506/511). Os códigos
    520–524 são ``GATEWAY`` e o 503 é ``THROTTLE`` quando traz ``Retry-After``.
    """
    status = int(status)
    if status in _GATEWAY:
        return Categoria.GATEWAY
    if status == 429:
        return Categoria.THROTTLE
    if status == 503:
        return (
            Categoria.THROTTLE
            if _tem_retry_after(headers)
            else Categoria.TRANSITORIO
        )
    if 400 <= status < 500:
        return (
            Categoria.TRANSITORIO
            if status in _TRANSITORIOS_4XX
            else Categoria.PERMANENTE
        )
    if 500 <= status < 600:
        return (
            Categoria.PERMANENTE
            if status in _PERMANENTES_5XX
            else Categoria.TRANSITORIO
        )
    return Categoria.PERMANENTE


def _retry_after_segundos(headers: Mapping[str, str] | None) -> float | None:
    """Interpreta ``Retry-After`` (segundos ou data HTTP) como segundos."""
    valor = _header(headers, "Retry-After")
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    try:
        return max(0.0, float(texto))
    except ValueError:
        pass
    try:
        data = parsedate_to_datetime(texto)
    except (TypeError, ValueError):
        return None
    if data is None:
        return None
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)
    delta = (data - datetime.now(timezone.utc)).total_seconds()
    return max(0.0, delta)


def _dados_da_excecao(
    exc: requests.RequestException,
) -> tuple[int | None, Mapping[str, str] | None]:
    """Extrai ``(status, headers)`` da resposta embutida na exceção, se houver."""
    resposta = getattr(exc, "response", None)
    status = getattr(resposta, "status_code", None)
    headers = getattr(resposta, "headers", None)
    return status, headers


def _classificar_excecao(
    exc: requests.RequestException,
    transitorios_extra: frozenset[int],
) -> tuple[Categoria, int | None, Mapping[str, str] | None]:
    """Deriva ``(categoria, status, headers)`` de uma exceção de requisição.

    Erros de rede sem resposta HTTP são repetíveis. Um ``HTTPError`` sem
    resposta associada é tratado como permanente, para não repetir erros de
    protocolo sem status conhecido.
    """
    status, headers = _dados_da_excecao(exc)
    if status is None:
        categoria = (
            Categoria.PERMANENTE
            if isinstance(exc, requests.HTTPError)
            else Categoria.TRANSITORIO
        )
    else:
        categoria = classificar(status, headers)
        if categoria is Categoria.PERMANENTE and status in transitorios_extra:
            categoria = Categoria.TRANSITORIO
    return categoria, status, headers


def _metodo_repetivel(metodo: str, repetivel: bool | None) -> bool:
    """Indica se o método pode ser repetido automaticamente."""
    if repetivel is not None:
        return bool(repetivel)
    return str(metodo).upper() in METODOS_IDEMPOTENTES


def _registrar(
    categoria: Categoria,
    status: int | None,
    indice: int,
    total: int,
) -> None:
    """Registra o descarte de uma repetição ou o esgotamento das tentativas."""
    motivo = (
        "categoria permanente"
        if categoria is Categoria.PERMANENTE
        else "tentativas esgotadas"
    )
    logger.warning(
        "HTTP %s classificado como %s (%s) após %d/%d tentativa(s); "
        "sem nova repetição",
        status,
        categoria.value,
        motivo,
        indice + 1,
        total,
    )


def _registrar_conteudo(indice: int, total: int) -> None:
    """Registra o esgotamento das tentativas por conteúdo inválido."""
    logger.warning(
        "Conteúdo inválido após %d/%d tentativa(s); sem nova repetição",
        indice + 1,
        total,
    )


def _espera(
    categoria: Categoria,
    headers: Mapping[str, str] | None,
    proxima: int,
    delays: Sequence[float],
    gateway_delays: Sequence[float],
    jitter: Callable[[], float],
) -> float:
    """Calcula a espera antes da próxima tentativa.

    Em ``THROTTLE`` com ``Retry-After``, usa o valor indicado limitado ao teto.
    Caso contrário aplica o backoff base (maior em ``GATEWAY``) com jitter.
    """
    if categoria is Categoria.THROTTLE:
        indicado = _retry_after_segundos(headers)
        if indicado is not None:
            return min(indicado, ESPERA_MAXIMA_S)
    base_seq = gateway_delays if categoria is Categoria.GATEWAY else delays
    if not base_seq:
        base_seq = delays or RETRY_DELAYS
    base = base_seq[min(proxima, len(base_seq) - 1)]
    return base * (1 + jitter())


def _aguardar(
    segundos: float,
    dormir: Callable[[float], None],
    cancelar: Callable[[], None] | None,
) -> None:
    """Chama o gancho de cancelamento e aguarda o intervalo informado."""
    if cancelar is not None:
        cancelar()
    if segundos > 0:
        dormir(segundos)


def executar_com_retry(
    fn: Callable[[], T],
    *,
    metodo: str = "GET",
    repetivel: bool | None = None,
    transitorios_extra: frozenset[int] = frozenset(),
    delays: Sequence[float] = RETRY_DELAYS,
    sleep: Callable[[float], None] | None = None,
    jitter: Callable[[], float] | None = None,
    cancelar: Callable[[], None] | None = None,
    validar: Callable[[T], bool] | None = None,
) -> T:
    """Executa ``fn`` repetindo erros repetíveis conforme a política de status.

    Repete ``THROTTLE``, ``TRANSITORIO`` e ``GATEWAY`` (e erros de rede sem
    resposta) até ``len(delays)`` tentativas, apenas para métodos idempotentes
    ou quando ``repetivel=True``. ``transitorios_extra`` declara códigos
    normalmente permanentes como repetíveis neste ponto de chamada. ``sleep`` e
    ``jitter`` são injetáveis; ``cancelar`` pode levantar para interromper a
    espera entre tentativas.

    ``validar``, quando informado, inspeciona o resultado de ``fn``: um
    resultado que não passar na validação é tratado como tentativa repetível
    (categoria transitória) e consome o orçamento de tentativas; esgotado o
    orçamento sem resultado válido, levanta :class:`ConteudoInvalido`.
    """
    dormir, aleatorio, valida = _controles(sleep, jitter, validar)

    if not _metodo_repetivel(metodo, repetivel):
        return fn()

    sequencia = tuple(delays) or (0.0,)
    total = len(sequencia)
    indice = 0
    while True:
        if cancelar is not None:
            cancelar()
        try:
            resultado = fn()
        except requests.RequestException as exc:
            categoria, status, headers = _classificar_excecao(
                exc, transitorios_extra
            )
            if categoria is Categoria.PERMANENTE or indice >= total - 1:
                _registrar(categoria, status, indice, total)
                raise
            indice += 1
            _aguardar(
                _espera(
                    categoria, headers, indice, sequencia, RETRY_DELAYS_GATEWAY, aleatorio
                ),
                dormir,
                cancelar,
            )
            continue
        if valida(resultado):
            return resultado
        if indice >= total - 1:
            _registrar_conteudo(indice, total)
            raise ConteudoInvalido(total)
        indice += 1
        _aguardar(
            _espera(
                Categoria.TRANSITORIO,
                None,
                indice,
                sequencia,
                RETRY_DELAYS_GATEWAY,
                aleatorio,
            ),
            dormir,
            cancelar,
        )


def _sempre_valido(_resultado: object) -> bool:
    """Validador padrão: aceita qualquer resultado."""
    return True


def _controles(
    sleep: Callable[[float], None] | None,
    jitter: Callable[[], float] | None,
    validar: Callable[[T], bool] | None,
) -> tuple[Callable[[float], None], Callable[[], float], Callable[[T], bool]]:
    """Resolve os ganchos injetáveis com seus valores padrão."""
    dormir = sleep if sleep is not None else _sleep_padrao
    aleatorio = jitter if jitter is not None else random.random
    valida = validar if validar is not None else _sempre_valido
    return dormir, aleatorio, valida
