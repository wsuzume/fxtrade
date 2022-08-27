from abc import ABC, abstractmethod

class ChartAPI(ABC):
    @staticmethod
    @abstractmethod
    def make_ticker(from_code, to_code):
        pass

    @abstractmethod
    def __init__(self, api_key):
        pass

    @property
    @abstractmethod
    def tickers(self):
        pass
    
    @property
    @abstractmethod
    def cranges(self):
        pass
    
    @property
    @abstractmethod
    def intervals(self):
        pass
    
    @property
    @abstractmethod
    def max_cranges(self):
        pass
    
    @property
    @abstractmethod
    def default_crange_intervals(self):
        pass
    
    @property
    @abstractmethod
    def default_timestamp_filter(self):
        pass
    
    @property
    @abstractmethod
    def default_save_fstring(self):
        pass
    
    @property
    @abstractmethod
    def default_save_iterator(self):
        pass
    
    @property
    @abstractmethod
    def empty(self):
        pass

    @abstractmethod
    def download(self, ticker, crange, interval, t, as_dataframe):
        pass
    
    def download_now(self, ticker, as_dataframe=True):
        crange, interval = self.now
        
        return self.download(ticker, crange, interval, as_dataframe)
    
    def download_maxlong(self, ticker, as_dataframe=True):
        crange, interval = self.maxlong
        
        return self.download(ticker, crange, interval, as_dataframe)

class TradeAPI(ABC):
    @staticmethod
    @abstractmethod
    def make_ticker(from_code, to_code):
        pass

    @abstractmethod
    def __init__(self, api_key, api_secret):
        pass
    
    @abstractmethod
    def minimum_order_quantity(self, code):
        pass
    
    @abstractmethod
    def maximum_order_quantity(self, code):
        pass
    
    @abstractmethod
    def get_balance(self):
        pass
    
    @abstractmethod
    def get_commission(self, product_code=None):
        pass
    
    @abstractmethod
    def get_ticker(self, code):
        pass
    
    @abstractmethod
    def get_best_bid(self, code):
        pass
    
    @abstractmethod
    def get_best_ask(self, code):
        pass
    
    @abstractmethod
    def get_history(self, start_date=None):
        pass
    
    @abstractmethod
    def buy(self, size):
        pass
    
    @abstractmethod
    def sell(self, size):
        pass