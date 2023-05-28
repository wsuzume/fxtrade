import pytest
import pandas as pd

from pathlib import Path

from fxtrade.stock import Stock
from fxtrade.wallet import Wallet

def test_join():
    w = Wallet()

    w.join(None)
    assert len(w) == 0

    w.join('MSFT')
    assert 'MSFT' in w
    assert w['MSFT'] == Stock('MSFT', 0)

    w.join(Stock('AAPL', 10))
    assert w['AAPL'] == Stock('AAPL', 10)

    w.join(['A', 'B', 'C', 'D'])
    assert 'A' in w
    assert 'B' in w
    assert 'C' in w
    assert 'D' in w

    w.join(pd.Series([10, 20, 30, 40], index=['E', 'F', 'G', 'H']))
    assert 'E' in w
    assert 'F' in w
    assert 'G' in w
    assert 'H' in w

    w.join([
        Stock('I', 60),
        Stock('J', 70),
        Stock('K', 80),
    ])
    assert 'I' in w
    assert 'J' in w
    assert 'K' in w

    with pytest.raises(TypeError):
        w.join(123)
    
    w2 = Wallet(Stock('L', 90))
    w.join(w2)

    assert 'L' in w

def test_add_sub():
    w = Wallet()

    w.add(Stock('BTC', 5))
    w.add(Stock('BTC', 3))

    assert w['BTC'] == Stock('BTC', 8)

    w.sub(Stock('BTC', 2))

    assert w['BTC'] == Stock('BTC', 6)

    w2 = Wallet(Stock('BTC', 4))
    w.add(w2)

    assert w['BTC'] == Stock('BTC', 10)


    w1 = Wallet(Stock('BTC', 6))
    w2 = Wallet(Stock('BTC', 4))

    w3 = w1 - w2
    assert w1['BTC'] == Stock('BTC', 6)
    assert w2['BTC'] == Stock('BTC', 4)
    assert w3['BTC'] == Stock('BTC', 2)

def test_codes():
    w = Wallet(['A', 'B', 'C'])

    assert w.codes == ['A', 'B', 'C']

def test_io():
    w = Wallet([
        Stock('USD', 60),
        Stock('BTC', 70),
        Stock('ETH', 80),
    ])

    Path('./tests/data').mkdir(exist_ok=True)
    path = Path('./tests/data/wallet.csv')

    path.unlink(missing_ok=True)

    w.to_csv(path)
    w2 = Wallet.from_csv(path)

    assert w2['USD'] == 60
    assert w2['BTC'] == 70
    assert w2['ETH'] == 80

    w += Stock('USD', 100)

    w.to_csv(path)
    w2 = Wallet.from_csv(path)

    assert w2['USD'] == 160
    assert w2['BTC'] == 70
    assert w2['ETH'] == 80

    df = Wallet.read_csv(path)

    assert len(df) == 2

    path.unlink(missing_ok=True)