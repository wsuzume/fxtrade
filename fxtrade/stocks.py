from .stock import Stock

class USD(Stock):
    def __init__(self, quantity):
        super().__init__('USD', quantity)
    
class JPY(Stock):
    def __init__(self, quantity):
        super().__init__('JPY', quantity)

class BTC(Stock):
    def __init__(self, quantity):
        super().__init__('BTC', quantity)