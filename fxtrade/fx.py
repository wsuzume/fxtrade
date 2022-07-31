from datetime import datetime

from typing import Iterable

from .stock import Rate
from .trade import Trade

class FX:
    def __init__(self, wallet, chart, trader):
        self.wallet = wallet
        self.chart = chart
        self.trader = trader
    
    def create_emulator(self, root_dir):
        new_chart = self.chart.create_emulator(root_dir)
        new_trader = self.trader.create_emulator()
        return FX(self.wallet.copy(), new_chart, new_trader)
    
    def sync_wallet(self, codes=None):
        self.wallet = self.trader.get_wallet(codes)
        return self.wallet
    
    def update_history(self, start_date):
        self.trader.history = self.trader.get_history(start_date)
        return self.trader.history
    
    def get_max_available(self, code=None):
        # 買い値
        bid_rate = self.trader.get_best_bid(code=code)
        
        jpy = self.wallet['JPY']
        
        btc = (jpy / bid_rate).floor(6)
        jpy = (btc * bid_rate).ceil(0)

        return Trade(jpy, btc, t=None)
    
    def get_max_salable(self, code=None, commission=None):
        commission = self.trader.get_commission()

        # 売り値
        ask_rate = self.trader.get_best_ask(code=code)

        btc = (self.wallet['BTC'] * (1 - commission)).floor()
        jpy = (btc * ask_rate).ceil()

        return Trade(btc, jpy, t=None)
    
    def get_last_trade(self):
        last_trade = self.trader.get_history(start_date=datetime(2022, 2, 1)).df.iloc[0]
        
        return Trade.from_series(last_trade)
    
    def buy(self, trade):
        return self.trader.buy(trade)
    
    def sell(self, trade):
        return self.trader.sell(trade)
    
    def apply(self, function, t=None):
        return function(self, t)
    
    def back_test(self, function, ts):
        for t in ts:
            trade = function(self, t)
            
        return
    
    def order(self, trade):
        if trade is None:
            return None
        
        if isinstance(trade, Trade):
            if trade.x.code == 'JPY':
                return self.buy(trade)
            else:
                return self.sell(trade)
        
        ret = []
        if isinstance(trade, Iterable):
            for tr in trade:
                ret.append(self.order(tr))
            return ret
        
        raise TypeError(f"{type(trade)} trade is not supported")
            
    def execute(self, function):
        t = datetime.now()
        
        trade = self.apply(function, t)
        
        return self.order(trade)