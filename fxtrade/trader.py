from fractions import Fraction
from pathlib import Path
from typing import Iterable, Optional, Type, Union

from .trade import History
from .api import TradeAPI
from .chart import Chart
from .dirmap import DirMap
from .stock import CurrencyPair
from .wallet import Wallet

from .stocks import JPY, BTC

class Trader:
    def __init__(self,
                 currency_pair: CurrencyPair,
                 api: Type[TradeAPI],
                 chart: Chart,
                 wallet: Wallet=None,
                 history: History=None,
                 data_dir: Optional[Union[str, Path]]=None):
        self.currency_pair = currency_pair.copy()
        self.api = api
        self.chart = chart
        self.wallet = Wallet(wallet)[[self.currency_pair.initial, self.currency_pair.terminal]]
        self.history = History(history)
        self.data_dir = data_dir
    
    def create_emulator(self, emulator_dir, trader_dir, chart_dir):
        chart = self.chart.create_emulator(emulator_dir, chart_dir)
        api = TraderEmulatorAPI(self, chart, emulator_dir)
        return Trader(currency_pair=self.currency_pair, api=api, chart=chart, wallet=self.wallet, history=self.history, data_dir=trader_dir)
    
    def get_wallet(self, codes=None):
        return self.api.get_balance().filter_stocks(codes)
    
    def sync_wallet(self, codes=None):
        if codes is None:
            codes = self.wallet.codes
        self.wallet = self.get_wallet(codes)
        return self.wallet
    
    def get_ticker(self, code=None, t=None):
        return self.api.get_ticker(code, t=t)
    
    def get_best_bid(self):
        code = self.api.make_currency_pair(self.currency_pair)
        return self.api.get_best_bid(code=code)
    
    def get_best_ask(self):
        code = self.api.make_currency_pair(self.currency_pair)
        return self.api.get_best_ask(code=code)
    
    def get_commission(self):
        return self.api.get_commission()
    
    def get_history(self, start_date=None):
        return self.api.get_history(start_date)

    def sync_history(self, start_date=None):
        self.history = self.get_history(start_date)
        return self.history

    def get_chart(self, t=None):
        return self.chart.download(t)

    def sync_chart(self, crange_interval: Union[str, Iterable[str]]=None, t=None, data_dir=None, update: bool=True, save: bool=True):
        return self.chart.sync(crange_interval, t, data_dir, update, save)
    
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
        self.wallet = trader.wallet.copy()
        self.history = trader.history.copy()
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
    
    def get_balance(self, t=None):
        return self.wallet.copy()
    
    def get_commission(self, product_code=None, t=None):
        return Fraction('0.0015')
    
    def get_ticker(self, code, t=None):
        crange_interval = self.chart.api.default_crange_interval
        ret = self.chart.download(crange_interval, t=t)[crange_interval].iloc[-1]
        return {
            'timestamp': ret.name,
            'best_bid': ret['high'],
            'best_ask': ret['low'],
        }
    
    def get_best_bid(self, code, t=None):
        ret = self.chart.download('1mo-15m', t=t)['1mo-15m'].iloc[-1]
        return ret['high']
    
    def get_best_ask(self, code, t=None):
        ret = self.chart.download('1mo-15m', t=t)['1mo-15m'].iloc[-1]
        return ret['low']
    
    def get_history(self, start_date=None, t=None):
        return self.history
    
    def buy(self, size, t=None):
        pass

    def sell(self, size, t=None):
        pass