from library.process import Pipeline

from .utils.adjust_corporate_actions import AdjustCorporateActions
from .utils.filter_stocks import FilterStocks
from .utils.log_return import LogReturn
from .utils.moving_average import MovingAverage
from .utils.normalize_price import NormalizePrice
from .utils.return_zscore import ReturnZScore
from .utils.slow_stochastic import SlowStochastic
from .utils.trend_flags import TrendFlags
from .utils.volume_indicators import VolumeIndicators


def build_pipeline(events: str) -> Pipeline:

    return Pipeline(
        [
            FilterStocks(),
            NormalizePrice(),
            AdjustCorporateActions(events),
            LogReturn(),
            ReturnZScore(),
            SlowStochastic(),
            MovingAverage(),
            TrendFlags(),
            VolumeIndicators(),
        ]
    )
