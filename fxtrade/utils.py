import numpy as np
import pandas as pd

from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Union, Iterable, List, Tuple

from .core import type_checked, is_instance_list
from .period import Period
from .timeseries import year_sections, month_sections, day_sections

def standardize(df: pd.DataFrame):
    """
    使用するカラムを選択する
    """
    df = type_checked(df, pd.DataFrame)

    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError(f"df.index must be {pd.DatetimeIndex}.")
        
    ohlc_col = ['timestamp', 'open', 'high', 'low', 'close']
    ohlcv_col = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

    if not (set(ohlc_col) <= set(df.columns)):
        raise ValueError(f"df must have columns at least {ohlc_col}.")
    
    if set(ohlcv_col) <= set(df.columns):
        columns = ohlcv_col
    else:
        columns = ohlc_col

    return df[columns].sort_index()

def normalize(df: pd.DataFrame, dt: timedelta):
    """
    インデックスを正しい刻みにする
    """
    df = type_checked(df, pd.DataFrame)

    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError(f"df.index must be {pd.DatetimeIndex}.")

    # TODO

    return df

def focus(x, t, fstring=None, column=None):
    def _focus(s, t):
        if t is None:
            return True
        elif isinstance(t, datetime):
            return s <= t
        elif is_instance_list(t, datetime, n=1):
            return s >= t[0]
        elif is_instance_list(t, datetime, n=2):
            return t[0] <= s <= t[1]
        raise TypeError("t must be instance of datetime or Tuple[datetime, datetime]")

    if isinstance(x, pd.DataFrame):
        df = x

        if column is not None:
            idx = df[column]

            if is_instance_list(idx, datetime):
                idx = pd.DatetimeIndex(idx)
            else:
                if fstring is None:
                    raise ValueError(f"fstring must be specified when specified column's element is not instance of {datetime}.")
                idx = pd.DatetimeIndex([ datetime.strptime(s, fstring) for s in idx ])
        else:
            idx = df.index

            if not isinstance(idx, pd.DatetimeIndex):
                if fstring is None:
                    raise ValueError(f"fstring must be specified when index is not instance of {pd.DatetimeIndex}.")
                idx = pd.DatetimeIndex([ datetime.strptime(s, fstring) for s in idx ])

        if t is None:
            return df.copy()
        elif isinstance(t, datetime):
            return df[idx <= t].copy()
        elif is_instance_list(t, datetime, n=1):
            return df[(idx >= t[0])].copy()
        elif is_instance_list(t, datetime, n=2):
            return df[(idx >= t[0]) & (idx <= t[1])].copy()
        else:
            raise TypeError()

    elif isinstance(x, datetime):
        return _focus(x, t)

    elif isinstance(x, str):
        if fstring is None:
            raise ValueError(f"fstring must be specified when x is str or Path.")
        s = datetime.strptime(x, fstring)
        return _focus(s, t)

    elif isinstance(x, Path):
        return focus(x.name, t, fstring=fstring)

    elif is_instance_list(x, (datetime, str, Path)):
        return [ v for v in x if focus(v, t, fstring=fstring) ]
    
    raise TypeError()
    
# # interpolate したレコードは timestamp が NaN になるようにしている
# def normalize(df: pd.DataFrame, interval: pd.Timedelta,
#               ascending: bool = False,
#               interpolate_columns: List[str]=['open', 'close', 'high', 'low', 'volume']) -> pd.DataFrame:
#     """
#     NaN で計算が滞らないように線形補間する
#     """
#     df = df.copy()
#     b = df.index[0]
#     end = df.index[-1]
    
#     begin = get_first_timestamp(b, interval)
#     delta = to_timedelta(interval)
    
#     timeindex = set(normalized_timeindex(begin, end, delta))
#     idx = timeindex - set(df.index)
    
#     for i in sorted(list(idx)):
#         df.loc[i] = np.nan
    
#     df = df.sort_index()
#     df[interpolate_columns] = df[interpolate_columns].interpolate()
    
#     if not ascending:
#         df = df.sort_index(ascending=ascending)
    
#     return df

def default_timestamp_filter(period: Period):
    return {
        Period('1d'): lambda x: (x.hour == 0) and (x.minute == 0) \
                            and (x.second == 0) and (x.nanosecond == 0),
        Period('15m'): lambda x: (x.minute % 15 == 0) \
                            and (x.second == 0) and (x.nanosecond == 0),
        Period('1m'): lambda x: (x.second == 0) and (x.nanosecond == 0),
    }[period]

def default_save_fstring(period: Period):
    return {
            Period('1d'): '%Y.csv',
            Period('15m'): '%Y-%m.csv',
            Period('1m'): '%Y-%m-%d.csv',
    }[period]

def default_save_iterator(period: Period):
    return {
            Period('1d'): year_sections,
            Period('15m'): month_sections,
            Period('1m'): day_sections,
    }[period]

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

def default_read_function(path: Union[str, Path], parse_dates=True) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0, parse_dates=parse_dates)

def default_merge_function(df_prev: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    return merge(df_prev, df)

def default_glob_function(dir_path: Union[str, Path]) -> List[str]:
    return sorted(Path(dir_path).glob('*.csv'))

def default_restore_function(paths: Iterable[Union[str, Path]]) -> pd.DataFrame:
    dfs = []
    for path in paths:
        dfs.append(default_read_function(path))

    df_ret = dfs[0]
    for df in dfs[1:]:
        df_ret = default_merge_function(df_ret, df)

    return df_ret.sort_index()

def default_save_function(
        df: pd.DataFrame,
        dir_path: Union[str, Path],
        save_iterator: Callable[[datetime, datetime], Iterable[Tuple[datetime, datetime]]],
        save_fstring: str,
        timestamp_filter: Callable[[datetime], bool]=None,
        column: str=None,
        parse_dates=True
    ) -> Path:
    save_dir = Path(dir_path)
    save_dir.mkdir(parents=True, exist_ok=True)

    if len(df) == 0:
       raise ValueError(f"dataframe size is zero: no data to save.")
    
    df = df.sort_index()

    if column is None:
        idx = pd.Series(df.index)
    else:
        idx = df[column]

    # 期間ごとに小分けにしてイテレート
    for begin, end in save_iterator(idx.iloc[0], idx.iloc[-1]):
        save_name = begin.strftime(save_fstring)
        path = save_dir / save_name
        
        # 小分けにしたデータフレーム
        df_part = focus(df, (begin, end), column=column)

        # 過去に同期間が保存されていれば読み込んでマージ
        if path.exists():
            df_prev = default_read_function(path, parse_dates)
            df_part = default_merge_function(df_prev, df_part)
        
        # 保存するデータを選択する
        if timestamp_filter is not None:
            save_idx = pd.Series(df_part.index).apply(timestamp_filter)
            df_part = df_part.loc[save_idx.values]
        
        # 保存する
        df_part.to_csv(path, index=True)
    
    return save_dir
