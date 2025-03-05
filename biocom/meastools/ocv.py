import numpy as np
import asyncio
from pathlib import Path
from typing import Union

from ..com.server import OLECOM, DeviceChannel
from ..mps.techniques.sequence import TechniqueSequence
from ..mps.techniques.ocv import OCVParameters
from ..mps.common import EweVs, IRange, IVs, Bandwidth, BLDeviceModel, SampleType
from ..mps import config as cfg
from ..mpr import read_mpr




def run_ocv(
        server: OLECOM, 
        device_channel: DeviceChannel,
        mps_file: Path,
        duration: float = 5, 
        dt: float = 0.1, 
        **kwargs):

    ocv = OCVParameters(
        duration,
        dt,
        **kwargs
    )
    
    seq = TechniqueSequence([ocv])
    config = cfg.set_defaults(device_channel.model, seq, 
                              SampleType.CORROSION)
    
    server.load_techniques(device_channel, seq, config, mps_file)

    server.run_channel(device_channel, mps_file)

    # print_stats = ['Status', 'Technique number', 'Time', 'Connection', 'Result code']
    # while time.monotonic() <= start + 30:
    #     stat = ole.check_measure_status(device_id, channel)
    #     print("Status at {:.3f} s:".format(time.monotonic() - start), {k: v for k, v in stat.items() if k in print_stats})
    #     # is_running = ole.channel_is_running(device_id, channel)
    #     # is_stopped = ole.channel_is_running(device_id, channel)
    #     # print("Run status at {:.1f} s: {}".format(time.monotonic() - start, is_running))
    #     # print("Stop status at {:.1f} s: {}".format(time.monotonic() - start, is_stopped))
        
    #     if stat['Status'] == 0 and time.monotonic() - start > 1.0:
    #         break
        
    #     time.sleep(1.0)

    return server.get_data_filename(device_channel, 0)


def read_ocv(mpr_file: Path, n_points: Union[int, None] = 10, agg='mean') -> float:
    """Read OCV from file and estimate the OCV by aggregating the 
    last n_points points.

    :param Path mpr_file: Path to mpr file.
    :param int n_points: Number of points to aggregate, starting from 
        the end of the file and moving back. If None, use all points in 
        the file. Defaults to 10.
    :param str agg: Aggregation function to use. Any numpy function
        is allowed (e.g. 'mean', 'median', 'max'). 
        Defaults to 'mean'.
    :return float: Aggregated OCV.
    """
    mpr = read_mpr(Path(mpr_file), unscale=True)
    if n_points is None:
        n_points = len(mpr.data)
    return getattr(np, agg)(mpr.data['Ewe/V'][-n_points:])
