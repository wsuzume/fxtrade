import pandas as pd

from abc import ABC, abstractmethod
from fractions import Fraction
from typing import Callable, List, Optional, Union

from .core import type_checked
from .code import CodePair
from .period import CRangePeriod
from .stock import Stock
from .wallet import Wallet

class ChartAPI(ABC):
    @staticmethod
    def make_code_pair_string(base: Union[str, CodePair], quote: Optional[str]=None) -> str:
        if isinstance(base, str):
            return f"{base}-{quote}"
        elif isinstance(base, CodePair):
            return f"{base.base}-{base.quote}"
        raise TypeError("unrecognized type arguments")

    @staticmethod
    def make_crange_period_string(crange_period) -> str:
        return f"{crange_period.crange}-{crange_period.period}"
    
    @staticmethod
    def code_pair_from_string(s: str) -> CodePair:
        xs = type_checked(s, str).split('-')

        if len(xs) != 2:
            raise ValueError("format must be '{base}-{quote}'")

        base, quote = xs
        return CodePair(base, quote)

    @staticmethod
    def crange_period_from_string(s: str) -> CRangePeriod:
        xs = type_checked(s, str).split('-')

        if len(xs) != 2:
            raise ValueError("format must be '{crange}-{period}'")
        
        crange, period = xs
        return CRangePeriod(crange, period)

    @abstractmethod
    def __init__(self,
                 crange_periods,
                 timestamp_filter,
                 save_fstring,
                 save_iterator):
        self._crange_periods = crange_periods
        self._timestamp_filter = timestamp_filter
        self._save_fstring = save_fstring
        self._save_iterator = save_iterator

    @abstractmethod
    def freeze(self):
        pass

    @property
    @abstractmethod
    def empty(self) -> pd.DataFrame:
        pass

#     @property
#     @abstractmethod
#     def code_pairs(self) -> List[CodePair]:
#         pass
    
    @property
    @abstractmethod
    def cranges(self) -> List[str]:
        pass
    
    @property
    @abstractmethod
    def periods(self) -> List[str]:
        pass
    
#     @property
#     @abstractmethod
#     def max_cranges(self) -> List[str]:
#         pass
    
    @property
    @abstractmethod
    def default_crange_period(self) -> str:
        pass

    @abstractmethod
    def is_valid_crange_period(self, crange_period: str) -> bool:
        pass

    @property
    @abstractmethod
    def default_crange_periods(self) -> List[str]:
        pass
    
    # @property
    # @abstractmethod
    # def default_timestamp_filter(self) -> Callable:
    #     pass
    
    # @property
    # @abstractmethod
    # def default_save_fstring(self) -> str:
    #     pass
    
    # @property
    # @abstractmethod
    # def default_save_iterator(self) -> Callable:
    #     pass
    

#     @abstractmethod
#     def download(self, code_pair, crange, period, t, as_dataframe: bool) -> pd.DataFrame:
#         pass

class TraderAPI(ABC):
    # @staticmethod
    # def make_ticker(from_code, to_code) -> str:
    #     return f"{from_code}-{to_code}"

    # @staticmethod
    # def make_code_pair_string(pair) -> str:
    #     return f"{pair.quote}-{pair.base}"

    @staticmethod
    def make_code_pair_string(base: Union[str, CodePair], quote: Optional[str]=None) -> str:
        if isinstance(base, str):
            return f"{base}-{quote}"
        elif isinstance(base, CodePair):
            return f"{base.base}-{base.quote}"
        raise TypeError("unrecognized type arguments")

    @abstractmethod
    def __init__(self, api_key, api_secret):
        pass

    @abstractmethod
    def freeze(self):
        pass
    
    @abstractmethod
    def minimum_order_quantity(self, code, t) -> Stock:
        pass
    
    @abstractmethod
    def maximum_order_quantity(self, code, t) -> Stock:
        pass
    
    @abstractmethod
    def download_wallet(self) -> Wallet:
        pass
    
#     @abstractmethod
#     def get_commission(self, product_code=None) -> Fraction:
#         pass
    
#     @abstractmethod
#     def get_best_bid_and_ask(self, code) -> Ticker:
#         pass
    
#     @abstractmethod
#     def get_best_bid(self, code) -> Rate:
#         pass
    
#     @abstractmethod
#     def get_best_ask(self, code) -> Rate:
#         pass
    
#     @abstractmethod
#     def get_history(self, start_date=None) -> History:
#         pass
    
#     @abstractmethod
#     def buy(self, size, t=None) -> Union[Trade, FailedTrade]:
#         pass
    
#     @abstractmethod
#     def sell(self, size, t=None) -> Union[Trade, FailedTrade]:
#         pass
