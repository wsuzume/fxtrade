# """
# Utilities to assist in processing time series data.
# """

import numpy as np
import pandas as pd

from datetime import datetime, timedelta
from typing import Union, Optional, Iterable

from .period import is_divisor, to_period_str, parse, DIVISORS

def delta(ts: Iterable) -> pd.Timedelta:
    """
    Given an equally spaced time index, return the interval.
    """
    dts = pd.Series(ts).diff().value_counts()
    if len(dts) != 1:
        raise ValueError("all timedelta must be the same")
    
    return dts.index[0]

def split_into_chunks(df: pd.DataFrame):
    """
    等間隔で繋がっている部分列に分割する
    """
    dts = pd.Series(df.index).diff()[1:]
    dt = dts.value_counts().index[0]
    
    idx = [0] + list(dts[(dts != dt)].index) + [dts.index[-1]]
    
    xs = []
    for begin, end in zip(idx, idx[1:]):
        xs.append(df.iloc[begin: end].copy())
    
    xs = [ x for x in xs if len(x) >= 2 ]
    
    return xs

def time_arange(begin, end, dt, with_end=True):
    if not with_end:
        return pd.Index(np.arange(begin, end, dt))
    return pd.Index(np.arange(begin, end + dt, dt))

def get_first_timestamp(ts: datetime, period: str) -> pd.Timestamp:
    if isinstance(period, timedelta):
        period = to_period_str(period)

    if not is_divisor(period):
        raise ValueError(f"period must be one of {DIVISORS}.")
    
    t, u = parse(period)
    if u in ['d', 'D']:
        return pd.Timestamp(ts.year, ts.month, ts.day)
    elif u in ['h', 'H']:
        return pd.Timestamp(ts.year, ts.month, ts.day,
                                int(t) * (ts.hour // int(t)))
    elif u in ['m', 'M']:
        return pd.Timestamp(ts.year, ts.month, ts.day, ts.hour,
                                int(t) * (ts.minute // int(t)))
    elif u in ['s', 'S']:
        return pd.Timestamp(ts.year, ts.month, ts.day, ts.hour, ts.minute,
                                int(t) * (ts.second // int(t)))
    
    raise RuntimeError('unknown error')

def normalize_time_index(df, begin, end, dt):
    begin = get_first_timestamp(begin, dt)

    idx = time_arange(begin, end, dt, with_end=True)

    use_idx = pd.Index([ i for i in df.index if i in set(idx) ])

    new_df = pd.DataFrame([], index=idx, columns=df.columns)
    new_df.loc[use_idx] = df.loc[use_idx]

    return new_df


# def with_timestamp(x=None, scope='day', format_str=None):
#     fmt = {
#         'year': '%Y',
#         'month': '%Y%m',
#         'day': '%Y%m%d',
#         'hour': '%Y%m%dT%H',
#         'minute': '%Y%m%dT%H%M',
#         'second': '%Y%m%dT%H-%M-%S',
#         'millisecond': '%Y%m%dT%H-%M-%S-%f',
#     }
    
#     format_str = fmt[scope] if format_str is None else format_str
    
#     t = datetime.datetime.now()
#     tstamp = t.strftime(format_str)
    
#     if x is None:
#         return tstamp
#     return f'{tstamp}_{x}'

# def delta(ts: Iterable) -> pd.Timedelta:
#     """
#     Given an equally spaced time index, return the interval.
#     """
#     dts = pd.Series(ts).diff().value_counts()
#     if len(dts) != 1:
#         raise ValueError("all timedelta must be the same")
    
#     return dts.index[0]

# def to_timedelta(interval: str) -> pd.Timedelta:
#     """
#     Convert a string representing a period of time,
#     such as '1d' or '1h', to pandas.Timedelta.
#     """
#     if interval not in INTERVALS:
#         raise ValueError(f"interval must be one of {INTERVALS}")
    
#     if interval in MINUTES:
#         return pd.Timedelta(minutes=MINUTES[interval])
#     elif interval in HOURS:
#         return pd.Timedelta(hours=HOURS[interval])
#     elif interval in DAYS:
#         return pd.Timedelta(days=DAYS[interval])
    
#     raise RuntimeError("unknown error")

# def select(df: pd.DataFrame,
#            year: Optional[int]=None,
#            month: Optional[int]=None,
#            day: Optional[int]=None,
#            hour: Optional[int]=None,
#            minute: Optional[int]=None,
#            second: Optional[int]=None
#           ):
    
#     idx = pd.Series(np.repeat(True, len(df)))
    
#     if year is not None:
#         idx &= pd.Series(df.index).apply(lambda x: x.year == year)
#     if month is not None:
#         idx &= pd.Series(df.index).apply(lambda x: x.month == month)
#     if day is not None:
#         idx &= pd.Series(df.index).apply(lambda x: x.day == day)
#     if hour is not None:
#         idx &= pd.Series(df.index).apply(lambda x: x.hour == hour)
#     if minute is not None:
#         idx &= pd.Series(df.index).apply(lambda x: x.minute == minute)
#     if second is not None:
#         idx &= pd.Series(df.index).apply(lambda x: x.second == second)
    
#     return df.loc[idx.values].copy()

# def merge(df_prev: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
#     if len(df_prev) == 0:
#         return df
    
#     idx_prev = set(df_prev.index)
#     idx = set(df.index)
    
#     intersec = idx_prev & idx
    
#     # 共通部分で NaN を含まない新しい情報
#     idx_new_inter = set(df.loc[sorted(list(intersec))].dropna().index)
    
#     # 共通部分から idx_new を除いた古い情報
#     idx_old_inter = intersec - idx_new_inter
    
#     # 共通部分を取り除いて、共通部分の中から使う情報を付け加えた情報
#     idx_old = (idx_prev - intersec) | idx_old_inter
#     idx_new = (idx - intersec) | idx_new_inter
    
#     df = pd.concat([
#                 df_prev.loc[sorted(list(idx_old))],
#                 df.loc[sorted(list(idx_new))],
#          ], axis=0).sort_index()
    
#     return df

# def default_merge_function(df_prev, df):
#     return merge(df_prev, df)
    
# def default_restore_function(load_dir):
#     paths = sorted(list(load_dir.glob('*')))
#     if len(paths) == 0:
#         raise FileNotFoundError(f"No file to read in '{load_dir}'")

#     dfs = []
#     for path in paths:
#         dfs.append(pd.read_csv(path, index_col=0, parse_dates=True))

#     df_ret = dfs[0]
#     for df in dfs[1:]:
#         df_ret = default_merge_function(df_ret, df)

#     return df_ret.sort_index()

# def validate_index(df):
#     idx_diff = pd.Series(df.index).diff().value_counts()
        
#     p_diff = idx_diff.index[pd.Series(idx_diff.index) > pd.Timedelta(0)]
#     m_diff = idx_diff.index[pd.Series(idx_diff.index) < pd.Timedelta(0)]

#     if len(p_diff) > 0 and len(m_diff) > 0:
#         raise ValueError("index is not sorted")
#     elif len(p_diff) > 0:
#         ascending = True
#     elif len(m_diff) > 0:
#         ascending = False
#     else:
#         raise ValueError("could not find which way it is sorted")
    
#     return {'ascending': ascending}

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