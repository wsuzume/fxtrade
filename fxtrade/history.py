from __future__ import annotations

import numpy as np
import pandas as pd

from fractions import Fraction
from pathlib import Path
from typing import Optional, Union, Iterable, List
from io import StringIO

from .core import is_instance_list
from .trade import Trade, TradePair
from .safeattr import SafeAttrABC, immutable, protected
from .timeseries import month_sections
from .utils import focus, default_read_function, default_write_function, default_save_function

class History(SafeAttrABC):
    """
    Keep all transactions in a dataframe.
    """
    @classmethod
    @property
    def columns(cls):
        return Trade.columns
    
    @classmethod
    @property
    def datetime_columns(cls):
        return Trade.datetime_columns

    @classmethod
    @property
    def numeric_columns(cls):
        return Trade.numeric_columns
    
    @classmethod
    @property
    def string_columns(cls):
        return Trade.string_columns

    @classmethod
    def normalize(cls, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        columns = set(df.columns)
        for col in cls.columns:
            if col not in columns:
                raise ValueError(f"df must have columns at least {cls.columns}.")

        for col in cls.datetime_columns:
            df[col] = df[col].apply(pd.Timestamp)
        for col in cls.numeric_columns:
            df[col] = df[col].apply(Fraction)
        for col in cls.string_columns:
            df[col] = df[col].apply(str)
        
        return df.sort_values('t')
    
    @classmethod
    def read_csv(cls, path: Union[str, Path]) -> pd.DataFrame:
        df = default_read_function(path, parse_dates=['t'])
        return cls.normalize(df)
    
    @classmethod
    def from_csv(cls, path: Union[str, Path]) -> History:
        return History(cls.read_csv(path))

    @staticmethod
    def empty() -> pd.DataFrame:
        return pd.DataFrame([], columns=Trade.columns)

    def __init__(self,
                 trade: Optional[Union[Trade, Iterable[Trade], pd.DataFrame, History]]=None):
        """
        Parameters
        ----------
        trade : Union[Trade, Iterable[Trade]], optional
            A trade or a list of trades.
        """
        self.df = protected(
            self.empty(),
            type_=pd.DataFrame
        )

        if trade is not None:
            self.add(trade)
    
    def __repr__(self):
        return self.dumps()
    
    def dump(self, f, indent=2, nest=1):
        tab = " " * indent * nest
        last_tab = " " * (indent * (nest - 1))
        if self.n_trades == 0:
            f.write(f"History(n_trades={self.n_trades})")
        else:
            f.write(f"History(\n")
            f.write(f"{tab}n_trades={self.n_trades},\n")
            f.write(f"{tab}first_timestamp={self.first_timestamp},\n")
            f.write(f"{tab}last_timestamp={self.last_timestamp}\n")
            f.write(f"{last_tab})")
    
    def dumps(self, indent=4):
        with StringIO() as f:
            self.dump(f, indent=indent)
            ret = f.getvalue()
        return ret

    @property
    def df_float(self):
        df = self.df.copy()

        df.loc[:, ['X(t)', 'Y(t+dt)', 'R(yt/xt)']] = df.loc[:, ['X(t)', 'Y(t+dt)', 'R(yt/xt)']].applymap(float)

        return df

    @property
    def n_trades(self):
        return len(self.df)

    @property
    def first_timestamp(self):
        return self.df['t'].min()
    
    @property
    def last_timestamp(self):
        return self.df['t'].max()

    def clear(self):
        self._df = self.empty()

    def focus(self, t) -> History:
        return History(focus(self._df, t, column='t'))

    def copy(self) -> History:
        """Return the copy of history.
        """
        return History(self)

    def to_csv(self, path: Union[str, Path]):
        return default_write_function(self.df, path)

    def __getitem__(self, idx):
        if len(self.df) == 0:
            return None
        return Trade.from_series(self.df.iloc[idx])
    
    def add(self, trade: Optional[Union[Trade, Iterable[Trade], pd.DataFrame, History]]) -> History:
        """
        Add a trade or a list of trades to the history.
        """
        if trade is None:
            return self
        elif isinstance(trade, History):
            df = trade.df
        elif isinstance(trade, pd.DataFrame):
            df = trade
        elif isinstance(trade, pd.Series):
            df = pd.DataFrame([ trade ])
        elif isinstance(trade, Trade):
            df = pd.DataFrame([ trade.as_series() ])
        elif is_instance_list(trade, Trade):
            df = pd.DataFrame([ t.as_series() for t in trade ])
        else:
            raise TypeError("trade must be type of Trade or Iterable[Trade]")
            
        df = pd.concat([self._df, df]).reset_index(drop=True)
        self._df = self.normalize(df)

        return self
    
    def drop(self, idx):
        """
        Drop the records which specified by idx.
        """
        self._df = self.df.drop(idx)

    def save(self, data_dir: Union[str, Path], save_function=None, save_fstring=None, save_iterator=None):
        if save_function is None:
            save_function = default_save_function
        if save_fstring is None:
            save_fstring = '%Y-%m.csv'
        if save_iterator is None:
            save_iterator = month_sections
        
        return save_function(
            df=self.df,
            dir_path=data_dir,
            save_iterator=save_iterator,
            save_fstring=save_fstring,
            timestamp_filter=None,
            column='t',
            parse_dates=['t']
        )
        
    def read(self, data_dir: Union[str, Path], t=None) -> pd.DataFrame:
        data_dir = Path(data_dir)
        dfs = []
        for path in data_dir.glob('*.csv'):
            dfs.append(self.read_csv(path))
        
        return pd.concat(dfs, axis=0).sort_values('t')
    
    def load(self, data_dir: Union[str, Path], t=None) -> pd.DataFrame:
        self._df = self.read(data_dir=data_dir)
        return self.df
    
    def as_trade_list(self,
                      sort_by: Union[str, list[str]]=None,
                      ascending: Optional[Union[bool, list[bool]]]=True) -> List[Trade]:
        """
        Decompose history to a list of trades
        """
        if sort_by is None:
            df = self.df
        else:
            df = self.df.sort_values(by=sort_by, ascending=ascending)
        return [ Trade.from_series(x) for _, x in df.iterrows() ]
    
    def get_pair_trade_index(self, trade: Trade, ascending: bool=True):
        """
        Return the index of previous trades that should be paired with given trade.
        """
        df = self._df[(self._df['from'] == trade.y.code) & (self._df['to'] == trade.x.code)]
        df = df[df['t'] <= trade.t].sort_values(by='R(yt/xt)', ascending=ascending)
        
        if len(df) == 0:
            return pd.Index([])
        
        amount = trade.x
        idx = []
        for i, row in df.iterrows():
            idx.append(i)
            Yt = row['Y(t+dt)']
            if Yt >= amount:
                break
            amount -= Yt
        
        return df.loc[idx].index
    
    def settle(self, trade: Trade, ascending: bool=True, copy: bool=True):
        pair_idx = self.get_pair_trade_index(trade, ascending)
        
        if len(pair_idx) == 0:
            return self, None
        
        report = Report()
        for idx in pair_idx:
            pair, trade = self[idx].settle(trade)
            report.add(pair)
        
        hist = self if not copy else self.copy()
        hist.drop(pair_idx)
        hist.add(trade)
        
        return hist, report
    
    def close(self):
        """
        Divide trades to date into those with confirmed
        profits or losses and those that have yet to be confirmed.
        """
        trade_list = self.as_trade_list(sort_by='t', ascending=True)
        
        hist = History()
        
        hist.add(trade_list.pop(0))
        
        report = Report()
        for trade in trade_list:
            hist, settled = hist.settle(trade)
            if settled is None:
                hist.add(trade)
            else:
                report.add(settled)
        
        return hist, report
    
    def group_by_code(self):
        df = self._df
        
        group = [ '-'.join([row['from'], row['to']]) for _, row in df.iterrows() ]
        group = pd.Series(group, index=df.index)
        
        return df.groupby(group)
    
    def describe(self, code_from: str, code_to: str):
        df = self._df
        
        df = df[(df['from'] == code_from) & (df['to'] == code_to)]
        
        rate_mean = np.nan
        if df['X(t)'].sum() != 0:
            rate_mean = df['Y(t+dt)'].sum() / df['X(t)'].sum()

        vmin = df['R(yt/xt)'].min()
        mins = df[df['R(yt/xt)'] == vmin]

        vmax = df['R(yt/xt)'].max()
        maxs = df[df['R(yt/xt)'] == vmax]

        return pd.Series([
            code_from,
            code_to,
            Fraction(0),
            Fraction(0),
            df['X(t)'].sum(),
            df['Y(t+dt)'].sum(),
            rate_mean,
            mins['X(t)'].sum(),
            mins['Y(t+dt)'].sum(),
            vmin,
            maxs['X(t)'].sum(),
            maxs['Y(t+dt)'].sum(),
            vmax,
        ], index=TradeSummary.columns)
    
    def summarize(self, origin: Optional[str]=None):
        hist, report = self.close()
        
        ret = []
        if len(report._df) != 0:
            idx_dict = report.group_by_code().indices
            for idx in idx_dict.values():
                rep = report.df.loc[idx]

                code_X = rep.iloc[0]['code_X']
                code_Y = rep.iloc[0]['code_Y']

                pos_idx = (hist._df['from'] == code_X) & (hist._df['to'] == code_Y)
                pos = History(hist._df[pos_idx])
                
                desc = pos.describe(code_X, code_Y)
                desc['used'] = float(rep['X(s)'].sum())
                desc['earned'] = float(rep['Z(t+dt)'].sum())

                ret.append(desc)
        
        df = pd.DataFrame(ret, columns=TradeSummary.columns)
        
        if len(hist._df) != 0:
            ret = []
            idx_dict = hist.group_by_code().indices
            for idx in idx_dict.values():
                rec = hist._df.loc[idx]

                code_X = rec.iloc[0]['from']
                code_Y = rec.iloc[0]['to']
            
                pos = df[(df['capital'] == code_X) & (df['via'] == code_Y)]
                
                if len(pos) != 0:
                    break
                
                desc = History(rec).describe(code_X, code_Y)
                ret.append(desc)
            
            df = pd.concat([df, pd.DataFrame(ret)], axis=0)
        
        if origin is None:
            df = df.sort_values(by=['capital', 'via'])
        else:
            primary_idx = (df['capital'] == origin)
            secondary_idx = (df['via'] == origin)
        
            primary_df = df[primary_idx].sort_values(by=['via'])
            secondary_df = df[secondary_idx].sort_values(by=['capital'])
            other_df = df[~primary_idx & ~secondary_idx].sort_values(by=['capital', 'via'])
            
            df = pd.concat([primary_df, secondary_df, other_df], axis=0)
            
        return df.reset_index(drop=True)

class TradeSummary:
    @classmethod
    @property
    def columns(cls):
        return pd.Index([
            'capital', 'via', 'used', 'earned', 'position', 'hold', 'rate_mean',
            'position_min', 'hold_min', 'rate_min', 'position_max', 'hold_max', 'rate_max',
        ])

class Report:
    @staticmethod
    def from_dataframe(df):
        ret = Report()
        ret._df = df.copy()
        return ret
    
    def __init__(self, trade_pair: Optional[Union[TradePair, Iterable[TradePair]]]=None):
        self._df = pd.DataFrame([], columns=TradePair.columns)
        
        if trade_pair is not None:
            self.add(trade_pair)
    
    def copy(self):
        return Report.from_dataframe(self._df)
    
    def add(self, trade_pair: Optional[Union[TradePair, Iterable[TradePair], Report]], copy: bool=False):
        if trade_pair is None:
            return
        
        rep = self if not copy else self.copy()
        
        df = None
        if isinstance(trade_pair, Report):
            df = trade_pair._df
        if isinstance(trade_pair, TradePair):
            df = pd.DataFrame([ trade_pair.as_series() ])
        elif isinstance(trade_pair, Iterable):
            df = pd.DataFrame([ tp.as_series() for tp in trade_pair ])
        
        if df is None:
            raise TypeError("trade_pair must be type of TradePair or Iterable[TradePair]")
        
        rep._df = pd.concat([rep._df, df]).reset_index(drop=True)
        
        return rep
    
    @property
    def df(self):
        return self._df.copy()
    
    def as_trade_pair_list(self):
        return [ TradePair.from_series(x) for _, x in self.df.iterrows() ]
    
    def group_by_code(self):
        df = self._df
        
        group = [ '-'.join([row['code_X'], row['code_Y'], row['code_Z']]) for _, row in df.iterrows() ]
        group = pd.Series(group, index=df.index)
        
        return df.groupby(group)