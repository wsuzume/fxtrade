import json
import os
import warnings

from pathlib import Path
from typing import Union, Optional

def mask_string(key):
    X = '*' * len(key)
    return key[:4] + X[4:]

def mask_dict(xs):
    ret = {}
    for sname, service in xs.items():
        ys = {}
        for kname, key in service.items():
            ys[kname] = mask_string(key)
        ret[sname] = ys
    
    return ret

class KeyHold:
    def __init__(self, path: Optional[Union[str, Path]]=None, create: bool=False):
        if path is not None:
            self.path = Path(path)
        else:
            self.path = Path(os.environ['HOME']) / '.config/keyhold/keys.json'
        
        self.create = create
        self._dict = {}
        
        if self.create:
            self.ensure_configfile()
        
        self.load()

    def ensure_configfile(self, path: Optional[Union[str, Path]]=None):
        if path is not None:
            path = Path(path)
        else:
            path = self.path

        if path.is_file():
            return
        
        if path.exists():
            raise RuntimeError("path exists but is not file.")
        
        if not self.create:
            raise FileNotFoundError('config file not exists.')
        
        with open(path, 'w'):
            warnings.warn(RuntimeWarning('new config file created.'))
    
    def __repr__(self):
        return f"'{str(self.path)}'\n" + \
                json.dumps(mask_dict(self._dict), indent=2)
    
    def __getitem__(self, key):
        return self._dict[key]
    
    def __setitem__(self, key, val):
        self._dict[key] = val
    
    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self._dict, f, indent=2)
    
    def load(self):
        with open(self.path, 'r') as f:
            try:
                self._dict = json.load(f)
            except:
                self._dict = {}
