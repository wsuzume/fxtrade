
class FX:
    def __init__(self, chart, trader):
        self.chart = chart
        self.trader = trader
    
    def apply(self, function, t):
        return function(self, t)
    
    def back_test(self, function, ts):
        
        for t in ts:
            trade = function(self, t)
            
        return