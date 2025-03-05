import matplotlib.pyplot as plt
import time
from biocom.com.server import OLECOM, DeviceChannel
from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.techniques.chrono import CAParameters
from biocom.mps.techniques.ocv import OCVParameters
from biocom.mps.common import EweVs, IRange, IVs, Bandwidth, BLDeviceModel, SampleType
from biocom.mps.write_utils import set_decimal_separator
import biocom.mps.config as cfg
from biocom.mps.write import write_techniques

from biocom.meastools.ocv import run_ocv, read_ocv
from biocom.meastools.galv import run_iac_chrono_test, read_iac_chrono
from biocom.mpr import read_mpr
from biocom.processing.chrono import process_ivt_simple, ControlMode


from pathlib import Path

set_decimal_separator(comma=True)


write_dir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_LPSCl_SymIonBlock_50mg\T_dep")
# # write_dir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\dummy_DC3")
# # write_dir = Path('.')

# ocv_fname = 'OCV_IampTest_olecom'
# ocv_mps_file = write_dir.joinpath(f'{ocv_fname}.mps')

# ca_fname = 'CA_IampTest_olecom'
# ca_mps_file = write_dir.joinpath(f'{ca_fname}.mps')

# ch00 = DeviceChannel(0, 0, BLDeviceModel.SP300)

# ole = OLECOM()

# ole.launch_server()
# time.sleep(1)

# cfg.set_versions('11.52')

# # Run OCV
# t0 = time.monotonic()
# ocv_mpr_file = run_ocv(ole, ch00, ocv_mps_file, duration=5)
# while not ole.channel_is_done(ch00):
#     time.sleep(0.1)
# t1 = time.monotonic()
# print('OCV runtime: {:.2f} s'.format(t1 - t0))

# v_oc = read_ocv(ocv_mpr_file)
# print('OCV: {:.3f} V'.format(v_oc))
# # v_oc = 0

# # Run current test
# t2 = time.monotonic()
# ca_mpr_file = run_iac_chrono_test(ole, ch00, ca_mps_file, v_dc=v_oc, v_ac=0.01, step_duration=3, dt=1e-2)
# while not ole.channel_is_done(ch00):
#     time.sleep(0.1)
# t3 = time.monotonic()
# print('CA runtime: {:.2f} s'.format(t3 - t2))

# print("total time: {:.2f} s".format(t3 - t0))

# iv, i_dc, i_ac = read_iac_chrono(ca_mpr_file, v_oc, 0.01)
# print('i_dc: {:.2e}'.format(i_dc))
# print('i_ac: {:.2e}'.format(i_ac))


# ca_mpr = read_mpr(ca_mpr_file, unscale=True)
# fig, axes = plt.subplots(1, 2, figsize=(8, 3))
# axes[0].plot(ca_mpr.data['time/s'], ca_mpr.data['I/A'])
# axes[1].plot(ca_mpr.data['time/s'], ca_mpr.data['Ewe/V'])
# fig.tight_layout()
# plt.show()


mpr_file = write_dir.joinpath(f"PEIS_IacTest_25-30_#0_C02.mpr")
mpr = read_mpr(mpr_file)
# iv = process_ivt_simple(ca_mpr.data['time/s'], ca_mpr.data['I/A'], ca_mpr.data['Ewe/V'], ControlMode.POT)
# iv.dvdi
# iv.eval_iac(0, 0.01)
# read_iac(ca_mpr_file, 0.0004, 0.01)
mpr.data["-Im(Z)/Ohm"] + mpr.data["Re(Z)/Ohm"], mpr.data['|Z|/Ohm']