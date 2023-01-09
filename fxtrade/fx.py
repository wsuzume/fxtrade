import json

from datetime import datetime
from io import StringIO

from pathlib import Path
from typing import Iterable, Optional, Type, Union

from .api import CodePair, ChartAPI, TradeAPI
from .stock import Numeric, Stock, Rate
from .trade import Trade, History
from .chart import Chart
from .trader import Trader
from .wallet import Wallet

class FX:
    def __init__(self, origin: str, chart_api=None, trader_api=None, data_dir=None):
        self._origin = origin

        self._chart_api = chart_api
        self._trader_api = trader_api

        self._data_dir = None if data_dir is None else Path(data_dir)

        self._market = {}
    
    def __getitem__(self, key):
        return self.market[key]

    def __repr__(self):
        return self.dumps()

    def dump(self, f, indent=4):
        tab = " " * indent
        tabtab = " " * (indent * 2)
        f.write(f"FX(origin='{self.origin}',\n")
        f.write(f"{tab}data_dir='{self.data_dir}',\n")
        f.write(f"{tab}markets={{\n")
        for key, trader in self._market.items():
            f.write(f"{tabtab}'{key}': ")
            trader.dump(f, indent=indent, nest=3)
            f.write(f",\n")
        f.write(f"{tab}}}\n")
        f.write(f")")
    
    def dumps(self, indent=4):
        with StringIO() as f:
            self.dump(f, indent=indent)
            ret = f.getvalue()
        return ret

    @property
    def origin(self):
        return self._origin

    @property
    def trader_api(self):
        if self._trader_api is None:
            raise RuntimeError("default trader api is not defined")
        return self._trader_api
    
    @property
    def chart_api(self):
        if self._chart_api is None:
            raise RuntimeError("default chart api is not defined")
        return self._chart_api

    @property
    def data_dir(self):
        return self._data_dir

    @property
    def trader_dir(self):
        if self._data_dir is None:
            raise RuntimeError("data_dir not defined")
        return self._data_dir / 'trader'
    
    @property
    def chart_dir(self):
        if self._data_dir is None:
            raise RuntimeError("data_dir not defined")
        return self._data_dir / 'chart'

    @property
    def market(self):
        return self._market

#     def initial(self, q: Numeric):
#         return Stock(self.origin, q)
    
#     def terminal(self, code: str, q: Numeric):
#         return Stock(code, q)
    
    def generate_client(self,
                          code: str,
                          crange_period: Optional[Union[str, Iterable[str]]]=None,
                          key: Optional[str]=None,
                          wallet: Wallet=None,
                          history: History=None,
                          trader_api: Optional[Type[TradeAPI]]=None,
                          chart_api: Optional[Type[ChartAPI]]=None,
                          trader_dir: Optional[Union[str, Path]]=None,
                          chart_dir: Optional[Union[str, Path]]=None,
                         ):
        trader_api = trader_api if trader_api is not None else self.trader_api
        chart_api = chart_api if chart_api is not None else self.chart_api
        
        trader_dir = trader_dir if trader_dir is not None else self.trader_dir
        chart_dir = chart_dir if chart_dir is not None else self.chart_dir

        code_pair = CodePair(code, self.origin)

        chart = Chart(chart_api, code_pair=code_pair, data_dir=chart_dir, crange_period=crange_period)

        key = key if key is not None else code
        self._market[key] = Trader(
            code_pair=code_pair.copy(),
            api=trader_api,
            chart=chart,
            wallet=wallet,
            history=history,
            data_dir=trader_dir
        )

#     def create_emulator(self, emulator_dir, data_dir):
#         fx = FX(self.origin, data_dir=data_dir)
        
#         for key, trader in self.market.items():
#             fx._market[key] = trader.create_emulator(emulator_dir, fx.trader_dir, fx.chart_dir)

#         return fx

#     @property
#     def wallet(self):
#         w = Wallet()
#         for trader in self._market.values():
#             w += trader.wallet
#         return w

#     def get_wallet(self):
#         w = Wallet()
#         for trader in self._market.values():
#             w += trader.get_wallet()
#         return w

#     def sync_wallet(self):
#         for trader in self._market.values():
#             trader.sync_wallet()
#         return self.wallet
    
#     @property
#     def history(self):
#         hist = {}
#         for key, trader in self._market.items():
#             hist[key] = trader.history
#         return hist
    
#     def get_history(self, start_date=None):
#         hist = {}
#         for key, trader in self._market.items():
#             hist[key] = trader.get_history(start_date)
#         return hist

#     def sync_history(self, start_date=None):
#         hist = {}
#         for key, trader in self._market.items():
#             hist[key] = trader.sync_history(start_date)
#         return hist
    
#     def sync_chart(self):
#         for trader in self._market.values():
#             trader.sync_chart()
#         return self

#     def sync(self, start_date=None):
#         self.sync_wallet()
#         self.sync_history(start_date)
#         self.sync_chart()
#         return self
    
#     def load_chart(self, start_date=None):
#         for trader in self._market.values():
#             trader.load_chart()
#         return self
    
#     def get_max_available(self, code):
#         # 買い値
#         bid_rate = self[code].get_best_bid()
        
#         init = self.wallet[self.origin]
        
#         term = (init / bid_rate).floor(6)
#         init = (term * bid_rate).ceil(0)

#         return Trade(init, term, t=None)
    
#     def get_max_salable(self, code, commission=None):
#         commission = self[code].get_commission()

#         # 売り値
#         ask_rate = self[code].get_best_ask()

#         term = (self.wallet[code] * (1 - commission)).floor()
#         init = (term * ask_rate).ceil()

#         return Trade(term, init, t=None)
    
#     def get_last_trade(self, code):
#         last_trade = self[code].get_history(start_date=datetime(2022, 2, 1)).df.iloc[0]
        
#         return Trade.from_series(last_trade)
    
#     def buy(self, trade, code=None):
#         if code is None:
#             code = trade.y.code
#         return self[code].buy(trade)
    
#     def sell(self, trade, code=None):
#         if code is None:
#             code = trade.x.code
#         return self[code].sell(trade)
    
#     def apply(self, function, t=None):
#         return function(self, t)
    
#     def back_test(self, function, ts):
#         for t in ts:
#             trade = function(self, t)
            
#         return
    
    # def order(self, trade):
    #     if trade is None:
    #         return None
        
    #     if isinstance(trade, Trade):
    #         if trade.x.code == 'JPY':
    #             return self.buy(trade)
    #         else:
    #             return self.sell(trade)
        
    #     ret = []
    #     if isinstance(trade, Iterable):
    #         for tr in trade:
    #             ret.append(self.order(tr))
    #         return ret
        
    #     raise TypeError(f"{type(trade)} trade is not supported")
            
    # def execute(self, function):
    #     t = datetime.now()
        
    #     trade = self.apply(function, t)
        
    #     return self.order(trade)