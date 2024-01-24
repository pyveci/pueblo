import typing as t

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


def getMixedTypeDict() -> t.Tuple[pd.Index, t.Dict[str, t.Any]]:
    index = pd.Index(["a", "b", "c", "d", "e"])

    data = {
        "A": [0.0, 1.0, 2.0, 3.0, 4.0],
        "B": [0.0, 1.0, 0.0, 1.0, 0.0],
        "C": ["foo1", "foo2", "foo3", "foo4", "foo5"],
        "D": pd.bdate_range("1/1/2009", periods=5),
    }

    return index, data


def makeMixedDataFrame() -> pd.DataFrame:
    return pd.DataFrame(getMixedTypeDict()[1])
