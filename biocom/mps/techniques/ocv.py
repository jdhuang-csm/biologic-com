from enum import Enum, StrEnum
from dataclasses import dataclass, field
import numpy as np
from numpy import ndarray
import datetime
from typing import Union, Optional, List

from ... import units
from ..common import (
    IRange, EweVs, IVs, get_i_range
)
from .technique import HardwareParameters, TechniqueParameters, _hardware_param_map, _loop_param_map
from ..write_utils import format_duration
from ...utils import merge_dicts


@dataclass
class _OCVParameters(object):
    """_summary_

    :param float duration: _description_
    """
    duration: float
    record_dt: float
    dvdt_limit: float = 0.0  # mV/h
    record_average: bool = False
    record_dv: float = 0.0  # mV
    
    technique_name = "Open Circuit Voltage"
    abbreviation = "OCV"
    
    _param_map = merge_dicts(
        {
            'tR (h:m:s)': '_duration_formatted',
            'dER/dt (mV/h)': 'dvdt_limit',
            'record': '_record',
            'dER (mV)': 'record_dv',
            'dtR (s)': 'record_dt' 
        },
        # only E range applies to OCV; no I range or bandwidth
        {k: v for k, v in _hardware_param_map.items() if k[:7] == 'E range'},
    )
    
@dataclass
class OCVParameters(HardwareParameters, _OCVParameters, TechniqueParameters):    
    @property
    def _record(self):
        if self.record_average:
            return "<Ewe>"
        return "Ewe"
    
    @property
    def _duration_formatted(self):
        return format_duration(self.duration)