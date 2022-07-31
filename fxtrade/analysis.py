import numpy as np
import pandas as pd


import plotly.graph_objects as go
from matplotlib import pyplot as plt
from scipy.stats import laplace

from .timeseries import delta

def log10(df: pd.DataFrame):
    columns = ['open', 'close', 'high', 'low', 'volume']
    
    df = df.copy()
    df[columns] = df[columns].applymap(np.log10)
    
    return df

def diff(xs: pd.Series):
    return xs.diff().dropna()

def geomeans(xs, alpha, dt):
    xs = xs.dropna()
    if len(xs) == 0:
        return xs
    
    ts = pd.Series(xs.index, index=xs.index).diff().apply(lambda x: x.total_seconds())
    ts /= dt.total_seconds()

    Xt = pd.DataFrame([xs, ts]).T.reset_index(drop=True)
    
    molecule = Xt.iloc[0, 0]
    denominator = 1.0
    
    gmeans = np.empty(len(xs))
    gmeans[0] = molecule
    
    for i, x, t in Xt.iloc[1:].itertuples():
        beta = alpha ** t
        molecule = molecule * beta + x
        denominator = denominator * beta + 1
        
        gmeans[i] = molecule / denominator
    
    return pd.Series(gmeans, index=xs.index)

def geovariances(xs, alpha, dt):
    gmeans = geomeans(xs, alpha, dt)
    return geomeans((xs - gmeans) ** 2, alpha, dt)

def infinite_trade_result(xs, ys):
    residue = xs - ys
    return xs[residue > 0].sum() - ys[residue < 0].sum()

def over_under_ratio(xs, ys):
    residue = xs - ys
    over = (residue > 0).sum()
    under = (residue < 0).sum()
    if under == 0:
        return np.nan
    return over / under

def straddle_count(xs, ys):
    residue = xs - ys
    count = np.sum(np.diff(residue > 0) > 0)
    if count == 0:
        return np.nan
    return count

def estimate_laplace_param(xs: pd.Series):
    loc = xs.median()    
    scale = np.abs(xs - loc).mean()
    
    return loc, scale

def estimate_brown_param(xs: pd.Series):
    loc, scale = estimate_laplace_param(xs)

    dt = delta(xs.index)
    
    return scale / np.sqrt(dt.total_seconds())

def calc_brown_param(scale: float, dt: pd.Timedelta):
    return scale * np.sqrt(dt.total_seconds())

def estimate_probability(xs, window=1, loc=None, scale=None):
    dt = window * delta(xs.index)
    b = estimate_brown_param(xs)
    
    ys = xs.rolling(window).sum()
    
    loc = loc if loc is not None else ys.median()
    scale = scale if scale is not None else calc_brown_param(b, dt)
    
    ps = laplace.cdf(-np.abs(ys-loc), loc=0, scale=scale) * 2
    
    return pd.Series(ps, index=xs.index)

def analyze(xs: pd.Series):
    df = pd.DataFrame(index=xs.index)
    df['dt'] = df.index - df.index[0]
    
    df[xs.name] = xs
    
    df['log'] = xs.apply(np.log10)
    df['diff'] = df['log'].diff()
    df['prob'] = estimate_probability(df['diff'])
    
    return df

def plot_laplace(xs):
    loc, scale = estimate_laplace_param(xs)
    
    vs = np.linspace(-scale*10, scale*10, 100)
    ys = laplace.pdf(vs, loc, scale)
    bins = plt.hist(xs, bins=vs)

    a = bins[0].max() / ys.max()

    plt.plot(vs, ys * a)
    
    plt.grid(True)
    plt.show()