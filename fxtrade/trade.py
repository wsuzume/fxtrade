from __future__ import annotations

import numpy as np
import pandas as pd

from fractions import Fraction
from pathlib import Path
from typing import Optional, Union, Iterable, List

from .core import is_instance_list
from .const import Const
from .stock import as_numeric, Numeric, Stock, Rate

TRADE = Const({'BUY', 'SELL', 'DEPOSIT', 'WITHDRAW'})

class Transfer:
    """Transfer of funds outside of transactions.
    """
    @classmethod
    def deposit(cls):
        pass
    
    @classmethod
    def withdraw(cls):
        pass

    def __init__(self, x: Stock, t: Optional[pd.Timestamp]):
        if t is None:
            t = pd.Timestamp.now()
        self.x = x
    
class Trade:
    """Represent a single transaction.
    Consists from the stock before transaction and the stock after transaction.
    """
    @classmethod
    @property
    def columns(cls):
        return pd.Index([
            't', 'order_id', 'from', 'X(t)', 'to', 'Y(t+dt)', 'R(yt/xt)'
        ])

    @classmethod
    @property
    def datetime_columns(cls):
        return pd.Index(['t'])

    @classmethod
    @property
    def numeric_columns(cls):
        return pd.Index(['X(t)', 'Y(t+dt)', 'R(yt/xt)'])
    
    @classmethod
    @property
    def string_columns(cls):
        return pd.Index(['order_id', 'from', 'to'])

    @staticmethod
    def from_series(s: pd.Series):
        """Create Trade from pandas.Series. Columns must be
        pd.Index(['t', 'order_id', 'from', 'X(t)', 'to', 'Y(t+dt)', 'R(yt/xt)'])
        """
        x = Stock(s['from'], s['X(t)'])
        y = Stock(s['to'], s['Y(t+dt)'])
        t = s['t']
        order_id = s['order_id']

        r = Rate.from_stocks(x, y)
        
        if r.r != s['R(yt/xt)']:
            raise ValueError("invalid rate on R(yt/xt).")
        
        return Trade(x=x, y=y, t=t, order_id=order_id)
    
    @staticmethod
    def from_stock_and_rate(stock: Stock, rate: Rate, t=None, order_id=None):
        """Create Trade from Stock and Rate.
        """
        x = stock
        y = stock * rate
        
        return Trade(x, y, t, order_id)
    
    def __init__(self,
                 x: Stock,
                 y: Stock,
                 t: Optional[pd.Timestamp]=None,
                 order_id: Optional[str]=None):
        """
        Parameters
        ----------
        x : Stock
            The stock before the transaction.
        y : Stock
            The stock after the transaction.
        t : pandas.Timestamp, optional
            The time at which the transaction took place. If not specified, the current time will be set.
        order_id : str, optional
            Order ID.
        """
        if t is None:
            t = pd.Timestamp.now()
        
        self.t = t
        self._x = x
        self._y = y
        
        self.order_id = order_id
    
    @property
    def x(self) -> Stock:
        """The stock before the transaction.
        """
        return self._x
    
    @property
    def y(self) -> Stock:
        """The stock after the transaction.
        """
        return self._y
    
    @property
    def rate(self) -> Rate:
        """The rate at the transaction.
        """
        if self.x == 0:
            return np.nan
        return Rate.from_stocks(self.x, self.y)
    
    def __repr__(self):
        r = self.rate.r if isinstance(self.rate, Rate) else np.nan
        
        if self.order_id is None:
            return f"Trade({self.t} | R(yt/xt): {float(r)} | "\
                   f"X(t): {float(self.x.q)}{self.x.code} -> Y(t+dt): {float(self.y.q)}{self.y.code})"
        return f"Trade({self.order_id} | {self.t} | R(yt/xt): {float(r)} | "\
               f"X(t): {float(self.x.q)}{self.x.code} -> Y(t+dt): {float(self.y.q)}{self.y.code})"
    
    def as_series(self) -> pd.Series:
        """Convert to pandas.Series.
        """
        return pd.Series([self.t, self.order_id,
                          self.x.code, self.x.q,
                          self.y.code, self.y.q,
                          self.rate.r], index=Trade.columns)
    
    def split_x(self, x: Stock):
        """
        Split a trade by x into two trades.
        """
        if x.code != self.x.code:
            raise TypeError(f"stock code must be {self.x.code}")
        if x >= self.x:
            raise ValueError(f"quantity of splitter must be smaller than {self.x}")
        
        x1 = x
        x2 = self.x - x
        
        y1 = x1 * self.rate
        y2 = x2 * self.rate
        
        return Trade(x1, y1, self.t, self.order_id), Trade(x2, y2, self.t, self.order_id)
    
    def split_y(self, y: Stock):
        """
        Split a trade by y into two trades.
        """
        if y.code != self.y.code:
            raise TypeError(f"stock code must be {self.y.code}")
        if y >= self.y:
            raise ValueError(f"quantity of splitter must be smaller than {self.y}")
        
        y1 = y
        y2 = self.y - y
        
        x1 = y1 / self.rate
        x2 = y2 / self.rate
        
        return Trade(x1, y1, self.t, self.order_id), Trade(x2, y2, self.t, self.order_id)
    
    def split(self, z: Stock):
        """
        Split a trade into two trades. Whether it is divided by
        x or y is automatically determined by the code.
        """
        if z.code == self.x.code:
            return self.split_x(z)
        elif z.code == self.y.code:
            return self.split_y(z)
        raise TypeError(f"stock code must be {self.x.code} or {self.y.code}")
    
    def settle(self, trade):
        """
        Calculate the confirmed profit and remaining unrealized profit from the two trades.
        """
        if self.t > trade.t:
            raise ValueError(f"trade.t must be greater than or equal to self.t")
        
        if self.y == trade.x:
            return TradePair(self, trade), None
        elif self.y < trade.x:
            settled, unsettled = trade.split(self.y)
            return TradePair(self, settled), unsettled
        else:
            settled, unsettled = self.split(trade.x)
            return TradePair(settled, trade), unsettled
    
    def xfloor(self, n=0):
        """
        Truncate the pre-trade stock on the specified digit.
        """
        x = self.x.floor(n)
        y = x * self.rate
        
        return Trade(x, y, self.t, self.order_id)
    
    def yfloor(self, n=6):
        """
        Truncate the post-trade stock on the specified digit.
        """
        y = self.y.floor(n)
        x = y / self.rate
        
        return Trade(x, y, self.t, self.order_id)
    
    def floor(self, n=6):
        """
        Truncate the post-trade stock on the specified digit.
        """
        return self.yfloor(n)
    
    def xceil(self, n=0):
        """
        Round up the pre-trade stock on the specified digit.
        """
        x = self.x.ceil(n)
        y = x * self.rate
        
        return Trade(x, y, self.t, self.order_id)
    
    def yceil(self, n=6):
        """
        Round up the post-trade stock on the specified digit.
        """
        y = self.y.ceil(n)
        x = y / self.rate
        
        return Trade(x, y, self.t, self.order_id)
    
    def ceil(self, n=6):
        """
        Round up the post-trade stock on the specified digit.
        """
        return self.yceil(n)
    
    def __mul__(self, other):
        """Try to multiply the other to both x and y.
        """
        return Trade(self.x * other, self.y * other, self.t, self.order_id)
    
    def __truediv__(self, other):
        """Try to devide by the other to both x and y.
        """
        return Trade(self.x / other, self.y / other, self.t, self.order_id)
    
    def __floordiv__(self, other):
        """Try to devide by the other to both x and y and calculate floor().
        """
        return Trade(self.x / other, self.y / other, self.t, self.order_id).floor()
    
    def __mod__(self, other):
        """Try to devide by the other to both x and y and calculate ceil().
        """
        return Trade(self.x / other, self.y / other, self.t, self.order_id).ceil()

class FailedTrade:
    def __init__(self, message):
        self.message = message

class TradePair:
    """Pair of transactions with confirmed profit or loss.
    """
    @classmethod
    @property
    def columns(cls):
        return pd.Index([
            'before_id', 'after_id', 's', 't',
            'X(s)', 'Y(s+ds)=Y(t)', 'Z(t+dt)', 'code_X', 'code_Y', 'code_Z',
            'R(ys/xs)', 'R(zt/yt)', 'R(zt/xs)',
        ])

    @staticmethod
    def from_series(s):
        """Create TradePair from pandas.Series. Columns must be
        pd.Index(['before_id', 'after_id', 's', 't',
        'X(s)', 'Y(s+ds)=Y(t)', 'Z(t+dt)', 'code_X', 'code_Y', 'code_Z',
        'R(ys/xs)', 'R(zt/yt)', 'R(zt/xs)']).
        """
        before = Trade(x=Stock(s['code_X'], s['X(s)']),
                       y=Stock(s['code_Y'], s['Y(s+ds)=Y(t)']),
                       order_id=s['before_id'], t=s['s'])
        
        after = Trade(x=Stock(s['code_Y'], s['Y(s+ds)=Y(t)']),
                      y=Stock(s['code_Z'], s['Z(t+dt)']),
                      order_id=s['after_id'], t=s['t'])
        
        if before.rate.r != s['R(ys/xs)']:
            raise ValueError('invalid rate on R(ys/xs)')
        if after.rate.r != s['R(zt/yt)']:
            raise ValueError('invalid rate on R(zt/yt)')
        
        return TradePair(before, after)
    
    def __init__(self, before: Trade, after: Trade):
        """
        Parameters
        ----------
        before : Trade
            A trade you made.
        after : Trade
            A trade in which profit or loss are determined.
        """
        if before.t > after.t:
            raise ValueError(f"before.t must be smaller than or equal to after.t but {before.t} and {after.t}")
        if before.y != after.x:
            raise ValueError(f"before.y must be equal to after.x but {before.y} and {after.x}")
        
        self.before = before
        self.after = after
        
    def __repr__(self):
        return f"TradePair({self.before.x} -> {self.before.y} -> {self.after.y})"
    
    def as_series(self):
        """Convert to pandas.Series.
        """
        return pd.Series([
                            self.before.order_id,
                            self.after.order_id,
                            self.before.t,
                            self.after.t,
                            self.before.x.q,
                            self.before.y.q,
                            self.after.y.q,
                            self.before.x.code,
                            self.before.y.code,
                            self.after.y.code,
                            self.before.rate.r,
                            self.after.rate.r,
                            (self.before.rate * self.after.rate).r,
                         ], index=TradePair.columns)
        
class History:
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
    def typecast(cls, df):
        df = df[cls.columns].copy()

        for col in cls.datetime_columns:
            df[col] = df[col].apply(pd.Timestamp)
        for col in cls.numeric_columns:
            df[col] = df[col].apply(Fraction)
        for col in cls.string_columns:
            df[col] = df[col].apply(str)
        
        return df
    
    @classmethod
    def read_csv(cls, path):
        path = Path(path)
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return cls.typecast(df)
    
    @classmethod
    def from_csv(cls, path):
        return History(cls.read_csv(path))

    def __init__(self, trade: Optional[Union[Trade, Iterable[Trade]]]=None):
        """
        Parameters
        ----------
        trade : Union[Trade, Iterable[Trade]], optional
            A trade or a list of trades.
        """
        self._df = pd.DataFrame([], columns=Trade.columns)
        
        if trade is not None:
            self.add(trade)
    
    def __repr__(self):
        return f"History(N={len(self._df)})"
    
    @property
    def df(self) -> pd.DataFrame:
        """Return the copy of history dataframe.
        """
        return self._df.copy()
    
    def copy(self) -> History:
        """Return the copy of history.
        """
        return History(self._df)

    def to_csv(self, path, append=True):
        df = self._df

        path = Path(path)
        if path.exists():
            df_old = self.read_csv(path)
            df = pd.concat([df_old, df], axis=0).sort_index()
        
        return df.to_csv(path, index=True)

    def __getitem__(self, idx):
        return Trade.from_series(self._df.loc[idx])
    
    def add(self, trade: Optional[Union[Trade, Iterable[Trade], History]]) -> History:
        """
        Add a trade or a list of trades to the history.
        """
        if trade is None:
            return self
        elif isinstance(trade, History):
            df = trade._df
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
        self._df = self.typecast(df)

        return self
    
    def drop(self, idx):
        """
        Drop the records which specified by idx.
        """
        self._df = self._df.drop(idx)
    
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
        Return the index of previous trades that should be paired with the trade.
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

        return pd.Series([code_from,
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
                pos = History(hist._df[pos_idx], copy=False)
                
                desc = pos.describe(code_X, code_Y)
                desc['used'] = rep['X(s)'].sum()
                desc['earned'] = rep['Z(t+dt)'].sum()

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
                
                desc = History.from_dataframe(rec, copy=False).describe(code_X, code_Y)
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