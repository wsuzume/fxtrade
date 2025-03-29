import pytest

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from fxtrade.pseudo import pseudo
from fxtrade.period import Period
from fxtrade.utils import standardize, focus, \
    default_timestamp_filter, default_save_fstring, default_save_iterator

def test_standardize():
    s = datetime(2022, 2, 1)
    t = datetime(2022, 2, 15)
    dt = timedelta(minutes=1)

    df = pseudo(s, t, dt)

    df_st = standardize(df)

    assert len(df_st.columns) == 6
    assert df_st.index[0] == datetime(2022, 2, 1)
    assert df_st.index[-1] == datetime(2022, 2, 14, 23, 59)
    assert len(df) == len(df_st)

def test_focus():
    # datetime に対しては時間比較
    assert focus(datetime(2022, 2, 1), datetime(2022, 2, 2)) is True
    assert focus(datetime(2022, 2, 2), datetime(2022, 2, 2)) is True
    assert focus(datetime(2022, 2, 3), datetime(2022, 2, 2)) is False

    # str に対しても時間比較（fstring が必要）
    assert focus('2022-02-01', datetime(2022, 2, 2), fstring='%Y-%m-%d')

    # Path は name に対して時間比較（fstring が必要）
    assert focus(Path('data/2022-02-01.csv'), datetime(2022, 2, 2), fstring='%Y-%m-%d.csv')

    # List に対しては抽出処理
    xs = [
        datetime(2022, 2, 1),
        datetime(2022, 2, 2),
        datetime(2022, 2, 3),
        datetime(2022, 2, 4),
        datetime(2022, 2, 5),
    ]

    assert len(focus(xs, datetime(2022, 2, 3))) == 3

    xs = [
        '2022-02-01',
        '2022-02-02',
        '2022-02-03',
        '2022-02-04',
        '2022-02-05',
    ]

    assert len(focus(xs, datetime(2022, 2, 3), fstring='%Y-%m-%d')) == 3

    xs = [
        Path('data/2022-02-01.csv'),
        Path('data/2022-02-02.csv'),
        Path('data/2022-02-03.csv'),
        Path('data/2022-02-04.csv'),
        Path('data/2022-02-05.csv'),
    ]

    assert len(focus(xs, datetime(2022, 2, 3), fstring='%Y-%m-%d.csv')) == 3

    # DataFrame に対しても抽出処理
    s = datetime(2022, 2, 1)
    t = datetime(2022, 2, 15)
    dt = timedelta(minutes=1)

    df = pseudo(s, t, dt)
    df = standardize(df)

    df_focus = focus(df, datetime(2022, 2, 3))

    assert df_focus.index[0] == datetime(2022, 2, 1)
    assert df_focus.index[-1] == datetime(2022, 2, 3)

    df_focus = focus(df, (datetime(2022, 2, 2), datetime(2022, 2, 3)))

    assert df_focus.index[0] == datetime(2022, 2, 2)
    assert df_focus.index[-1] == datetime(2022, 2, 3)

def test_default_timestamp_filter():
    s = datetime(2022, 2, 1)
    t = datetime(2022, 2, 15)
    dt = timedelta(minutes=1)

    df = pseudo(s, t, dt)
    df = standardize(df)
    
    f = default_timestamp_filter(Period('1d'))

    idx = pd.Series(df.index, index=df.index).apply(f)
    df_f = df.loc[idx]

    # 14 日分
    assert len(df_f) == 14

    f = default_timestamp_filter(Period('15m'))

    idx = pd.Series(df.index, index=df.index).apply(f)
    df_f = df.loc[idx]

    # 14 日分 * 24 時間 * 15 分おき
    assert len(df_f) == 14 * 24 * 4

    f = default_timestamp_filter(Period('1m'))

    idx = pd.Series(df.index, index=df.index).apply(f)
    df_f = df.loc[idx]

    # 14 日分 * 24 時間 * 1 分おき
    assert len(df_f) == 14 * 24 * 60

def test_default_save_fstring():
    fstring = default_save_fstring(Period('1d'))
    assert fstring == '%Y.csv'

    fstring = default_save_fstring(Period('15m'))
    assert fstring == '%Y-%m.csv'

    fstring = default_save_fstring(Period('1m'))
    assert fstring == '%Y-%m-%d.csv'

def test_save_iterator():
    iter = default_save_iterator(Period('1d'))
    assert iter.__name__ == 'year_sections'

    iter = default_save_iterator(Period('15m'))
    assert iter.__name__ == 'month_sections'

    iter = default_save_iterator(Period('1m'))
    assert iter.__name__ == 'day_sections'

def test_merge():
    pass

def test_default_read_function():
    pass

def test_default_glob_function():
    pass

def test_default_restore_function():
    pass

def test_default_save_function():
    pass