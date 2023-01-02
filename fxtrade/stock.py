""" Deals with stocks and operations on them.
"""

import math
import warnings

import numpy as np

from fractions import Fraction
from typing import Any, Union, Optional

_FLOAT_PRECISE_DIGIT_NUMBER = 6

Numeric = Union[int, str, float, Fraction]

def can_be_precise_num(x: Any) -> bool:
    """
    Return whether the value can be calculated with precision.
    """
    if isinstance(x, float):
        x = str(x)
        # +1 is for point
        if len(x) <= _FLOAT_PRECISE_DIGIT_NUMBER + 1:
            return True
        warnings.warn(UserWarning(
            "using float and the number of digits may be too large: " + \
            "the accuracy of the calculation may be lost. use str, int, " + \
            "or fractions.Fraction instead."))
        return False
    
    return isinstance(x, int) or isinstance(x, str) or isinstance(x, Fraction)

def as_numeric(x: Any):
    """
    Convert numbers to fractions.Fraction for accuracy.
    """
    if x is None:
        return None
    if not can_be_precise_num(x):
        raise TypeError("x must be type of str, int, float, or fractions.Fraction")
    
    x = x if not isinstance(x, float) else str(x)

    return x if isinstance(x, Fraction) else Fraction(x)

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
    
    def __str__(self):
        return f"CodePair(base='{self.base}', quote='{self.quote}')"

    def copy(self):
        return CodePair(self.base, self.quote)

class Stock:
    """
    Stock consists from code and quantity.
    """
    def __init__(self, code: str, q: Numeric):
        """
        Parameters
        ----------
        code : str
            Product code or name of the stock.
        q : Numeric
            Quantity of the stock.
        """
        if not isinstance(code, str):
            raise TypeError("code must be type of str")
        
        self._code = str(code)
        self._q = as_numeric(q)

    @property
    def code(self) -> str:
        """
        Return its code.
        """
        return self._code

    @property
    def q(self) -> Fraction:
        """
        Return its quantity.
        """
        return self._q
    
    def copy(self):
        return Stock(self.code, self.q)

    def floor(self, n: int=6):
        """
        Return floor at the specified digit.

        Parameters
        ----------
        n : int, default 6
            Specify the n-th decimal place. Must be non-negative number.
        """
        p = 10 ** n
        return Stock(self.code, str(math.floor(float(self.q) * p) / p))
    
    def ceil(self, n: int=0):
        """
        Return ceil at the specified digit.

        Parameters
        ----------
        n : int, default 0
            Specify the n-th decimal place. Must be non-negative number.
        """
        p = 10 ** n
        return Stock(self.code, str(math.ceil(float(self.q) * p) / p))
    
    def __repr__(self):
        return f"Stock({self.code}, {self.q})"
    
    def _is_same_stock(self, other):
        if not isinstance(other, Stock):
            return False
        if self.code != other.code:
            raise TypeError(f"operation undefined between {self.code} and {other.code}")
        return True
    
    def _is_numeric(self, other):
        if not isinstance(other, Fraction):
            raise TypeError(f"other must be instance of fractions.Fraction")
    
    def __abs__(self):
        """Return absolute of the stock.
        """
        return Stock(self.code, abs(self.q))
    
    def __pos__(self):
        """Return positive of the stock.
        """
        return Stock(self.code, +self.q)
    
    def __neg__(self):
        """Return negative of the stock.
        """
        return Stock(self.code, -self.q)
    
    def __lt__(self, other):
        """Compare the stocks if the codes are the same.
        Else try to compare the stock quantity with the other.
        """
        if self._is_same_stock(other):
            return self.q < other.q
        return self.q < other
        
    def __le__(self, other):
        """Compare the stocks if the codes are the same.
        Else try to compare the stock quantity with the other.
        """
        if self._is_same_stock(other):
            return self.q <= other.q
        return self.q <= other
    
    def __eq__(self, other):
        """Compare the stocks if the codes are the same.
        Else try to compare the stock quantity with the other.
        """
        if self._is_same_stock(other):
            return self.q == other.q
        return self.q == other
    
    def __ne__(self, other):
        """Compare the stocks if the codes are the same.
        Else try to compare the stock quantity with the other.
        """
        if self._is_same_stock(other):
            return self.q != other.q
        return self.q != other
    
    def __gt__(self, other):
        """Compare the stocks if the codes are the same.
        Else try to compare the stock quantity with the other.
        """
        if self._is_same_stock(other):
            return self.q > other.q
        return self.q > other
    
    def __ge__(self, other):
        """Compare the stocks if the codes are the same.
        Else try to compare the stock quantity with the other.
        """
        if self._is_same_stock(other):
            return self.q >= other.q
        return self.q >= other
    
    def __add__(self, other):
        """Return sum of the stocks if the codes are the same.
        If the other is not instance of Stock, try to add the other to the stock quantity.
        """
        if self._is_same_stock(other):
            return Stock(self.code, self.q + other.q)
        return Stock(self.code, self.q + other)
    
    def __radd__(self, other):
        """Try to add the other to the stock quantity.
        """
        return Stock(self.code, self.q + as_numeric(other))
    
    def __sub__(self, other):
        """Return difference between the stocks if the codes are the same.
        If the other is not instance of Stock, try to subtract the other from the stock quantity.
        """
        if self._is_same_stock(other):
            return Stock(self.code, self.q - other.q)
        return Stock(self.code, self.q - other)
        
    def __rsub__(self, other):
        """Try to subtract the stock quantity from the other.
        """
        return Stock(self.code, as_numeric(other) - self.q)
    
    def __mul__(self, other):
        """Try to multiply the other to the stock if the other is instance of Rate.
        Else try to multiply the other to the stock quantity.
        """
        if isinstance(other, Rate):
            return other * self
        return Stock(self.code, self.q * as_numeric(other))
    
    def __rmul__(self, other):
        """Try to multiply the other to the stock quantity.
        """
        return Stock(self.code, self.q * as_numeric(other))
    
    def __truediv__(self, other):
        """Try to multiply inverse of the other to the stock if the other is instance of Rate.
        Else try to divide the stock quantity by other.
        """
        if isinstance(other, Rate):
            return ~other * self
        return Stock(self.code, self.q / as_numeric(other))
    
    def __floordiv__(self, other):
        """Try to divide the stock quantity by the other.
        """
        return Stock(self.code, self.q // as_numeric(other))
    
    def __mod__(self, other):
        """Try to return the remainder of the stock quantity divided by the other.
        """
        return Stock(self.code, self.q % as_numeric(other))
    
    def __pow__(self, other, modulo=None):
        """Try to return the stock powered by the other.
        """
        return Stock(self.code, pow(self.q, as_numeric(other), as_numeric(modulo)))

class Rate:
    """
    Deal with the trading rate of the stock. 
    Since the concept of large/small of rate is determined by
    the from_code and the to_code relatively,
    a large/small comparison is not supported.
    """
    @classmethod
    def from_stocks(cls, before: Stock, after: Stock):
        """
        Return the rate at which A is converted to B.
        """
        if not isinstance(before, Stock) or not isinstance(after, Stock):
            raise TypeError(f"both before and after must be type of Stock")
        return Rate(before.code, after.code, after.q / before.q)
    
    def __init__(self, from_code: str, to_code: str, r: Numeric):
        """
        Parameters
        ----------
        from_code : str
            Product code before conversion.
        to_code : str
            Product code after conversion.
        r : Numeric
            Conversion rate.
        """
        if not isinstance(from_code, str):
            raise TypeError("from_code must be type of str")
        if not isinstance(to_code, str):
            raise TypeError("to_code must be type of str")
        
        self._from_code = from_code
        self._to_code = to_code
        self._r = as_numeric(r)
    
    @property
    def from_code(self):
        """Product code before conversion.
        """
        return self._from_code
    
    @property
    def to_code(self):
        """Product code after conversion.
        """
        return self._to_code

    @property
    def r(self):
        """Conversion rate.
        """
        return self._r
    
    def __repr__(self):
        return f"Rate({self.from_code}->{self.to_code}: {float(self.r)})"
    
    def __invert__(self):
        """
        Swap from_code and to_code, and take the reciprocal for r.
        """
        return Rate(self.to_code, self.from_code, 1 / self.r)
    
    def _is_chainable(self, other):
        if isinstance(other, Rate) and (self.to_code == other.from_code):
            return True
        if isinstance(other, Stock) and (self.from_code == other.code):
            return True
        return False
    
    def __eq__(self, other):
        """True iff from_code, to_code, and r are all the same.
        """
        if not isinstance(other, Rate):
            raise TypeError(f"comparison undefined between Rate and {type(other)}")
        
        if (self.from_code == other.from_code) \
            and (self.to_code == other.to_code) \
            and (self.r == other.r):
            return True
        
        return False
    
    def __ne__(self, other):
        """Inverse of __eq__.
        """
        return not (self == other)

    def __mul__(self, other):
        """Try to chain the other if it is instance of Rate.
        Else if the other is instance of Stock, try to convert with the rate.
        Else try to multiply the other to r.
        """
        if isinstance(other, Rate):
            if not self._is_chainable(other):
                raise TypeError(f"cannot be chained {self} and {other}")
            return Rate(self.from_code, other.to_code, self.r * other.r)
        
        if isinstance(other, Stock):
            if not self._is_chainable(other):
                raise TypeError(f"cannot be chained {self} and {other}")
            return Stock(self.to_code, self.r * other.q)
        
        return Rate(self.from_code, self.to_code, self.r * as_numeric(other))
    
    def __rmul__(self, other):
        """
        Try to multiply the other to r.
        """
        return Rate(self.from_code, self.to_code, self.r * as_numeric(other))
    
    def __truediv__(self, other):
        """Try to chain the ~other if it is instance of Rate.
        Else try to devide r by the other.
        """
        if isinstance(other, Rate):
            return self * ~other
        
        return Rate(self.from_code, self.to_code, self.r / as_numeric(other))
    
    def __rtruediv__(self, other):
        """Try to multiply the other to ~self.
        """
        return as_numeric(other) * ~self
    
    def __pow__(self, other, modulo=None):
        """Try to be powered by the other.
        """
        if self.from_code != self.to_code:
            raise TypeError(f"from_code and to_code must be the same but now {self.from_code} and {self.to_code}")
        return Rate(self.from_code, self.to_code, pow(self.r, as_numeric(other), as_numeric(modulo)))

