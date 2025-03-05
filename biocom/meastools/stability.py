import numpy as np
from numpy import ndarray
import scipy.ndimage as ndi
from pathlib import Path
import asyncio
from collections import deque
import time
from typing import Callable, Optional, Union

from ..com.server import OLECOM, DeviceChannel
from ..mps.common import EweVs, Bandwidth, SampleType
from ..mps.techniques.eis import PEISParameters
from ..mps.techniques.sequence import TechniqueSequence
from ..mps import config as cfg


def load_z_stability_test(
        server: OLECOM, 
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
    
    server.load_techniques(device_channel, seq, config, mps_file)
    
    
async def run_z_stability_test_async(
        server: OLECOM, 
        device_channel: DeviceChannel,
        min_wait: float,
        timeout: float, 
        window: int = 10,
        rate_thresh: float = 0.01
        ):
    # assume that settings are already loaded
    z_log = deque()
    
    # Write to a single mpr file and overwrite at each iteration
    mpr_file = server.get_settings(device_channel).replace(".mps", ".mpr")

    start_time = time.monotonic()
    elapsed = 0
    stable = False
    while not (stable and elapsed > min_wait):
        # Launch z measurement
        output_file = server.run_channel(device_channel, output_file=mpr_file)
        
        await server.wait_for_channel_async(device_channel, min_wait=1.0, timeout=120.0)
        
        elapsed = time.monotonic() - start_time
        data = server.get_eis_value(output_file, 0)
        z_log.append([elapsed, data['Re(Z)/Ohm'], data['-Im(Z)/Ohm']])
        
        if len(z_log >= window):
            z_arr = np.array(z_log)[-window:]
            z_mod = np.sum(z_arr[:, 1:] **2, axis=1) ** 0.5
            # Calculate rate of change as % of |Z| per minute
            stable = value_is_stable(z_arr[:, 0], z_arr[:, 1:], z_mod * rate_thresh)

        if elapsed > timeout:
            break
        
    return stable
    
    

def value_is_stable(
        times: Union[ndarray, list], 
        values: Union[ndarray, list], 
        rate_thresh: float, 
        filter_values: bool = True, 
        filter_func: Optional[Callable[[ndarray]]] = None,
        relative: bool = False):
    times = np.array(times)
    values = np.array(values)
    
    if np.ndim(values) > 1:
        # Vector of values
        # Ensure that all entries are stable
        return all([value_is_stable(v) for v in values.T])
    
    if relative:
        # Analyze changes relative to median value
        values = values / np.median(values)

    if filter_values:
        # Filter measured values to reduce impact of noise
        if filter_func is None:
            filter_func = lambda x: ndi.gaussian_filter1d(x, 1, mode='nearest')
        values = filter_func(values)

    # Get rate of change per minute
    fit = np.polyfit(times / 60, values, deg=1)
    rate = fit[0]
    # print('slope: {:.6f} units/min'.format(slope))

    # If rate is below threshold, property has equilibrated
    if abs(rate) <= rate_thresh:
        return True
    else:
        return False
    
