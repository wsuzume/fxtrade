import numpy as np
import pandas as pd

from datetime import timedelta
from scipy.stats import laplace

from typing import Callable, Optional, Tuple, Iterable

from .core import type_checked
from .utils import standardize
from .timeseries import split_into_chunks, normalize_time_index

def delta(ts: Iterable) -> pd.Timedelta:
    """
    Given an equally spaced time index, return the interval.
    """
    return pd.Series(ts).diff().value_counts().index[0]

def estimate_laplace_param(xs: pd.Series) -> Tuple[float, float]:
    """
    Return the maximum likelihood estimate of the parameters of Laplace distribution
    assuming that the input follows to it.
    First-order differences in currency price movements
    tend to follow a Laplace distribution. Especially in the case of Bitcoin.

    Parameters
    ----------
    xs : pandas.Series
        Contains any real-valued data considered to follow the Laplace distribution.
    """
    # loc = xs.median()    
    # scale = np.abs(xs - loc).mean()
    
    return laplace.fit(xs)

def estimate_brown_param(xs: pd.Series, return_dt: bool=False) -> float:
    """
    Return the scale parameter of Brownian motion assuming that the input follows to it.
    Unit time is 1 second.

    Parameters
    ----------
    xs : pandas.Series
        Contains any real-valued data considered to follow the Brownian motion.
    """
    _, scale = estimate_laplace_param(xs)

    dt = delta(xs.index)
    
    param = scale / np.sqrt(dt.total_seconds())

    if return_dt:
        return param, dt
    return param

def calc_brown_param(scale: float, dt: pd.Timedelta) -> float:
    """
    Return the variance of the Brownian motion at dt.

    Parameters
    ----------
    scale : float
        Any positive float value. Use estimate_brown_param to estimate this parameter.
    dt : pandas.Timedelta
        Any positive pandas.Timedelta.
    """
    return scale * np.sqrt(dt.total_seconds())

def brownianize(xs):
    return np.log10(xs).diff().dropna()

class Brownian:
    def __init__(self, ohlc: pd.DataFrame, dt: Optional[timedelta]=None):
        self._data = standardize(ohlc)
        self._dt = type_checked(dt, timedelta, optional=True)

        self._loc, self._scale = None, None

        self._t = 0
    
    def __repr__(self):
        return f"Brownian(dt={self._dt}, loc={self._loc}, scale={self._scale})"
    
    @property
    def begin(self):
        return self._data.index.min()
    
    @property
    def end(self):
        return self._data.index.max()
    
    def iterate(self):
        return self._data.iterrows()
    
    def reset_tick(self):
        self._t = 0

    def tick(self):
        if self._t >= len(self._data):
            return None
        ret = self._data.iloc[self._t].copy()
        self._t += 1
        return ret

    def fit(self, dropna_subset=None):
        dt = delta(self._data.index)
        if (self._dt is not None) and (dt != self._dt):
            raise ValueError(f"specified dt not match with estimated dt with ohlc.")
        
        xs = split_into_chunks(self._data.dropna(subset=dropna_subset))

        ys = [ brownianize(x['open']).values for x in xs ]

        vs = np.concatenate(ys)

        loc, scale = laplace.fit(vs)

        self._dt = dt
        self._loc = loc
        self._scale = scale / np.sqrt(dt.total_seconds())

        return self
    
    def transform(self):
        self._data = normalize_time_index(self._data, self.begin, self.end, self._dt)

        return self
