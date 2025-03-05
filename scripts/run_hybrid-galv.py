
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


# Run current test
ca_fname = 'CA_IacTest_olecom'
ca_mps_file = write_dir.joinpath(f'{ca_fname}.mps')

hybrid_fname = 'HybridGalv_Triple_BW9'
hy_mps_file = write_dir.joinpath(f'{hybrid_fname}.mps')


t0 = time.monotonic()
ca_mpr_file = run_iac_chrono_test(ole, ch00, ca_mps_file, v_dc=0, v_ac=0.01, 
                           step_duration=3, dt=1e-2, v_vs=EweVs.EOC)
# Wait to ensure the channel starts
print_status = ["Status", 'Technique number', "Connection"]
for n in range(100):
    res = ole.check_measure_status(ch00)
    print(n, ", ".join([f"{k}: {v}" for k, v in res.items() if k in print_status]), ole.channel_is_done(ch00))
    time.sleep(0.1)
t1 = time.monotonic()
print('CA runtime: {:.2f} s'.format(t1 - t0))

# Extract OCV
ca_mpr = read_mpr(ca_mpr_file, unscale=True)
liniv = process_ivt_simple(ca_mpr.data['time/s'], ca_mpr.data['I/A'], ca_mpr.data['Ewe/V'], ControlMode.POT)
v_oc = liniv.eval_v(0)
print('v_oc: {:.3f} V'.format(v_oc))

# Extract dc and ac currents
iv, i_dc, i_ac = read_iac_chrono(ca_mpr_file, v_oc, 0.01)
print('i_dc: {:.2e}'.format(i_dc))
print('i_ac: {:.2e}'.format(i_ac))

# Overwrite i_dc to 0 since we want open circuit

go = input("Continue?")

if go.upper() == "Y":

    # Configure hybrid sequence
    t_long = 5

    currents = [i_dc, i_dc + i_ac, i_dc - i_ac, i_dc]
    durations = [1, t_long, t_long, t_long]


    cp = CPParameters(
        currents,
        durations,
        1e-3,
        IVs.NONE,
        v_limits=None,
        dq_limits=None,
        v_range_min=-1.,
        v_range_max=1.,
        record_average=False,
        bandwidth=Bandwidth.BW9
    )

    eis = PEISParameters(
        0.0, 
        0.01,
        EweVs.EOC,
        5e6,
        1e2,
        10,
        v_range_min=-1.,
        v_range_max=1.,
        i_range=IRange.AUTO,
        bandwidth=Bandwidth.BW9
    )

    seq = TechniqueSequence([cp, eis])

    config = cfg.set_defaults(device, seq, SampleType.CORROSION)


    ole.load_techniques(ch00, seq, config, hy_mps_file)


    start = time.monotonic()
    ole.run_channel(ch00, hy_mps_file)

    print_stats = ['Status', 'Technique number', 'Time', 'Connection', 'Result code']

    # Wait to ensure the channel starts
    # time.sleep(1.0)
    # while not ole.channel_is_done(ch00):
    #     print("Channel running at {:.1f} s".format(time.monotonic() - start))
    #     time.sleep(1.0)
    for n in range(100):
        res = ole.check_measure_status(ch00)
        print(n, ", ".join([f"{k}: {v}" for k, v in res.items() if k in print_status]), ole.channel_is_done(ch00))
        time.sleep(0.1)
        
        
    print("Channel stopped after {:.1f} s".format(time.monotonic() - start))