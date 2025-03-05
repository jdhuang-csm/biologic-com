from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..common import Bandwidth, IRange, Filter
from ..config import FullConfiguration
from ..write_utils import FilePath, format_value


# Column width for parameter tables
_fixed_width = 20


def pad_text(text):
    p = _fixed_width - len(text)
    return text + ' ' * p

def value2str(value):
    return pad_text(format_value(value))


@dataclass
class HardwareParameters(object):
    """
    Common hardware parameters configurable for any technique.
    """
    v_range_min: float = -10.0
    v_range_max: float = 10.0
    i_range: Optional[IRange] = None
    i_range_min: Optional[IRange] = None
    i_range_max: Optional[IRange] = None
    i_range_init: Optional[IRange] = None
    bandwidth: Bandwidth = Bandwidth.BW7
    filtering: Filter = Filter.NONE
    
    @property
    def i_range_min_(self):
        return self.i_range_min or "Unset"
    
    @property
    def i_range_max_(self):
        return self.i_range_max or "Unset"
    
    @property
    def i_range_init_(self):
        return self.i_range_init or "Unset"
    
    # def apply(self, other: object):
    #     """Apply settings from this instance to a TechniqueParameters
    #     instance.

    #     :param TechniqueParameters other: _description_
    #     """
    #     for name in self.__dataclass_fields__.keys():
    #         setattr(other, name, getattr(self, name))


_hardware_param_map = {
    "E range min (V)": "v_range_min",
    "E range max (V)": "v_range_max",
    "I Range": "i_range",
    "Bandwidth": "bandwidth",
}

# For techniques that allow Auto Limited IRange,
# such as CA
_hardware_param_map_ilimit = {
    "E range min (V)": "v_range_min",
    "E range max (V)": "v_range_max",
    "I Range": "i_range",
    "I Range min": "i_range_min_",
    "I Range max": "i_range_max_",
    "I Range init": "i_range_init_",
    "Bandwidth": "bandwidth",
}

_loop_param_map = {
    "goto Ns'": "goto_ns",
    "nc cycles": "nc_cycles"
}



class TechniqueParameters(object):
    """Base class for all technique parameter classes.

    :param dict _param_map: Dict mapping file field names to class 
        attribute names
    :param str technique_name: Name of technique
    """
    _param_map: dict
    
    technique_name: str
    abbreviation: str
    
    def key2str(self, key):
        attr = self._param_map[key]
        return f'{pad_text(key)}{value2str(getattr(self, attr))}'
    
    def apply_configuration(self, configuration: FullConfiguration):
        # For techniques that pull information from device/sample configuration
        # By default, do nothing
        pass
    
    def param_text(self, technique_number: int):        
        # Formatted parameters
        text_list = [
            self.key2str(key)
            for key in self._param_map.keys()
        ]
        return '\n'.join(text_list)

    
    
# @dataclass
# class LoopParameters(object):
#     goto_ns: int = 0
#     nc_cycles: int = 0

#     _loop_param_map = {
#         "goto Ns'": "goto_ns",
#         "nc cycles": "nc_cycles"
#     }

#     def __post_init__(self):
#         self._param_map = merge_dicts(self._param_map, self._loop_param_map)

# TODO: figure out nr cycles, inc. cycle in PEIS and GEIS