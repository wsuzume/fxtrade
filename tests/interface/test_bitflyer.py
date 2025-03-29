import pytest
from pprint import pprint

from fxtrade.interface.bitflyer import *

def test_get_markets():
    response = get_markets()
    response.raise_for_status()

def test_Market_get():
    markets = Market.get()
    for m in markets:
        assert isinstance(m, Market)

def test_get_ticker():
    response = get_ticker(product_code='BTC_JPY')
    response.raise_for_status()

def test_Ticker_get():
    ticker = Ticker.get()
    assert isinstance(ticker, Ticker)

def test_get_board():
    response = get_board(product_code='BTC_JPY')
    response.raise_for_status()

def test_Board_get():
    board = Board.get()
    assert isinstance(board, Board)

def test_get_boardstate():
    response = get_boardstate()
    response.raise_for_status()

def test_BoardState_get():
    bs = BoardState.get()
    assert isinstance(bs, BoardState)

def test_get_executions():
    response = get_executions()
    response.raise_for_status()

def test_Execution_get():
    executions = Execution.get()
    for exec in executions:
        assert isinstance(exec, Execution)

def test_get_coporateleverage():
    response = get_corporateleverage()
    response.raise_for_status()

def test_CorporateLeverage_get():
    cl = CorporateLeverage.get()
    assert isinstance(cl, CorporateLeverage)

def test_get_chats():
    response = get_chats()
    response.raise_for_status()

def test_Chat_get():
    chats = Chat.get()
    for chat in chats:
        assert isinstance(chat, Chat)