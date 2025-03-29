from .stock import Stock

class USD(Stock):
    """
    Child class of Stock, which code is bound to "USD".
    """
    def __init__(self, q):
        """
        Parameters
        ----------
        q : Numeric
            Quantity of the stock.
        """
        super().__init__('USD', q)
    
class JPY(Stock):
    """
    Child class of Stock, which code is bound to "JPY".
    """
    def __init__(self, q):
        """
        Parameters
        ----------
        q : Numeric
            Quantity of the stock.
        """
        super().__init__('JPY', q)

class BTC(Stock):
    """
    Child class of Stock, which code is bound to "BTC".
    """
    def __init__(self, q):
        """
        Parameters
        ----------
        q : Numeric
            Quantity of the stock.
        """
        super().__init__('BTC', q)