class FX:
    def __init__(self, chart, trader):
        self.chart = chart
        self.trader = trader
    
    def create_emulator(self, root_dir):
        new_chart = self.chart.create_emulator(root_dir)
        new_trader = self.trader.create_emulator()
        return FX(new_chart, new_trader)
    
    def buy(self, trade):
        print(trade)
    
    def apply(self, function, t):
        return function(self, t)
    
    def back_test(self, function, ts):
        for t in ts:
            trade = function(self, t)
            
        return