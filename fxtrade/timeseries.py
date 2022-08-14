"""
Utilities to assist in processing time series data.
"""

import numpy as np
import pandas as pd

from datetime import datetime, timedelta
from typing import Union, Optional, Iterable

INTERVALS = [
    '1m', '5m', '10m', '15m', '30m',
    '1h', '3h', '6h', '12h',
    '1d', '3d', '5d', '7d',
]

MINUTES = {'1m': 1, '5m': 5, '10m': 10, '15m': 15, '30m': 30, }
HOURS = {'1h': 1, '3h': 3, '6h': 6, '12h': 12, }
DAYS = {'1d': 1, '3d': 3, '5d': 5, '7d': 7, }

def with_timestamp(x=None, scope='day', format_str=None):
    fmt = {
        'year': '%Y',
        'month': '%Y%m',
        'day': '%Y%m%d',
        'hour': '%Y%m%dT%H',
        'minute': '%Y%m%dT%H%M',
        'second': '%Y%m%dT%H-%M-%S',
        'millisecond': '%Y%m%dT%H-%M-%S-%f',
    }
    
    format_str = fmt[scope] if format_str is None else format_str
    
    t = datetime.datetime.now()
    tstamp = t.strftime(format_str)
    
    if x is None:
        return tstamp
    return f'{tstamp}_{x}'

def delta(ts: Iterable) -> pd.Timedelta:
    """
    Given an equally spaced time index, return the interval.
    """
    dts = pd.Series(ts).diff().value_counts()
    if len(dts) != 1:
        raise ValueError("all timedelta must be the same")
    
    return dts.index[0]

def to_timedelta(interval: str) -> pd.Timedelta:
    """
    Convert a string representing a period of time,
    such as '1d' or '1h', to pandas.Timedelta.
    """
    if interval not in INTERVALS:
        raise ValueError(f"interval must be one of {INTERVALS}")
    
    if interval in MINUTES:
        return pd.Timedelta(minutes=MINUTES[interval])
    elif interval in HOURS:
        return pd.Timedelta(hours=HOURS[interval])
    elif interval in DAYS:
        return pd.Timedelta(days=DAYS[interval])
    
    raise RuntimeError("unknown error")
    
# ダウンサンプリング & 中途半端な時間に取得したデータを削除
def down_sampling(df: pd.DataFrame, interval: str):
    """
    Return dataframe which is applied down sampling with specified interval.
    Data recorded at the halfway point will be deleted.
    """
    if interval not in INTERVALS:
        raise ValueError(f"interval must be one of {INTERVALS}")
    
    # 残すデータのインデックス
    if interval in MINUTES:
        idx = pd.Series(df.index).apply(
                lambda x: x.minute % MINUTES[interval] == 0 and x.second == 0)
    elif interval in HOURS:
        idx = pd.Series(df.index).apply(
                lambda x: x.hour % HOURS[interval] == 0 and x.minute == 0 and x.second == 0)
    elif interval in DAYS:
        idx = pd.Series(df.index).apply(
                lambda x: x.day % DAYS[interval] == 0 and x.hour == 0 and x.minute == 0 and x.second == 0)
    
    return df.loc[idx.values].copy()
    
def get_first_timestamp(ts: pd.Timestamp, interval: str) -> pd.Timestamp:
    if interval not in ['1d', '15m', '1m']:
        raise ValueError("interval must be one of ['1d', '15m', '1m']")
    
    table = {
        '1d': pd.Timestamp(ts.year, ts.month, ts.day),
        '15m': pd.Timestamp(ts.year, ts.month, ts.day, ts.hour, 15 * (ts.minute // 15)),
        '1m': pd.Timestamp(ts.year, ts.month, ts.day, ts.hour, ts.minute),
    }
    
    return table[interval]

def normalized_timeindex(start: Union[int, pd.Timestamp],
                         end: Union[int, pd.Timestamp],
                         delta: [int, pd.Timedelta]) -> pd.Series:
    if start >= end:
        raise ValueError("end must be larger than start")
    
    return pd.Series(np.arange(start, end, delta))

def select(df: pd.DataFrame,
           year: Optional[int]=None,
           month: Optional[int]=None,
           day: Optional[int]=None,
           hour: Optional[int]=None,
           minute: Optional[int]=None,
           second: Optional[int]=None
          ):
    
    idx = pd.Series(np.repeat(True, len(df)))
    
    if year is not None:
        idx &= pd.Series(df.index).apply(lambda x: x.year == year)
    if month is not None:
        idx &= pd.Series(df.index).apply(lambda x: x.month == month)
    if day is not None:
        idx &= pd.Series(df.index).apply(lambda x: x.day == day)
    if hour is not None:
        idx &= pd.Series(df.index).apply(lambda x: x.hour == hour)
    if minute is not None:
        idx &= pd.Series(df.index).apply(lambda x: x.minute == minute)
    if second is not None:
        idx &= pd.Series(df.index).apply(lambda x: x.second == second)
    
    return df.loc[idx.values].copy()

def merge(df_prev: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    if len(df_prev) == 0:
        return df
    
    idx_prev = set(df_prev.index)
    idx = set(df.index)
    
    intersec = idx_prev & idx
    
    # 共通部分で NaN を含まない新しい情報
    idx_new_inter = set(df.loc[sorted(list(intersec))].dropna().index)
    
    # 共通部分から idx_new を除いた古い情報
    idx_old_inter = intersec - idx_new_inter
    
    # 共通部分を取り除いて、共通部分の中から使う情報を付け加えた情報
    idx_old = (idx_prev - intersec) | idx_old_inter
    idx_new = (idx - intersec) | idx_new_inter
    
    df = pd.concat([
                df_prev.loc[sorted(list(idx_old))],
                df.loc[sorted(list(idx_new))],
         ], axis=0).sort_index()
    
    return df

def validate_index(df):
    idx_diff = pd.Series(df.index).diff().value_counts()
        
    p_diff = idx_diff.index[pd.Series(idx_diff.index) > pd.Timedelta(0)]
    m_diff = idx_diff.index[pd.Series(idx_diff.index) < pd.Timedelta(0)]

    if len(p_diff) > 0 and len(m_diff) > 0:
        raise ValueError("index is not sorted")
    elif len(p_diff) > 0:
        ascending = True
    elif len(m_diff) > 0:
        ascending = False
    else:
        raise ValueError("could not find which way it is sorted")
    
    return {'ascending': ascending}

def this_year_first(t: pd.Timestamp):
    return datetime(t.year, 1, 1)

def next_year_first(t: pd.Timestamp):
    return datetime(t.year+1, 1, 1)

def count_years(begin: pd.Timestamp, end: pd.Timestamp):
    return end.year - begin.year

def add_years(t, dy):
    return datetime(t.year+dy, t.month, t.day)

def year_sections(begin, end):
    if begin >= end:
        raise ValueError("begin must be before than end")
    
    b = this_year_first(begin)
    e = next_year_first(end)
    
    for i in range(count_years(b, e)):
        x = add_years(b, i)
        y = add_years(b, i+1)
        yield (x, y)

def this_month_first(t):
    return datetime(t.year, t.month, 1)
    
def next_month_first(t):
    if t.month == 12:
        return datetime(t.year+1, 1, 1)
    return datetime(t.year, t.month+1, 1)

def count_months(begin, end):
    years = end.year - begin.year
    months = end.month - begin.month
    
    return years * 12 + months

def add_months(t, dm):
    year = t.year + (dm // 12)
    month = t.month + (dm % 12)
    
    if month > 12:
        year += 1
        month -= 12
    
    return datetime(year, month, t.day)

def month_sections(begin, end):
    if begin >= end:
        raise ValueError("begin must be before than end")
    
    b = this_month_first(begin)
    e = next_month_first(end)
    
    for i in range(count_months(b, e)):
        x = add_months(b, i)
        y = add_months(b, i+1)
        yield (x, y)
        
def this_day_first(t):
    return datetime(t.year, t.month, t.day)

def next_day_first(t):
    return datetime(t.year, t.month, t.day) + timedelta(days=1)

def count_days(begin, end):
    return (end - begin).days

def add_days(t, dd):
    return t + timedelta(days=dd)

def day_sections(begin, end):
    if begin >= end:
        raise ValueError("begin must be before than end")
    
    b = this_day_first(begin)
    e = next_day_first(end)
    
    for i in range(count_days(b, e)):
        x = add_days(b, i)
        y = add_days(b, i+1)
        yield (x, y)