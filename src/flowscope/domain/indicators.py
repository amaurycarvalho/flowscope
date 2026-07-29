from flowscope.domain.engine import IndicatorEngine
from flowscope.domain.strategies import (
    AverageFinancialTicketStrategy,
    AverageTradeSizeStrategy,
    BuyingPressureStrategy,
    CLVStrategy,
    DailyEfficiencyStrategy,
    DailyMoneyFlowStrategy,
    DominanceScoreStrategy,
    FinancialDensityStrategy,
    MedianPriceStrategy,
    MoneyFlowMultiplierStrategy,
    MoneyFlowVolumeStrategy,
    RangePercentualStrategy,
    RangeStrategy,
    SellingPressureStrategy,
    TopTickersStrategy,
    TradeDensityStrategy,
    TypicalPriceStrategy,
    VolumeDensityStrategy,
    VolumeProfileStrategy,
    VWAPDistanceStrategy,
    VWAPStrategy,
    WeightedCloseStrategy,
)


def default_engine(tick_size: float = 0.01, top_n: int = 15) -> IndicatorEngine:
    engine = IndicatorEngine()
    engine.register(
        RangeStrategy(),
        TypicalPriceStrategy(),
        MedianPriceStrategy(),
        WeightedCloseStrategy(),
        CLVStrategy(),
        MoneyFlowMultiplierStrategy(),
        BuyingPressureStrategy(),
        SellingPressureStrategy(),
        MoneyFlowVolumeStrategy(),
        AverageTradeSizeStrategy(),
        AverageFinancialTicketStrategy(),
        RangePercentualStrategy(),
        DailyEfficiencyStrategy(),
        DailyMoneyFlowStrategy(),
        DominanceScoreStrategy(),
        FinancialDensityStrategy(),
        TradeDensityStrategy(),
        VolumeDensityStrategy(),
        VWAPDistanceStrategy(),
        VWAPStrategy(),
        VolumeProfileStrategy(tick_size),
        TopTickersStrategy(top_n),
    )
    return engine
