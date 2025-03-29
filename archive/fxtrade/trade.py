from __future__ import annotations

import numpy as np
import pandas as pd

from fractions import Fraction
from pathlib import Path
from typing import Optional, Union, Iterable, List

from .stock import as_numeric, Numeric, Stock, Rate
from .safeattr import SafeAttrABC, immutable, protected
from .utils import focus, default_save_iterator, default_save_fstring, default_save_function

# class Transfer:
#     """Transfer of currencies outside of transactions.
#     """
#     @classmethod
#     def deposit(cls, x: Stock, t: Optional[pd.Timestamp]=None):
#         return Transfer(x, t)
    
#     @classmethod
#     def withdraw(cls, x: Stock, t: Optional[pd.Timestamp]=None):
#         return Transfer(-x, t)

#     @classmethod
#     def fee(cls, x: Stock, t: Optional[pd.Timestamp]=None):
#         return Transfer(-x, t)

#     def __init__(self, x: Stock, t: Optional[pd.Timestamp]=None):
#         if t is None:
#             t = pd.Timestamp.now()
#         self.x = x
    
class Trade:
    """Represent a single transaction.
    Consists from the stock before transaction and the stock after transaction.
    """
    @classmethod
    @property
    def columns(cls):
        return pd.Index([
            't', 'id', 'from', 'X(t)', 'to', 'Y(t+dt)', 'R(yt/xt)'
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
        return pd.Index(['id', 'from', 'to'])
    
    @property
    def info_columns(self):
        return pd.Index([ k for k in self.info.keys() ])

    @property
    def all_columns(self):
        return pd.Index(
            list(self.columns) + list(self.info_columns)
        )

    @classmethod
    def from_series(cls, s: pd.Series):
        """Create Trade from pandas.Series. Columns must be
        pd.Index(['t', 'id', 'from', 'X(t)', 'to', 'Y(t+dt)', 'R(yt/xt)'])
        """
        x = Stock(s['from'], s['X(t)'])
        y = Stock(s['to'], s['Y(t+dt)'])
        t = s['t']
        id = s['id']

        r = Rate.from_stocks(x, y)
        
        if r.r != s['R(yt/xt)']:
            raise ValueError("invalid rate on R(yt/xt).")
        
        info = { idx: s[idx] for idx in s.index if idx not in set(cls.columns) }
        
        return Trade(x=x, y=y, t=t, id=id, **info)
    
    @staticmethod
    def from_stock_and_rate(stock: Stock, rate: Rate, t=None, id=None):
        """Create Trade from Stock and Rate.
        """
        x = stock
        y = stock * rate
        
        return Trade(x, y, t, id)
    
    def __init__(self,
                 x: Stock,
                 y: Stock,
                 t: Optional[pd.Timestamp]=None,
                 id: Optional[str]=None,
                 **kwargs):
        """
        Parameters
        ----------
        x : Stock
            The stock before the transaction.
        y : Stock
            The stock after the transaction.
        t : pandas.Timestamp, optional
            The time at which the transaction took place. If not specified, the current time will be set.
        id : str, optional
            ID to distinguish that transaction from others.
        kwargs
            Additional infomation of the trade.
        """
        if t is None:
            t = pd.Timestamp.now()
        
        self.t = t
        self._x = x
        self._y = y
        
        self.id = id

        self.info = { k: v for k, v in kwargs.items() }
    
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
        
        if self.id is None:
            return f"Trade({self.t} | R(yt/xt): {float(r)} | "\
                   f"X(t): {float(self.x.q)}{self.x.code} -> Y(t+dt): {float(self.y.q)}{self.y.code})"
        return f"Trade({self.id} | {self.t} | R(yt/xt): {float(r)} | "\
               f"X(t): {float(self.x.q)}{self.x.code} -> Y(t+dt): {float(self.y.q)}{self.y.code})"
    
    def as_series(self) -> pd.Series:
        """Convert to pandas.Series.
        """

        # r = self.rate
        # if not isinstance(r, Rate):
        #     r = np.nan

        xs = [
            self.t, self.id,
            self.x.code, self.x.q,
            self.y.code, self.y.q,
            self.rate.r,
        ]
        columns = list(Trade.columns)

        for k, v in self.info.items():
            xs.append(v)
            columns.append(k)

        return pd.Series(xs, index=columns)
    
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
        
        return Trade(x1, y1, self.t, self.id, **self.info), Trade(x2, y2, self.t, self.id, **self.info)
    
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
        
        return Trade(x1, y1, self.t, self.id, **self.info), Trade(x2, y2, self.t, self.id, **self.info)
    
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
        
        return Trade(x, y, self.t, self.id, **self.info)
    
    def yfloor(self, n=6):
        """
        Truncate the post-trade stock on the specified digit.
        """
        y = self.y.floor(n)
        x = y / self.rate
        
        return Trade(x, y, self.t, self.id, **self.info)
    
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
        
        return Trade(x, y, self.t, self.id, **self.info)
    
    def yceil(self, n=6):
        """
        Round up the post-trade stock on the specified digit.
        """
        y = self.y.ceil(n)
        x = y / self.rate
        
        return Trade(x, y, self.t, self.id, **self.info)
    
    def ceil(self, n=6):
        """
        Round up the post-trade stock on the specified digit.
        """
        return self.yceil(n)
    
    def __mul__(self, other):
        """Try to multiply the other to both x and y.
        """
        return Trade(self.x * other, self.y * other, self.t, self.id, **self.info)
    
    def __truediv__(self, other):
        """Try to devide by the other to both x and y.
        """
        return Trade(self.x / other, self.y / other, self.t, self.id, **self.info)
    
    def __floordiv__(self, other):
        """Try to devide by the other to both x and y and calculate floor().
        """
        return Trade(self.x / other, self.y / other, self.t, self.id, **self.info).floor()
    
    def __mod__(self, other):
        """Try to devide by the other to both x and y and calculate ceil().
        """
        return Trade(self.x / other, self.y / other, self.t, self.id, **self.info).ceil()

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
                       id=s['before_id'], t=s['s'])
        
        after = Trade(x=Stock(s['code_Y'], s['Y(s+ds)=Y(t)']),
                      y=Stock(s['code_Z'], s['Z(t+dt)']),
                      id=s['after_id'], t=s['t'])
        
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
                            self.before.id,
                            self.after.id,
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
