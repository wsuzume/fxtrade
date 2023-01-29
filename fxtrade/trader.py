from io import StringIO
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Optional, Type, Union

from .trade import History
from .api import CodePair, TraderAPI
from .chart import Chart
# from .dirmap import DirMap
from .wallet import Wallet

from .stocks import JPY, BTC

class Trader:
    def __init__(self,
                 api: Type[TraderAPI],
                 code_pair: CodePair,
                 chart: Chart,
                 wallet: Wallet=None,
                 history: History=None,
                 data_dir: Optional[Union[str, Path]]=None):
        self.api = api
        self.code_pair = code_pair.copy()
        self.chart = chart
        self.wallet = Wallet(wallet)[[self.code_pair.base, self.code_pair.quote]]
        self.history = History(history)
        self.data_dir = data_dir
    
    def __getitem__(self, key):
        return self.chart[key]

    def __repr__(self):
        return self.dumps()

    def dump(self, f, indent=4, nest=1):
        tab = " " * indent * nest
        last_tab = " " * (indent * (nest - 1))
        f.write(f"Trader(api={self.api},\n")
        f.write(f"{tab}code_pair={self.code_pair},\n")
        f.write(f"{tab}data_dir='{self.data_dir}',\n")
        f.write(f"{tab}wallet=")
        self.wallet.dump(f, indent=indent, nest=nest + 1)
        f.write(f",\n")
        f.write(f"{tab}chart=")
        self.chart.dump(f, indent=indent, nest=nest + 1)
        f.write(f"\n")
        f.write(f"{last_tab})")
    
    def dumps(self, indent=4):
        with StringIO() as f:
            self.dump(f, indent=indent)
            ret = f.getvalue()
        return ret
    
    def create_emulator(self, trader_data_dir, chart_data_dir, trader_src_dir, chart_src_dir):
        trader_api = TraderEmulatorAPI(api=self.api, source_dir=trader_src_dir)
        chart = self.chart.create_emulator(data_dir=chart_data_dir, source_dir=chart_src_dir)

        return Trader(
            api=trader_api,
            code_pair=self.code_pair,
            chart=chart,
            wallet=self.wallet,
            history=self.history,
            data_dir=trader_data_dir,
        )
        # chart = self.chart.create_emulator(emulator_dir, chart_dir)
        # api = TraderEmulatorAPI(self, chart, emulator_dir)
        # return Trader(code_pair=self.code_pair, api=api, chart=chart, wallet=self.wallet, history=self.history, data_dir=trader_dir)
    
#     def get_wallet(self, codes=None):
#         return self.api.get_balance().filter_stocks(codes)
    
#     def sync_wallet(self, codes=None):
#         if codes is None:
#             codes = self.wallet.codes
#         self.wallet = self.get_wallet(codes)
#         return self.wallet
    
#     def get_chart(self, code=None, t=None):
#         return self.api.get_chart(code, t=t)
    
#     def get_best_bid(self):
#         code = self.api.make_code_pair(self.code_pair)
#         return self.api.get_best_bid(code=code)
    
#     def get_best_ask(self):
#         code = self.api.make_code_pair(self.code_pair)
#         return self.api.get_best_ask(code=code)
    
#     def get_commission(self):
#         return self.api.get_commission()
    
#     def get_history(self, start_date=None):
#         return self.api.get_history(start_date)

#     def sync_history(self, start_date=None):
#         self.history = self.get_history(start_date)
#         return self.history

#     def get_chart(self, t=None):
#         return self.chart.download(t=t)

#     def load_chart(self, t=None):
#         return self.chart.load(t=t)

#     def sync_chart(self, crange_interval: Union[str, Iterable[str]]=None, t=None, data_dir=None, update: bool=True, save: bool=True):
#         return self.chart.sync(crange_interval, t, data_dir, update, save)
    
#     def minimum_order_quantity(self, code):
#         return self.api.minimum_order_quantity(code)
    
#     def maximum_order_quantity(self, code):
#         return self.api.maximum_order_quantity(code)
    
#     def buy(self, trade):
#         if trade.y < self.minimum_order_quantity(trade.y.code):
#             raise ValueError('under minimum')
#         if trade.y > self.maximum_order_quantity(trade.y.code):
#             raise ValueError('over maximum')
        
#         return self.api.buy(float(trade.y.q), t=trade.t)
    
#     def sell(self, trade):
#         if trade.x < self.minimum_order_quantity(trade.x.code):
#             raise ValueError('under minimum')
#         if trade.x > self.maximum_order_quantity(trade.x.code):
#             raise ValueError('over maximum')
            
#         return self.api.sell(float(trade.x.q), t=trade.t)

class TraderDummyAPI(TraderAPI):
    def __init__(self):
        pass

    def __repr__(self):
        return f"TraderDummyAPI()"

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

class TraderEmulatorAPI(TraderAPI):
    def __init__(self, api, source_dir=None):
        self._api = api.freeze()
        self._source_dir = source_dir
    
    def __repr__(self):
        return f"TraderEmulatorAPI(api={self._api.__class__.__name__}, source_dir='{self._source_dir}')"

    def freeze(self):
        raise RuntimeError(f"can't freeze any more.")
        
#         self.api = trader.api
#         self.wallet = trader.wallet.copy()
#         self.history = trader.history.copy()
#         self.chart = chart
#         self.data_dir = Path(data_dir)

#     def minimum_order_quantity(self, code, t=None):
#         qs = {
#             'BTC': BTC('0.001'),
#         }
#         return qs[code]
    
#     def maximum_order_quantity(self, code, t=None):
#         qs = {
#             'BTC': BTC('1000'),
#         }
#         return qs[code]
    
#     def get_balance(self, t=None):
#         return self.wallet.copy()
    
#     def get_commission(self, product_code=None, t=None):
#         return Fraction('0.0015')
    
#     def get_best_bid_and_ask(self, code, t=None):
#         crange_interval = self.chart.api.default_crange_interval
#         ret = self.chart.download(crange_interval, t=t)[crange_interval].iloc[-1]
#         return {
#             'timestamp': ret.name,
#             'best_bid': ret['high'],
#             'best_ask': ret['low'],
#         }
    
#     def get_best_bid(self, code, t=None):
#         ret = self.chart.download('1mo-15m', t=t)['1mo-15m'].iloc[-1]
#         return ret['high']
    
#     def get_best_ask(self, code, t=None):
#         ret = self.chart.download('1mo-15m', t=t)['1mo-15m'].iloc[-1]
#         return ret['low']
    
#     def get_history(self, start_date=None, t=None):
#         return self.history
    
#     def buy(self, size, t=None):
#         return f"Buy({size})", t

#     def sell(self, size, t=None):
#         return f"Sell({size})", t