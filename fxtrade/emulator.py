class Emulator:
    def __init__(self, ticker, date_dir):
        self.ticker = ticker
        self.dirmap = DirMap(root_dir=Path(data_dir) / ticker)
        self.dfs = {}

class ChartEmulatorAPI:
    def __init__(self):
        pass

class TraderEmulatorAPI:
    def __init__(self):
        pass