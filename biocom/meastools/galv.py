import numpy as np
from pathlib import Path
from typing import Union, Optional, Tuple

from ..com.server import OLECOM, DeviceChannel
from ..mps.techniques.sequence import TechniqueSequence
from ..mps.techniques.chrono import CAParameters
from ..mps.techniques.eis import PEISParameters
from ..mps.common import EweVs, IRange, IVs, Bandwidth, BLDeviceModel, SampleType
from ..mps import config as cfg
from ..mpr import read_mpr
from ..mps.write import write_techniques

from ..processing.chrono import ControlMode, process_ivt_simple, LinearIV, process_ivt_drt

# Chrono methods
def run_iac_chrono_test(
        server: OLECOM, 
        device_channel: DeviceChannel,
        mps_file: Path,
        v_dc: float,
        v_ac: float,
        step_duration: float, 
        dt: float, 
        t_init: Optional[float] = None,
        t_final: Optional[float] = None,
        bandwidth: Optional[Bandwidth] = None,
        **kwargs):
    
    t_dc = max(0.1, step_duration * 0.1)
    
    if t_final is None:
        t_final = step_duration
        
    if t_init is None:
        t_init = t_dc
        
    step_durations = [t_init, step_duration, step_duration, t_final]
    step_voltages = [v_dc, v_dc + v_ac, v_dc - v_ac, v_dc]
    
    if bandwidth is None:
        # Use highest available bandwidth
        bandwidth = Bandwidth(device_channel.model.max_bandwidth)
    
    ca = CAParameters(
        step_voltages,
        step_durations,
        dt,
        bandwidth=bandwidth,
        **kwargs
    )
    print("step durations:", ca.step_durations, ca._step_durations_formatted)
    print("I Range:", ca.i_range)
    print("I Range init:", ca.i_range_init)
    
    seq = TechniqueSequence([ca])
    config = cfg.set_defaults(device_channel.model, seq, 
                              SampleType.CORROSION)
    
    # write_techniques(seq, config, mps_file.parent.joinpath(mps_file.name.replace(".mps", "_tmp.mps")))
    
    server.load_techniques(device_channel, seq, config, mps_file)

    server.run_channel(device_channel, mps_file)

    return server.get_data_filename(device_channel, 0)


def process_iac_chrono_test(mpr_file: Path, use_drt: bool = False) -> LinearIV:
    mpr = read_mpr(Path(mpr_file), unscale=True)
    
    if "<I>/A" in mpr.data.dtype.fields.keys():
        i_field = "<I>/A"
    else:
        i_field = "I/A"
        
    if use_drt:
        iv = process_ivt_drt(
            mpr.data['time/s'], mpr.data[i_field], mpr.data['Ewe/V'],
            ControlMode.POT
        )
    else:
        iv = process_ivt_simple(
            mpr.data['time/s'], mpr.data[i_field], mpr.data['Ewe/V'],
            ControlMode.POT
        )
    
    return iv
    
def read_iac_chrono(
        mpr_file: Path,
        v_dc: float,
        v_ac: float,
        use_drt=False) -> Tuple[LinearIV, float, float]:
    iv = process_iac_chrono_test(mpr_file, use_drt=use_drt)
    
    return iv, iv.eval_iac(v_dc, v_ac)

# Frequency methods
def load_iac_z_test(server: OLECOM, 
        device_channel: DeviceChannel,
        mps_file: Path,
        v_dc: float,
        v_ac: float,
        f: float,
        v_vs: EweVs = EweVs.REF,
        bandwidth: Optional[Bandwidth] = None,
        **kwargs):
    if bandwidth is None:
        # Use highest available bandwidth
        bandwidth = Bandwidth(device_channel.model.max_bandwidth)
    
    eis = PEISParameters(
        v_dc,
        v_ac,
        v_vs,
        f,
        f,
        bandwidth=bandwidth,
        **kwargs
    )
        
    seq = TechniqueSequence([eis])
    config = cfg.set_defaults(device_channel.model, seq, 
                              SampleType.CORROSION)
    
    # write_techniques(seq, config, mps_file.parent.joinpath(mps_file.name.replace(".mps", "_tmp.mps")))
    
    return server.load_techniques(device_channel, seq, config, mps_file)
    
def run_iac_z_test(
        server: OLECOM, 
        device_channel: DeviceChannel,
        mps_file: Path,
        v_dc: float,
        v_ac: float,
        f: float,
        v_vs: EweVs = EweVs.REF,
        bandwidth: Optional[Bandwidth] = None,
        **kwargs):
    
    load_iac_z_test(
        server,
        device_channel,
        mps_file,
        v_dc,
        v_ac,
        f,
        v_vs,
        bandwidth,
        **kwargs
    )

    server.run_channel(device_channel, mps_file)

    return server.get_data_filename(device_channel, 0)


def process_iac_z_test(mpr_file: Path) -> LinearIV:
    mpr = read_mpr(Path(mpr_file), unscale=True)
    
    i_mid = mpr.data["<I>/A"][0]  
    v_mid = mpr.data["<Ewe>/V"][0]  
    # zmod = mpr.data["|Z|/Ohm"][0]
    
    # Assuming RC behavior, zimag will be converted to zreal at low frequencies
    zreal = mpr.data["Re(Z)/Ohm"][0]
    zimag = mpr.data["-Im(Z)/Ohm"][0]
    
    return LinearIV(i_mid, v_mid, np.sqrt(zreal ** 2 + zimag ** 2))