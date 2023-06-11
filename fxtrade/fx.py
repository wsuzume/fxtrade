import json
import glob

from datetime import datetime
from io import StringIO

from pathlib import Path
from typing import Any, Iterable, Optional, Type, Union

from .core import type_checked, is_instance_list
from .safeattr import SafeAttrABC, immutable, protected
from .api import CodePair, ChartAPI, TraderAPI
from .stock import Numeric, Stock, Rate
from .trade import Trade
from .history import History
from .chart import Chart, ChartEmulatorAPI
from .trader import Trader, TraderEmulatorAPI
from .wallet import Wallet
from .logger import Logger, is_logger

def assert_valid_name(name):
    if name == '':
        raise ValueError(f"null string is not allowed for name.")

    return True

class FX(SafeAttrABC):
    def __init__(self,
            name: str,
            origin: str,
            chart_api: Type[ChartAPI]=None,
            trader_api: Type[TraderAPI]=None,
            data_dir: Optional[Union[str, Path]]=None,
            logger: Any=None):
        self.name = immutable(name, str)
        assert_valid_name(self.name)

        self.origin = immutable(origin, str)
        self.chart_api = immutable(chart_api, ChartAPI, optional=True)
        self.trader_api = immutable(trader_api, TraderAPI, optional=True)

        data_dir = Path(data_dir) / self.name if data_dir is not None else None
        self.data_dir = immutable(data_dir, Path, f=Path, optional=True)
        
        self.market = protected({}, dict)

        self.logger = immutable(self.set_logger(logger))

    
    def __getitem__(self, key):
        return self.market[key]

    def __repr__(self):
        return self.dumps()

    def dump(self, f, indent=4):
        tab = " " * indent
        tabtab = " " * (indent * 2)
        f.write(f"FX(name='{self.name}',\n")
        f.write(f"{tab}origin='{self.origin}',\n")
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
    def trader_dir(self):
        if self.data_dir is None:
            raise RuntimeError("data_dir not defined")
        return self.data_dir / 'trader'
    
    @property
    def chart_dir(self):
        if self.data_dir is None:
            raise RuntimeError("data_dir not defined")
        return self.data_dir / 'chart'

    @property
    def log_dir(self):
        if self.data_dir is None:
            raise RuntimeError("data_dir is not defined")
        return self.data_dir / 'log'
    
    def get_market(self, key=None):
        if key is None:
            market = self._market
        elif isinstance(key, str):
            market = { key: self._market[key] }
        elif is_instance_list(key, str):
            market = { k: self._market[k] for k in key }
        else:
            raise TypeError(f"key must be instance of NoneType, str, Iterable[str].")
        
        return market
    
    def generate_client(self,
                          code: str,
                          crange_period: Optional[Union[str, Iterable[str]]]=None,
                          key: Optional[str]=None,
                          wallet: Wallet=None,
                          history: History=None,
                          trader_api: Optional[Type[TraderAPI]]=None,
                          chart_api: Optional[Type[ChartAPI]]=None,
                          trader_dir: Optional[Union[str, Path]]=None,
                          chart_dir: Optional[Union[str, Path]]=None,
                         ):
        trader_api = trader_api if trader_api is not None else self.trader_api
        chart_api = chart_api if chart_api is not None else self.chart_api
        
        trader_dir = Path(trader_dir) if trader_dir is not None else self.trader_dir
        chart_dir = Path(chart_dir) if chart_dir is not None else self.chart_dir

        code_pair = CodePair(code, self.origin)

        chart = Chart(
            code_pair=code_pair,
            api=chart_api,
            data_dir=chart_dir,
            crange_period=crange_period
        )

        key = key if key is not None else code
        self._market[key] = Trader(
            code_pair=code_pair.copy(),
            api=trader_api,
            chart=chart,
            wallet=wallet,
            history=history,
            data_dir=trader_dir
        )
    
    def set_logger(self,
                   logger: Any=None,
                   log_dir: Optional[Union[str, Path]]=None
                  ):
        log_dir = Path(log_dir) if log_dir is not None else self.log_dir

        if logger is None:
            self._logger = Logger(self.name, None)
        else:
            if not is_logger(logger):
                raise ValueError(f"not logger.")
            self._logger = logger

        return self._logger

    def _list_data_dir(self):
        xs = sorted(glob.glob(str(self._data_dir / '*')))
        return [ Path(x).name for x in xs ]
    
    def clear(self):
        for key in self.market.keys():
            self.market[key].clear()
        return self

    def create_emulator(self, name, data_dir=None, trader_src_dir=None, chart_src_dir=None):
        name = type_checked(name, str)
        assert_valid_name(name)

        data_dir = Path(data_dir) if data_dir is not None else Path(self._data_dir)
        trader_src_dir = Path(trader_src_dir) \
            if trader_src_dir is not None else Path(self.trader_dir)
        chart_src_dir = Path(chart_src_dir) \
            if chart_src_dir is not None else Path(self.chart_dir)

        fx = FX(name=name, origin=self.origin, data_dir=data_dir)

        if (fx._data_dir.absolute() == self._data_dir.absolute()) \
            and (fx.name in self._list_data_dir()):
            # Saving emulator's data in true trader's data directory is very dangerous.
            # And if using the same name with true traders, it will destroy true data. 
            raise ValueError(f"'{fx.name}' is already exists in '{fx._data_dir}'.")
        
        for key, trader in self._market.items():
            fx._market[key] = trader.create_emulator(
                                trader_data_dir=fx.trader_dir,
                                chart_data_dir=fx.chart_dir,
                                trader_src_dir=trader_src_dir,
                                chart_src_dir=chart_src_dir,
                              )

        return fx

    @property
    def wallet(self):
        w = Wallet()
        for trader in self._market.values():
            w += trader.wallet
        return w
    
    @property
    def wallets(self):
        ws = {}
        for key, trader in self._market.items():
            ws[key] = trader.wallet.copy()
        return ws

    def save_wallet(self, key=None, t=None, append=False, verbose=False):
        market = self.get_market(key)

        if len(market) == 0:
            self.logger.info(f"FX save_wallet() ... no trader to save.")
        paths = {}
        for key, trader in market.items():
            path, msg = trader.save_wallet(t=t, append=append, verbose=True)
            paths[key] = path

            if verbose:
                self.logger.info(msg)

            self.logger.info(f"FX['{key}'] save_wallet() -> '{path}'.")

        return paths
    
    def read_wallet(self, key=None, total=False):
        market = self.get_market(key)

        if len(market) == 0:
            self.logger.info(f"FX read_wallet() ... no trader to read.")
        
        ws = {}
        for key, trader in market.items():
            w, path = trader.read_wallet(return_t=False, verbose=True)
            ws[key] = w
            self.logger.info(f"FX['{key}'] read_wallet() <- '{path}'.")
        
        if not total:
            return ws
        
        return Wallet.total(ws)

    def load_wallet(self, key=None, total=False):
        market = self.get_market(key)

        if len(market) == 0:
            self.logger.info(f"FX load_wallet() ... no trader to load.")
        for key, trader in market.items():
            _, path = trader.load_wallet(return_t=False, verbose=True)
            self.logger.info(f"FX['{key}'] load_wallet() <- '{path}'.")
        
        if not total:
            return self.wallets
        
        return self.wallet

    def download_wallet(self, key=None, total=False):
        market = self.get_market(key)

        if len(market) == 0:
            self.logger.info(f"FX download_wallet() ... no trader to download.")

        ws = {}
        for key, trader in market.items():
            ws[key] = trader.download_wallet()
            self.logger.info(f"FX['{key}'] download_wallet() <- {trader.api}.")
        
        if not total:
            return ws
        
        return Wallet.total(ws)
    
    def update_wallet(self, key=None, total=False):
        market = self.get_market(key)

        if len(market) == 0:
            self.logger.info(f"FX update_wallet() ... no trader to update.")
        
        for key, trader in market.items():
            trader.update_wallet()
            self.logger.info(f"FX['{key}'] update_wallet() <- {trader.api}.")
        
        if not total:
            return self.wallets
        
        return self.wallet
    
    def sync_wallet(self, key=None, total=False, verbose: bool=False):
        market = self.get_market(key)

        if len(market) == 0:
            self.logger.info(f"FX sync_wallet() ... no trader to sync.")
        
        for key, trader in market.items():
            _, path, msg = trader.sync_wallet(verbose=True)

            if verbose:
                self.logger.info(msg)

            self.logger.info(f"FX['{key}'] sync_wallet() <- {trader.api} -> {path}.")
        
        if not total:
            return self.wallets
        
        return self.wallet
    
    def save_chart(self, crange_period: Union[str, Iterable[str]]=None, data_dir=None):
        ret = {}
        for name, trader in self._market.items():
            ret[name] = trader.sync_chart(crange_period=crange_period, data_dir=data_dir)
        return ret

    def read_chart(self, t=None, crange_period: Union[str, Iterable[str]]=None, data_dir=None):
        ret = {}
        for name, trader in self._market.items():
            ret[name] = trader.read_chart(t=t, crange_period=crange_period, data_dir=data_dir)
        return ret

    def load_chart(self, t=None, crange_period: Union[str, Iterable[str]]=None, data_dir=None):
        ret = {}
        for name, trader in self._market.items():
            ret[name] = trader.load_chart(t=t, crange_period=crange_period, data_dir=data_dir)
        return ret

    def download_chart(self, t=None, crange_period: Union[str, Iterable[str]]=None):
        ret = {}
        for name, trader in self._market.items():
            ret[name] = trader.download_chart(t=t, crange_period=crange_period)
        return ret

    def update_chart(self, t=None, crange_period=None, interval=None, force=False):
        ret = {}
        for name, trader in self._market.items():
            ret[name] = trader.update_chart(t=t, crange_period=crange_period, interval=interval, force=force)
        return ret

    def sync_chart(self, t=None, crange_period=None, data_dir=None, interval=None, force=False):
        ret = {}
        for name, trader in self._market.items():
            ret[name] = trader.sync_chart(t=t, crange_period=crange_period, data_dir=data_dir, interval=interval, force=force)
        return ret

    def save(self):
        pass

    def load(self):
        pass

    def update(self):
        pass

    def sync(self):
        pass

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