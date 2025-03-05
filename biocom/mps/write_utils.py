import numpy as np
from enum import Enum
from pathlib import Path
from typing import Union


FilePath = Union[Path, str]

_decimal_sep_comma = False

def set_decimal_separator(comma=False):
    global _decimal_sep_comma
    _decimal_sep_comma = comma


def float2str(value: float, precision: int):
    text = "{x:.{p}f}".format(x=value, p=precision)
    if _decimal_sep_comma:
        return text.replace('.', ',')
    return text


def format_value(value, precision: int = 3):
    # Convert enums to values
    if isinstance(value, Enum):
        value = value.value

    # Convert bools to ints
    if isinstance(value, bool):
        return str(int(value))

    # Format floats with appropriate separator
    if isinstance(value, float) or isinstance(value, np.floating):
        return float2str(value, precision)

    # Strings or ints: return raw value
    return str(value)


def split_duration(duration: float):
    """Convert duration in seconds to hours, minutes, seconds, and milliseconds

    :param float duration: Duration in seconds
    :return Tuple[float, float, float, float]: hours, minutes, seconds, milliseconds
    """
    # Get hours, minutes, seconds
    h = int(duration / 3600.)
    m = int((duration % 3600.) / 60.)
    s = int(duration % 60.)

    # Get milliseconds
    ms = duration % 1
    ms = ms * 1000
    
    return h, m, s, ms

def format_duration(duration: float):
    """Format duration (in seconds) as text for mps file"""
    # Get hours, minutes, seconds
    h = int(duration / 3600.)
    m = int((duration % 3600.) / 60.)
    s = int(duration % 60.)

    # Get decimal seconds
    ds = round(duration % 1, 4)
    ds = '{:.4f}'.format(ds).split('.')[1]

    text = '{:02}:{:02}:{:02}.{}'.format(h, m, s, ds)
    if _decimal_sep_comma:
        return text.replace('.', ',')
    return text

