import warnings

import numpy as np
import pandas as pd

from copy import deepcopy
from datetime import datetime, timedelta
from io import StringIO
from glob import glob
from pathlib import Path
from types import EllipsisType
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, Iterable, Mapping

# from .analysis import log10
from .api import CodePair, CRangePeriod, ChartAPI
from .core import type_checked, type_checked_copy, is_instance_list, is_instance_dict
from .period import Period

from .timeseries import year_sections, month_sections, day_sections
from .utils import focus, standardize, \
    default_timestamp_filter, default_save_fstring, default_save_iterator, \
    default_glob_function, default_save_function, \
    default_restore_function, default_merge_function

from .safeattr import immutable, protected, SafeAttrABC

class Board(SafeAttrABC):
    default_glob_function = default_glob_function
    default_save_function = default_save_function
    default_restore_function = default_restore_function
    default_merge_function = default_merge_function

    def __init__(self,
                 code_pair: Union[str, CodePair],
                 crange_period: Union[str, CRangePeriod],
                 name: Union[str, CRangePeriod]=None,
                 api: Type[ChartAPI]=None,
                 data_dir: Optional[Union[str, Path]]=None,
                 df: Optional[pd.DataFrame]=None,
                 interval: Optional[Union[timedelta, Period]]=None,
                 timestamp_filter: Optional[Callable[[datetime], bool]]=None,
                 save_fstring: Optional[str]=None,
                 save_iterator: Optional[Callable[[datetime, datetime], Iterable[Tuple[datetime, datetime]]]]=None,
                 glob_function=default_glob_function,
                 save_function=default_save_function,
                 restore_function=default_restore_function,
                 merge_function=default_merge_function,
                 ):
        self.name = immutable(name, (str, CRangePeriod), optional=True)
        self.api = immutable(api, ChartAPI, optional=True)

        self.code_pair = immutable(code_pair, (str, CodePair), copy=True)
        self.crange_period = immutable(crange_period, (str, CRangePeriod), copy=True)
        
        self.data_dir = immutable(data_dir, Path, f=Path, optional=True)

        if df is None and self.api is not None:
            df = self.api.empty

        self.df = protected(df, pd.DataFrame, optional=True, copy=True)
        self.interval = protected(interval, (timedelta, Period), optional=True, copy=True)

        self.glob_function = immutable(glob_function)
        self.save_function = immutable(save_function)
        self.restore_function = immutable(restore_function)
        self.merge_function = immutable(merge_function)

        if self.period not in { Period('1d'), Period('15m'), Period('1m') }:
            if timestamp_filter is None:
                raise KeyError(f"{self.period} not in table.")
            if save_fstring is None:
                raise KeyError(f"{self.period} not in table.")
            if save_iterator is None:
                raise KeyError(f"{self.period} not in table.")

        self.timestamp_filter = immutable(
            timestamp_filter if timestamp_filter is not None 
                             else default_timestamp_filter(self.period)
        )

        self.save_fstring = immutable(
            save_fstring if save_fstring is not None
                         else default_save_fstring(self.period)
        )

        self.save_iterator = immutable(
            save_iterator if save_iterator is not None
                          else default_save_iterator(self.period)
        )
    
    def __repr__(self):
        return self.dumps()

    def dump(self, f, indent=2, nest=1):
        tab = " " * indent * nest
        last_tab = " " * (indent * (nest - 1))
        if isinstance(self.name, str):
            f.write(f"Board(name='{self.name}',\n")
        else:
            f.write(f"Board(name={self.name},\n")
        f.write(f"{tab}api={self.api},\n")
        f.write(f"{tab}code_pair={self.code_pair},\n")
        f.write(f"{tab}crange_period={self.crange_period},\n")
        if isinstance(self.data_dir, Path):
            f.write(f"{tab}data_dir='{self.data_dir}',\n")
        else:
            f.write(f"{tab}data_dir={self.data_dir},\n")
        f.write(f"{tab}interval={self.interval},\n")
        f.write(f"{tab}first_updated={self.first_updated},\n")
        f.write(f"{tab}last_updated={self.last_updated},\n")
        f.write(f"{last_tab})")

    def dumps(self, indent=4):
        with StringIO() as f:
            self.dump(f, indent=indent)
            ret = f.getvalue()
        return ret

#     def copy(self, api=None):
#         if api is None:
#             api = self.api
#         return Board(code_pair=self.code_pair,
#                      crange_interval=self.crange_interval,
#                      api=api,
#                      df=self.df.copy(),
#                      interval=self.interval)
    
    @property
    def crange(self):
        return self.crange_period.crange
    
    @property
    def period(self):
        return self.crange_period.period

    @property
    def first_updated(self):
        if len(self.df) == 0:
            return None
        
        return self.df.index[0]

    @property
    def last_updated(self):
        if len(self.df) == 0:
            return None
        
        return self.df.index[-1]
    
    def set_interval(self, interval):
        self._interval = interval
        return self

    def should_be_updated(self, interval=None):
        interval = self.arg_interval(interval)

        if interval is None:
            return True
        if self.last_updated is None:
            return True
        
        now = pd.Timestamp.now()
        if (now - self.last_updated) > interval:
            return True
        
        return False
    
    def focus(self, t=None):
        self._df = focus(self.df, t)
        return self.df

    def flush(self):
        self._df = self.api.empty
        return self.df

    def save(self, data_dir=None, save_function=None):
        data_dir = self.arg_data_dir(data_dir)
        
        save_function = self.arg_save_function(save_function)

        return save_function(
            df=self.df,
            dir_path=data_dir,
            save_iterator=self.save_iterator,
            save_fstring=self.save_fstring,
            timestamp_filter=self.timestamp_filter
        )

    def read(self,
             t=None,
             data_dir=None,
             save_fstring=None,
             glob_function=None,
             restore_function=None):
        data_dir = self.arg_data_dir(data_dir)

        save_fstring = self.arg_save_fstring(save_fstring)
        glob_function = self.arg_glob_function(glob_function)
        restore_function = self.arg_restore_function(restore_function)

        read_dir = Path(data_dir)
        if not read_dir.exists():
            raise FileNotFoundError(f"Directory not found '{read_dir}'")

        paths = glob_function(read_dir)
        if len(paths) == 0:
            raise FileNotFoundError(f"No file to read in '{read_dir}'")

        paths = focus(paths, t, fstring=save_fstring)
        if len(paths) == 0:
            raise FileNotFoundError(f"No files remained after applying filter.")

        df = standardize(restore_function(paths))
        
        return focus(df, t)
    
    def load(self,
             t=None,
             data_dir=None,
             save_fstring=None,
             glob_function=None,
             restore_function=None):
        data_dir = self.arg_data_dir(data_dir)

        df = self.read(
            t=t,
            data_dir=data_dir,
            save_fstring=save_fstring,
            glob_function=glob_function,
            restore_function=restore_function
        )

        self._df = df

        return df

    def download(self, t=None):
        df = self.api.download(code_pair=self.code_pair,
                               crange_period=self.crange_period,
                               t=t)
        return focus(standardize(df), t)
    
    def update(self, t=None, interval=None, force=False, merge_function=None):
        merge_function = self.arg_merge_function(merge_function)
        interval = self.arg_interval(interval)

        if (not force) and (not self.should_be_updated(interval)):
            return None

        df = self.download(t)
        df = focus(merge_function(self.df, df), t)

        self._df = df

        return df

    def sync(self,
             t=None,
             data_dir=None,
             interval=None,
             force=False,
             save_fstring=None,
             glob_function=None,
             save_function=None,
             restore_function=None,
             merge_function=None):
        data_dir = self.arg_data_dir(data_dir)

        glob_function = self.arg_glob_function(glob_function)
        save_function = self.arg_save_function(save_function)
        restore_function = self.arg_restore_function(restore_function)
        merge_function = self.arg_merge_function(merge_function)

        self.load(
            t=t,
            data_dir=data_dir,
            save_fstring=save_fstring,
            glob_function=glob_function,
            restore_function=restore_function
        )
        
        df_updated = self.update(
            t=t,
            interval=interval,
            force=force,
            merge_function=merge_function
        )

        self.save(
            data_dir=data_dir,
            save_function=save_function
        )

        return df_updated
    
#     # def normalize(self):
#     #     pass
    
#     # def select(self):
#     #     pass

# class LogChart:
#     def __init__(self, dfs):
#         self.dfs = dfs
    
#     def __getitem__(self, key):
#         return log10(self.dfs[key])

class Chart(SafeAttrABC):
    def _make_crange_period(self,
            crange_period: Union[str, CRangePeriod, EllipsisType],
            name: Optional[Union[str, CRangePeriod]]=None):
        if isinstance(name, CRangePeriod):
            if crange_period is not ...:
                raise ValueError(f"crange_period must be ... {EllipsisType} when name is instance of {CRangePeriod}.")
        if name is not None:
            if not isinstance(name, (str, CRangePeriod)):
                raise TypeError(f"name must be instance of {str} or {CRangePeriod} but actual type {type(name)}.")
            if crange_period is ...:
                crange_period = name
            else:
                # name is ignored
                pass

        if isinstance(crange_period, str):
            return self.api.crange_period_from_string(crange_period)
        elif isinstance(crange_period, CRangePeriod):
            return crange_period.copy()

        raise TypeError(f"crange_period must be instance of {str} or {CRangePeriod} but actual type {(type(crange_period))}.")

    def _make_crange_period_list(self,
            crange_period: Union[str, CRangePeriod,
                                Iterable[Union[str, CRangePeriod]]]):
        xs = crange_period
        if isinstance(xs, (str, CRangePeriod)):
            return [ self._make_crange_period(xs) ]
        elif is_instance_list(xs, (str, CRangePeriod)):
            return [ self._make_crange_period(x) for x in xs ]
        raise TypeError(f"crange_period must be instance of {str}, {CRangePeriod}, {Iterable[Union[str, CRangePeriod]]}.")

    def _make_crange_period_dict(self,
            crange_period: Union[str, CRangePeriod,
                                Iterable[Union[str, CRangePeriod]],
                                Mapping[str, Union[str, CRangePeriod]]]):
        xs = crange_period
        if isinstance(xs, (str, CRangePeriod)):
            return { xs: self._make_crange_period(xs) }
        elif is_instance_dict(xs, kt=(str, CRangePeriod), vt=(str, CRangePeriod, EllipsisType)):
            return { name: self._make_crange_period(crange_period, name=name) for name, crange_period in xs.items() }
        elif is_instance_list(crange_period, (str, CRangePeriod)):
            return { x: self._make_crange_period(x) for x in xs }
        raise TypeError(f"crange_period must be instance of {str}, {CRangePeriod}, {Iterable[Union[str, CRangePeriod]]}, or {Mapping[str, Union[str, CRangePeriod, EllipsisType]]}.")

    def __init__(self,
                 api: Type[ChartAPI],
                 code_pair: CodePair,
                 data_dir: Union[str, Path],
                 crange_period: Union[CRangePeriod, Iterable[CRangePeriod]]=None
                ):
        self.api = immutable(api, ChartAPI)
        self.code_pair = self._to_code_pair(code_pair)
        self.data_dir = immutable(data_dir, Path, f=Path, optional=True)
        self.board = {}

        if crange_period is None:
            crange_period = [ self.api.default_crange_period ]
        for name, cp in self._make_crange_period_dict(crange_period).items():
            self.add(cp, name=name, api=self.api)
    
    def __getitem__(self, key):
        return self.board[key]

    def __repr__(self):
        return self.dumps()

    def dump(self, f, indent=2, nest=1):
        tab = " " * indent * nest
        tabtab = " " * (indent * (nest + 1))
        last_tab = " " * (indent * (nest - 1))

        f.write(f"Chart(api={self.api},\n")
        f.write(f"{tab}code_pair={self.code_pair},\n")
        f.write(f"{tab}data_dir='{self.data_dir}',\n")
        f.write(f"{tab}crange_period={self.crange_period},\n")
        f.write(f"{tab}board={{\n")
        for key, board in self.board.items():
            if isinstance(key, str):
                f.write(f"{tabtab}'{key}': ")
            else:
                f.write(f"{tabtab}{key}: ")
            board.dump(f, indent=indent, nest=nest+2)
            f.write(f",\n")
        f.write(f"{tab}}}\n")
        f.write(f"{last_tab})")
    
    def dumps(self, indent=4):
        with StringIO() as f:
            self.dump(f, indent=indent)
            ret = f.getvalue()
        return ret
    
    @property
    def crange_period(self):
        return list(self.board.keys())

    def create_emulator(self, data_dir, source_dir, on_memory=False):
        chart_api = ChartEmulatorAPI(api=self.api, source_dir=source_dir, on_memory=on_memory)
        
        return Chart(
            api=chart_api,
            code_pair=self.code_pair,
            data_dir=data_dir,
            crange_period=self.crange_period,
        )
    
    def _to_code_pair(self, code_pair: Union[str, CodePair]):
        if isinstance(code_pair, str):
            return self.api.code_pair_from_string(code_pair)
        elif isinstance(code_pair, CodePair):
            return code_pair.copy()
        raise TypeError(f"code_pair must be instance of {str} or {CodePair}")
        
    def add(self, crange_period: Union[str, CRangePeriod], name: Optional[str]=None, data_dir=None, api=None, interval=None):
        api = self.arg_api(api)
        crange_period = self._make_crange_period(crange_period)
        if name is None:
            name = crange_period
        else:
            name = type_checked(name, (str, CRangePeriod))

        if not api.is_valid_crange_period(crange_period):
            raise ValueError(f"invalid crange_period: '{crange_period}'")
        
        if data_dir is None:
            data_dir = self.data_dir / self.code_pair.short / crange_period.short

        self.board[name] = \
            Board(
                name=name,
                api=api,
                code_pair=self.code_pair,
                crange_period=crange_period,
                data_dir=data_dir,
                interval=interval
            )
        
        return self

#     def copy(self, api=None, data_dir=None):
#         if api is None:
#             api = self.api
#         if data_dir is None:
#             data_dir = self.data_dir
        
#         chart = Chart(api, self.code_pair, data_dir, self.crange_interval)
#         for key, board in self.board.items():
#             chart.board[key] = board.copy(api=api)
        
#         return chart


#     @property
#     def dfs(self):
#         return { k: v.df for k, v in self.board.items() }
    
    def flush(self, crange_period: Union[str, Iterable[str]]=None):
        for key in self._to_crange_interval_list(crange_period):
            board = self.board[key]
            board.flush()

        return self

    def save(self, crange_period: Union[str, Iterable[str]]=None, data_dir=None):
        if crange_period is None:
            crange_period = list(self.board.keys())
        else:
            crange_period = self._make_crange_period_list(crange_period)

        for key in crange_period:
            board = self.board[key]
            if data_dir is None:
                board.save()
            else:
                save_dir = Path(data_dir) / board.code_pair.short / board.crange_period.short
                board.save(data_dir=save_dir)
        
        return self

    def read(self, crange_period: Union[str, Iterable[str]]=None, t=None, data_dir=None):
        if crange_period is None:
            crange_period = list(self.board.keys())
        else:
            crange_period = self._make_crange_period_list(crange_period)
        
        ret = {}
        for key in crange_period:
            board = self.board[key]
            if data_dir is None:
                ret[board.name] = board.read(t=t)
            else:
                read_dir = Path(data_dir) / board.code_pair.short / board.crange_period.short
                ret[board.name] = board.read(t=t, data_dir=read_dir)

        return ret

    def load(self, crange_period: Union[str, Iterable[str]]=None, t=None, data_dir=None):
        data_dir = self.arg_data_dir(data_dir)

        if crange_period is None:
            crange_period = list(self.board.keys())
        else:
            crange_period = self._make_crange_period_list(crange_period)
        
        ret = {}
        for key in crange_period:
            board = self.board[key]
            if data_dir is None:
                ret[key] = board.load(t=t)
            else:
                load_dir = Path(data_dir) / board.code_pair.short / board.crange_period.short
                ret[key] = board.load(t=t, data_dir=load_dir)

        return ret

    def download(self, crange_period: Union[str, Iterable[str]]=None, t=None):
        if crange_period is None:
            crange_period = list(self.board.keys())
        else:
            crange_period = self._make_crange_period_list(crange_period)

        ret = {}
        for key in crange_period:
            ret[key] = self.board[key].download(t=t)
        
        return ret
    
    def update(self, crange_period=None, t=None, interval=None, force=False):
        if crange_period is None:
            crange_period = list(self.board.keys())
        else:
            crange_period = self._make_crange_period_list(crange_period)
        
        ret = {}
        for key in crange_period:
            ret[key] = self.board[key].update(t=t, interval=interval, force=force)
        
        return ret

    def sync(self, crange_period=None, t=None, data_dir=None, interval=None, force=False):
        if crange_period is None:
            crange_period = list(self.board.keys())
        else:
            crange_period = self._make_crange_period_list(crange_period)
        
        ret = {}
        for key in crange_period:
            board = self.board[key]
            if data_dir is None:
                ret[key] = board.sync(t=t, interval=interval, force=force)
            else:
                sync_dir = Path(data_dir) / board.code_pair.short / board.crange_period.short
                ret[key] = board.sync(t=t, data_dir=sync_dir, interval=interval, force=force)
        
        return ret

class ChartDummyAPI(ChartAPI):
    def __init__(self):
        pass

    def __repr__(self):
        return f"ChartDummyAPI()"
    
    def freeze(self):
        return self

    @property
    def cranges(self):
        return ['max']
    
    @property
    def periods(self):
        return ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w']
    
    @property
    def empty(self):
        return pd.DataFrame([], columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'quotevolume'])
    
    @property
    def default_crange_period(self) -> str:
        return CRangePeriod('max', '15m')

    @property
    def default_crange_periods(self):
        return [
            CRangePeriod('max', '1h'),
            CRangePeriod('max', '15m'),
            CRangePeriod('max', '1m'),
        ]
    
    def is_valid_crange_period(self, crange_period: str) -> bool:
        table = {
            CRangePeriod('max', '1d'),
            CRangePeriod('max', '15m'),
            CRangePeriod('max', '1m'),
        }
        
        return crange_period in table

class ChartEmulatorAPI(SafeAttrABC, ChartAPI):
    def __init__(self,
                 api,
                 source_dir: Path,
                 on_memory=False
                ):
        self.api = immutable(api.freeze())
        self.source_dir = immutable(source_dir, Path, f=Path)
        self.on_memory = immutable(on_memory, bool)

        self.board = {}
    
    def __repr__(self):
        return f"ChartEmulatorAPI(api={self._api.__class__.__name__}, source_dir='{self._source_dir}')"

    def freeze(self):
        raise RuntimeError("can't freeze any more.")

#     @property
#     def empty(self):
#         return self.api.empty

#     @property
#     def code_pairs(self):
#         return self.api.code_pairs
    
    @property
    def cranges(self):
        return self.api.cranges
    
    @property
    def periods(self):
        return self.api.periods
    
#     @property
#     def max_cranges(self):
#         return self.api.max_cranges

    def is_valid_crange_period(self, crange_period: str) -> bool:
        return self.api.is_valid_crange_period(crange_period)

    @property
    def code_pairs(self):
        return self.api.code_pairs

    @property
    def default_crange_period(self):
        return self.api.default_crange_period

    @property
    def default_crange_periods(self):
        return self.api.default_crange_periods
    
    @property
    def empty(self):
        return self.api.empty

#         # 過去のデータをロードするようにつくりなおす
        
#         df = self.board[crange_interval].df
        
#         if t is None:
#             pass
#         elif isinstance(t, datetime):
#             df = df[df.index <= t]
#         elif is_instance_list(t, datetime, 2):
#             if t[1] is None:
#                 df = df[df.index >= t[0]]
#             else:
#                 df = df[(df.index >= t[0]) & (df.index <= t[1])]
#         else:
#             TypeError(f"")
            
#         return df.copy()

    def download(self, code_pair, crange_period=None, t=None, as_dataframe=True):
        """
        t ... ignored if as_dataframe is False
        """
        if code_pair not in self.code_pairs:
            raise ValueError(f"ticker '{code_pair}' not in {self.code_pairs}")

        if crange_period is None:
            crange_period = self.default_crange_period

        if str(crange_period.crange) not in self.cranges:
            raise ValueError(f"crange '{crange_period.crange}' not in {self.cranges}")
        if str(crange_period.period) not in self.periods:
            raise ValueError(f"interval '{crange_period.period}' not in {self.periods}")

        name = code_pair.short + '_' + crange_period.short
        
        if name not in self.board:
            self.board[name] = Board(
                code_pair=code_pair,
                crange_period=crange_period,
                data_dir=self.source_dir / code_pair.short / crange_period.short
            )
        
            if self.on_memory:
                self.board[name].load()

        if self.on_memory:
            return focus(self.board[name].df, t)
        
        return self.board[name].read(t=t)