from typing import Any, Iterable, Mapping, Union, Optional


class Const:
    def __init__(self, consts: Optional[Union[Iterable[str], Mapping[str, Any]]]=None):
        if consts is None:
            return
        elif isinstance(consts, Mapping):
            for k, v in consts.items:
                if not isinstance(k, str):
                    raise TypeError("all keys must be str")
                self.__setattr__(k, v)
        elif isinstance(consts, Iterable):
            for c in consts:
                if not isinstance(c, str):
                    raise TypeError("all elements must be str")
                self.__setattr__(c, c)
        else:        
            raise TypeError("consts must be type of Optional[Union[Iterable[str], Mapping[str, Any]]]")
    
    def __setattr__(self, key, val):
        if key in self.__dict__:
            raise AttributeError(f"Can't rebind const {name}")
        self.__dict__[key] = val
        
    def __contains__(self, item):
        return item in self.__dict__.values()