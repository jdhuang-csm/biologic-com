from enum import Enum, StrEnum, auto
from typing import Union, Optional

from ..utils import merge_dicts

def to_sentence_case(x: str):
    """
    Convert string to sentence case (first letter capitalized)
    """
    return x[0].upper() + x[1:].lower()
    

class SentenceCaseEnum(StrEnum):
    """
    Enum for which the automatic (default) entry value is the 
    equal to the name converted to sentence case, i.e.:
    default_value = to_sentence_case(name)
    """
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[str]) -> str:
        return to_sentence_case(name)


EweVs = SentenceCaseEnum('EweVs', ['REF', 'EOC', 'ECTRL', 'EMEAS'])
# If potential control is set to Ewe-Ece, then REF becomes CE

# class EweVsEce(StrEnum):
#     CE = 'CE'
    
class ControlMode(StrEnum):
    POT = "Potentiostatic"
    GALV = "Galvanostatic"
    

class IVs(SentenceCaseEnum):
    NONE  = "<None>"
    ICTRL = auto()
    IMEAS = auto()
    
class TriggerType(StrEnum):
    RISING = "Rising Edge"
    FALLING = "Falling Edge"
    

ChannelGrounding = SentenceCaseEnum("ChannelGrounding", ["FLOATING", "GROUNDED"])

class IRange(StrEnum):
    AUTO      = "Auto"
    AUTOLIMIT = "Auto Limited"
    n10       = "10 nA"
    n100      = "100 nA"
    u1        = f"1 {chr(181)}A"
    u10       = f"10 {chr(181)}A"
    u100      = f"100 {chr(181)}A"
    m1        = "1 mA"
    m10       = "10 mA"
    m100      = "100 mA"
    a1        = "1 A"
    
    
class Bandwidth(Enum):
    """
    Bandwidths
    """
    BW1 = 1  # "Slow"
    BW2 = 2
    BW3 = 3
    BW4 = 4
    BW5 = 5  # "Medium"
    BW6 = 6
    BW7 = 7  # "Fast"
    # NOTE: 8 and 9 only available for SP300 series
    BW8 = 8
    BW9 = 9
    
    
    
class Filter(StrEnum):
    """
    Filter frequencies
    """
    NONE = "<None>"
    k50  = "50 kHz"
    k1   = "1 kHz"
    h5   = "5 Hz"
    
    
# class DriftCorrection(Enum):
#     OFF = 0
#     ON  = 1
    
    
class PotentialControl(StrEnum):
    EWE     = "Ewe"
    EWE_ECE = "Ewe-Ece"
    
# TODO: check other cable types
CableType = SentenceCaseEnum("CableType", ["STANDARD"])
    
class TurnToOCV(StrEnum):
    TRUE  = "Turn to OCV between techniques"
    FALSE = "Do not turn to OCV between techniques"
    
    @classmethod
    def from_bool(cls, val: bool):
        return getattr(cls, str(val).upper())
    
class ElectrodeConnection(StrEnum):
    STANDARD = "standard"
    CETOGND  = "CE to ground"
    WETOGND  = "WE to ground"
    
class CycleDefinition(StrEnum):
    CHARGE_DISCHARGE = "Charge/Discharge"
    DISCHARGE_CHARGE = "Discharge/Charge"
    
class ReferenceElectrode(StrEnum):
    NONE = "(unspecified)"
    AgAgClKCl3_5M = "Ag/AgCl / KCl (3.5M) (0.205 V)"
    AgAgClKClSat = "Ag/AgCl / KCl (sat'd) (0.197 V)"
    AgAgClNaClSat = "Ag/AgCl / NaCl (sat'd) (0.194 V)"
    HgHg2SO4K2SO4Sat = "Hg/Hg2SO4 / K2SO4 (sat'd) (0.650 V)"
    NHE = "NHE Normal Hydrogen Electrode (0.000 V)"
    SCE = "SCE Saturated Calomel Electrode (0.241 V)"
    SSCE = "SSCE Sodium Saturated Calomel Electrode (0.236 V)"
    
    
class SampleType(SentenceCaseEnum):
    CORROSION = auto()
    BATTERY   = auto()
    MATERIALS = auto()
    
    
class BLDeviceModel(StrEnum):
    SP150 = "SP-150"
    SP200 = "SP-200"
    SP300 = "SP-300"
    VMP300 = "VMP-300"
    VSP300 = "VSP-300"
    
    @property
    def series(self):
        return int(self.value.split('-')[1])
    
    @property
    def max_bandwidth(self):
        if self.series == 300:
            # 300-series go up to 9
            return 9
        else:
            # Other devices only go to 7
            return 7
        
    @property
    def has_filtering(self):
        # Only 300-series devices have filters
        return self.series == 300
    
    def validate_bandwidth(self, bandwidth: Bandwidth):
        if Bandwidth.value > self.max_bandwidth:
            raise ValueError(f"The maximum bandwidth for model {self.value} is {self.max_bandwidth}, "
                             f"but a bandwidth of {bandwidth.value} was specified.")
            
    def validate_filter(self, filtering: Filter):
        if (not self.has_filtering) and filtering != Filter.NONE:
            raise ValueError(f"Filtering is not available for model {self.value}.")
    
    
def get_i_range(i_max: float):
    i_max = abs(i_max)
    
    if i_max < 1e-8:
        return IRange.n10
    elif i_max < 1e-7:
        return IRange.n100
    elif i_max < 1e-6:
        return IRange.u1
    elif i_max < 10e-6:
        return IRange.u10
    elif i_max < 100e-6:
        return IRange.u100
    elif i_max < 1e-3:
        return IRange.m1
    elif i_max < 1e-2:
        return IRange.m10
    elif i_max < 1e-1:
        return IRange.m100
    else:
        return IRange.a1


# class RecordEwe(StrEnum):
#     RAW = "Ewe"
#     AVG = "<Ewe>"

# class RecordI(StrEnum):
#     RAW = "I"
#     AVG = "<I>"

class DQUnits(Enum):
    C   = "C"
    # mC  = "mC"
    AH  = "A.h"
    

# TODO: move this to a different module, rename this one to enums
    # def __post_init__(self):
    #     self._param_map = merge_dicts(self._param_map, self._hardware_param_map)
    

    
    
    



    
  