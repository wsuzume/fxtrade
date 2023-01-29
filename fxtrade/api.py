import pandas as pd

from abc import ABC, abstractmethod
from fractions import Fraction
from typing import Callable, List, Optional, Union

from .core import type_checked
from .stock import Stock, Rate
# from .ticker import Ticker
from .trade import Trade, FailedTrade, History
from .wallet import Wallet

class CodePair:
    """
    The base currency is the first currency in a currency pair.
    The second is the quote or counter currency.
    The quote for the currency pair shows how much of the quote currency
    it takes to purchase one unit of the other.
    """
    def __init__(self, base: str, quote: str):
        self._base = str(base)
        self._quote = str(quote)
    
    @property
    def base(self):
        return self._base
    
    @property
    def quote(self):
        return self._quote
    
    def __repr__(self):
        return f"CodePair(base='{self.base}', quote='{self.quote}')"

    def __str__(self):
        return f"CodePair(base='{self.base}', quote='{self.quote}')"

    def copy(self):
        return CodePair(self.base, self.quote)

class CrangePeriod:
    def __init__(self, crange: str, period: str):
        self._crange = crange
        self._period = period
    
    @property
    def crange(self):
        return self._crange
    
    @property
    def period(self):
        return self._period
    
    def __repr__(self):
        return f"CrangePeriod(crange='{self.crange}', period='{self.period}')"

    def __str__(self):
        return f"CrangePeriod(crange='{self.crange}', period='{self.period}')"
    
    def copy(self):
        return CrangePeriod(self.crange, self.period)
    
    @property
    def short(self):
        return '-'.join([self.crange, self.period])

    def __hash__(self):
        return hash(self.short)
    
    def __eq__(self, other):
        if isinstance(other, CrangePeriod):
            if self.crange == other.crange and self.period == other.period:
                return True
        return False

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
    def crange_period_from_string(s: str) -> CrangePeriod:
        xs = type_checked(s, str).split('-')

        if len(xs) != 2:
            raise ValueError("format must be '{crange}-{period}'")
        
        crange, period = xs
        return CrangePeriod(crange, period)

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def freeze(self):
        pass

#     @property
#     @abstractmethod
#     def code_pairs(self) -> List[CodePair]:
#         pass
    
#     @property
#     @abstractmethod
#     def cranges(self) -> List[str]:
#         pass
    
#     @property
#     @abstractmethod
#     def periods(self) -> List[str]:
#         pass
    
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

#     @property
#     @abstractmethod
#     def default_crange_periods(self) -> List[str]:
#         pass
    
#     @property
#     @abstractmethod
#     def default_timestamp_filter(self) -> Callable:
#         pass
    
#     @property
#     @abstractmethod
#     def default_save_fstring(self) -> str:
#         pass
    
#     @property
#     @abstractmethod
#     def default_save_iterator(self) -> Callable:
#         pass
    
    @property
    @abstractmethod
    def empty(self) -> pd.DataFrame:
        pass

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
    
#     @abstractmethod
#     def minimum_order_quantity(self, code) -> Stock:
#         pass
    
#     @abstractmethod
#     def maximum_order_quantity(self, code) -> Stock:
#         pass
    
#     @abstractmethod
#     def get_wallet(self) -> Wallet:
#         pass
    
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
