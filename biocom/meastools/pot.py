import numpy as np
from pathlib import Path
from typing import Union, Optional, Tuple

from ..com.server import OLECOM, DeviceChannel
from ..mps.techniques.sequence import TechniqueSequence
from ..mps.techniques.chrono import CAParameters
from ..mps.common import EweVs, IRange, IVs, Bandwidth, BLDeviceModel, SampleType, get_i_range
from ..mps import config as cfg
from ..mpr import read_mpr
from ..mps.write import write_techniques

from ..processing.chrono import ControlMode, process_ivt_simple


def load_irange_test(
        server: OLECOM, 
        device_channel: DeviceChannel,
        mps_file: Path,
        v_dc: float,
        v_ac: float,
        step_duration: float = 0.5, 
        dt: float = 1e-3, 
        t_init: Optional[float] = None,
        t_final: Optional[float] = None,
        **kwargs):
    
    t_dc = max(0.1, step_duration * 0.1)
    
    if t_final is None:
        t_final = t_dc
        
    if t_init is None:
        t_init = t_dc
        
    step_durations = [t_init] + [step_duration] * 4  + [t_final]
    step_voltages = [v_dc, v_dc + v_ac, v_dc - v_ac, v_dc + v_ac, v_dc - v_ac, v_dc]
    
    ca = CAParameters(
        step_voltages,
        step_durations,
        dt,
        bandwidth=device_channel.model.max_bandwidth,
        **kwargs
    )
    # print("step durations:", ca.step_durations, ca._step_durations_formatted)
    # print("I Range:", ca.i_range)
    # print("I Range init:", ca.i_range_init)
    
    seq = TechniqueSequence([ca])
    config = cfg.set_defaults(device_channel.model, seq, 
                              SampleType.CORROSION)
    
    write_techniques(seq, config, mps_file.parent.joinpath(mps_file.name.replace(".mps", "_tmp.mps")))
    
    return server.load_techniques(device_channel, seq, config, mps_file)


def read_irange_test(mpr_file: Path):
    mpr = read_mpr(Path(mpr_file), unscale=True)
    i = mpr.data["I/A"]
    i_max = np.max(np.abs(i))
    return i_max, get_i_range(i_max)