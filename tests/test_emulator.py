# from fxtrade.interface.yfinance import YahooFinanceAPI
# from fxtrade.emulator import ChartEmulatorAPI, TraderEmulatorAPI

# def test_ChartEmulatorAPI():
#     chart_api = YahooFinanceAPI(api_key='***')

#     assert 'BTC-JPY' == ChartEmulatorAPI.make_ticker('BTC', 'JPY')

#     api = ChartEmulatorAPI(api=chart_api)

#     assert 'BTC-JPY' in api.tickers
#     assert 'USD-JPY' in api.tickers

#     assert '10y' in api.cranges
#     assert '1mo' in api.cranges
#     assert '5d' in api.cranges

#     assert '1d' in api.intervals
#     assert '15m' in api.intervals
#     assert '1m' in api.intervals

#     assert '10y' == api.max_cranges['1d']
#     assert '1mo' == api.max_cranges['15m']
#     assert '5d' == api.max_cranges['1m']

#     assert ('10y', '1d') == api.default_crange_intervals['10y-1d']
#     assert ('1mo', '15m') == api.default_crange_intervals['1mo-15m']
#     assert ('5d', '1m') == api.default_crange_intervals['5d-1m']

#     assert '10y-1d' in api.default_timestamp_filter
#     assert '1mo-15m' in api.default_timestamp_filter
#     assert '5d-1m' in api.default_timestamp_filter

#     assert '10y-1d' in api.default_save_fstring
#     assert '1mo-15m' in api.default_save_fstring
#     assert '5d-1m' in api.default_save_fstring

#     assert '10y-1d' in api.default_save_iterator
#     assert '1mo-15m' in api.default_save_iterator
#     assert '5d-1m' in api.default_save_iterator

#     assert api.empty.shape == (0, 6)
    
#     # with pytest.raises(HTTPError):
#     #     # this code will be resulted in 403 client error because
#     #     # we didn't specify the api_key
#     #     api.download('BTC-JPY', '10y', '1d')


# def test_TraderEmulatorAPI():
#     pass