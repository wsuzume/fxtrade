from pathlib import Path
from typing import Optional, Type, Union

from .trade import History
from .api import TradeAPI
from .dirmap import DirMap

class Trader:
    def __init__(self,
                 api: Type[TradeAPI],
                 history: History=None,
                 data_dir: Optional[Union[str, Path]]=None):
        self.api = api
        self.history = history
        self.dirmap = DirMap(root_dir=Path(data_dir))
        
    def create_emulator(self):
        return None