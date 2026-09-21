from pyspark.sql import Column, Window, WindowSpec
from pyspark.sql import functions as F


def by_ticker() -> WindowSpec:
    """
    Base window: partitioned by ticker and ordered by trade date.
    """
    return Window.partitionBy("ticker").orderBy("trade_date")


def array_median(values: Column | str) -> Column:
    """
    Exact median of a numeric array; null when the array is empty.
        Sorts the array, takes the two middle elements and averages them.
    """
    ordered = F.array_sort(values)
    size = F.size(ordered)
    lower = F.try_element_at(ordered, F.floor((size + 1) / 2).cast("int"))
    upper = F.try_element_at(ordered, F.ceil((size + 1) / 2).cast("int"))
    return F.when(size > 0, (lower + upper) / 2)
