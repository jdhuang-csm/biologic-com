import time
from biocom.com.server import OLECOM, DeviceChannel
from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.techniques.chrono import CPParameters
from biocom.mps.techniques.eis import PEISParameters
from biocom.mps.techniques.ocv import OCVParameters
from biocom.mps.common import EweVs, IRange, IVs, Bandwidth, BLDeviceModel, SampleType
from biocom.mps.write_utils import set_decimal_separator
import biocom.mps.config as cfg
from biocom.mps.write import write_techniques

from pathlib import Path

set_decimal_separator(comma=True)

# write_dir = Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM_SymIonBlock_100mg\olecom_test')
write_dir = Path('.')

fname = 'OCV-PEIS_olecom'
mps_file = write_dir.joinpath(f'{fname}.mps')
out_file = write_dir.joinpath(fname)

v_range_min = -0.1
v_range_max = 0.1

device = BLDeviceModel.SP300


ocv = OCVParameters(
    10.0,
    0.5,
    0.0,
    v_range_min=v_range_min,
    v_range_max=v_range_max
)

peis = PEISParameters(
    0.0,
    0.01,
    EweVs.EOC,
    1e5,
    1e-1,
    bandwidth=Bandwidth.BW8,
    i_range=IRange.AUTO,
    average=3,
    v_range_min=v_range_min,
    v_range_max=v_range_max,
)

seq = TechniqueSequence([ocv, peis])
config = cfg.set_defaults(device, seq, SampleType.CORROSION)

ch00 = DeviceChannel(0, 0, name='test')


ole = OLECOM()

ole.launch_server()
# time.sleep(5)

cfg.set_versions('11.52', '11.52', '11.52')

ole.load_techniques(ch00, seq, config, mps_file)


start = time.monotonic()
ole.run_channel(ch00, mps_file)

print_stats = ['Status', 'Technique number', 'Time', 'Connection', 'Current point index', "Total point index"]
while time.monotonic() <= start + 600:
    stat = ole.check_measure_status(ch00)
    print("Status at {:.3f} s:".format(time.monotonic() - start), {k: v for k, v in stat.items() if k in print_stats})
    # is_running = ole.channel_is_running(device_id, channel)
    # is_stopped = ole.channel_is_running(device_id, channel)
    # print("Run status at {:.1f} s: {}".format(time.monotonic() - start, is_running))
    # print("Stop status at {:.1f} s: {}".format(time.monotonic() - start, is_stopped))
    done = ole.channel_is_done(ch00)
    print("DONE:", done)
    if done and time.monotonic() - start > 10.0:
        break
    
    time.sleep(1.0)

ole.get_data_filename(ch00, 0)

# stat = ole.check_measure_status(ch00)
type(stat["Status"])
