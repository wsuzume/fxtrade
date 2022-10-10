from abc import ABC, abstractmethod
from fractions import Fraction
from typing import Union

from .stock import Stock, Rate
from .ticker import Ticker
from .trade import Trade, FailedTrade, History
from .wallet import Wallet

class ChartAPI(ABC):
    @staticmethod
    def make_ticker(from_code, to_code):
        return f"{from_code}-{to_code}"

    @staticmethod
    def make_crange_interval(crange, interval):
        return f"{crange}-{interval}"

    @abstractmethod
    def __init__(self, api_key):
        pass

    @property
    @abstractmethod
    def tickers(self):
        pass
    
    @property
    @abstractmethod
    def cranges(self):
        pass
    
    @property
    @abstractmethod
    def intervals(self):
        pass
    
    @property
    @abstractmethod
    def max_cranges(self):
        pass
    
    @property
    def default_crange_interval(self):
        pass

    @property
    @abstractmethod
    def default_crange_intervals(self):
        pass
    
    @property
    @abstractmethod
    def default_timestamp_filter(self):
        pass
    
    @property
    @abstractmethod
    def default_save_fstring(self):
        pass
    
    @property
    @abstractmethod
    def default_save_iterator(self):
        pass
    
    @property
    @abstractmethod
    def empty(self):
        pass

    @abstractmethod
    def download(self, ticker, crange, interval, t, as_dataframe):
        pass
    
    def download_now(self, ticker, as_dataframe=True):
        crange, interval = self.now
        
        return self.download(ticker, crange, interval, as_dataframe)
    
    def download_maxlong(self, ticker, as_dataframe=True):
        crange, interval = self.maxlong
        
        return self.download(ticker, crange, interval, as_dataframe)

class TradeAPI(ABC):
    @staticmethod
    def make_ticker(from_code, to_code) -> str:
        return f"{from_code}-{to_code}"

    @staticmethod
    def make_currency_pair(pair):
        return f"{pair.terminal}-{pair.initial}"

    @abstractmethod
    def __init__(self, api_key, api_secret):
        pass
    
    @abstractmethod
    def minimum_order_quantity(self, code) -> Stock:
        pass
    
    @abstractmethod
    def maximum_order_quantity(self, code) -> Stock:
        pass
    
    @abstractmethod
    def get_balance(self) -> Wallet:
        pass
    
    @abstractmethod
    def get_commission(self, product_code=None) -> Fraction:
        pass
    
    @abstractmethod
    def get_ticker(self, code) -> Ticker:
        pass
    
    @abstractmethod
    def get_best_bid(self, code) -> Rate:
        pass
    
    @abstractmethod
    def get_best_ask(self, code) -> Rate:
        pass
    
    @abstractmethod
    def get_history(self, start_date=None) -> History:
        pass
    
    @abstractmethod
    def buy(self, size) -> Union[Trade, FailedTrade]:
        pass
    
    @abstractmethod
    def sell(self, size) -> Union[Trade, FailedTrade]:
        pass