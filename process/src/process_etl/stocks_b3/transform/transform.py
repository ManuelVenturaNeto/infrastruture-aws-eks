from pathlib import Path

from library.process import Dag

from .utils.adjust_corporate_actions import AdjustCorporateActions
from .utils.filter_stocks import FilterStocks
from .utils.log_return import LogReturn
from .utils.moving_average import MovingAverage
from .utils.normalize_price import NormalizePrice
from .utils.return_zscore import ReturnZScore
from .utils.slow_stochastic import SlowStochastic
from .utils.trend_flags import TrendFlags
from .utils.volume_indicators import VolumeIndicators


def build_dag(events: Path) -> Dag:
    """
    Builds the transform DAG with notebook steps 5 to 12, in the original order.
    """
    return Dag(
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
