from enum import StrEnum
from dataclasses import dataclass, field
import numpy as np
from numpy import ndarray
import datetime
from typing import Union, Optional, List

from .stepwise import StepwiseTechniqueParameters

from ... import units
from ..common import (
    IRange, EweVs, IVs, DQUnits, get_i_range
)
from .technique import (
    HardwareParameters, _hardware_param_map, _hardware_param_map_ilimit, _loop_param_map
)
from ..write_utils import format_duration
from ...utils import merge_dicts, isiterable


    # mAH = "mA.h"
    
    
# def process_list_values(vals: list, base_unit: Optional[str], replace_none=None):
#     scaled_vals = [units.get_scaled_value(v) for v in vals]
#     unit = [units.get_prefix_char(v) + base_unit for v in vals]
    
#     if replace_none is not None:
#         # Replace Nones with specified value
#         scaled_vals = [v or replace_none for v in scaled_vals]
        
#     return scaled_vals, unit
    
    
class ChronoParametersBase(object):
    step_durations: list
    
    @property
    def num_steps(self):
        return len(self.step_durations)
    
    # def listify_attr(self, name: str, base_unit: str = None, replace_none=None):
    #     """Format stepwise attribute as list.

    #     :param str name: Attribute name.
    #     :param str base_unit: base unit (e.g. V, A, C). If provided, 
    #         appropriate unit prefixes will be selected and values
    #         will be scaled accordingly. The scaled values and prefixed
    #         units will be stored in _{name}_scaled and _{name}_units,
    #         respectively. Defaults to None (no scaling).
    #     :param Any replace_none: If provided, replace None with this 
    #         value. Defaults to None (no replacement).
    #     """
    #     vals = getattr(self, name)
        
    #     if not isiterable(vals) or isinstance(vals, str):
    #         # Convert scalar to list
    #         vals = [vals or replace_none] * self.num_steps
    #     elif replace_none is not None:
    #         # Replace Nones
    #         vals = [v or replace_none for v in vals]
            
    #     setattr(self, name, vals)
        
    #     if base_unit is not None:
    #         # Scale values and get units
    #         scaled_vals, unit = process_list_values(vals, base_unit)
    #         setattr(self, f"_{name}_scaled", scaled_vals)
    #         setattr(self, f"_{name}_unit", unit)
    

@dataclass
class _CPParameters(object):
    step_currents: Union[list, ndarray]
    step_durations: Union[list, ndarray]
    record_dt: Union[float, List[float]]
    i_vs: Union[IVs, List[IVs]] = IVs.NONE
    v_limits: Optional[List[float]] = None
    dq_limits: Optional[List[float]] = None
    dq_units: DQUnits = DQUnits.AH
    record_average: bool = False
    record_dv_mV: float = 0.0  # mV
    
    # Placeholders
    goto_ns: int = 0
    nc_cycles: int = 0
    
    technique_name = "Chronopotentiometry"
    abbreviation = "CP"
    
    _param_map = merge_dicts(
        {
            'Ns': 'step_index',
            'Is': '_step_currents_scaled',
            'unit Is': '_step_currents_unit',
            'vs.': 'i_vs',
            'ts (h:m:s)': '_step_durations_formatted',
            'EM (V)': 'v_limits',
            'dQM': '_dq_limits_scaled',
            'unit dQM': '_dq_limits_unit',
            'record': '_record',
            'dEs (mV)': 'record_dv_mV',
            'dts (s)': 'record_dt' 
        },
        _hardware_param_map,
        _loop_param_map
    )
    
@dataclass
class CPParameters(HardwareParameters, _CPParameters, ChronoParametersBase, StepwiseTechniqueParameters):
    
    def __post_init__(self):
        # super().__post_init__()
        # Format stepwise settings as lists
        self.step_currents = list(self.step_currents)
        self.step_durations = list(self.step_durations)
        
        # Process stepwise list arguments
        self.listify_attr("i_vs")
        self.listify_attr("record_dt")
        self.listify_attr("v_limits", replace_none="pass")
        # With scaling and unit selection
        self.listify_attr("step_currents", base_unit="A")
        self.listify_attr("dq_limits", base_unit=self.dq_units.value, replace_none=0.0)
        
        # Checks
        if len(self.step_currents) != self.num_steps:
            raise ValueError('Length of step_currents must match length of step_durations')
        for name in ["i_vs", "v_limits", "dq_limits"]:
            if len(getattr(self, name)) != self.num_steps:
                raise ValueError(f'{name} must either be a single value of a list of same length as step_durations')
        
        # TODO: check IRange behavior. Should this be set based only on ac_amp?
        if self.i_range is None:
            self.i_range = get_i_range(np.max(np.abs(self.step_currents)))
            
        if self.num_steps == 1:
            # If there is only one step, we don't write Ns to mps file
            # _param_map is a class attribute, so we need to copy it first
            self._param_map = self._param_map.copy()
            del self._param_map["Ns"]
            
        # Process lists
        # self._step_currents_scaled, self._step_currents_unit = process_list_values(self.step_currents, "A")
        # self._dq_limits_scaled, self._dq_limits_unit = process_list_values(self.dq_limits, self.dq_units.value)

        
    @property
    def _record(self):
        if self.record_average:
            return "<Ewe>"
        return "Ewe"
    
    # @property
    # def _record_dv_mv(self):
    #     return self.record_dv * 1000.0
   
    @property
    def _step_durations_formatted(self):
        return [format_duration(t) for t in self.step_durations]


@dataclass
class _CAParameters(object):
    step_voltages: Union[list, ndarray]
    step_durations: Union[list, ndarray]
    record_dt: Union[float, List[float]]
    v_vs: Union[EweVs, List[EweVs]] = EweVs.REF
    i_limits_min: Optional[List[float]] = None
    i_limits_max: Optional[List[float]] = None
    dq_limits: Optional[List[float]] = None
    dq_units: DQUnits = DQUnits.AH
    record_average: bool = False
    record_di: float = 0.0  # mV
    record_dq: float = 0.0
    
    # Placeholders
    goto_ns: int = 0
    nc_cycles: int = 0
    
    technique_name = "Chronoamperometry / Chronocoulometry"
    abbreviation = "CA"
    
    _param_map = merge_dicts(
        {
            'Ns': 'step_index',
            'Ei (V)': 'step_voltages',
            'vs.': 'v_vs',
            'ti (h:m:s)': '_step_durations_formatted',
            'Imax': '_i_limits_max_scaled',
            'unit Imax': '_i_limits_max_unit',
            'Imin': '_i_limits_min_scaled',
            'unit Imin': '_i_limits_min_unit',
            'dQM': '_dq_limits_scaled',
            'unit dQM': '_dq_limits_unit',
            'record': '_record',
            'dI': '_record_di_scaled',
            'unit dI': '_record_di_unit',
            'dQ': '_record_dq_scaled',
            'unit dQ': '_record_dq_unit',
            'dt (s)': 'record_dt',
            'dta (s)': 'record_dt'
        },
        _hardware_param_map_ilimit,
        _loop_param_map
    )
    
    
@dataclass
class CAParameters(HardwareParameters, _CAParameters, ChronoParametersBase, StepwiseTechniqueParameters):
    
    def __post_init__(self):
        # super().__post_init__()
        
        # Format stepwise settings as lists
        self.step_voltages = list(self.step_voltages)
        self.step_durations = list(self.step_durations)
        
        if self.i_range is None:
            self.i_range = IRange.AUTO
        
        # Process stepwise list arguments
        self.listify_attr("i_range", replace_none=IRange.AUTO)
        for name in ["i_range_min", "i_range_max", "i_range_init"]:
            self.listify_attr(name, replace_none="Unset")
        # self.listify_attr("step_voltages")
        for name in ["v_vs", "record_dt"]:
            self.listify_attr(name)
            
        # With scaling and unit selection
        self.listify_attr("record_di", base_unit="A", replace_none=0.0)
        self.listify_attr("record_dq", base_unit=self.dq_units.value, replace_none=0.0)
        self.listify_attr("i_limits_max", base_unit="A", replace_none="pass")
        self.listify_attr("i_limits_min", base_unit="A", replace_none="pass")
        self.listify_attr("dq_limits", base_unit=self.dq_units.value, replace_none="pass")
        
        # print('num_steps:', self.num_steps)
        # print('step_voltages:', self.step_voltages, len(self.step_voltages))
        
        # Checks
        if len(self.step_voltages) != self.num_steps:
            raise ValueError('Length of step_currents must match length of step_durations')
        for name in ["v_vs", "i_limits_min", "i_limits_max", "dq_limits"]:
            if len(getattr(self, name)) != self.num_steps:
                raise ValueError(f"{name} must either be a single value of a list of same length "
                                 f"as step_durations. Received value: {getattr(self, name)}")
        
        
        if self.num_steps == 1:
            # If there is only one step, we don't write Ns to mps file
            # _param_map is a class attribute, so we need to copy it first
            self._param_map = self._param_map.copy()
            del self._param_map["Ns"]
            
        # Process lists
        # self._step_currents_scaled, self._step_currents_unit = process_list_values(self.step_currents, "A")
        # self._dq_limits_scaled, self._dq_limits_unit = process_list_values(self.dq_limits, self.dq_units.value)
    

        
    @property
    def _record(self):
        if self.record_average:
            return "<I>"
        return "I"
    
    # @property
    # def _record_dv_mv(self):
    #     return self.record_dv * 1000.0
   
    @property
    def _step_durations_formatted(self):
        return [format_duration(t) for t in self.step_durations]        
    
    
    
