import copy
import pandas as pd

from fractions import Fraction
from pathlib import Path
from typing import Iterable

from .stock import Stock

class Wallet:
    @staticmethod
    def read_csv(path):
        path = Path(path)
        return pd.read_csv(path, index_col=0, parse_dates=True).applymap(Fraction)

    @classmethod
    def from_dataframe(cls, df, codes=None):
        xs = df.sort_index().iloc[-1]
        return Wallet(xs).filter_stocks(codes)
    
    @classmethod
    def from_csv(cls, path, codes=None):
        df = cls.read_csv(path)
        return Wallet.from_dataframe(df, codes)

    """
    Manage your stocks.
    """
    def __init__(self, xs=None):
        self.stocks = {}

        if xs is not None:
            self.join(xs)
    
    def __repr__(self):
        return f"Wallet({self.stocks})"
    
    def __getitem__(self, key):
        return self.stocks[key]
    
    def __setitem__(self, key, val):
        # all codes must be upper case
        key = key.upper()
        if isinstance(val, Stock):
            self.stocks[key] = val
        else:
            self.stocks[key] = Stock(key, val)

    def copy(self):
        w = Wallet()
        w.stocks = copy.deepcopy(self.stocks)
        return w

    @property
    def codes(self):
        return list(self.stocks.keys())
    
    def filter_stocks(self, codes=None):
        if codes is None:
            return self
        elif isinstance(codes, str):
            self.stocks = { codes: self.stocks[codes] }
        else:
            self.stocks = { k: v for k, v in self.stocks.items() if k in codes }
        
        return self
    
    @property
    def df(self):
        return self.to_dataframe()

    def to_dataframe(self, t=None):
        if t is None:
            t = pd.Timestamp.now().round('S')

        cols = [ k for k in self.stocks.keys() ]
        vals = [ v.q for v in self.stocks.values() ]

        df = pd.DataFrame([vals], index=[t], columns=cols)

        return df
    
    def to_csv(self, path, t=None, append=True):
        df = self.to_dataframe(t)

        path = Path(path)
        if append and path.exists():
            df_old = self.read_csv(path)
            df = pd.concat([df_old, df], axis=0).sort_index()
        
        return df.to_csv(path, index=True)

    def join(self, code: str):
        if isinstance(code, str):
            self[code] = Stock(code, 0)
        elif isinstance(code, pd.Series):
            for c, q in code.iteritems():
                self[c] = Stock(c, q)
        elif isinstance(code, Iterable):
            for c in code:
                self[c] = Stock(c, 0)
        
        return self

    def add(self, stock):
        if stock.code not in self.stocks:
            self[stock.code] = stock
        else:
            self[stock.code] += stock
        return self
    
    def sub(self, stock):
        if stock.code not in self.stocks:
            self[stock.code] = -stock
        else:
            self[stock.code] -= stock
        return self

    def __iadd__(self, other):
        return self.add(other)
    
    def __isub__(self, other):
        return self.sub(other)