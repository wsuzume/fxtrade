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
        if path is None:
            self._path = None
        elif isinstance(path, Path):
            self._path = path
        elif isinstance(path, Directory):
            self._path = path.path
        else:
            self._path = Path(path)
            
        self.default_query = '*'
    
    @property
    def is_valid(self):
        return self._path is not None
    
    def raise_for_invalid(self):
        if not self.is_valid:
            raise ValueError(f"invalid directory: path is None")
    
    @property
    def path(self):
        return self._path
    
    def __str__(self):
        self.raise_for_invalid()
        return str(self._path)
    
    def __repr__(self):
        if not self.is_valid:
            return "InvalidDirectory"
        return f"Directory('{str(self._path)}')"
    
    def __len__(self):
        return len(self.glob())
    
    def __iter__(self):
        return self.iglob()
    
    def __truediv__(self, other):
        if not self.is_valid:
            return Directory(other)
        return Directory(self._path / other)

    def cd(self, name):
        self.raise_for_invalid()
        
        query = str(self._path / self.default_query)
        dirs = set([ os.path.basename(p) for p in glob(query) if os.path.isdir(p) ])
        
        if name not in dirs:
            raise FileNotFoundError(f"directory '{name}' not in '{self._path}'")
        
        return Directory(self._path / name)
        
    def __getitem__(self, key):
        self.raise_for_invalid()
        return self.cd(key)
    
    def __delitem__(self, key):
        self.raise_for_invalid()
        dest = self.cd(key)
        dest.rmtree()
    
    def exists(self):
        self.raise_for_invalid()
        return self._path.exists()
    
    def ensure(self, verbose=False):
        if self._path is None:
            status = 'Skipped'
        elif self.exists():
            status = 'OK'
        else:
            os.makedirs(str(self._path), exist_ok=True)
            status = 'Created'
        if verbose:
            x = f"'{str(self._path)}'" if self._path is not None else 'None'
            print(f"Directory: {x}  ... {status}")
        return self
    
    def mkdir(self, name):
        self.raise_for_invalid()
        os.mkdir(str(self / name))
    
    def makedirs(self, name, exist_ok=False):
        self.raise_for_invalid()
        os.makedirs(str(self / name), exist_ok=exist_ok)
    
    def rmdir(self):
        self.raise_for_invalid()
        os.rmdir(str(self))
    
    def rmtree(self):
        self.raise_for_invalid()
        shutil.rmtree(str(self))

    def glob(self, query=None, recursive=False):
        self.raise_for_invalid()
        query = query if query is not None else self.default_query
        return glob(str(self.path / query), recursive=recursive)
    
    def iglob(self, query=None, recursive=False):
        self.raise_for_invalid()
        query = query if query is not None else self.default_query
        return iglob(str(self.path / query), recursive=recursive)
    
    def now(self, name=None, scope='day', format_str=None):
        self.raise_for_invalid()
        return self.path / with_timestamp(name, scope, format_str)
    
    def iloc(self, idx, return_None=False):
        if not self.is_valid:
            return None
        
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
    def __init__(self, root_dir='.', default_query='*'):
        self._root_dir = Directory(root_dir)
        self.default_query = default_query
        
        self._branch = {}
        
    def __repr__(self):
        if len(self._branch) == 0:
            xs = '{}'
        else:
            xs = ['{\n']
            for k, v in self._branch.items():
                if v is None:
                    xs.append(f"  '{k}': None,\n")
                else:
                    xs.append(f"  '{k}': '{v}',\n")
            xs.append('}')
            xs = ''.join(xs)
        return f"DirMap('{str(self._root_dir)}', {xs})"
    
    def __str__(self):
        return f"DirMap('{str(self._root_dir)}', {self._branch})"
    
    @property
    def root_dir(self):
        return self._root_dir
    
    @property
    def branch(self):
        return deepcopy(self._branch)
    
    def __getitem__(self, key):
        return self.cd(key, inherit=False, raise_for_invalid=False)
    
    def __setitem__(self, key, val):
        if val is None:
            self.add_branch(key, val, reserve=True)
        else:
            self.add_branch(key, val)
    
    def cd(self, name, inherit=False, raise_for_invalid=True):
        if self._branch[name] is None:
            if raise_for_invalid:
                Directory(self._branch[name]).raise_for_invalid()
            else:
                return None
            
        if inherit:
            return Directory(self.root_dir / self._branch[name], self.default_query)
        
        return Directory(self.root_dir / self._branch[name])
    
    def add_branch(self, x=None, path=None, reserve=False):
        if isinstance(x, str):
            if reserve and (path is None):
                self._branch[x] = None
            else:
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
        
        raise TypeError(f"x must be str, Mapping, or Iterable")
    
    def ensure(self, verbose=True):
        def ensure_path(key, path):
            if path is None:
                status = 'Skipped'
            elif os.path.exists(str(path)):
                status = 'OK'
            else:
                os.makedirs(str(path))
                status = 'Created'
            if verbose:
                x = f"'{path}'" if path is not None else 'None'
                print(f"  {key}: {x}  ... {status}")
        
        if verbose:
            print('[Branch]')
        ensure_path('root', self.root_dir)
        if len(self._branch) != 0:
            for k, v in self._branch.items():
                path = self.root_dir / v if v is not None else None
                ensure_path(k, path)
    
    def glob(self, query=None, recursive=False):
        query = query if query is not None else self.default_query
        return glob(str(self.root_dir / query), recursive=recursive)