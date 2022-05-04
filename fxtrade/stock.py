from fractions import Fraction
from typing import Union, Optional

Numeric = Union[int, str, Fraction]

def can_be_precise_num(x):
    return isinstance(x, int) or isinstance(x, str) or isinstance(x, Fraction)

def as_numeric(x):
    if x is None:
        return None
    if not can_be_precise_num(x):
        raise TypeError("x must be type of int, str, or fractions.Fraction")
    return x if isinstance(x, Fraction) else Fraction(x)

class Stock:
    def __init__(self, code: str, q: Numeric):
        if not isinstance(code, str):
            raise TypeError("code must be type of str")
        
        self.code = code
        self._q = as_numeric(q)

    @property
    def q(self):
        return self._q
        
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
        return Stock(self.code, abs(self.q))
    
    def __pos__(self):
        return Stock(self.code, +self.q)
    
    def __neg__(self):
        return Stock(self.code, -self.q)
    
    def __lt__(self, other):
        if self._is_same_stock(other):
            return self.q < other.q
        return self.q < other
        
    def __le__(self, other):
        if self._is_same_stock(other):
            return self.q <= other.q
        return self.q <= other
    
    def __eq__(self, other):
        if self._is_same_stock(other):
            return self.q == other.q
        return self.q == other
    
    def __ne__(self, other):
        if self._is_same_stock(other):
            return self.q != other.q
        return self.q != other
    
    def __gt__(self, other):
        if self._is_same_stock(other):
            return self.q > other.q
        return self.q > other
    
    def __ge__(self, other):
        if self._is_same_stock(other):
            return self.q >= other.q
        return self.q >= other
    
    def __add__(self, other):
        if self._is_same_stock(other):
            return Stock(self.code, self.q + other.q)
        return Stock(self.code, self.q + other)
    
    def __radd__(self, other):
        return Stock(self.code, self.q + as_numeric(other))
    
    def __sub__(self, other):
        if self._is_same_stock(other):
            return Stock(self.code, self.q - other.q)
        return Stock(self.code, self.q - other)
        
    def __rsub__(self, other):
        return Stock(self.code, as_numeric(other) - self.q)
    
    def __mul__(self, other):
        if isinstance(other, Rate):
            return other * self
        return Stock(self.code, self.q * as_numeric(other))
    
    def __rmul__(self, other):
        return Stock(self.code, self.q * as_numeric(other))
    
    def __truediv__(self, other):
        if isinstance(other, Rate):
            return ~other * self
        return Stock(self.code, self.q / as_numeric(other))
    
    def __floordiv__(self, other):
        return Stock(self.code, self.q // as_numeric(other))
    
    def __mod__(self, other):
        return Stock(self.code, self.q % as_numeric(other))
    
    def __pow__(self, other, modulo=None):
        return Stock(self.code, pow(self.q, as_numeric(other), as_numeric(modulo)))

class Rate:
    @classmethod
    def from_stocks(cls, before, after):
        if not isinstance(before, Stock) or not isinstance(after, Stock):
            raise TypeError(f"both before and after must be type of Stock")
        return Rate(before.code, after.code, after.q / before.q)
    
    def __init__(self, from_code: str, to_code: str, r: Numeric):
        if not isinstance(from_code, str):
            raise TypeError("from_code must be type of str")
        if not isinstance(to_code, str):
            raise TypeError("to_code must be type of str")
        
        self.from_code = from_code
        self.to_code = to_code
        self._r = as_numeric(r)
    
    @property
    def r(self):
        return self._r
    
    def __repr__(self):
        return f"Rate({self.from_code}->{self.to_code}: {float(self.r)})"
    
    def __invert__(self):
        return Rate(self.to_code, self.from_code, 1 / self.r)
    
    def _is_chainable(self, other):
        if isinstance(other, Rate) and (self.to_code == other.from_code):
            return True
        if isinstance(other, Stock) and (self.from_code == other.code):
            return True
        return False
    
    def __eq__(self, other):
        if not isinstance(other, Rate):
            raise TypeError(f"comparison undefined between Rate and {type(other)}")
        
        if (self.from_code == other.from_code) \
            and (self.to_code == other.to_code) \
            and (self.r == other.r):
            return True
        
        return False
    
    def __ne__(self, other):
        return not (self == other)
    
    def __mul__(self, other):
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
        return Rate(self.from_code, self.to_code, self.r * as_numeric(other))
    
    def __truediv__(self, other):
        if isinstance(other, Rate):
            if not self._is_chainable(other):
                raise TypeError(f"cannot be chained {self} and {other}")
            return Rate(self.from_code, other.to_code, self.r / other.r)
        
        return Rate(self.from_code, self.to_code, self.r / as_numeric(other))
    
    def __rtruediv__(self, other):
        return as_numeric(other) * ~self
    
    def __pow__(self, other, modulo=None):
        if self.from_code != self.to_code:
            raise TypeError(f"from_code and to_code must be the same but now {self.from_code} and {self.to_code}")
        return Rate(self.from_code, self.to_code, pow(self.r, as_numeric(other), as_numeric(modulo)))

