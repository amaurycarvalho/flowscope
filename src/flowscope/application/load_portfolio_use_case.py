from collections.abc import Callable

from flowscope.application.ports import DataRepository


class PortfolioNotFoundError(Exception):
    pass


class InvalidIndexError(Exception):
    pass


VALID_INDICES = {"IBOV", "IDIV", "IFIX"}


class LoadIndexPortfolioUseCase:
    def __init__(self, repository: DataRepository):
        self._repository = repository

    def execute(
        self, index: str,
        progress_callback: Callable[[str, bool], None] | None = None,
    ) -> list[str]:
        if index not in VALID_INDICES:
            raise InvalidIndexError(
                f"Invalid index: {index}. Valid indices: {', '.join(sorted(VALID_INDICES))}"
            )

        tickers = self._repository.get_index_tickers(
            index, progress_callback=progress_callback,
        )

        if not tickers:
            raise PortfolioNotFoundError(
                f"Não foi possível carregar a carteira {index}."
            )

        return tickers
