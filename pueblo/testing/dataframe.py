import logging
import random
import typing as t
from collections import OrderedDict
from inspect import signature

import pandas as pd
from pandas._testing import makeMixedDataFrame, makeTimeDataFrame
from pandas.io.formats.info import DataFrameInfo

logger = logging.getLogger(__name__)


default_rows_count = 150_000


class DataFrameFactory:
    """
    Create dataframes for testing purposes.
    """

    def __init__(self, rows: int = default_rows_count, columns: int = 99):
        self.rows = int(rows)
        self.columns = int(columns)

    def make(self, which: str, **options) -> pd.DataFrame:
        fun: t.Callable = getattr(self, f"make_{which}")
        sig = signature(fun)

        kwargs = OrderedDict()
        if "rows" in sig.parameters:
            kwargs["rows"] = self.rows
        if "columns" in sig.parameters:
            kwargs["columns"] = self.columns

        logger.info("Creating data frame")
        df = fun(**kwargs)  # noqa: PD901

        # Debug
        df.info()
        info = DataFrameInfo(data=df)
        logger.info(f"Memory usage: {info.memory_usage_string.strip()}")

        return df

    @staticmethod
    def make_dummy() -> pd.DataFrame:
        records = [{"foo": "baz", "bar": "qux"}]
        return pd.DataFrame.from_records(records)

    @staticmethod
    def make_mixed() -> pd.DataFrame:
        return makeMixedDataFrame()

    def make_dateindex(self) -> pd.DataFrame:
        return makeTimeDataFrame(nper=self.rows, freq="S")

    @staticmethod
    def make_wide(rows: int = default_rows_count, columns: int = 99) -> pd.DataFrame:
        """
        https://github.com/influxdata/influxdb-client-python/blob/master/examples/ingest_large_dataframe.py
        """
        import numpy as np

        col_data: t.Dict[str, t.Any] = {
            "time": np.arange(0, rows, 1, dtype=int),
            "tag": np.random.choice(["tag_a", "tag_b", "test_c"], size=(rows,)),
        }
        for n in range(2, columns + 1):
            col_data[f"col{n}"] = random.randint(1, 10)  # noqa: S311

        return pd.DataFrame(data=col_data).set_index("time")
