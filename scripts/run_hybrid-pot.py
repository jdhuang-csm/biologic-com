
import matplotlib.pyplot as plt
import time
from biocom.com.server import OLECOM, DeviceChannel
from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.techniques.chrono import CAParameters, CPParameters
from biocom.mps.techniques.ocv import OCVParameters
from biocom.mps.techniques.eis import PEISParameters, GEISParameters
from biocom.mps.common import EweVs, IRange, IVs, Bandwidth, BLDeviceModel, SampleType
from biocom.mps.write_utils import set_decimal_separator
import biocom.mps.config as cfg
from biocom.mps.write import write_techniques

from biocom.meastools.ocv import run_ocv, read_ocv
from biocom.meastools.galv import run_iac_chrono_test, read_iac_chrono
from biocom.processing.chrono import process_ivt_simple, ControlMode
from biocom.mpr import read_mpr

from pathlib import Path

set_decimal_separator(comma=True)


# write_dir = Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM_SymIonBlock_100mg\olecom_test')
write_dir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_LPSCl_SymIonBlock_50mg\olecom")
# write_dir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\dummy_DC3")


device = BLDeviceModel.SP300
ch00 = DeviceChannel(0, 0, device)

ole = OLECOM()

ole.launch_server()
time.sleep(1)

cfg.set_versions('11.52')



hybrid_fname = 'HybridPot_Triple'
hy_mps_file = write_dir.joinpath(f'{hybrid_fname}.mps')


t0 = time.monotonic()

v_dc = 0
v_ac = 0.01

# Configure hybrid sequence
t_long = 2

voltages = [v_dc, v_dc + v_ac, v_dc - v_ac, v_dc]
durations = [1, t_long, t_long, t_long]


ca = CAParameters(
    voltages,
    durations,
    1e-3,
    v_vs=EweVs.EOC,
    v_range_min=-1.,
    v_range_max=1.
)

eis = PEISParameters(
    0.0, 
    0.01,
    EweVs.EOC,
    1e6,
    1e2,
    10,
    i_range=IRange.AUTO,
    v_range_min=-1.,
    v_range_max=1.
)

seq = TechniqueSequence([ca, eis])

config = cfg.set_defaults(device, seq, SampleType.CORROSION)


ole.load_techniques(ch00, seq, config, hy_mps_file)


start = time.monotonic()
ole.run_channel(ch00, hy_mps_file)


while not ole.channel_is_done(ch00):
    time.sleep(1.0)
    
    print("Channel running at {:.1f} s".format(time.monotonic() - start))
    
print("Channel stopped after {:.1f} s".format(time.monotonic() - start))