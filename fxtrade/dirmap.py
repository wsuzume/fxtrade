import os
import shutil

from copy import deepcopy
from glob import glob, iglob
from pathlib import Path

from typing import Callable, Iterable, Mapping

class Directory:
    """
    Make easy to manipulate directories.
    """
    def __init__(self, path, default_query='*'):
        if isinstance(path, Path):
            self._path = path
        elif isinstance(path, Directory):
            self._path = path.path
        else:
            self._path = Path(path)
            
        self.default_query = default_query

    @property
    def path(self):
        """Return the path of the directory.
        """
        return self._path
    
    def __str__(self):
        return str(self.path)
    
    def __repr__(self):
        return f"Directory('{str(self.path)}')"
    
    def __len__(self):
        """Return the number of files and directories which are contained in the directory.
        """
        return len(self.glob())
    
    def __iter__(self):
        """Return files and directories iteratively (not sorted).
        """
        return self.iglob()
    
    def __truediv__(self, other):
        """Return the directory to which the paths are joined. (inherit=False)
        """
        return self.join(other, inherit=False)
    
    def join(self, other, inherit=False):
        """Return the directory to which the paths are joined.
        """
        if isinstance(other, Directory):
            other = other.path

        if inherit:
            return Directory(self.path / other, self.default_query)
        return Directory(self.path / other)

    def absolute(self):
        """Return the absolute path of the directory.
        """
        return Directory(self.path.absolute())

    def files(self, sort=True, wrap=False):
        """Return all files which are contained in the directory.
        """
        query = str(self.path / '*')
        files = [ os.path.basename(p) for p in glob(query) if os.path.isfile(p) ]

        files = files if not sort else sorted(files)

        if not wrap:
            return files
        return [ Path(f) for f in files ]
    
    def dirs(self, sort=True, wrap=False):
        """Return all directories which are contained in the directory.
        """
        query = str(self.path / '*')
        dirs = [ os.path.basename(p) for p in glob(query) if os.path.isdir(p) ]

        dirs = dirs if not sort else sorted(dirs)

        if not wrap:
            return dirs
        return [ Directory(d) for d in dirs ]

    def cd(self, key, inherit=False, return_None=False):
        """Return the directory which is specified by the key. The specified directory must be exist,
        otherwise raises FileNotFoundError or return None.
        """
        if isinstance(key, int):
            dirs = self.dirs(sort=True, wrap=False)
            if len(dirs) == 0:
                if return_None:
                    return None
                raise FileNotFoundError(f"No directory in '{self.path}'")
            
            if key >= len(dirs):
                if return_None:
                    return None
                raise FileNotFoundError(f"File index out of range")

            return self.join(dirs[key], inherit=inherit)

        dirs = set(self.dirs(sort=False, wrap=False))
        if key not in dirs:
            raise FileNotFoundError(f"directory '{key}' not in '{self.path}'")
        
        return self.join(key, inherit=inherit)
    
    def iloc(self, idx, return_None=False):
        """Return file or directory specified by index in lexicographic order.
        """
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
        """Return the first file or directory specified by index in lexicographic order.
        """
        return self.iloc(0, return_None)
    
    def last(self, return_None=True):
        """Return the last file or directory specified by index in lexicographic order.
        """
        return self.iloc(-1, return_None)

    def __getitem__(self, key):
        """Return the directory which is specified by the key. The specified directory must be exist,
        otherwise raises FileNotFoundError.
        """
        return self.cd(key)
    
    def __delitem__(self, key):
        """Delete the directory which is specified by the key.
        """
        dest = self.cd(key)
        dest.rmtree()
    
    def exists(self):
        """Return whether a file or directory exists in the path.
        """
        return self.path.exists()
    
    def isfile(self):
        return os.path.isfile(str(self.path))
    
    def isdir(self):
        return os.path.isdir(str(self.path))
    
    def ensure(self, is_file_ok=False, verbose=False):
        """Check whether the directory is exist or not,
        and create if it doesn't exists.
        """
        if self.isfile():
            if not is_file_ok:
                raise RuntimeError('File exists at the path.')
            status = 'OK'
        elif self.isdir():
            status = 'OK'
        else:
            self.makedirs(exist_ok=True)
            status = 'Created'
        if verbose:
            x = f"'{str(self.path)}'"
            print(f"Directory: {x}  ... {status}")
        return self
    
    def mkdir(self, name=None):
        if name is None:
            os.mkdir(str(self))
        else:
            os.mkdir(str(self / name))
    
    def makedirs(self, name=None, exist_ok=False):
        if name is None:
            os.makedirs(str(self), exist_ok=exist_ok)
        else:
            os.makedirs(str(self / name), exist_ok=exist_ok)
    
    def rmdir(self, name=None):
        if name is None:
            os.rmdir(str(self))
        else:
            os.rmdir(str(self / name))

    def rmtree(self, name=None):
        if name is None:
            shutil.rmtree(str(self))
        else:
            shutil.rmtree(str(self / name))

    def glob(self, query=None, recursive=False):
        query = query if query is not None else self.default_query
        return glob(str(self.path / query), recursive=recursive)
    
    def iglob(self, query=None, recursive=False):
        query = query if query is not None else self.default_query
        return iglob(str(self.path / query), recursive=recursive)
        
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
                raise FileNotFoundError("directory not exists")
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