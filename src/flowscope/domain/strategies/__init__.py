"""Subpacote com as estratégias de indicadores do FlowScope."""

from flowscope.domain.strategies.base import IndicatorStrategy
from flowscope.domain.strategies.daily_money_flow import DailyMoneyFlowStrategy
from flowscope.domain.strategies.density import (
    FinancialDensityStrategy,
    TradeDensityStrategy,
    VolumeDensityStrategy,
)
from flowscope.domain.strategies.dominance_score import DominanceScoreStrategy
from flowscope.domain.strategies.efficiency import DailyEfficiencyStrategy
from flowscope.domain.strategies.flow import (
    BuyingPressureStrategy,
    CLVStrategy,
    MoneyFlowMultiplierStrategy,
    MoneyFlowVolumeStrategy,
    SellingPressureStrategy,
)
from flowscope.domain.strategies.price import (
    MedianPriceStrategy,
    RangePercentualStrategy,
    RangeStrategy,
    TypicalPriceStrategy,
    WeightedCloseStrategy,
)
from flowscope.domain.strategies.size import (
    AverageFinancialTicketStrategy,
    AverageTradeSizeStrategy,
)
from flowscope.domain.strategies.volume import (
    TopTickersStrategy,
    VolumeProfileStrategy,
    VWAPStrategy,
)
from flowscope.domain.strategies.vwap_distance import VWAPDistanceStrategy

__all__ = [
    "AverageFinancialTicketStrategy",
    "AverageTradeSizeStrategy",
    "BuyingPressureStrategy",
    "CLVStrategy",
    "DailyEfficiencyStrategy",
    "DailyMoneyFlowStrategy",
    "DominanceScoreStrategy",
    "FinancialDensityStrategy",
    "IndicatorStrategy",
    "MedianPriceStrategy",
    "MoneyFlowMultiplierStrategy",
    "MoneyFlowVolumeStrategy",
    "RangePercentualStrategy",
    "RangeStrategy",
    "SellingPressureStrategy",
    "TopTickersStrategy",
    "TradeDensityStrategy",
    "TypicalPriceStrategy",
    "VWAPDistanceStrategy",
    "VWAPStrategy",
    "VolumeDensityStrategy",
    "VolumeProfileStrategy",
    "WeightedCloseStrategy",
]
