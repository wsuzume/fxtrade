import datetime
import os
import shutil

from copy import deepcopy
from glob import glob, iglob
from pathlib import Path

from typing import Callable, Iterable, Mapping

def with_timestamp(x=None, scope='day', format_str=None):
    fmt = {
        'year': '%Y',
        'month': '%Y%m',
        'day': '%Y%m%d',
        'hour': '%Y%m%dT%H',
        'minute': '%Y%m%dT%H%M',
        'second': '%Y%m%dT%H-%M-%S',
        'millisecond': '%Y%m%dT%H-%M-%S-%f',
    }
    
    format_str = fmt[scope] if format_str is None else format_str
    
    t = datetime.datetime.now()
    tstamp = t.strftime(format_str)
    
    if x is None:
        return tstamp
    return f'{tstamp}_{x}'

class Directory:
    def __init__(self, path, default_query='*'):
        if isinstance(path, Path):
            self._path = path
        elif isinstance(path, Directory):
            self._path = path.path
        else:
            self._path = Path(path)
            
        self.default_query = '*'
    
    @property
    def path(self):
        return self._path
    
    def __str__(self):
        return str(self._path)
    
    def __repr__(self):
        return f"Directory('{str(self._path)}')"
    
    def __len__(self):
        return len(self.glob())
    
    def __iter__(self):
        return self.iglob()
    
    def __truediv__(self, other):
        return Directory(self._path / other)

    def cd(self, name):
        query = str(self._path / self.default_query)
        dirs = set([ os.path.basename(p) for p in glob(query) if os.path.isdir(p) ])
        
        if name not in dirs:
            raise FileNotFoundError(f"directory '{name}' not in '{self._path}'")
        
        return Directory(self._path / name)
        
    def __getitem__(self, key):
        return self.cd(key)
    
    def __delitem__(self, key):
        dest = self.cd(key)
        dest.rmtree()
    
    def ensure(self):
        os.makedirs(str(self))
        return self
    
    def mkdir(self, name):
        os.mkdir(str(self / name))
    
    def makedirs(self, name, exist_ok=False):
        os.makedirs(str(self / name), exist_ok=exist_ok)
    
    def rmdir(self):
        os.rmdir(str(self))
    
    def rmtree(self):
        shutil.rmtree(str(self))

    def glob(self, query=None, recursive=False):
        query = query if query is not None else self.default_query
        return glob(str(self.path / query), recursive=recursive)
    
    def iglob(self, query=None, recursive=False):
        query = query if query is not None else self.default_query
        return iglob(str(self.path / query), recursive=recursive)
    
    def now(self, name=None, scope='day', format_str=None):
        return self.path / with_timestamp(name, scope, format_str)
    
    def iloc(self, idx, return_None=False):
        ps = sorted(self.glob())
        if len(ps) == 0:
            if return_None:
                return None
            raise FileNotFoundError(f"No file in '{self.path}'")
        
        if idx >= len(ps):
            if return_None:
                return None
            raise FileNotFoundError(f"File index out of range")
        
        p = ps[idx]
        
        if os.path.isdir(p):
            return Directory(p)
        return Path(p)
    
    def first(self, return_None=True):
        return self.iloc(0, return_None)
    
    def last(self, return_None=True):
        return self.iloc(-1, return_None)
        
class DirMap:
    def __init__(self, name, root_dir=None, default_query='*'):
        self._name = name
        self._root_dir = Directory(root_dir)
        self.default_query = default_query
        
        self._branch = {}
        
    def __repr__(self):
        return f"Haze({self.name}, {str(self._branch)})"
    
    @property
    def name(self):
        return self._name
    
    @property
    def root_dir(self):
        return self._root_dir
    
    @property
    def data_dir(self):
        return self.root_dir / self.name
    
    @property
    def branch(self):
        return deepcopy(self._branch)
    
    def __getitem__(self, key):
        return self.cd(key, inherit=False)
    
    def cd(self, name, inherit=False):
        if inherit:
            return Directory(self.data_dir / self._branch[name], self.default_query)
        return Directory(self.data_dir / self._branch[name])
    
    def add_branch(self, x=None, path=None):
        if isinstance(x, str):
            self._branch[x] = x if path is None else path
            return
        elif isinstance(x, Mapping):
            for k, v in x.items():
                self._branch[k] = v
            return
        elif isinstance(x, Iterable):
            for k in x:
                self._branch[k] = k
            return
        
        raise TypeError(f"")
    
    def ensure(self):
        def ensure_path(path):
            if os.path.exists(str(path)):
                status = 'OK'
            else:
                os.makedirs(str(path))
                status = 'Created'
            print(' ', path, '  ...', status)
        
        print('[Branch]')
        ensure_path(self.data_dir)
        if len(self._branch) != 0:
            for k, v in self._branch.items():
                path = self.data_dir / v
                ensure_path(path)
    
    def glob(self, query=None, recursive=False):
        query = query if query is not None else self.default_query
        return glob(str(self.data_dir / query), recursive=recursive)