from enum import Enum, StrEnum, auto
from dataclasses import dataclass, fields
from collections import namedtuple
import numpy as np
from numpy import ndarray
import pandas as pd
from pandas import DataFrame
import datetime
from pathlib import Path
from typing import Union, Optional, List


from .stepwise import StepwiseTechniqueParameters
from ... import units
from ..common import (
    IRange, EweVs, IVs, get_i_range, Bandwidth, Filter, SentenceCaseEnum, TriggerType)
from ..config import FullConfiguration
from .technique import (
    HardwareParameters, _hardware_param_map, _hardware_param_map_ilimit, _loop_param_map
)
# from .eis import GEISAmpVariable, parse_frequency
from .eis import estimate_duration, PointDensity
from ..write_utils import format_duration
from ...utils import merge_dicts, isiterable



class MBLimitType(SentenceCaseEnum):
    TIME = auto()
    EWE = auto()
    ECE = auto()
    EWE_ECE = "Ewe-Ece"
    I = "I"
    IABS = "|I|"
    QABS = "|Q|"
    POWER = auto()
    ENERGY = "|Energy|"
    DIDT = "dI/dt"
    DIDT_ABS = "|dI/dt|"
    DSOC = "|SoC|" # todo: add delta symbol
    X = "X"
    DEDT = "dE/dt"
    NEG_DE = "-deltaE"
    DEDT_ABS = "|dE/dt|"
    T = "T"
    DTDT_ABS = "|dT/dt|"
    AUX1 = "Analog IN1"
    AUX2 = "Analog IN2"
    
    
ThreshTypeConfig = namedtuple("ThreshTypeConfig", ["base_unit", "scale_value", "factor_range"])

_limit_type_config = {
    MBLimitType.TIME: ThreshTypeConfig("s", True, None),
    MBLimitType.EWE: ThreshTypeConfig("V", True, (1e-3, 1)),
    MBLimitType.ECE: ThreshTypeConfig("V", True, (1e-3, 1)),
    MBLimitType.EWE_ECE: ThreshTypeConfig("V", True, (1e-3, 1)),
    MBLimitType.I: ThreshTypeConfig("A", True, (1e-9, 1)),
    MBLimitType.IABS: ThreshTypeConfig("A", True, (1e-9, 1)),
    MBLimitType.QABS: ThreshTypeConfig("A.h", True, (1e-6, 1)),
    MBLimitType.POWER: ThreshTypeConfig("W", True, (1e-6, 1)),
    MBLimitType.ENERGY: ThreshTypeConfig("W.h", True, (1e-6, 1e3)),
    MBLimitType.DIDT: ThreshTypeConfig("mA/s", True, (1e-6, 1)),
    MBLimitType.DIDT_ABS: ThreshTypeConfig("mA/s", True, (1e-6, 1)),
    MBLimitType.DSOC: ThreshTypeConfig("%", False, None),
    MBLimitType.X: ThreshTypeConfig("", False, None),
    MBLimitType.DEDT: ThreshTypeConfig("V/s", True, (1e-3, 1)),
    MBLimitType.NEG_DE: ThreshTypeConfig("V", True, (1e-3, 1)),
    MBLimitType.DEDT_ABS: ThreshTypeConfig("V/s", True, (1e-3, 1)),
    MBLimitType.T: ThreshTypeConfig("C", False, None), # TODO: add degree symbol
    MBLimitType.DTDT_ABS: ThreshTypeConfig("C/mn", False, None),
    MBLimitType.AUX1: ThreshTypeConfig("V", False, None),
    MBLimitType.AUX2:ThreshTypeConfig("V", False, None),   
}
    
    
class MBLimitComparison(Enum):
    LT = "<"
    GT = ">"
    
    
class MBLimitAction(Enum):
    NEXT = "Next sequence"
    GOTO = "Goto sequence"
    STOP = "Stop"
    

class MBLimitQ(Enum):
    QLIMIT = "Q limit"
    QPREV = "Q prev"
    QSEQ = "Q seq"
    CDN = "C / N"
    CTN = "C x N"
    
    
class MBLimit(object):
    def __init__(
        self, 
        limit_type: MBLimitType, 
        comparison: MBLimitComparison, 
        value: float,
        action: MBLimitAction,
        goto_seq: Optional[int] = None,
        q_limit_type: Optional[MBLimitQ] = None
    ):
        if action in (MBLimitAction.STOP, MBLimitAction.NEXT): 
            if goto_seq is not None:
                raise ValueError(f"goto_seq cannot be specified for action {action.value}")
        else:
            if goto_seq is None:
                raise ValueError(f"goto_seq must be specified for action {action.value}")
        
        if limit_type == MBLimitType.QABS:
            if q_limit_type is None:
                raise ValueError("q_limit_type must be specified for limit_type QABS")
        else:
            if q_limit_type is not None:
                raise ValueError("q_limit_type can only be specified for limit_type QABS")
        
        # self.base_unit = None
        self.value_unit = None
        
        self.limit_type = limit_type
        self.comparison = comparison
        self.value = value
        self.action = action
        
        if self.action == MBLimitAction.STOP:
            self.goto_seq = 9999
        elif self.action == MBLimitAction.NEXT:
            self.goto_seq = 1
        else:
            self.goto_seq = goto_seq
            
        if self.limit_type == MBLimitType.QABS:
            self.q_limit_type = q_limit_type
        else:
            # Default value (ignored)
            self.q_limit_type = MBLimitQ.QLIMIT
           
    def set_limit_value(self, value: float):
        self._raw_value = value
        if self.limit_type == MBLimitType.TIME:
            self._value, self.value_unit = units.get_scaled_time(value)
        else:
            config: ThreshTypeConfig = _limit_type_config[self.limit_type]
            if config.scale_value:
                # Scale the limit value and get the corresponding prefix
                factor_lims = config.factor_range if config.factor_range is not None else (None, None)
                self._value, prefix = units.get_scaled_value_and_prefix(value, *factor_lims)
                self.value_unit = f"{prefix}{config.base_unit}"
            else:
                # Don't scale the value
                self._value = value
                self.value_unit = config.base_unit
            
    def get_limit_value(self):
        return self._value
            
    value = property(get_limit_value, set_limit_value)
    
    def copy(self):
        # Set optional inputs based on enums for appropriate initialization
        goto_seq = self.goto_seq if self.action == MBLimitAction.GOTO else None
        q_limit_type = self.q_limit_type if self.limit_type == MBLimitType.QABS else None
            
        # Provide the raw value to ensure proper scaling and units
        return MBLimit(self.limit_type, self.comparison, self._raw_value, self.action, goto_seq, q_limit_type)
       
        
    
class MBRecordType(SentenceCaseEnum):
    TIME = auto()
    EWE = auto()
    ECE = auto()
    EWE_ECE = "Ewe-Ece"
    I = "I"
    Q = "Q"
    POWER = auto()
    ENERGY = auto()
    
_record_type_config = {
    MBRecordType.TIME: ThreshTypeConfig("s", True, None),
    MBRecordType.EWE: ThreshTypeConfig("V", True, (1e-3, 1)),
    MBRecordType.ECE: ThreshTypeConfig("V", True, (1e-3, 1)),
    MBRecordType.EWE_ECE: ThreshTypeConfig("V", True, (1e-3, 1)),
    MBRecordType.I: ThreshTypeConfig("A", True, (1e-9, 1)),
    MBRecordType.POWER: ThreshTypeConfig("W", True, (1e-6, 1)),
    MBRecordType.ENERGY: ThreshTypeConfig("W.h", True, (1e-6, 1e3)),
}
    
class MBRecordCriterion(object):
    def __init__(self, record_type: MBRecordType, value: float):
        self.value_unit = None
        
        self.record_type = record_type
        self.value = value
        
    def set_value(self, value: float):
        if self.record_type == MBRecordType.TIME:
            self._value, self.value_unit = units.get_scaled_time(value)
        else:
            config: ThreshTypeConfig = _record_type_config[self.record_type]
            if config.scale_value:
                # Scale the limit value and get the corresponding prefix
                factor_lims = config.factor_range if config.factor_range is not None else (None, None)
                self._value, prefix = units.get_scaled_value_and_prefix(value, *factor_lims)
                self.value_unit = f"{prefix}{config.base_unit}"
            else:
                # Don't scale the value
                self._value = value
                self.value_unit = config.base_unit
                
    def get_value(self):
        return self._value
                
    value = property(get_value, set_value)
    


@dataclass
class MBParametersBase(object):
    technique_name = "Modulo Bat"
    abbreviation = "MB"
    
    ctrl_type: Union[list, str] = None
    auto_rest: int = 0
    
    # Placeholders
    apply_IC: str = "I"
    current_potential: str = "current"
    ctrl1_val: Optional[float] = None
    ctrl1_val_unit: Optional[str] = None
    ctrl1_val_vs: Optional[Union[IVs, EweVs]] = None
    ctrl2_val: Optional[float] = None
    ctrl2_val_unit: Optional[str] = None
    ctrl2_val_vs: Optional[Union[IVs, EweVs]] = None
    ctrl3_val: Optional[float] = None
    ctrl3_val_unit: Optional[str] = None
    ctrl3_val_vs: Optional[Union[IVs, EweVs]] = None
    N: float = 0.0
    charge_discharge: str = "Charge" # TODO: need to select charge/discharge based on sign of current?
    charge_discharge_1: str = "Charge"
    apply_IC_1: str = "I"
    N1: float = 0.0
    ctrl4_val: Optional[float] = None
    ctrl4_val_unit: Optional[str] = None
    ctrl5_val: Optional[float] = None
    ctrl5_val_unit: Optional[str] = None
    ctrl_tM: int = 0
    ctrl_seq: int = 0
    ctrl_repeat: int = 0
    ctrl_trigger: TriggerType = TriggerType.FALLING
    ctrl_TO_t: float = 0.0
    ctrl_TO_t_unit: str = "s"
    ctrl_Nd: int = 6
    ctrl_Na: int = 2
    ctrl_corr: int = 0
    
    # Limits
    lim_nb: int = 0
    
    lim1_type: Optional[MBLimitType] = None
    lim1_comp: Optional[MBLimitComparison] = None
    lim1_Q: Optional[MBLimitQ] = None
    lim1_value: Optional[float] = None
    lim1_value_unit: Optional[str] = None
    lim1_action: Optional[MBLimitAction] = None
    lim1_seq: Optional[int] = None
    
    lim2_type: Optional[MBLimitType] = None
    lim2_comp: Optional[MBLimitComparison] = None
    lim2_Q: Optional[MBLimitQ] = None
    lim2_value: Optional[float] = None
    lim2_value_unit: Optional[str] = None
    lim2_action: Optional[MBLimitAction] = None
    lim2_seq: Optional[int] = None
    
    lim3_type: Optional[MBLimitType] = None
    lim3_comp: Optional[MBLimitComparison] = None
    lim3_Q: Optional[MBLimitQ] = None
    lim3_value: Optional[float] = None
    lim3_value_unit: Optional[str] = None
    lim3_action: Optional[MBLimitAction] = None
    lim3_seq: Optional[int] = None
    
    # Recording criteria
    rec_nb: int = 0
    rec1_type: Optional[MBRecordType] = None
    rec1_value: Optional[float] = None
    rec1_value_unit: Optional[str] = None
    
    rec2_type: Optional[MBRecordType] = None
    rec2_value: Optional[float] = None
    rec2_value_unit: Optional[str] = None
    
    rec3_type: Optional[MBRecordType] = None
    rec3_value: Optional[float] = None
    rec3_value_unit: Optional[str] = None
    
    

    # placeholders = [
    #     'current_potential',
    #     'ctrl1_val',
    #     'ctrl1_val_unit',
    #     'ctrl1_val_vs',
    #     'ctrl2_val',
    #     'ctrl2_val_unit',
    #     'ctrl2_val_vs',
    #     'ctrl3_val',
    #     'ctrl3_val_unit',
    #     'ctrl3_val_vs',
    #     'N',
    #     'charge_discharge',
    #     'charge_discharge_1',
    #     'apply_IC_1',
    #     'N1',
    #     'ctrl4_val',
    #     'ctrl4_val_unit',
    #     'ctrl5_val',
    #     'ctrl5_val_unit',
    #     'ctrl_tM',
    #     'ctrl_seq',
    #     'ctrl_repeat',
    #     'ctrl_trigger',
    #     'ctrl_TO_t',
    #     'ctrl_TO_t_unit',
    #     'ctrl_Nd',
    #     'ctrl_Na',
    #     'ctrl_corr',
    #     'rec_nb',
    #     'rec1_type',
    #     'rec1_value',
    #     'rec1_value_unit',
    #     'auto_rest'
    # ]
    
    
    # _full_param_map = merge_dicts(
    #     {
    #         "Ns": "step_index",
    #         'ctrl_type': 'ctrl_type',
    #         'Apply I/C': 'apply_IC',
    #         'current/potential': 'current_potential',
    #         'ctrl1_val': 'ctrl1_val',
    #         'ctrl1_val_unit': 'ctrl1_val_unit',
    #         'ctrl1_val_vs': 'ctrl1_val_vs',
    #         'ctrl2_val': 'ctrl2_val',
    #         'ctrl2_val_unit': 'ctrl2_val_unit',
    #         'ctrl2_val_vs': 'ctrl2_val_vs',
    #         'ctrl3_val': 'ctrl3_val',
    #         'ctrl3_val_unit': 'ctrl3_val_unit',
    #         'ctrl3_val_vs': 'ctrl3_val_vs',
    #         'N': 'N',
    #         'charge/discharge': 'charge_discharge',
    #         'charge/discharge_1': 'charge_discharge_1',
    #         'Apply I/C_1': 'apply_IC_1',
    #         'N1': 'N1',
    #         'ctrl4_val': 'ctrl4_val',
    #         'ctrl4_val_unit': 'ctrl4_val_unit',
    #         'ctrl5_val': 'ctrl5_val',
    #         'ctrl5_val_unit': 'ctrl5_val_unit',
    #         'ctrl_tM': 'ctrl_tM',
    #         'ctrl_seq': 'ctrl_seq',
    #         'ctrl_repeat': 'ctrl_repeat',
    #         'ctrl_trigger': 'ctrl_trigger',
    #         'ctrl_TO_t': 'ctrl_TO_t',
    #         'ctrl_TO_t_unit': 'ctrl_TO_t_unit',
    #         'ctrl_Nd': 'ctrl_Nd',
    #         'ctrl_Na': 'ctrl_Na',
    #         'ctrl_corr': 'ctrl_corr',
    #         # Limits
    #         'lim_nb': 'lim_nb',
    #         'lim1_type': 'lim1_type',
    #         'lim1_comp': 'lim1_comp',
    #         'lim1_Q': 'lim1_Q',
    #         'lim1_value': 'lim1_value',
    #         'lim1_value_unit': 'lim1_value_unit',
    #         'lim1_action': 'lim1_action',
    #         'lim1_seq': 'lim1_seq',
    #         'lim2_type': 'lim2_type',
    #         'lim2_comp': 'lim2_comp',
    #         'lim2_Q': 'lim2_Q',
    #         'lim2_value': 'lim2_value',
    #         'lim2_value_unit': 'lim2_value_unit',
    #         'lim2_action': 'lim2_action',
    #         'lim2_seq': 'lim2_seq',
    #         'lim3_type': 'lim3_type',
    #         'lim3_comp': 'lim3_comp',
    #         'lim3_Q': 'lim3_Q',
    #         'lim3_value': 'lim3_value',
    #         'lim3_value_unit': 'lim3_value_unit',
    #         'lim3_action': 'lim3_action',
    #         'lim3_seq': 'lim3_seq',
    #         # Recording criteria
    #         'rec_nb': 'rec_nb',
    #         'rec1_type': 'rec1_type',
    #         'rec1_value': 'rec1_value',
    #         'rec1_value_unit': 'rec1_value_unit',
    #         'rec2_type': 'rec2_type',
    #         'rec2_value': 'rec2_value',
    #         'rec2_value_unit': 'rec2_value_unit',
    #         'rec3_type': 'rec3_type',
    #         'rec3_value': 'rec3_value',
    #         'rec3_value_unit': 'rec3_value_unit',
    #     },
    #     {k: _hardware_param_map_ilimit[k] for k in list(_hardware_param_map_ilimit.keys())[:-1]},
    #     {
    #         "auto rest": "auto_rest",
    #         "Bandwidth": "bandwidth"
    #     },   
    # )
    
    
    @property 
    def num_steps(self):
        return len(self.ctrl_type)
    
    def set_ctrl_val(self, ctrl_num: int, value: float, base_unit: str, scale_value: bool = True):
        if scale_value:
            scaled_value, prefix = units.get_scaled_value_and_prefix(value)
        else:
            scaled_value = value
            prefix = ""
            
        setattr(self, f"ctrl{ctrl_num}_val", scaled_value)
        setattr(self, f"ctrl{ctrl_num}_val_unit", f"{prefix}{base_unit}")
    
    def reset_limits(self):
        # Clear all limits
        self.lim_nb = 0
        for i in range(1, 4):
            for name in ["type", "comp", "Q", "value", "value_unit", "action", "seq"]:
                setattr(self, f"lim{i}_{name}", None)
                
    def add_limit(self, limit: MBLimit):
        if self.lim_nb >= 3:
            raise ValueError("The maximum number of limits (3) has already been set")
        
        self.lim_nb = self.lim_nb + 1
        for name, lim_att in zip(
            ["type", "comp", "Q", "value", "value_unit", "action", "seq"],
            ["limit_type", "comparison", "q_limit_type", "value", "value_unit", "action", "goto_seq"]
        ):
            setattr(self, f"lim{self.lim_nb}_{name}", getattr(limit, lim_att))
            
    def set_limits(self, limits: List[MBLimit]):
        for limit in limits:
            self.add_limit(limit)
        
    def add_record_criterion(self, criterion: MBRecordCriterion):
        if self.rec_nb >= 3:
            raise ValueError("The maximum number of recording criteria (3) has already been set")
        
        self.rec_nb = self.rec_nb + 1
        for name, rec_att in zip(
            ["type", "value", "value_unit"],
            ["record_type", "value", "value_unit"]
        ):
            setattr(self, f"rec{self.rec_nb}_{name}", getattr(criterion, rec_att))
            
    def reset_record_criteria(self):
        # Clear all recording criteria
        self.rec_nb = 0
        for i in range(1, 4):
            for name in ["type", "value", "value_unit"]:
                setattr(self, f"rec{i}_{name}", None)
                
    def set_record_criteria(self, record_criteria: List[MBRecordCriterion]):
        for crit in record_criteria:
            self.add_record_criterion(crit)
            
    # @property
    # def _param_map(self):
    #     param_map = self._full_param_map.copy()
        
    #     # Remove unused limits and recording criteria
    #     if self.lim_nb == 0:
    #         del param_map["lim_nb"]
            
    #     for n in range(self.lim_nb + 1, 4):
    #         for name in ["type", "comp", "Q", "value", "value_unit", "action", "seq"]:
    #             del param_map[f"lim{n}_{name}"]
                
    #     if self.rec_nb == 0:
    #         del param_map["rec_nb"]
            
    #     for n in range(self.rec_nb + 1, 4):
    #         for name in ["type", "value", "value_unit"]:
    #             del param_map[f"rec{n}_{name}"]
                
    #     return param_map
        
        
        
    
# ==========================
# Constant Current
# ==========================    
class MBConstantCurrent(MBParametersBase):
    def __init__(self, 
            current: float, 
            limits: List[MBLimit],
            record_criteria: List[MBRecordCriterion],
            i_vs: IVs = IVs.NONE,
        ):
        
        # Set charge/discharge based on current sign and use absolute current
        if current >= 0:
            charge_discharge = "Charge"
        else:
            charge_discharge = "Discharge"
            
        current = abs(current)
        
        super().__init__(
            ctrl_type="CC",
            apply_IC="I",
            current_potential="current",
            ctrl1_val_vs=i_vs,
            charge_discharge=charge_discharge
        )
        
        self.set_ctrl_val(1, current, "A")
                
        self.set_limits(limits)
        self.set_record_criteria(record_criteria)
        

# ==========================
# Constant Voltage
# ==========================    
class MBConstantVoltage(MBParametersBase):
    def __init__(self, 
            voltage: float, 
            limits: List[MBLimit],
            record_criteria: List[MBRecordCriterion],
            v_vs: EweVs = EweVs.REF,
        ):
        
        
        super().__init__(
            ctrl_type="CV",
            apply_IC="I",
            current_potential="current",
            ctrl1_val_vs=v_vs,
        )
        
        self.set_ctrl_val(1, voltage, "V")
                
        self.set_limits(limits)
        self.set_record_criteria(record_criteria)
            

# ==========================
# Urban profile
# ==========================
def make_urban_table(technique_number: int, sequence_number: int, profile: Union[Path, DataFrame]):
    # Make table of time and signal values to define urban profile in mps file
    if not isinstance(profile, DataFrame):
        profile = pd.read_csv(profile)
        
    fields = list(profile.columns)
    time_field = [f for f in fields if f[:4] == "Time"][0]
    time_index = fields.index(time_field)
    signal_name = fields[time_index + 1]
    
    header = [
        "Urban Profile Table",
        f"Technique Number : {technique_number}",
        f"Sequence : {sequence_number}",
        "Number of Values : {:.0f}".format(len(profile)),
        f"Values : Time/s, {signal_name}",
    ]
    
    header = "\n".join(header)
    
    table = profile.to_csv(None, sep="\t", float_format="%.9f", 
                           header=False, lineterminator="\n", index=False)
    
    return header + "\n" + table
    
    
class MBUrbanProfile(MBParametersBase):
    def __init__(self, 
            profile: Union[Path, DataFrame], 
            limits: List[MBLimit],
            record_criteria: List[MBRecordCriterion]
            ):
        
        super().__init__(
            ctrl_type="UP",
            apply_IC="I",
            current_potential="current"
        )
        
        self.profile = profile
        
        self.set_limits(limits)
        self.set_record_criteria(record_criteria)
    
    # TODO: need to handle profile table in technique_sequence
    def profile_table(self, technique_number, sequence_number):
        table = make_urban_table(technique_number, sequence_number, self.profile)
        return table
    
# ==========================
# EIS
# ==========================
    
class EISAmpUnit(StrEnum):
    V = "V"
    A = "A"
    
    
class MBEISBase(MBParametersBase):
    def __init__(self, 
            ctrl_type: str,
            f_max: float,
            f_min: float,
            ac_amp: float,
            ac_amp_unit: EISAmpUnit,
            ppd: int,
            limits: List[MBLimit],
            average: int = 2
            ):
        
        
        super().__init__(
            ctrl_type=ctrl_type,
            apply_IC="I",
            ctrl_Nd=ppd,
            ctrl_Na=average
        )
        
        # NOTE: DC current/voltage is fixed at last measured value!
        
        # AC amplitude goes to ctrl_val1
        self.set_ctrl_val(1, ac_amp, ac_amp_unit.value)
        
        if ac_amp_unit == EISAmpUnit.V:
            self.current_potential = "potential"
        else:
            self.current_potential = "current"
        
        # Set frequencies: f_max goes to ctrl_val2, f_min to ctrl_val3
        self.set_ctrl_val(2, f_max, "Hz")
        self.set_ctrl_val(3, f_min, "Hz")
        
        # Record settings as unscaled, readable attributes
        self.f_min = f_min
        self.f_max = f_max
        self.ppd = ppd
        
        self.set_limits(limits)
        
    def add_limit(self, limit: MBLimit):
        if limit.action == MBLimitAction.STOP:
            raise ValueError("STOP action for limits is not available for EIS steps")
        
        super().add_limit(limit)
        
    @property
    def expected_duration(self):
        return estimate_duration(self.f_min, self.f_max, self.ppd, average=self.ctrl_Na, wait=0.0, point_density=PointDensity.PPD)
        
    
class MBGEIS(MBEISBase):
    def __init__(self, 
            f_max: float,
            f_min: float,
            ac_amp: float,
            ac_amp_unit: EISAmpUnit,
            ppd: int,
            limits: List[MBLimit],
            average: int = 2
            ):
        
        super().__init__(
            "GEIS",
            f_max,
            f_min,
            ac_amp,
            ac_amp_unit,
            ppd,
            limits,
            average
        )
        
        
class MBPEIS(MBEISBase):
    def __init__(self, 
            f_max: float,
            f_min: float,
            ac_amp: float,
            ppd: int,
            limits: List[MBLimit],
            average: int = 2
            ):
        
        super().__init__(
            "PEIS",
            f_max,
            f_min,
            ac_amp,
            EISAmpUnit.V,
            ppd,
            limits,
            average
        )
        
        
# ==========================
# Rest (OCV)
# ==========================
class MBRest(MBParametersBase):
    def __init__(self, 
            limits: List[MBLimit],
            record_criteria: List[MBRecordCriterion]
            ):
        super().__init__(ctrl_type="Rest", current_potential="potential")
        self.set_limits(limits)
        self.set_record_criteria(record_criteria)

# ==========================
# Loop
# ==========================
class MBLoop(MBParametersBase):
    def __init__(self, goto_seq: int, n_times: int):
        super().__init__(ctrl_type="Loop", ctrl_seq=goto_seq, ctrl_repeat=n_times)
        
# ==========================
# Triggers
# ==========================     
class MBTriggerIn(MBParametersBase):
    def __init__(self, edge=TriggerType.RISING):
        super().__init__(ctrl_type="TI", ctrl_trigger=edge)
        
class MBTriggerOut(MBParametersBase):
    def __init__(self, duration_s: float, edge=TriggerType.RISING):
        scaled_duration, duration_unit = units.get_scaled_time(duration_s)
        super().__init__(ctrl_type="TO", ctrl_TO_t=scaled_duration, ctrl_TO_t_unit=duration_unit, ctrl_trigger=edge)
        
        
    
    
    

# @dataclass
# class MBSequence(HardwareParameters, MBParametersBase, StepwiseTechniqueParameters):
    
#     def __post_init__(self):
#         # super().__post_init__()
        
#         # Process stepwise list arguments
#         self.listify_attr("ctrl_type")
#         # self.listify_attr("apply_ic")
        
#         self.listify_attr("i_range", replace_none=IRange.AUTO)
#         for name in ["i_range_min", "i_range_max", "i_range_init"]:
#             self.listify_attr(name, replace_none="Unset")
        
        
#         for name in self.placeholders:
#             self.listify_attr(name, replace_none="")
        
#         # # TODO: check IRange behavior. Should this be set based only on ac_amp?
#         # if self.i_range is None:
#         #     self.i_range = get_i_range(np.max(np.abs(self.step_currents)))
        
#     @classmethod
#     def from_list(
#         cls, 
#         mb_list: List[MBParametersBase], 
#         v_range_min: float = -10.0,
#         v_range_max: float = 10.0,
#         i_range: Optional[IRange] = None,
#         i_range_min: Optional[IRange] = None,
#         i_range_max: Optional[IRange] = None,
#         i_range_init: Optional[IRange] = None,
#         bandwidth: Bandwidth = Bandwidth.BW7,
#         filtering: Filter = Filter.NONE,
#         # auto_rest: bool = False
#     ):
#         # Make lists for all fields
#         field_names = [f.name for f in fields(mb_list[0])]
#         field_input = {
#             k: [getattr(mb, k) for mb in mb_list] for k in field_names
#         }
        
#         out = cls(
#             **field_input, v_range_min=v_range_min, v_range_max=v_range_max, 
#             i_range=i_range, i_range_min=i_range_min, i_range_max=i_range_max, i_range_init=i_range_init,
#             bandwidth=bandwidth, filtering=filtering,
#         )
        
        
#         out.listify_attr("i_range", replace_none=IRange.AUTO)
#         for name in ["i_range_min", "i_range_max", "i_range_init"]:
#             out.listify_attr(name, replace_none="Unset")
        
        
#         for name in field_names:
#             if name not in ["i_range", "i_range_min", "i_range_max", "i_range_init"]:
#                 out.listify_attr(name, replace_none="")
                
#         return out
    
    
@dataclass
class MBSequence(HardwareParameters, MBParametersBase, StepwiseTechniqueParameters):
    _full_param_map = merge_dicts(
        {
            "Ns": "step_index",
            'ctrl_type': 'ctrl_type',
            'Apply I/C': 'apply_IC',
            'current/potential': 'current_potential',
            'ctrl1_val': 'ctrl1_val',
            'ctrl1_val_unit': 'ctrl1_val_unit',
            'ctrl1_val_vs': 'ctrl1_val_vs',
            'ctrl2_val': 'ctrl2_val',
            'ctrl2_val_unit': 'ctrl2_val_unit',
            'ctrl2_val_vs': 'ctrl2_val_vs',
            'ctrl3_val': 'ctrl3_val',
            'ctrl3_val_unit': 'ctrl3_val_unit',
            'ctrl3_val_vs': 'ctrl3_val_vs',
            'N': 'N',
            'charge/discharge': 'charge_discharge',
            'charge/discharge_1': 'charge_discharge_1',
            'Apply I/C_1': 'apply_IC_1',
            'N1': 'N1',
            'ctrl4_val': 'ctrl4_val',
            'ctrl4_val_unit': 'ctrl4_val_unit',
            'ctrl5_val': 'ctrl5_val',
            'ctrl5_val_unit': 'ctrl5_val_unit',
            'ctrl_tM': 'ctrl_tM',
            'ctrl_seq': 'ctrl_seq',
            'ctrl_repeat': 'ctrl_repeat',
            'ctrl_trigger': 'ctrl_trigger',
            'ctrl_TO_t': 'ctrl_TO_t',
            'ctrl_TO_t_unit': 'ctrl_TO_t_unit',
            'ctrl_Nd': 'ctrl_Nd',
            'ctrl_Na': 'ctrl_Na',
            'ctrl_corr': 'ctrl_corr',
            # Limits
            'lim_nb': 'lim_nb',
            'lim1_type': 'lim1_type',
            'lim1_comp': 'lim1_comp',
            'lim1_Q': 'lim1_Q',
            'lim1_value': 'lim1_value',
            'lim1_value_unit': 'lim1_value_unit',
            'lim1_action': 'lim1_action',
            'lim1_seq': 'lim1_seq',
            'lim2_type': 'lim2_type',
            'lim2_comp': 'lim2_comp',
            'lim2_Q': 'lim2_Q',
            'lim2_value': 'lim2_value',
            'lim2_value_unit': 'lim2_value_unit',
            'lim2_action': 'lim2_action',
            'lim2_seq': 'lim2_seq',
            'lim3_type': 'lim3_type',
            'lim3_comp': 'lim3_comp',
            'lim3_Q': 'lim3_Q',
            'lim3_value': 'lim3_value',
            'lim3_value_unit': 'lim3_value_unit',
            'lim3_action': 'lim3_action',
            'lim3_seq': 'lim3_seq',
            # Recording criteria
            'rec_nb': 'rec_nb',
            'rec1_type': 'rec1_type',
            'rec1_value': 'rec1_value',
            'rec1_value_unit': 'rec1_value_unit',
            'rec2_type': 'rec2_type',
            'rec2_value': 'rec2_value',
            'rec2_value_unit': 'rec2_value_unit',
            'rec3_type': 'rec3_type',
            'rec3_value': 'rec3_value',
            'rec3_value_unit': 'rec3_value_unit',
        },
        {k: _hardware_param_map_ilimit[k] for k in list(_hardware_param_map_ilimit.keys())[:-1]},
        {
            "auto rest": "auto_rest",
            "Bandwidth": "bandwidth"
        },   
    )
    
    def __init__(
        self, 
        mb_list: List[MBParametersBase], 
        v_range_min: float = -10.0,
        v_range_max: float = 10.0,
        i_range: Optional[IRange] = None,
        i_range_min: Optional[IRange] = None,
        i_range_max: Optional[IRange] = None,
        i_range_init: Optional[IRange] = None,
        bandwidth: Bandwidth = Bandwidth.BW7,
        filtering: Filter = Filter.NONE,
        auto_rest: bool = False
    ):

        # init hardware parameters
        super().__init__(
            v_range_min=v_range_min, v_range_max=v_range_max, 
            i_range=i_range, i_range_min=i_range_min, i_range_max=i_range_max, i_range_init=i_range_init,
            bandwidth=bandwidth, filtering=filtering,
        )
        
        # Make lists of all MB fields: one entry per step
        field_names = [f.name for f in fields(mb_list[0])]
        field_input = {
            k: [getattr(mb, k) for mb in mb_list] for k in field_names
        }
        
        for k, v in field_input.items():
            setattr(self, k, v)
        
        # Store the list of MBParam objects for reference
        self.mb_list = mb_list
        
        # Set a single value for auto_rest, which is listified below
        self.auto_rest = auto_rest
        
        
        self.listify_attr("i_range", replace_none=IRange.AUTO)
        for name in ["i_range_min", "i_range_max", "i_range_init"]:
            self.listify_attr(name, replace_none="Unset")
        
        
        for name in field_names:
            if name not in ["i_range", "i_range_min", "i_range_max", "i_range_init"]:
                self.listify_attr(name, replace_none="")
           
    @property
    def max_lim_nb(self):
        return max(self.lim_nb)
    
    @property
    def max_rec_nb(self):
        return max(self.rec_nb)
                
    @property
    def _param_map(self):
        param_map = self._full_param_map.copy()
        
        # Remove unused limits and recording criteria
        if self.max_lim_nb == 0:
            del param_map["lim_nb"]
            
        for n in range(self.max_lim_nb + 1, 4):
            for name in ["type", "comp", "Q", "value", "value_unit", "action", "seq"]:
                del param_map[f"lim{n}_{name}"]
                
        if self.max_rec_nb == 0:
            del param_map["rec_nb"]
            
        for n in range(self.max_rec_nb + 1, 4):
            for name in ["type", "value", "value_unit"]:
                del param_map[f"rec{n}_{name}"]
                
        return param_map
    
    def get_urban_tables(self, technique_number: int):
        tables = []
        for i, mb in enumerate(self.mb_list):
            if isinstance(mb, MBUrbanProfile):
                tables.append(mb.profile_table(technique_number, i))
                
        return tables
                
        
        
        
        
        

# TODO: provide a list of signal arrays or files
@dataclass    
class _MBUrbanProfileList():
    
    profiles: List[Union[Path, DataFrame]]
    record_dt: float
    
    
@dataclass    
class MBUrbanProfileList(MBSequence, _MBUrbanProfileList):
    
    def __post_init__(self):
        
        self.ctrl_type = ["UP"] * len(self.profiles)
        
        # Process sample interval
        dt_value, dt_units = units.get_scaled_time(self.record_dt)
        self.rec1_value = dt_value
        self.rec1_value_unit = dt_units
        self.rec1_type = "Time"
        
        super().__post_init__()
        
        if len(self.profiles) == 1:
            # If there is only one profile, we don't write Ns to mps file
            # _param_map is a class attribute, so we need to copy it first
            self._param_map = self._param_map.copy()
            del self._param_map["Ns"]
        
    def param_text(self, technique_number, configuration: FullConfiguration):
        # Get main technique text
        text = super().param_text(technique_number, configuration)
        
        for i, profile in enumerate(self.profiles):
            table = make_urban_table(technique_number, i, profile)
            
            text += "\n\n" + table
        
        return text
        
        
        


# MBUrbanProfileList(profiles=['a', 'b'])
