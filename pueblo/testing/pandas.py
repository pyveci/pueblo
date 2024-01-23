import numpy as np
import pandas as pd


def makeTimeDataFrame(nper=None, freq="B") -> pd.DataFrame:
    """
    pandas 2.2.0 removed `pandas._testing.makeTimeDataFrame`.

    TST/CLN: Remove makeTime methods
    https://github.com/pandas-dev/pandas/pull/56264

    :param nper:
    :param freq:
    :return:
    """
    return pd.DataFrame(
        np.random.default_rng(2).standard_normal((nper, 4)),
        columns=pd.Index(list("ABCD"), dtype=object),
        index=pd.date_range("2000-01-01", periods=nper, freq=freq),
    )
