from typing import Any, Callable, Iterable, Mapping

def type_checked(x: Any, t: Any):
    if not isinstance(x, t):
        raise TypeError(f"x must be instance of {t} but actual type {type(x)}.")
    return x

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

def is_instance_dict(xs: Any, kt: Any=None, vt: Any=None):
    if not isinstance(xs, Mapping):
        return False
    key_is_valid = True
    val_is_valid = True
    if kt is not None:
        key_is_valid = all([ isinstance(key, kt) for key in xs.keys() ])
    if vt is not None:
        val_is_valid = all([ isinstance(val, vt) for val in xs.values() ])

    return key_is_valid and val_is_valid