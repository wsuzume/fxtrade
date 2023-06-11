import numpy as np
import pandas as pd

from io import StringIO
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Optional, Type, Union

from .api import CodePair, TraderAPI
from .chart import Chart, ChartEmulatorAPI
from .wallet import Wallet
from .trade import Trade
from .history import History
from .period import CRangePeriod
from .stock import Stock, Rate
from .stocks import JPY, BTC
from .safeattr import SafeAttrABC, immutable, protected
from .utils import default_save_iterator

class Trader(SafeAttrABC):
    def __init__(self,
                 api: Type[TraderAPI],
                 code_pair: CodePair,
                 chart: Chart,
                 data_dir: Optional[Union[str, Path]]=None,
                 wallet: Optional[Wallet]=None,
                 history: Optional[History]=None):
        self.api = immutable(api, TraderAPI)
        self.code_pair = immutable(code_pair.copy(), CodePair)
        self.chart = immutable(chart, Chart)
        self.data_dir = immutable(data_dir, Path, f=Path, optional=True)
        
        self.wallet = protected(
            Wallet(wallet)[[self.code_pair.base, self.code_pair.quote]],
            type_=Wallet,
            optional=True
        )
        
        self.history = protected(
            History(history),
            type_=History,
            optional=True
        )

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
        f.write(f"{tab}history=")
        self.history.dump(f, indent=indent, nest=nest + 1)
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
    
    def clear(self):
        self.wallet.clear()
        self.history.clear()
        self.chart.clear()

        return self

    def create_emulator(self, trader_data_dir, chart_data_dir, trader_src_dir, chart_src_dir):
        chart = self.chart.create_emulator(data_dir=chart_data_dir, source_dir=chart_src_dir)

        chart_for_trader_api = Chart(
            code_pair=self.code_pair,
            api=self.chart.api.freeze(),
            data_dir=chart_src_dir
        )

        trader_api = TraderEmulatorAPI(
            api=self.api,
            chart=chart_for_trader_api,
            source_dir=trader_src_dir
        )

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

    # Chart wrapper
    def save_chart(self, crange_period: Union[str, Iterable[str]]=None, data_dir=None):
        return self.chart.save(crange_period=crange_period, data_dir=data_dir)

    def read_chart(self, t=None, crange_period: Union[str, Iterable[str]]=None, data_dir=None):
        return self.chart.read(t=t, crange_period=crange_period, data_dir=data_dir)

    def load_chart(self, t=None, crange_period: Union[str, Iterable[str]]=None, data_dir=None):
        return self.chart.load(t=t, crange_period=crange_period, data_dir=data_dir)

    def download_chart(self, t=None, crange_period: Union[str, Iterable[str]]=None):
        return self.chart.download(t=t, crange_period=crange_period)

    def update_chart(self, t=None, crange_period=None, interval=None, force=False):
        return self.chart.update(t=t, crange_period=crange_period, interval=interval, force=force)
    
    def sync_chart(self, t=None, crange_period=None, data_dir=None, interval=None, force=False):
        return self.chart.sync(t=t, crange_period=crange_period, data_dir=data_dir, interval=interval, force=force)

    # Trader api wrapper
    def minimum_order_quantity(self):
        """
        最小注文可能金額
        """
        return self.api.minimum_order_quantity(self.code_pair)
    
    def maximum_order_quantity(self):
        """
        最大注文可能金額
        """
        return self.api.maximum_order_quantity(self.code_pair)
    
    def get_commission(self):
        """
        取引手数料
        """
        return self.api.get_commission(self.code_pair)
    
    def get_best_bid(self):
        """
        最低買値
        """
        return self.api.get_best_bid(self.code_pair)
    
    def get_best_ask(self):
        """
        最高売値
        """
        return self.api.get_best_ask(self.code_pair)
    
    def get_max_available(self):
        """
        買い注文可能な最大量。Bitflyer の場合、実際に取引後に手に入るのはここから手数料を引いた量。
        """

        # 買い値
        bid_rate = self.get_best_bid()
        
        init = self.wallet[self.code_pair.quote]

        term = (init / bid_rate).floor(6)
        init = (term * bid_rate).ceil(0)

        return Trade(init, term, t=None)
    
    def get_max_salable(self):
        """
        売り注文可能な最大量。Bitflyer の場合、この額からさらに手数料が引かれる。
        """
        commission = self.get_commission()

        # 売り値
        ask_rate = self.get_best_ask()

        term = (self.wallet[self.code_pair.base] * (1 - commission)).floor()
        init = (term * ask_rate).ceil()

        return Trade(term, init, t=None)

    def buy(self, x: Union[Stock, Trade], t=None, *, permit=False) -> Any:
        """
        間違えて購入しないように購入する対象を明示する Stock しか許可しない。
        うっかり取引しないように permit=True を指定しないと取引は実行されない。
        サービスによってレスポンスが異なるので戻り値は API のものをそのまま返す。
        """

        if not permit:
            raise RuntimeError(f"The trade was aborted due to lack of permit=True flag.")

        if isinstance(x, Trade):
            x = x.y
        elif not isinstance(x, Stock):
            raise TypeError(f"x must be instance of Stock or Trade.")

        if x.code != self.code_pair.base:
            raise ValueError(f"This trader manipulates {self.code_pair.base} but actual code {x.code}.")

        minimum = self.minimum_order_quantity()
        maximum = self.maximum_order_quantity()
        if x < minimum:
            raise ValueError(f'{x} is under minimum order quantity {minimum}.')
        if x > maximum:
            raise ValueError(f'{x} is over maximum order quantity {maximum}.')
        
        return self.api.buy(float(x.q), t=t, wallet=self.wallet, history=self.history)
    
    def sell(self, x: Union[Stock, Trade], t=None, *, permit=False) -> Any:
        """
        間違えて購入しないように購入する対象を明示する Stock しか許可しない。
        うっかり取引しないように permit=True を指定しないと取引は実行されない。
        サービスによってレスポンスが異なるので戻り値は API のものをそのまま返す。
        """
        if not permit:
            raise RuntimeError(f"The trade was aborted due to lack of permit=True flag.")
        
        if isinstance(x, Trade):
            x = x.x
        elif not isinstance(x, Stock):
            raise TypeError(f"x must be instance of Stock or Trade.")

        if x.code != self.code_pair.base:
            raise ValueError(f"This trader manipulates {self.code_pair.base} but actual code {x.code}.")

        minimum = self.minimum_order_quantity()
        maximum = self.maximum_order_quantity()
        if x < minimum:
            raise ValueError(f'{x} is under minimum order quantity {minimum}.')
        if x > maximum:
            raise ValueError(f'{x} is over maximum order quantity {maximum}.')
            
        return self.api.sell(float(x.q), t=t, wallet=self.wallet, history=self.history)

    @property
    def wallet_dir(self):
        if self.data_dir is None:
            raise ValueError(f"wallet_dir is undefined when data_dir is None.")
        return self.data_dir / 'wallet'

    def get_wallet_path(self, path=None):
        if path is not None:
            return Path(path)
        return self.wallet_dir / 'wallet.csv'

    def save_wallet(self, path=None, t=None, append: bool=False, verbose: bool=True):
        path = self.get_wallet_path(path)

        path.parent.mkdir(parents=True, exist_ok=True)
        self.wallet.to_csv(path, t=t, append=append)

        if verbose:
            return path, 'msg'
        return path

    def read_wallet(self, path=None, return_t: bool=False, verbose: bool=False):
        path = self.get_wallet_path(path)

        if verbose:
            return Wallet.from_csv(path, code=self.code_pair, return_t=return_t), path

        return Wallet.from_csv(path, code=self.code_pair, return_t=return_t)

    def load_wallet(self, path=None, return_t: bool=False, verbose: bool=False):
        (self._wallet, t), path = self.read_wallet(path, return_t=True, verbose=True)

        if return_t and verbose:
            return (self.wallet, t), path
        elif return_t:
            return self.wallet, t
        elif verbose:
            return self.wallet, path
        return self.wallet

    def download_wallet(self):
        # codes は自動で決定。取引できる対象が trader ごとに固定されるため
        return self.api.download_wallet()[self.code_pair]
    
    def update_wallet(self):
        self._wallet = self.download_wallet()
        return self.wallet

    def sync_wallet(self, path=None, append=False, verbose: bool=False):
        self.update_wallet()
        path, msg = self.save_wallet(path, append=append, verbose=True)

        if verbose:
            return self.wallet, path, msg
        
        return self.wallet, path
    
    @property
    def history_dir(self):
        if self.data_dir is None:
            raise ValueError(f"history_dir is undefined when data_dir is None.")
        return self.data_dir / 'history'

    def save_history(self, dir_path=None):
        if dir_path is None:
            dir_path = self.history_dir

        self.history.save(dir_path)

        return dir_path
    
    def read_history(self, dir_path=None, t=None):
        if dir_path is None:
            dir_path = self.history_dir
        
        return self.history.read(dir_path)

    def load_history(self, dir_path=None, t=None):
        if dir_path is None:
            dir_path = self.history_dir

        self.history.load(dir_path)

        return dir_path

    def download_history(self, t=None) -> History:
        return self.api.download_history(t=t)
    
    def update_history(self, t=None) -> History:
        self._history = self.download_history(t=t)
        return self._history

    def sync_history(self, t=None):
        return self.update_history(t)
    
    def save(self):
        return
    
    def load(self):
        return

    def update(self):
        return
    
    def sync(self):
        return

class TraderDummyAPI(TraderAPI):
    def __init__(self):
        pass

    def __repr__(self):
        return f"TraderDummyAPI()"

    def freeze(self):
        return self

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
    
    def download_wallet(self):
        return Wallet({'JPY': 0, 'BTC': 0})

class TraderEmulatorAPI(TraderAPI):
    def __init__(self, api, chart, source_dir):
        self._api = api.freeze()
        self._chart = chart
        self._source_dir = Path(source_dir)

        self._id = 0

    def __repr__(self):
        return f"TraderEmulatorAPI(api={self._api.__class__.__name__}, source_dir='{self._source_dir}')"

    def freeze(self):
        raise RuntimeError(f"can't freeze any more.")

#         self.api = trader.api
#         self.wallet = trader.wallet.copy()
#         self.history = trader.history.copy()
#         self.chart = chart
#         self.data_dir = Path(data_dir)

    def get_commission(self, code_pair=None):
        return Fraction(3, 2000)

    def minimum_order_quantity(self, code, t=None):
        return self._api.minimum_order_quantity(code, t)
    
    def maximum_order_quantity(self, code, t=None):
        return self._api.maximum_order_quantity(code, t)
    
    def download_wallet(self):
        path = self._source_dir / 'wallet' / 'wallet.csv'
        return Wallet.from_csv(path, return_t=False)
    
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
    
    def buy(self, x, t=None, wallet=None, history=None):
        # この中に History に取引記録を追加する処理を書く
        if t is None:
            raise ValueError(f"t must be specified.")

        df = self._chart[CRangePeriod('max', '15m')].read(t=(t - timedelta(hours=1), t))

        chart = df[df.index == t].iloc[0]
        high, low = chart[['high', 'low']]

        virtual_price = np.round(np.random.uniform(low, high))

        r = Rate(from_code='BTC', to_code='JPY', r=str(virtual_price))

        base = Stock('BTC', x)
        quote = base * r

        base = base * (1 - self.get_commission())

        trade = Trade(quote, base, t=t, id=self._id)

        self._id += 1

        if quote > wallet['JPY']:
            raise ValueError("okane tarinai")

        wallet['BTC'] += base
        wallet['JPY'] -= quote

        if history is not None:
            history.add(trade)

        return trade

    def sell(self, x, t=None, wallet=None, history=None):
        if t is None:
            raise ValueError(f"t must be specified.")
        
        df = self._chart[CRangePeriod('max', '15m')].read(t=(t - timedelta(hours=1), t))

        chart = df[df.index == t].iloc[0]
        high, low = chart[['high', 'low']]

        virtual_price = np.round(np.random.uniform(low, high))

        r = Rate(from_code='BTC', to_code='JPY', r=str(virtual_price))

        base = Stock('BTC', x)
        quote = base * r

        base = base * (1 + self.get_commission())

        trade = Trade(base, quote, t=t, id=self._id)

        self._id += 1

        if base > wallet['BTC']:
            raise ValueError("okane tarinai")

        wallet['BTC'] -= base
        wallet['JPY'] += quote

        if history is not None:
            history.add(trade)

        return trade