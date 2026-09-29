from unittest.mock import MagicMock

import pytest

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.application.load_portfolio_use_case import (
    InvalidIndexError,
    LoadIndexPortfolioUseCase,
    PortfolioNotFoundError,
)


class TestLoadIndexPortfolioUseCase:
    def test_indice_valido_retorna_tickers(self):
        repo = MagicMock()
        repo.get_index_tickers.return_value = ["PETR4", "VALE3"]
        uc = LoadIndexPortfolioUseCase(repo)
        result = uc.execute("IBOV")
        assert result == ["PETR4", "VALE3"]

    def test_indice_invalido_levanta_error(self):
        repo = MagicMock()
        uc = LoadIndexPortfolioUseCase(repo)
        with pytest.raises(InvalidIndexError):
            uc.execute("INVALIDO")

    def test_portfolio_vazio_levanta_not_found(self):
        repo = MagicMock()
        repo.get_index_tickers.return_value = []
        uc = LoadIndexPortfolioUseCase(repo)
        with pytest.raises(PortfolioNotFoundError):
            uc.execute("IBOV")

    def test_executa_repassa_progress_callback(self):
        repo = MagicMock()
        repo.get_index_tickers.return_value = ["PETR4"]
        uc = LoadIndexPortfolioUseCase(repo)
        cb = MagicMock()
        uc.execute("IBOV", progress_callback=cb)
        repo.get_index_tickers.assert_called_once_with(
            "IBOV", progress_callback=cb, cancel_token=None,
        )

    def test_executa_repassa_cancel_token(self):
        repo = MagicMock()
        repo.get_index_tickers.return_value = ["PETR4"]
        uc = LoadIndexPortfolioUseCase(repo)
        token = CancellationToken()
        uc.execute("IBOV", cancel_token=token)
        repo.get_index_tickers.assert_called_once_with(
            "IBOV", progress_callback=None, cancel_token=token,
        )

    def test_cancelamento_antes_de_buscar_levanta(self):
        repo = MagicMock()
        uc = LoadIndexPortfolioUseCase(repo)
        token = CancellationToken()
        token.request()
        with pytest.raises(OperacaoCancelada):
            uc.execute("IBOV", cancel_token=token)
        repo.get_index_tickers.assert_not_called()
