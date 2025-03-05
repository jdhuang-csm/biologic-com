from enum import Enum, StrEnum
from dataclasses import dataclass, field
import numpy as np
from numpy import ndarray
import datetime
from typing import Union, Optional, List

from .stepwise import StepwiseTechniqueParameters

from ... import units
from ..common import (
    IRange, EweVs, IVs, get_i_range
)
from .technique import TechniqueParameters
from ..write_utils import format_duration
from ...utils import merge_dicts, isiterable


@dataclass
class LoopParameters(TechniqueParameters):
    goto_Ne: int
    nt: int
    
    technique_name = "Loop"
    abbreviation = "Loop"
    
    _param_map = {
        "goto Ne": "goto_Ne",
        "nt times": "nt"
    }
    