from datetime import datetime
from typing import Iterable, Mapping, Optional

from fxtrade.fx import FX
from fxtrade.trade import Trade

def trade_algorithm(
            fx: FX,
            t: datetime,
        ) -> Iterable[Trade]:
    """
    Parameters
    ----------
    fx : FX
        FX クラスのインスタンス
    t : datetime.datetime
        現在時刻 または 取引判断を行う時刻
    
    Returns
    -------
    Iterable[Trade]
        実行する取引のリスト(またはイテラブル)
    """
    
    # 取引する通貨とその額を決める
    trades = ...
    
    return trades

def baseline(
            fx: FX,
            t: datetime,
        ) -> Iterable[Trade]:
    """
    Parameters
    ----------
    fx : FX
        FX クラスのインスタンス
    t : datetime.datetime
        現在時刻 または 取引判断を行う時刻
    
    Returns
    -------
    Iterable[Trade]
        実行する取引のリスト(またはイテラブル)
    """
    
    df = fx.chart.download('10y-1d', t=t)
    
    #print(t)
    #display(df)
    
    # 取引する通貨とその額を決める
    trades = [5]
    
    return trades