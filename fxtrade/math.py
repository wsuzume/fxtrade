import math
from fractions import Fraction


def floor(x: float | Fraction, n: int = 6) -> float:
    """
    Return floor at the specified digit.

    Parameters
    ----------
    n : int, default 6
        Specify the n-th decimal place. Must be non-negative number.
    """
    p = 10**n
    return math.floor(float(x * p)) / p
