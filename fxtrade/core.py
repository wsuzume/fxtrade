from typing import Any, Callable, Iterable, Mapping

def is_filtered_list(xs: Any, f: Callable[[Any], bool], n: int=None):
    if isinstance(xs, Mapping):
        return False
    if not isinstance(xs, Iterable):
        return False
    if (n is not None) and (len(xs) != n):
        return False
    
    return all([ f(x) for x in xs ])

def is_instance_list(xs: Any, t: Any, n: int=None):
    return is_filtered_list(xs, lambda x: isinstance(x, t), n)