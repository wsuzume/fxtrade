import pandas as pd

def standardize(df: pd.DataFrame):
    """
    使用するカラムを選択する
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("df.index must be type of pandas.DatetimeIndex")
        
    columns = ['timestamp', 'open', 'close', 'high', 'low', 'volume']
    
    return df[columns].copy()

# def time(df, t):
#     if t is not None:
#         df = df[df.index <= t].copy()
    
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

# def default_read_function(path: Union[str, Path]) -> pd.DataFrame:
#     return pd.read_csv(path, index_col=0, parse_dates=True)

# def default_merge_function(df_prev: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
#     return merge(df_prev, df)

# def default_glob_function(dir_path: Union[str, Path]) -> List[str]:
#     return sorted(list(Path(dir_path).glob('*.csv')))

# def default_restore_function(paths: Iterable[Union[str, Path]]) -> pd.DataFrame:
#     dfs = []
#     for path in paths:
#         dfs.append(default_read_function(path))

#     df_ret = dfs[0]
#     for df in dfs[1:]:
#         df_ret = default_merge_function(df_ret, df)

#     return df_ret.sort_index()

# def default_save_function(
#                 df: pd.DataFrame,
#                 dir_path: Union[str, Path],
#                 sections: Callable[[datetime, datetime], Iterable[Tuple[datetime, datetime]]],
#                 format_string: str,
#                 timestamp_filter: Callable[[datetime], bool]=None
#                 ) -> Path:
#     save_dir = Path(dir_path)
#     dirmap.ensure(save_dir)

#     if len(df) == 0:
#         warnings.warn(UserWarning(f"dataframe size is zero: no data to save."))
#         return save_dir
    
#     # 期間ごとに小分けにしてイテレート
#     for begin, end in sections(df.index[0], df.index[-1]):
#         save_name = begin.strftime(format_string)
#         path = save_dir / save_name
        
#         # 小分けにしたデータフレーム
#         df_part = df[(df.index >= begin) & (df.index < end)]

#         # 過去に同期間が保存されていれば読み込んでマージ
#         if path.exists():
#             df_prev = default_read_function(path)
#             df_part = default_merge_function(df_prev, df_part)
        
#         # 保存するデータを選択する
#         if timestamp_filter is not None:
#             save_idx = pd.Series(df_part.index).apply(
#                             timestamp_filter
#                         )
#             df_part = df_part.loc[save_idx.values]
        
#         # 保存する
#         df_part.to_csv(path, index=True)
    
#     return save_dir
