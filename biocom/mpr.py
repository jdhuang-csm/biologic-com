import numpy as np
from numpy import ndarray
from pathlib import Path
from galvani.BioLogic import MPRfile
import pandas as pd
from typing import Union

from . import units
from .utils import split_list

def read_mpr(file: Union[str, Path], unscale: bool = False):
    file = Path(file)
    mpr = MPRfile(file.__str__())
    
    if unscale:
        # Convert all units to base units (remove m, k, mu, etc. scaling)
        mpr.data = unscale_data(mpr.data)
        
    return mpr


def split_fieldname(fieldname: str):
    # Find last slash separator
    index = fieldname[::-1].find('/')
    if index == -1:
        return fieldname, None
    
    index = -(index + 1)
    name = fieldname[:index]
    unit = fieldname[index + 1:]
        
    return name, unit


def split_unit(unit: Union[str, None]):
    if unit is None:
        return None, None
    elif len(unit) > 1 and unit[0] in units._all_prefixes:
        prefix = unit[0]
        base_unit = unit[1:]
    else:
        prefix = None
        base_unit = unit
        
    return prefix, base_unit


def unscale_data(data: ndarray):
    # TODO: consider precision loss?
    # Determine prefixes and base units
    fieldnames = list(data.dtype.fields.keys())
    names, unit_list = split_list(fieldnames, split_fieldname)
    prefixes, base_units = split_list(unit_list, split_unit)
    
    # Check each field
    scaled = data.copy()
    new_fieldnames = fieldnames.copy()
    for i in range(len(names)):
        prefix = prefixes[i]
        if prefix is not None:
            # Remove prefix and return to raw scaling
            fieldname = fieldnames[i]
            up = units.UnitPrefix(prefix)
            scaled[fieldname] = up.scaled_to_raw(scaled[fieldname])
            new_fieldnames[i] = f'{names[i]}/{base_units[i]}'
            
    new_dtype = np.dtype(dict(zip(new_fieldnames, data.dtype.fields.values())))
    scaled.dtype = new_dtype
    return scaled

# dd = Path(r'J:\Home\AK_Zeier\User\jhuang2\data\echem\240702_NCM_SymIonBlock_50mg')

# mpr = read_mpr(dd.joinpath('CA_10s_C01.mpr'))

# # dir(mpr)

# # mpr.startdate
# # pd.DataFrame(mpr.data)

# # dir(mpr.data.dtype[1])
# # dir(mpr.data.dtype)
# mpr.data.dtype.fields.keys()
# # mpr.data['time/s']
# # type(mpr.data)

# type(mpr.data)
# mpr.data.dtype.fields

# scaled = unscale_data(mpr.data)
# mpr.data.dtype
# scaled.dtype
# mpr.data['Q charge/discharge/mA.h'],  scaled['Q charge/discharge/A.h']