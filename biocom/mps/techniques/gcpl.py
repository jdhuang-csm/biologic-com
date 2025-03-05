
from enum import Enum, StrEnum
from dataclasses import dataclass, field
import numpy as np
from numpy import ndarray
import datetime
from typing import Union, Optional, List

from .stepwise import StepwiseTechniqueParameters

from ... import units
from ..common import (
    IRange, EweVs, IVs, get_i_range, DQUnits
)
from ..config import FullConfiguration, BatteryCharacteristics
from .technique import (
    HardwareParameters, _hardware_param_map, _hardware_param_map_ilimit, _loop_param_map
)
from ..write_utils import format_duration
from ...utils import merge_dicts, isiterable


class CurrentSpec(Enum):
    I = "I"
    CDN = "C / N"
    CTN = "C x N"
    
    
def convert_currents(i_in, current_spec: CurrentSpec, q_theo: float):
    if isiterable(i_in):
        i_in = np.array(i_in)
        
    # Get currents in A based on battery capacity
    if current_spec == CurrentSpec.CTN:
        # i_in are N values (C x N)
        i_A = q_theo * i_in
    elif current_spec == CurrentSpec.CTN:
        # i_in are N values (C / N)
        i_A = q_theo / i_in
    else:
        # i_in are absolute current values in A
        i_A = i_in
        
    return i_A

@dataclass
class _GCPLParameters(object):
    
    current_spec: List[CurrentSpec]
    step_currents: Union[List[float], ndarray]
    current_signs: Union[List[int], ndarray]
    step_durations: Union[List[float], ndarray]
    E_M: Union[List[float], ndarray]
    dE1: Union[List[float], ndarray]
    dt1: Union[List[float], ndarray]
    
    # For E_m hold
    t_M: Optional[Union[List[float], ndarray]] = None
    I_m: Optional[List[float]] = None
    dIdt_m: Optional[List[float]] = None
    dQ: Optional[List[float]] = None
    dt_q: Optional[List[float]] = None
    
    # Limits
    dQ_m: Optional[Union[List[float], ndarray]] = None
    dx_m: Optional[Union[List[float], ndarray]] = None
    dSoc: Optional[Union[List[float], ndarray]] = None
    
    # Final rest period
    t_R: Optional[Union[List[float], ndarray]] = None
    dEdt_R: Optional[Union[List[float], ndarray]] = None
    dE_R: Optional[Union[List[float], ndarray]] = None
    dt_R: Optional[Union[List[float], ndarray]] = None
    
    
    E_L: Optional[float] = None
    i_vs: Union[IVs, List[IVs]] = IVs.NONE
    v_limits: Optional[List[float]] = None
    dq_limits: Optional[List[float]] = None
    dq_units: DQUnits = DQUnits.AH
    
    
    # Placeholders
    goto_ns: int = 0
    nc_cycles: int = 0
    
    technique_name = "Galvanostatic Cycling with Potential Limitation"
    abbreviation = "GCPL"
    
    _param_map = merge_dicts(
        {
            "Ns": "step_index",
            "Set I/C": "current_spec",
            "Is": "_step_i_A_scaled",
            "unit Is": "_step_i_A_unit",
            "vs.": "i_vs",
            "N": "N",
            "I sign": "_i_signs_formatted",
            "t1 (h:m:s)": "_step_durations_formatted",
        },
        {k: _hardware_param_map[k] for k in ["I range", "Bandwidth"]},
        {
            "dE1 (mV)": "dE1",
            "dt1 (s)": "dt1",
            "EM (V)": "E_M",
            "tM (h:m:s)": "_t_M_formatted",
            "Im": "_Im_scaled",
            "unit Im": "_Im_unit",
            "dI/dt": "_dIdt_m_scaled",
            "dunit dI/dt": "_dIdt_m_unit",
        },
        {k: _hardware_param_map[k] for k in ["E range min (V)", "E range max (V)"]},
        {
            "dq": "_dQ_scaled",
            "unit dq": "_dQ_unit",
            "dtq (s)": "dt_q",
            "dQM": "_dQ_m_scaled",
            "unit dQM": "_dQ_m_unit",
            "dxM": "dxM",
            "delta SoC (%)": "dSOC",
            "tR (h:m:s)": "_t_R_formatted",
            "dER/dt (mV/h)": "dEdt_R",
            "dER (mV)": "dE_R",
            "dtR (s)": "dtR" ,
            "EL (V)": "E_L",
        },
        _loop_param_map
    )
    
@dataclass
class GCPLParameters(HardwareParameters, _GCPLParameters, StepwiseTechniqueParameters):
    
    @property
    def _step_durations_formatted(self):
        return [format_duration(t) for t in self.step_durations]
    
    @property
    def _t_M_formatted(self):
        return [format_duration(t) for t in self.t_M]
    
    @property
    def _t_R_formatted(self):
        return [format_duration(t) for t in self.t_R]
    
    @property
    def num_steps(self):
        return len(self.step_durations)
    
    @property
    def _i_signs_formatted(self):
        ["> 0" if s >= 0 else "< 0" for s in self.current_signs]
        
        
    def apply_configuration(self, configuration: FullConfiguration):
        if not isinstance(configuration.sample, BatteryCharacteristics):
            raise TypeError("Sample type must be Battery for GCPL (SampleType.BATTERY or BatteryCharacteristics)")

        config: BatteryCharacteristics = configuration.sample
        
        # Get theoretical capacity in Ah
        self._Q_theo = config.capacity_mAh * 1e-3
        
        self.step_i_A = convert_currents(self.step_currents, self.current_spec, self._Q_theo)
            
        self.listify_attr("step_i_A", base_unit="A")
    
    
    def __post_init__(self):
        # super().__post_init__()
        # Format stepwise settings as lists
        self.step_currents = list(self.step_currents)
        self.step_durations = list(self.step_durations)
        self.current_signs = list(self.current_signs)
        self.E_M = list(self.E_M)
        
        # Initialize
        self.step_i_A = None
        
        # Process stepwise list arguments
        # current_spec: List[CurrentSpec]
        # step_currents: Union[List[float], ndarray]
        # step_durations: Union[List[float], ndarray]
        # E_m: Union[List[float], ndarray]
        # dE1: Union[List[float], ndarray]
        # dt1: Union[List[float], ndarray]
        
        # # For E_m hold
        # tM: Optional[Union[List[float], ndarray]] = None
        # I_m: Optional[List[float]] = None
        # didt_m: Optional[List[float]] = None
        # dQ: Optional[List[float]] = None
        # dt_q: Optional[List[float]] = None
        
        # # Limits
        # dQ_m: Optional[Union[List[float], ndarray]] = None
        # dx_m: Optional[Union[List[float], ndarray]] = None
        # dSoc: Optional[Union[List[float], ndarray]] = None
        
        # # Final rest period
        # t_R: Optional[Union[List[float], ndarray]] = None
        # dEdt_R: Optional[Union[List[float], ndarray]] = None
        # dE_R: Optional[Union[List[float], ndarray]] = None
        # dt_R: Optional[Union[List[float], ndarray]] = None
        
        
        # E_L: Optional[float] = None
        # i_vs: Union[IVs, List[IVs]] = IVs.NONE
        # v_limits: Optional[List[float]] = None
        # dq_limits: Optional[List[float]] = None
        # dq_units: DQUnits = DQUnits.AH
        
        # Main box
        for name in [
            "step_currents"
            "i_vs",
            "current_spec",
            "E_M",
            "dE1",
            "dt1"
        ]:
            self.listify_attr(name)
        
        
            
        # For EM hold
        self.listify_attr("t_M", replace_none=0.0)
        self.listify_attr("I_m", replace_none=0.0, base_unit="A")
        self.listify_attr("dIdt_m", replace_none=0.0, base_unit="A/s")
        self.listify_attr("dQ", replace_none=0.0, base_unit=self.dq_units.value)
        self.listify_attr("dt_q", replace_none=0.0)
        
        # Limits
        self.listify_attr("dQ_m", replace_none=0.0, base_unit=self.dq_units.value)
        self.listify_attr("dx_m", replace_none=0.0)
        self.listify_attr("dSoC", replace_none=0.0)
        
        # Final rest period
        self.listify_attr("t_R", replace_none=0.0)
        self.listify_attr("dEdt_R", replace_none=0.0)
        self.listify_attr("dE_R", replace_none=0.0)
        self.listify_attr("dt_R", replace_none=0.0)
        
        self.listify_attr("E_L", replace_none="pass")
        

        # if isinstance(self.i_vs, IVs):
        #     self.i_vs = [self.i_vs] * self.num_steps
            
        # if self.v_limits is None or np.isscalar(self.v_limits):
        #     self.v_limits = ['pass'] * self.num_steps
            
        # if self.dq_limits is None:
        #     self.dq_limits = [0.0] * self.num_steps
        
        # print('num_steps:', self.num_steps)
        # print('step_currents:', self.step_currents, len(self.step_currents))
        
        # Checks
        if len(self.step_currents) != self.num_steps:
            raise ValueError("Length of step_currents must match length of step_durations")
        # TODO: update checks
        for name in ["i_vs", "v_limits"]:
            if len(getattr(self, name)) != self.num_steps:
                raise ValueError(f"{name} must either be a single value of a list of same length as step_durations")
        
        # Set IRange automatically
        if self.i_range is None:
            self.i_range = [get_i_range(abs(i) for i in self.step_currents)]
            
        if self.num_steps == 1:
            # If there is only one step, we don't write Ns to mps file
            # _param_map is a class attribute, so we need to copy it first
            self._param_map = self._param_map.copy()
            del self._param_map["Ns"]
            
        # Process lists
        # self._step_currents_scaled, self._step_currents_unit = process_list_values(self.step_currents, "A")
        # self._dq_limits_scaled, self._dq_limits_unit = process_list_values(self.dq_limits, self.dq_units.value)

        