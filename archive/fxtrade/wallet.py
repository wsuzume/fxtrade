import copy
import pandas as pd

from fractions import Fraction
from pathlib import Path
from typing import Iterable

from .api import CodePair
from .core import is_instance_list, is_instance_dict
from .stock import Numeric, Stock

class Wallet:
    @staticmethod
    def read_csv(path):
        path = Path(path)
        return pd.read_csv(path, index_col=0, parse_dates=True).applymap(Fraction)

    @classmethod
    def from_dataframe(cls, df, code=None, return_t=False):
        stocks = df.sort_index().iloc[-1]
        w = Wallet(stocks).filter_stocks(code)
        if return_t:
            return w, stocks.name
        return w
    
    @classmethod
    def from_csv(cls, path, code=None, return_t=False):
        df = cls.read_csv(path)
        return Wallet.from_dataframe(df, code, return_t)

    @staticmethod
    def total(ws):
        wallet = Wallet()
        if isinstance(ws, Wallet):
            wallet += ws
        elif is_instance_dict(ws, vt=Wallet):
            for w in ws.values():
                wallet += w
        elif is_instance_list(ws, Wallet):
            for w in ws:
                wallet += w
        
        return wallet

    """
    Manage your stocks.
    """
    def __init__(self, stock=None):
        self._stocks = {}

        self.join(stock)
    
    def __repr__(self):
        return f"Wallet({self._stocks})"
    
    def __len__(self):
        return len(self._stocks)
    
    def __contains__(self, key):
        return key in self._stocks
    
    def __getitem__(self, key):
        if isinstance(key, str):
            return self._stocks[key]
        elif isinstance(key, CodePair):
            return self[[key.quote, key.base]]
        elif is_instance_list(key, str):
            w = Wallet()
            for k in key:
                if k not in self._stocks:
                    w._stocks[k] = Stock(k, 0)
                else:
                    w._stocks[k] = self._stocks[k].copy()
            return w
        else:
            raise TypeError("")
    
    def __setitem__(self, key, val):
        if isinstance(val, Stock):
            self._stocks[key] = val
        else:
            self._stocks[key] = Stock(key, val)

    def copy(self):
        return Wallet(self)
    
    def clear(self):
        stocks = {}

        for key, stock in self._stocks.items():
            stocks[key] = Stock(stock.code, 0)
        
        self._stocks = stocks

        return self

    def dump(self, f, indent=2, nest=1):
        tab = " " * indent * nest
        last_tab = " " * (indent * (nest - 1))
        f.write(f"Wallet({{\n")
        for code, q in self._stocks.items():
            f.write(f"{tab}'{code}': {q},\n")
        f.write(f"{last_tab}}})")

    @property
    def codes(self):
        return list(self._stocks.keys())
    
    def filter_stocks(self, code=None):
        if code is None:
            return self
        elif isinstance(code, str):
            if code not in self._stocks:
                raise ValueError(f"'{code}' not in Wallet({self._stocks})")
            self._stocks = { code: self._stocks[code] }
        elif isinstance(code, CodePair):
            if code.base not in self._stocks:
                raise ValueError(f"'{code.base}' not in Wallet({self._stocks})")
            if code.quote not in self._stocks:
                raise ValueError(f"'{code.quote}' not in Wallet({self._stocks})")
            self._stocks = { c: self._stocks[c] for c in [code.base, code.quote] }
        elif is_instance_list(code, str):
            for code in code:
                if code not in self._stocks:
                    raise ValueError(f"'{code}' not in Wallet({self._stocks})")
            self._stocks = { k: v for k, v in self._stocks.items() if k in code }
        
        return self
    
    @property
    def df(self):
        return self.to_dataframe()

    def to_dataframe(self, t=None):
        if t is None:
            t = pd.Timestamp.now().round('S')

        cols = [ k for k in self._stocks.keys() ]
        vals = [ v.q for v in self._stocks.values() ]

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
            for stock in x._stocks.values():
                self[stock.code] = stock.copy()
        elif isinstance(x, pd.Series):
            for c, q in x.items():
                self[c] = Stock(c, q)
        elif is_instance_list(x, str):
            for c in x:
                self[c] = Stock(c, 0)
        elif is_instance_list(x, Stock):
            for stock in x:
                self[stock.code] = stock.copy()
        elif is_instance_dict(x, kt=str, vt=Numeric):
            for k, v in x.items():
                self[k] = Stock(k, v)
        else:
            raise TypeError(f"unsupported type '{x}'")
        
        return self

    def __eq__(self, other):
        ret = (set(self._stocks.keys()) == set(other._stocks.keys()))
        for code, stock in self._stocks.items():
            if code not in other:
                return False
            ret &= (stock == other[code])
        return ret

    def add(self, x):
        if isinstance(x, Wallet):
            for stock in x._stocks.values():
                self.add(stock)
        elif isinstance(x, Stock):
            if x.code not in self._stocks:
                self[x.code] = x
            else:
                self[x.code] += x
        return self
    
    def sub(self, x):
        if isinstance(x, Wallet):
            for stock in x._stocks.values():
                self.sub(stock)
        elif isinstance(x, Stock):
            if x.code not in self._stocks:
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