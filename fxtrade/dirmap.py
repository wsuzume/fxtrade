import os
import shutil

from copy import deepcopy
from glob import glob, iglob
from pathlib import Path

from typing import Callable, Iterable, Mapping, Union

def files(path: Union[str, Path], sort: bool=True, wrap: bool=False):
    """Return all files which are contained in the directory.
    """
    path = Path(path)

    query = str(path / '*')
    files = [ os.path.basename(p) for p in glob(query) if os.path.isfile(p) ]

    files = files if not sort else sorted(files)

    if not wrap:
        return files
    return [ Path(f) for f in files ]

def dirs(path: Union[str, Path], sort: bool=True, wrap: bool=False):
    """Return all directories which are contained in the directory.
    """
    path = Path(path)

    query = str(path / '*')
    dirs = [ os.path.basename(p) for p in glob(query) if os.path.isdir(p) ]

    dirs = dirs if not sort else sorted(dirs)

    if not wrap:
        return dirs
    return [ Path(d) for d in dirs ]

def iloc(path, idx: int, return_None: bool=False):
    """Return file or directory specified by index in lexicographic order.
    """
    ps = sorted(path.glob())
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
    """Return the first file or directory specified by index in lexicographic order.
    """
    return self.iloc(0, return_None)

def last(self, return_None=True):
    """Return the last file or directory specified by index in lexicographic order.
    """
    return self.iloc(-1, return_None)

def cd(path, key, return_None=False):
    """Return the directory which is specified by the key. The specified directory must be exist,
    otherwise raises FileNotFoundError or return None.
    """
    if isinstance(key, int):
        dirs = dirs(path, sort=True, wrap=False)
        if len(dirs) == 0:
            if return_None:
                return None
            raise FileNotFoundError(f"No directory in '{path}'")
        
        if key >= len(dirs):
            if return_None:
                return None
            raise FileNotFoundError(f"File index out of range")

        return path / dirs[key]

    dirs = set(dirs(path, sort=False, wrap=False))
    if key not in dirs:
        raise FileNotFoundError(f"directory '{key}' not in '{path}'")
    
    return path / key

def exists(path):
    """Return whether a file or directory exists in the path.
    """
    return path.exists()

def isfile(path):
    return os.path.isfile(str(path))

def isdir(path):
    return os.path.isdir(str(path))

def mkdir(path, name=None):
    if name is None:
        os.mkdir(str(path))
    else:
        os.mkdir(str(path / name))

def makedirs(path, name=None, exist_ok=False):
    if name is None:
        os.makedirs(str(path), exist_ok=exist_ok)
    else:
        os.makedirs(str(path / name), exist_ok=exist_ok)

def rmdir(path, name=None):
    if name is None:
        os.rmdir(str(path))
    else:
        os.rmdir(str(path / name))

def rmtree(path, name=None):
    if name is None:
        shutil.rmtree(str(path))
    else:
        shutil.rmtree(str(path / name))

def ensure(path, is_file_ok=False, verbose=False):
    """Check whether the directory is exist or not,
    and create if it doesn't exists.
    """
    if isfile(path):
        if not is_file_ok:
            raise RuntimeError('File exists at the path.')
        status = 'OK'
    elif isdir(path):
        status = 'OK'
    else:
        makedirs(path, exist_ok=True)
        status = 'Created'
    if verbose:
        x = f"'{str(path)}'"
        print(f"Directory: {x}  ... {status}")
    return path

def glob(path, query=None, recursive=False):
    query = query if query is not None else '*'
    return glob(str(path / query), recursive=recursive)

def iglob(path, query=None, recursive=False):
    query = query if query is not None else '*'
    return iglob(str(path / query), recursive=recursive)
        
class DirMap:
    def __init__(self, root_dir='.', default_query='*'):
        self._root_dir = Path(root_dir)
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
    
    def cd(self, name, raise_for_invalid=True):
        if self._branch[name] is None:
            if raise_for_invalid:
                raise FileNotFoundError("directory not exists")
            else:
                return None
        
        return Path(self.root_dir / self._branch[name])
    
    def clear(self):
        self._branch = {}
    
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