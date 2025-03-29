import re

from datetime import timedelta
from typing import Union

from .core import type_checked

UNITS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 60 * 60 * 24,
    'w': 60 * 60 * 24 * 7,
    'S': 1,
    'M': 60,
    'H': 60 * 60,
    'D': 60 * 60 * 24,
    'W': 60 * 60 * 24 * 7,
}

MAX = ['max', 'Max', 'MAX']

def parse(s):
    s = type_checked(s, str)

    m = re.match('^(?P<quantity>[1-9][0-9]*)(?P<unit>[smhdwSMHDW])$', s)
    if m is None:
        t = -1
        u = s
    else:
        t = m['quantity']
        u = m['unit']
    
    return t, u

def to_seconds(t: Union[int, str], u: str=None):
    if u is None:
        t, u = parse(t)

    t = type_checked(t, (int, str))
    u = type_checked(u, str)

    if u not in UNITS:
        return -1
    
    if int(t) < 0:
        raise ValueError(f"t must be non-negative when u is in {MAX}.")

    return int(t) * int(UNITS[u])

def period(s):
    return to_seconds(s)

def to_period_str(dt):
    if dt.microseconds != 0:
        raise ValueError(f"microseconds is not supported.")
    if dt == timedelta(0):
        raise ValueError(f"dt == timedelta(0) is not allowed")
    
    table = {
        'd': 24 * 60 * 60,
        'h': 60 * 60,
        'm': 60,
        's': 1,
    }
    
    T = int(dt.total_seconds())
    
    for unit, length in table.items():
        c = T // length
        if (c > 0) and (T % length != 0):
            raise ValueError(f"{T} is longer than 1{unit} but is not divisible by {length}.")
        elif c > 0:
            return f"{c}{unit}"
    
    raise RuntimeError("unknown error")

DIVISORS = [
        '1d',
        '24h', '12h', '6h', '3h', '2h', '1h',
        '60m', '30m', '20m', '15m', '10m', '5m', '1m',
        '60s', '30s', '20s', '15s', '10s', '5s', '1s',
        '1D',
        '24H', '12H', '6H', '3H', '2H', '1H',
        '60M', '30M', '20M', '15M', '10M', '5M', '1M',
        '60S', '30S', '20S', '15S', '10S', '5S', '1S',
    ]

def is_divisor(s):
    if s in DIVISORS:
        return True
    
    return False

class Period:
    def __init__(self, s: str):
        if isinstance(s, Period):
            s = s.s
        
        self._s = type_checked(s, str)
        self._t, self._u = parse(self._s)
        self._seconds = to_seconds(self._s)
    
    @property
    def s(self):
        return self._s
    
    @property
    def t(self):
        return self._t
    
    @property
    def u(self):
        return self._u
    
    @property
    def seconds(self):
        return self._seconds
    
    def __repr__(self):
        return f"Period('{self.s}')"
    
    def __str__(self):
        return self.s

    def copy(self):
        return Period(self.s)

    def is_regular(self):
        return self.seconds >= 0

    def __hash__(self):
        return hash(self.s)

    def __eq__(self, other):
        if isinstance(other, int):
            return self.seconds == other
        elif isinstance(other, Period):
            if not self.is_regular() and not other.is_regular():
                return self.s == other.s
            elif not self.is_regular() and other.is_regular():
                return False
            elif self.is_regular() and not other.is_regular():
                return False
            return self.seconds == other.seconds
        raise TypeError(f"comparing is not supported between {self.__class__.__name__} and {type(other)}.")
    
    def __lt__(self, other):
        if isinstance(other, int):
            return self.seconds < other
        elif isinstance(other, Period):
            if not self.is_regular() and not other.is_regular():
                return self.s < other.s
            elif not self.is_regular() and other.is_regular():
                return True
            elif self.is_regular() and not other.is_regular():
                return False
            return self.seconds < other.seconds
        raise TypeError(f"comparing is not supported between {self.__class__.__name__} and {type(other)}.")
    
class CRange(Period):
    def __init__(self, s: str):
        super().__init__(s)
    
    def __repr__(self):
        return f"CRange('{self.s}')"

class CRangePeriod:
    def __init__(self, crange: str, period: str):
        self._crange = CRange(crange)
        self._period = Period(period)

        if self._period.seconds == -1:
            raise ValueError(f"unrecognized period '{self._period}'.")
    
    @property
    def crange(self):
        return self._crange
    
    @property
    def period(self):
        return self._period
    
    def __repr__(self):
        return f"CRangePeriod(crange='{self.crange.s}', period='{self.period.s}')"

    def __str__(self):
        return f"CRangePeriod(crange='{self.crange.s}', period='{self.period.s}')"
    
    def copy(self):
        return CRangePeriod(self.crange, self.period)
    
    @property
    def short(self):
        return '-'.join([self.crange.s, self.period.s])

    def __hash__(self):
        return hash(self.short)
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.short == other
        elif isinstance(other, CRangePeriod):
            if (self.crange == other.crange) and (self.period == other.period):
                return True
        return False
    
    def __lt__(self, other):
        if not isinstance(other, CRangePeriod):
            raise TypeError(f"comparing is not supported between {self.__class__.__name__} and {type(other)}.")
        return (self.crange, self.period) < (other.crange, other.period)