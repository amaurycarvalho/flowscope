"""Caso de uso para carregamento da carteira de um índice da B3."""

from collections.abc import Callable

from flowscope.application.cancellation import CancellationToken
from flowscope.application.ports import DataRepository


class PortfolioNotFoundError(Exception):
    """Erro quando não é possível obter a carteira do índice informado."""


class InvalidIndexError(Exception):
    """Erro quando o índice informado não é suportado."""


VALID_INDICES = {"IBOV", "IDIV", "IFIX"}


class LoadIndexPortfolioUseCase:
    """Carrega a lista de tickers da carteira de um índice da B3."""

    def __init__(self: "LoadIndexPortfolioUseCase", repository: DataRepository) -> None:
        """Inicializa o caso de uso com o repositório de dados."""
        self._repository = repository

    def execute(
        self: "LoadIndexPortfolioUseCase", index: str,
        progress_callback: Callable[[str, bool], None] | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> list[str]:
        """Valida o índice e retorna os tickers da carteira, informando o progresso via callback."""
        if index not in VALID_INDICES:
            raise InvalidIndexError(
                f"Invalid index: {index}. Valid indices: {', '.join(sorted(VALID_INDICES))}"
            )

        _checar(cancel_token)
        tickers = self._repository.get_index_tickers(
            index, progress_callback=progress_callback, cancel_token=cancel_token,
        )
        _checar(cancel_token)

        if not tickers:
            raise PortfolioNotFoundError(
                f"Não foi possível carregar a carteira {index}."
            )

        return tickers


def _checar(cancel_token: CancellationToken | None) -> None:
    """Lança ``OperacaoCancelada`` quando o cancelamento foi solicitado."""
    if cancel_token is not None:
        cancel_token.raise_if_cancelled()
