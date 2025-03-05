import numpy as np
from numpy import ndarray
from typing import Callable, Tuple, List, Union, Optional

def merge_dicts(*dicts):
    """Merge dictionaries. Equivalent to dict1 | dict2, but backwards 
    compatible. In the case of duplicate keys, dictionaries that appear
    later in the argument sequence take precedence.

    :return dict: Merged dictionary
    """
    # for backwards compatibility
    new = dicts[0].copy()
    for d in dicts:
        new.update(d)
    return new


def split_list(x: list, split_func: Callable) -> Tuple[List]:
    """Split each entry of a list with split_func, then return separate
    lists of the split_func outputs.

    :param list x: _description_
    :param Callable split_func: _description_
    :return Tuple[List]: A tuple of lists. The ith list contains the
        ith split_func output for all entries of the input 
        list.
    """
    split = [split_func(xi) for xi in x]
    return tuple([[s[i] for s in split] for i in range(len(split[0]))])


def isiterable(a) -> bool:
    """Check if a is iterable"""
    try:
        iter(a)
        return True
    except TypeError:
        return False
    
    
def nearest_index(x_array: ndarray, x_val: Union[float, ndarray], constraint: Optional[int] = None):
    """
    Get index of x_array corresponding to value closest to x_val
    :param ndarray x_array: Array in which to search
    :param Union[float, ndarray] x_val: Value(s) to match
    :param int constraint: If -1, find the nearest index for which x_array <= x_val. If 1, find the nearest index for
    which x_array >= x_val. If None, find the closest index regardless of direction
    :return: If x_val is scalar, a single integer indicating the index of the closest value in x_array.
        If x_val is an array, an array of integers of the same length as x_val indicating the index 
        of the closest value in x_array for each item in x_val.
    """
    if constraint is None:
        def func(arr, x):
            return np.abs(arr - x)
    elif constraint in [-1, 1]:
        def func(arr, x):
            out = np.zeros_like(arr) + np.inf
            constraint_index = constraint * arr >= constraint * x
            out[constraint_index] = constraint * (arr - x)[constraint_index]
            return out
    else:
        raise ValueError(f'Invalid constraint argument {constraint}. Options: None, -1, 1')

    if np.isscalar(x_val):
        obj_func = func(x_array, x_val)
        index = np.argmin(obj_func)
        max_of = obj_func
    else:
        aa, bb = np.meshgrid(x_array, np.array(x_val))
        obj_func = func(aa, bb)
        index = np.argmin(obj_func, axis=1)
        max_of = np.max(obj_func[index])
        

    # Validate index
    if max_of == np.inf:
        if constraint == -1:
            min_val = np.min(x_array)
            raise ValueError(f'No index satisfying {constraint} constraint: minimum array value {min_val} '
                             f'exceeds target value {x_val}')
        else:
            max_val = np.max(x_array)
            raise ValueError(f'No index satisfying {constraint} constraint: maximum array value {max_val} '
                             f'is less than target value {x_val}')

    return index


def nearest_value(x_array: ndarray, x_val: Union[float, ndarray], constraint: Optional[int] = None):
    index = nearest_index(x_array, x_val, constraint)
    return x_array[index]
