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

    @property
    def short(self):
        return f'{self.base}-{self.quote}'

    def copy(self):
        return CodePair(self.base, self.quote)
    
    def __eq__(self, other):
        if not isinstance(other, CodePair):
            raise TypeError("cannot compare")
        
        return (self._base, self._quote) == (other._base, other._quote)