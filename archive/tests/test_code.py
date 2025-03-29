import pytest

from fxtrade.code import CodePair

def test_CodePair():
    codepair = CodePair('BTC', 'JPY')
    
    assert codepair.base == 'BTC'
    assert codepair.quote == 'JPY'

    codepair2 = codepair.copy()

    assert codepair2.base == 'BTC'
    assert codepair2.quote == 'JPY'