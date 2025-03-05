import time
from biocom.com.server import OLECOM
from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.techniques.chrono import CPParameters
from biocom.mps.techniques.ocv import OCVParameters
from biocom.mps.common import EweVs, IRange, IVs, Bandwidth, BLDeviceModel, SampleType
from biocom.mps.write_utils import set_decimal_separator
import biocom.mps.config as cfg
from biocom.mps.write import write_techniques

from pathlib import Path

set_decimal_separator(comma=True)

write_dir = Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM_SymIonBlock_100mg\olecom_test')
# write_dir = Path('.')
fname = 'OCV-CP_olecom'
mps_file = write_dir.joinpath(f'{fname}.mps')
out_file = write_dir.joinpath(fname)

ocv = OCVParameters(
    10.0,
    0.1,
    0.0,
    v_range_min=-0.05,
    v_range_max=0.05
)

cp = CPParameters(
    [0, -1e-3, 1e-3],
    [1, 5, 5],
    1e-3,
    IVs.NONE,
    v_limits=None,
    dq_limits=None,
    v_range_min=-1.,
    v_range_max=1.,
    record_average=False
)

seq = TechniqueSequence([ocv, cp])

device = BLDeviceModel.SP300

config = cfg.set_defaults(device, seq, SampleType.CORROSION)

device_id = 0
channel = 0

ole = OLECOM()

ole.launch_server()
time.sleep(5)

cfg.set_versions('11.52', '11.52', '11.52')

ole.load_techniques(device_id, channel, seq, config, mps_file)


start = time.monotonic()
ole.run_channel(device_id, channel, mps_file)

print_stats = ['Status', 'Technique number', 'Time', 'Connection', 'Result code']
while time.monotonic() <= start + 30:
    stat = ole.check_measure_status(device_id, channel)
    print("Status at {:.3f} s:".format(time.monotonic() - start), {k: v for k, v in stat.items() if k in print_stats})
    # is_running = ole.channel_is_running(device_id, channel)
    # is_stopped = ole.channel_is_running(device_id, channel)
    # print("Run status at {:.1f} s: {}".format(time.monotonic() - start, is_running))
    # print("Stop status at {:.1f} s: {}".format(time.monotonic() - start, is_stopped))
    
    if stat['Status'] == 0 and time.monotonic() - start > 1.0:
        break
    
    time.sleep(1.0)

ole.get_data_filename(device_id, channel, 0)
ole.server.GetDataFilename(device_id, channel, 1)[0]
ole.get_channel_info(device_id, channel)
ole.toggle_popups(True)