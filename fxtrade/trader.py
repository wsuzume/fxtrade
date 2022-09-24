from fractions import Fraction
from pathlib import Path
from typing import Optional, Type, Union

from .trade import History
from .api import TradeAPI
from .dirmap import DirMap
from .wallet import Wallet

from .stocks import JPY, BTC

class Trader:
    def __init__(self,
                 api: Type[TradeAPI],
                 history: History=None,
                 data_dir: Optional[Union[str, Path]]=None):
        self.api = api
        self.history = history
    
    def create_emulator(self, chart, data_dir):
        api = TraderEmulatorAPI(self, chart, data_dir)
        history = None if self.history is None else self.history.copy()
        return Trader(api=api, history=history, data_dir=None)
    
    def get_wallet(self, codes=None):
        return self.api.get_balance().filter_stocks(codes)
    
    def get_ticker(self, code=None):
        return self.api.get_ticker(code)
    
    def get_best_bid(self, code=None):
        return self.api.get_best_bid(code=code)
    
    def get_best_ask(self, code=None):
        return self.api.get_best_ask(code=code)
    
    def get_commission(self):
        return self.api.get_commission()
    
    def get_history(self, start_date=None):
        return self.api.get_history(start_date)
    
    def minimum_order_quantity(self, code):
        return self.api.minimum_order_quantity(code)
    
    def maximum_order_quantity(self, code):
        return self.api.maximum_order_quantity(code)
    
    def buy(self, trade):
        if trade.y < self.minimum_order_quantity(trade.y.code):
            raise ValueError('under minimum')
        if trade.y > self.maximum_order_quantity(trade.y.code):
            raise ValueError('over maximum')
        
        return self.api.buy(float(trade.y.q))
    
    def sell(self, trade):
        if trade.x < self.minimum_order_quantity(trade.x.code):
            raise ValueError('under minimum')
        if trade.x > self.maximum_order_quantity(trade.x.code):
            raise ValueError('over maximum')
            
        return self.api.sell(float(trade.x.q))

class TraderEmulatorAPI(TradeAPI):
    def __init__(self, trader, chart, data_dir):
        self.api = trader.api
        self.chart = chart
        self.data_dir = Path(data_dir)

    def minimum_order_quantity(self, code, t=None):
        qs = {
            'BTC': BTC('0.001'),
        }
        return qs[code]
    
    def maximum_order_quantity(self, code, t=None):
        qs = {
            'BTC': BTC('1000'),
        }
        return qs[code]
    
    def get_balance(self, t):
        path = self.data_dir / 'wallet.json'
        pass
    
    def get_commission(self, product_code=None, t=None):
        return Fraction('0.0015')
    
    def get_ticker(self, code, t=None):
        pass
    
    def get_best_bid(self, code, t=None):
        pass
    
    def get_best_ask(self, code, t=None):
        pass
    
    def get_history(self, start_date=None, t=None):
        pass
    
    def buy(self, size, t=None):
        pass

    def sell(self, size, t=None):
        pass