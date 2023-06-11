# """Basic analysis tools for FX trade.
# """

import numpy as np
import pandas as pd
import warnings

import plotly.graph_objects as go
from matplotlib import pyplot as plt
from scipy.stats import laplace

from typing import Callable, Optional, Tuple, Iterable

def delta(ts: Iterable) -> pd.Timedelta:
    """
    Given an equally spaced time index, return the interval.
    """
    dts = pd.Series(ts).diff().value_counts()
    if len(dts) != 1:
        raise ValueError("all timedelta must be the same")
    
    return dts.index[0]

# def log10(df: pd.DataFrame, copy=True) -> pd.DataFrame:
#     """Return a dataframe which is applied numpy.log10 on columns ['open', 'close', 'high', 'low', 'volume'].
#     Copy will be created if copy is True (default True).
#     """
#     columns = ['open', 'close', 'high', 'low', 'volume']
    
#     df = df.copy() if copy else df
#     df[columns] = df[columns].applymap(np.log10)
    
#     return df

# def diff(xs: pd.Series) -> pd.Series:
#     """Return xs.diff().dropna().
#     """
#     return xs.diff().dropna()

# def emaverage(xs: pd.Series, alpha: float, dt: pd.Timedelta) -> pd.Series:
#     """
#     Return exponential moving average of xs.

#     Parameters
#     ----------
#     xs : pandas.Series
#         Contains data which should be calculated EMA. Its index must be type of pandas.DatetimeIndex.
#     alpha : float
#         The degree of weighting decrease. Between 0.8 to 0.9 recommended.
#     dt : pandas.Timedelta
#         Unit time. Weights decrease exponentially at a rate of alpha per unit time.
#     """
#     xs = xs.dropna()
#     if len(xs) == 0:
#         return xs
    
#     ts = pd.Series(xs.index, index=xs.index).diff().apply(lambda x: x.total_seconds())
#     ts /= dt.total_seconds()

#     Xt = pd.DataFrame([xs, ts]).T.reset_index(drop=True)
    
#     molecule = Xt.iloc[0, 0]
#     denominator = 1.0
    
#     ema = np.empty(len(xs))
#     ema[0] = molecule
    
#     for i, x, t in Xt.iloc[1:].itertuples():
#         beta = alpha ** t
#         molecule = molecule * beta + x
#         denominator = denominator * beta + 1
        
#         ema[i] = molecule / denominator
    
#     return pd.Series(ema, index=xs.index)

# def emvariances(xs: pd.Series, alpha: float, dt: pd.Timedelta):
#     """
#     Return exponential moving average of (xs - ema) ** 2.
#     Strictly speaking, this is not volatility, but it can be considered as some kind of
#     historical volatility (easy to calculate).
    
#     Parameters
#     ----------
#     xs : pandas.Series
#         Contains data which should be calculated EMV. Its index must be type of pandas.DatetimeIndex.
#     alpha : float
#         The degree of weighting decrease. Between 0.8 to 0.9 recommended.
#     dt : pandas.Timedelta
#         Unit time. Weights decrease exponentially at a rate of alpha per unit time.
#     """
#     ema = emaverage(xs, alpha, dt)
#     return emaverage((xs - ema) ** 2, alpha, dt)

# def trend_from_emaverage(ema: pd.Series, alpha: float, dt: pd.Timedelta) -> pd.Series:
#     """
#     Return calculated trend from EMA. Parameters alpha and dt should be the same with
#     which you used to calculate EMA.
#     """
#     return emaverage(ema.diff(), alpha=self.alpha, dt=self.dt)

# def trend(xs: pd.Series, alpha: float, dt: pd.Timedelta) -> pd.Series:
#     """
#     Return calculated trend from xs.
#     """
#     ema = emaverage(xs, alpha=self.alpha, dt=self.dt)
#     return trend_from_emaverage(ema, alpha=self.alpha, dt=self.dt)

# def turning_point(xs: pd.Series, alpha: float, dt: pd.Timedelta) -> Tuple[pd.Series, pd.Series]:
#     """
#     Return the turning points of the trend.
#     """
#     ema = emaverage(xs, alpha=self.alpha, dt=self.dt)
#     trend = trend_from_emaverage(ema, alpha=self.alpha, dt=self.dt)
    
#     ema = ema.loc[trend.index]
#     uptrend = ema.loc[(((trend > 0).astype(float)).diff() > 0).values]
#     downtrend = ema.loc[(((trend > 0).astype(float)).diff() < 0).values]

#     return uptrend, downtrend

# def rise(xs: pd.Series, window=3, p=0.4) -> pd.Series:
#     """
#     Return the rising points.
#     """
#     dif = xs.rolling(window).sum()
#     prob = estimate_probability(xs, window)

#     rise = prob[(dif > 0) & (prob < p)]

#     return rise

# def fall(xs: pd.Series, window=3, p=0.2) -> pd.Series:
#     """
#     Return the falling points
#     """
#     dif = xs.rolling(window).sum()
#     prob = estimate_probability(xs, window)
    
#     fall = prob[(dif < 0) & (prob < 0.2)]

#     return fall

# def infinite_trade_result(
#         low: pd.Series,
#         low_base: pd.Series,
#         high: Optional[pd.Series]=None,
#         high_base: Optional[pd.Series]=None,
#         f_time_to_sell: Optional[Callable[[pd.Series, pd.Series], pd.Series]]=None,
#         f_time_to_buy: Optional[Callable[[pd.Series, pd.Series], pd.Series]]=None
#     ) -> float:
#     """
#     Return how much you can make profit if you buy a fixed amount of stock always when you should buy 
#     and you sell a fixed amount of stock always when you should sell.
#     You sell some when low > low_base and You buy some when high < high_base.
#     Note that the logarithm should be taken for both low and high.

#     Parameters
#     ----------
#     low : pandas.Series
#         Contains logarithm of historical low price of the stock.
#     low_base : pandas.Series
#         Contains the criterion of sell timing.
#     high : pandas.Series, optional
#         Contains logarithm of historical high price of the stock. Will be overwritten by low when it's None.
#     high_base : pandas.Series, optional
#         Contains the criterion of buy timing. Will be overwritten by low_base when it's None.
#     f_time_to_sell : Optional[Callable[[pd.Series, pd.Series], pd.Series]], default (lambda low, low_base: low > low_base)
#         Be called as f_time_to_sell(low, low_base) and returns when you should sell.
#     f_time_to_buy : Optional[Callable[[pd.Series, pd.Series], pd.Series]], default (lambda high, high_base: high < high_base)
#         Be called as f_time_to_buy(high, high_base) and returns when you should buy.
#     """

#     high = high if high is not None else low
#     high_base = high_base if high_base is not None else low_base
    
#     # default: low price is bigger than expected
#     f_time_to_sell = f_time_to_sell if f_time_to_sell is not None else (lambda low, low_base: low > low_base)
#     # default: high price is smaller than expected
#     f_time_to_buy = f_time_to_buy if f_time_to_buy is not None else (lambda high, high_base: high < high_base)

#     time_to_sell = f_time_to_sell(low, low_base)
#     time_to_buy = f_time_to_buy(high, high_base)

#     duplication = set(low[time_to_sell].index) & set(high[time_to_buy].index)
#     if len(duplication) != 0:
#         warnings.warn(UserWarning(f"duplication detected on sell timings and buy timings"))

#     # you sell a fixed amount when you should sell.
#     sell = low[time_to_sell].sum()
    
#     # you buy a fixed amount when you should buy.
#     buy = high[time_to_buy].sum()
    
#     return sell - buy

# def sell_buy_timing_ratio(
#         low: pd.Series,
#         low_base: pd.Series,
#         high: Optional[pd.Series]=None,
#         high_base: Optional[pd.Series]=None,
#         f_time_to_sell: Optional[Callable[[pd.Series, pd.Series], pd.Series]]=None,
#         f_time_to_buy: Optional[Callable[[pd.Series, pd.Series], pd.Series]]=None
#     ) -> float:
#     """
#     Return the ratio of the sell timing counts to the buy timing counts.
#     Return numpy.nan when buy timing counts is 0 because you have no chance to buy the stock
#     and this indicator is completely meaningless. This indicator should be close to 1
#     because the risk of losing a lot of money or getting salted is reduced
#     if the chances of selling and buying are the same.

#     Parameters
#     ----------
#     low : pandas.Series
#         Contains logarithm of historical low price of the stock.
#     low_base : pandas.Series
#         Contains the criterion of sell timing.
#     high : pandas.Series, optional
#         Contains logarithm of historical high price of the stock. Will be overwritten by low when it's None.
#     high_base : pandas.Series, optional
#         Contains the criterion of buy timing. Will be overwritten by low_base when it's None.
#     f_time_to_sell : Optional[Callable[[pd.Series, pd.Series], pd.Series]], default (lambda low, low_base: low > low_base)
#         Be called as f_time_to_sell(low, low_base) and returns when you should sell.
#     f_time_to_buy : Optional[Callable[[pd.Series, pd.Series], pd.Series]], default (lambda high, high_base: high < high_base)
#         Be called as f_time_to_buy(high, high_base) and returns when you should buy.
#     """
#     high = high if high is not None else low
#     high_base = high_base if high_base is not None else low_base
    
#     # default: low price is bigger than expected
#     f_time_to_sell = f_time_to_sell if f_time_to_sell is not None else (lambda low, low_base: low > low_base)
#     # default: high price is smaller than expected
#     f_time_to_buy = f_time_to_buy if f_time_to_buy is not None else (lambda high, high_base: high < high_base)

#     time_to_sell = f_time_to_sell(low, low_base)
#     time_to_buy = f_time_to_buy(high, high_base)

#     duplication = set(low[time_to_sell].index) & set(high[time_to_buy].index)
#     if len(duplication) != 0:
#         warnings.warn(UserWarning(f"duplication detected on sell timings and buy timings"))
    
#     sell_timing_count = time_to_sell.sum()
#     buy_timing_count = time_to_buy.sum()
#     if buy_timing_count == 0:
#         return np.nan
#     return sell_timing_count / buy_timing_count

# def switch_count(
#         low: pd.Series,
#         low_base: pd.Series,
#         high: Optional[pd.Series]=None,
#         high_base: Optional[pd.Series]=None,
#         f_time_to_sell: Optional[Callable[[pd.Series, pd.Series], pd.Series]]=None,
#         f_time_to_buy: Optional[Callable[[pd.Series, pd.Series], pd.Series]]=None
#     ) -> int:
#     """
#     Return the number of times the time to sell and the time to buy have switched.
#     The higher this value, the more stock trading opportunities you have.

#     Parameters
#     ----------
#     low : pandas.Series
#         Contains logarithm of historical low price of the stock.
#     low_base : pandas.Series
#         Contains the criterion of sell timing.
#     high : pandas.Series, optional
#         Contains logarithm of historical high price of the stock. Will be overwritten by low when it's None.
#     high_base : pandas.Series, optional
#         Contains the criterion of buy timing. Will be overwritten by low_base when it's None.
#     f_time_to_sell : Optional[Callable[[pd.Series, pd.Series], pd.Series]], default (lambda low, low_base: low > low_base)
#         Be called as f_time_to_sell(low, low_base) and returns when you should sell.
#     f_time_to_buy : Optional[Callable[[pd.Series, pd.Series], pd.Series]], default (lambda high, high_base: high < high_base)
#         Be called as f_time_to_buy(high, high_base) and returns when you should buy.
#     """
#     high = high if high is not None else low
#     high_base = high_base if high_base is not None else low_base
    
#     # default: low price is bigger than expected
#     f_time_to_sell = f_time_to_sell if f_time_to_sell is not None else (lambda low, low_base: low > low_base)
#     # default: high price is smaller than expected
#     f_time_to_buy = f_time_to_buy if f_time_to_buy is not None else (lambda high, high_base: high < high_base)

#     time_to_sell = f_time_to_sell(low, low_base)
#     time_to_buy = f_time_to_buy(high, high_base)
    
#     duplication = set(low[time_to_sell].index) & set(high[time_to_buy].index)
#     if len(duplication) != 0:
#         warnings.warn(UserWarning(f"duplication detected on sell timings and buy timings"))
    
#     timings = pd.Series(np.zeros(len(low)), index=low.index, dtype=int)
    
#     # sell timing may be a priority because you lose a lot of money if you miss the crash of the price
#     timings[time_to_buy] = 1
#     timings[time_to_sell] = -1
#     timings = timings[timings != 0]
    
#     count = np.sum(np.diff(timings > 0))
    
#     return count

# def switch_ratio(
#         low: pd.Series,
#         low_base: pd.Series,
#         high: Optional[pd.Series]=None,
#         high_base: Optional[pd.Series]=None,
#         f_time_to_sell: Optional[Callable[[pd.Series, pd.Series], pd.Series]]=None,
#         f_time_to_buy: Optional[Callable[[pd.Series, pd.Series], pd.Series]]=None
#     ) -> int:
#     """
#     Return the ratio of switch_count to (len(low) - 1) // 2.
#     The higher this value, the more stock trading opportunities you have.
#     This value is normalized to have a maximum value of 1 and is often more useful than switch_count.

#     Parameters
#     ----------
#     low : pandas.Series
#         Contains logarithm of historical low price of the stock.
#     low_base : pandas.Series
#         Contains the criterion of sell timing.
#     high : pandas.Series, optional
#         Contains logarithm of historical high price of the stock. Will be overwritten by low when it's None.
#     high_base : pandas.Series, optional
#         Contains the criterion of buy timing. Will be overwritten by low_base when it's None.
#     f_time_to_sell : Optional[Callable[[pd.Series, pd.Series], pd.Series]], default (lambda low, low_base: low > low_base)
#         Be called as f_time_to_sell(low, low_base) and returns when you should sell.
#     f_time_to_buy : Optional[Callable[[pd.Series, pd.Series], pd.Series]], default (lambda high, high_base: high < high_base)
#         Be called as f_time_to_buy(high, high_base) and returns when you should buy.
#     """
#     N = len(low) - 1
#     if N <= 0:
#         return np.nan
#     return switch_count(low, low_base, high, high_base, f_time_to_sell, f_time_to_buy) / N

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
    loc = xs.median()    
    scale = np.abs(xs - loc).mean()
    
    return loc, scale

def estimate_brown_param(xs: pd.Series) -> float:
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
    
    return scale / np.sqrt(dt.total_seconds())

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

# def estimate_probability(
#         xs: pd.Series,
#         window: int=1,
#         loc: Optional[float]=None,
#         scale: Optional[float]=None
#     ) -> pd.Series:
#     """
#     Return the probability that the input will occur,
#     assuming it follows a Laplace distribution with loc, scale as parameters.
#     Parameters of the Laplace distribution are estimated from xs if not specified.
#     By specifying a value greater than 1 for window, joint probability can be
#     taken into account and more robust estimation can be performed.

#     Parameters
#     ----------
#     xs : pd.Series
#         Contains any real-valued data considered to follow the Laplace distribution.
#     window: int, default 1
#         Size of the moving window. Recommends 3 to detect a spike or crash.
#     loc : float, optional
#         Location parameter of Laplace distribution.
#     scale : float, optional
#         Scale parameter of Laplace distribution.
#     """
#     dt = window * delta(xs.index)
#     b = estimate_brown_param(xs)
    
#     ys = xs.rolling(window).sum()
    
#     loc = loc if loc is not None else ys.median()
#     scale = scale if scale is not None else calc_brown_param(b, dt)
    
#     ps = laplace.cdf(-np.abs(ys-loc), loc=0, scale=scale) * 2
    
#     return pd.Series(ps, index=xs.index)

# def analyze(xs: pd.Series) -> pd.DataFrame:
#     """
#     Return a dataframe of the input itself, the time difference
#     from the previous element, the logarithmic value, the log difference
#     from the previous element, and the probability that the input will occur.

#     Parameters
#     ----------
#     xs : pandas.Series
#         Contains historical price of the stock.
#     """
#     df = pd.DataFrame(index=xs.index)
#     df['dt'] = df.index - df.index[0]
    
#     df[xs.name] = xs
    
#     df['log'] = xs.apply(np.log10)
#     df['diff'] = df['log'].diff()
#     df['prob'] = estimate_probability(df['diff'])
    
#     return df

# def plot_laplace(xs: pd.Series):
#     """
#     Plot the fitted result assuming that the input follows a Laplace distribution.

#     Parameters
#     ----------
#     xs : pandas.Series
#         Contains any real-valued data considered to follow the Laplace distribution.
#     """
#     loc, scale = estimate_laplace_param(xs)
    
#     vs = np.linspace(-scale*10, scale*10, 100)
#     ys = laplace.pdf(vs, loc, scale)
#     bins = plt.hist(xs, bins=vs)

#     a = bins[0].max() / ys.max()

#     plt.plot(vs, ys * a)
    
#     plt.grid(True)
#     plt.show()