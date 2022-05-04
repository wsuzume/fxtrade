from __future__ import annotations

import numpy as np
import pandas as pd

from fractions import Fraction
from typing import Optional, Union, Iterable

from .const import Const
from .stock import as_numeric, Numeric, Stock, Rate

TRADE = Const({'BUY', 'SELL', 'DEPOSIT', 'WITHDRAW'})
TRADE.TRADE_COLUMNS = pd.Index([
    't', 'order_id', 'from', 'X(t)', 'to', 'Y(t+dt)', 'R(yt/xt)'
])
TRADE.TRADE_PAIR_COLUMNS = pd.Index([
    'before_id', 'after_id', 's', 't',
    'X(s)', 'Y(s+ds)=Y(t)', 'Z(t+dt)', 'code_X', 'code_Y', 'code_Z',
    'R(ys/xs)', 'R(zt/yt)', 'R(zt/xs)',
])
TRADE.TRADE_SUMMARY_COLUMNS = pd.Index([
    'capital', 'via', 'used', 'earned', 'position', 'hold', 'rate_mean',
    'position_min', 'hold_min', 'rate_min', 'position_max', 'hold_max', 'rate_max',
])


class Transfer:
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
    @staticmethod
    def from_series(s):
        x = Stock(s['from'], s['X(t)'])
        y = Stock(s['to'], s['Y(t+dt)'])
        t = s['t']
        order_id = s['order_id']

        r = Rate.from_stocks(x, y)
        
        if r.r != s['R(yt/xt)']:
            raise ValueError(f"")
        
        return Trade(x=x, y=y, t=t, order_id=order_id)
    
    def __init__(self,
                 x: Stock,
                 y: Stock,
                 t: Optional[pd.Timestamp]=None,
                 order_id: Optional[str]=None):
        if t is None:
            t = pd.Timestamp.now()
        
        self.t = t
        self.x = x
        self.y = y
        
        self.order_id = order_id
        
        self.rate = Rate.from_stocks(self.x, self.y)
    
    def __repr__(self):
        if self.order_id is None:
            return f"Trade({self.t} | R(yt/xt): {float(self.rate.r)} | "\
                   f"X(t): {float(self.x.q)}{self.x.code} -> Y(t+dt): {float(self.y.q)}{self.y.code})"
        return f"Trade({self.order_id} | {self.t} | R(yt/xt): {float(self.rate.r)} | "\
               f"X(t): {float(self.x.q)}{self.x.code} -> Y(t+dt): {float(self.y.q)}{self.y.code})"
    
    def as_series(self):
        return pd.Series([self.t, self.order_id,
                          self.x.code, self.x.q,
                          self.y.code, self.y.q,
                          self.rate.r], index=TRADE.TRADE_COLUMNS)
    
    def split_x(self, x: Stock):
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
        if z.code == self.x.code:
            return self.split_x(z)
        elif z.code == self.y.code:
            return self.split_y(z)
        raise TypeError(f"stock code must be {self.x.code} or {self.y.code}")
    
    def settle(self, trade):
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

class TradePair:
    @staticmethod
    def from_series(s):
        before = Trade(x=Stock(s['code_X'], s['X(s)']),
                       y=Stock(s['code_Y'], s['Y(s+ds)=Y(t)']),
                       order_id=s['before_id'], t=s['s'])
        
        after = Trade(x=Stock(s['code_Y'], s['Y(s+ds)=Y(t)']),
                      y=Stock(s['code_Z'], s['Z(t+dt)']),
                      order_id=s['after_id'], t=s['t'])
        
        if before.rate.r != s['R(ys/xs)']:
            raise ValueError('invalid record: rate not match')
        if after.rate.r != s['R(zt/yt)']:
            raise ValueError('invalid record: rate not match')
        
        return TradePair(before, after)
    
    def __init__(self, before: Trade, after: Trade):
        if before.t > after.t:
            raise ValueError(f"before.t must be smaller than or equal to after.t but {before.t} and {after.t}")
        if before.y != after.x:
            raise ValueError(f"before.y must be equal to after.x but {before.y} and {after.x}")
        
        self.before = before
        self.after = after
        
    def __repr__(self):
        return f"TradePair({self.before.x} -> {self.before.y} -> {self.after.y})"
    
    def as_series(self):
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
                         ], index=TRADE.TRADE_PAIR_COLUMNS)
        
class History:
    @staticmethod
    def from_dataframe(df, copy: bool=True):
        ret = History()
        ret._df = df if not copy else df.copy()
        return ret
    
    def __init__(self, trade: Optional[Union[Trade, Iterable[Trade]]]=None):
        self._df = pd.DataFrame([], columns=TRADE.TRADE_COLUMNS)
        
        if trade is not None:
            self.add(trade)
    
    def copy(self):
        return History.from_dataframe(self._df)
    
    @property
    def df(self):
        return self._df.copy()
    
    def __getitem__(self, idx):
        return Trade.from_series(self._df.loc[idx])
    
    def add(self, trade: Optional[Union[Trade, Iterable[Trade], History]], copy: bool=False):
        if trade is None:
            return
        
        hist = self if not copy else self.copy()
        
        df = None
        if isinstance(trade, History):
            df = trade._df
        if isinstance(trade, Trade):
            df = pd.DataFrame([ trade.as_series() ])
        elif isinstance(trade, Iterable):
            df = pd.DataFrame([ t.as_series() for t in trade ])
        
        if df is None:
            raise TypeError("trade must be type of Trade or Iterable[Trade]")
            
        hist._df = pd.concat([hist._df, df]).reset_index(drop=True)
        
        return hist
    
    def drop(self, idx):
        self._df = self._df.drop(idx)
    
    def as_trade_list(self,
                      sort_by: Union[str, list[str]]=None,
                      ascending: Optional[Union[bool, list[bool]]]=True):
        if sort_by is None:
            df = self.df
        else:
            df = self.df.sort_values(by=sort_by, ascending=ascending)
        return [ Trade.from_series(x) for _, x in df.iterrows() ]
    
    def get_pair_trade_index(self, trade: Trade, ascending: bool=True):
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
    
    def _settle(self, trade: Trade, ascending: bool=True, copy: bool=True):
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
    
    def settle(self, trade: Trade, ascending: bool=True, copy: bool=True):
        return self._settle(trade, copy)
    
    def close(self):
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
                         ], index=TRADE.TRADE_SUMMARY_COLUMNS)
    
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
                pos = History.from_dataframe(hist._df[pos_idx], copy=False)
                
                desc = pos.describe(code_X, code_Y)
                desc['used'] = rep['X(s)'].sum()
                desc['earned'] = rep['Z(t+dt)'].sum()

                ret.append(desc)
        
        df = pd.DataFrame(ret, columns=TRADE.TRADE_SUMMARY_COLUMNS)
        
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
    
class Report:
    @staticmethod
    def from_dataframe(df):
        ret = Report()
        ret._df = df.copy()
        return ret
    
    def __init__(self, trade_pair: Optional[Union[TradePair, Iterable[TradePair]]]=None):
        self._df = pd.DataFrame([], columns=TRADE.TRADE_PAIR_COLUMNS)
        
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