import copy

class Wallet:
    def __init__(self):
        self.stocks = {}
    
    def __repr__(self):
        return f"Wallet({self.stocks})"
    
    def __getitem__(self, key):
        return self.stocks[key]
    
    def copy(self):
        w = Wallet()
        w.stocks = copy.deepcopy(self.stocks)
        return w
    
    def filter_stocks(self, codes=None):
        if codes is None:
            return self
        
        self.stocks = { k: v for k, v in self.stocks.items() if k in codes }
        return self
    
    def add(self, stock):
        if stock.code not in self.stocks:
            self.stocks[stock.code] = stock
        else:
            self.stocks[stock.code] += stock
    
    def sub(self, stock):
        if stock.code not in self.stocks:
            self.stocks[stock.code] = -stock
        else:
            self.stocks[stock.code] -= stock