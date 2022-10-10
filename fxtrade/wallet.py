import copy
import pandas as pd

from fractions import Fraction
from pathlib import Path
from typing import Iterable

from .core import is_instance_list
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

        self.join(xs)
    
    def __repr__(self):
        return f"Wallet({self.stocks})"
    
    def __getitem__(self, key):
        if isinstance(key, str):
            return self.stocks[key]
        elif is_instance_list(key, str):
            w = Wallet()
            for k in key:
                if k not in self.stocks:
                    w.stocks[k] = Stock(k, 0)
                else:
                    w.stocks[k] = self.stocks[k].copy()
            return w
        else:
            raise TypeError("")
    
    def __setitem__(self, key, val):
        # all codes must be upper case
        key = key.upper()
        if isinstance(val, Stock):
            self.stocks[key] = val
        else:
            self.stocks[key] = Stock(key, val)

    def copy(self):
        return Wallet(self)

    @property
    def codes(self):
        return list(self.stocks.keys())
    
    def filter_stocks(self, codes=None):
        if codes is None:
            return self
        elif isinstance(codes, str):
            if codes not in self.stocks:
                raise ValueError(f"'{codes}' not in Wallet({self.stocks})")
            self.stocks = { codes: self.stocks[codes] }
        elif is_instance_list(codes, str):
            for code in codes:
                if code not in self.stocks:
                    raise ValueError(f"'{code}' not in Wallet({self.stocks})")
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

    def join(self, x: str):
        if x is None:
            return self
        elif isinstance(x, str):
            self[x] = Stock(x, 0)
        elif isinstance(x, Stock):
            self[x.code] = x.copy()
        elif isinstance(x, Wallet):
            for stock in x.stocks.values():
                self[stock.code] = stock.copy()
        elif isinstance(x, pd.Series):
            for c, q in x.iteritems():
                self[c] = Stock(c, q)
        elif is_instance_list(x, str):
            for c in x:
                self[c] = Stock(c, 0)
        elif is_instance_list(x, Stock):
            for stock in x:
                self[stock.code] = stock.copy()
        else:
            raise TypeError("unsupported type")
        
        return self

    def add(self, x):
        if isinstance(x, Wallet):
            for stock in x.stocks.values():
                self.add(stock)
        elif isinstance(x, Stock):
            if x.code not in self.stocks:
                self[x.code] = x
            else:
                self[x.code] += x
        return self
    
    def sub(self, x):
        if isinstance(x, Wallet):
            for stock in x.stocks.values():
                self.sub(stock)
        elif isinstance(x, Stock):
            if x.code not in self.stocks:
                self[x.code] = -x
            else:
                self[x.code] -= x
        return self

    def __add__(self, x):
        return self.copy().add(x)
    
    def __sub__(self, x):
        return self.copy().sub(x)
    
    def __iadd__(self, x):
        return self.add(x)
    
    def __isub__(self, x):
        return self.sub(x)