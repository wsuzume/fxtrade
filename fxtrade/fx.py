class FX:
    def __init__(self, chart, trade_api, history):
        self.chart = chart
        self.trade_api = trade_api
        self.history = history
    
    def apply(self, function):
        return function(chart, history)