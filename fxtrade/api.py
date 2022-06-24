from abc import ABC, abstractmethod

class ChartAPI(ABC):
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
    def max_crange(self):
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
    
    @property
    @abstractmethod
    def now(self):
        pass
    
    @property
    @abstractmethod
    def maxlong(self):
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
    @abstractmethod
    def __init__(self, api_key, api_secret):
        pass