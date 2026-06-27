from decimal import Decimal

from flowscope.domain.indicators import (
    calculate_cvd,
    calculate_volume_profile,
    calculate_vwap,
    select_top_tickers,
)


class TestCalculateVWAP:
    def test_single_ticker(self, mock_trades):
        petr4_trades = [t for t in mock_trades if t.ticker.value == "PETR4"]
        result = calculate_vwap(petr4_trades)
        assert "PETR4" in result
        vwap_val = result["PETR4"]["period_vwap"]
        total_price_vol = (
            Decimal("28.80") * Decimal("432000")
            + Decimal("28.40") * Decimal("340800")
        )
        total_vol = Decimal("432000") + Decimal("340800")
        expected = total_price_vol / total_vol
        assert vwap_val == expected

    def test_multi_ticker(self, mock_trades):
        result = calculate_vwap(mock_trades)
        assert "PETR4" in result
        assert "VALE3" in result

    def test_empty(self):
        assert calculate_vwap([]) == {}


class TestCalculateCVD:
    def test_cvd_positive(self, mock_trades):
        petr4_trades = [t for t in mock_trades if t.ticker.value == "PETR4"]
        result = calculate_cvd(petr4_trades)
        assert "PETR4" in result
        cvd = result["PETR4"]["accumulated_cvd"]
        assert cvd > 0

    def test_cvd_vale3(self, mock_trades):
        vale3_trades = [t for t in mock_trades if t.ticker.value == "VALE3"]
        result = calculate_cvd(vale3_trades)
        assert "VALE3" in result

    def test_empty(self):
        assert calculate_cvd([]) == {}


class TestCalculateVolumeProfile:
    def test_single_ticker(self, mock_trades):
        trades = [t for t in mock_trades if t.ticker.value == "PETR4"]
        result = calculate_volume_profile(trades, 0.01)
        assert "PETR4" in result
        profile = result["PETR4"]
        assert len(profile) > 0
        total_distributed = sum(profile.values(), Decimal("0"))
        total_fin_vol = (
            Decimal("432000") + Decimal("340800")
        )
        assert total_distributed == total_fin_vol

    def test_empty(self):
        assert calculate_volume_profile([], 0.01) == {}


class TestSelectTopTickers:
    def test_top_n(self, mock_trades):
        result = select_top_tickers(mock_trades, n=1)
        assert len(result) == 1

    def test_all_when_less_than_n(self, mock_trades):
        result = select_top_tickers(mock_trades, n=10)
        assert len(result) == 2
