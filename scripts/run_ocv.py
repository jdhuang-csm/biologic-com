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

from pathlib import Path

set_decimal_separator(comma=True)

write_dir = Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM_SymIonBlock_100mg\olecom_test')
# write_dir = Path('.')
fname = 'OCV_olecom'
mps_file = write_dir.joinpath(f'{fname}.mps')

ch00 = DeviceChannel(0, 0, BLDeviceModel.SP300)

ole = OLECOM()

ole.launch_server()
time.sleep(2)

cfg.set_versions('11.52', '11.52', '11.52')

run_ocv(ole, ch00, mps_file, 10, 0.1)

while not ole.channel_is_done(ch00):
    time.sleep(1.0)

mpr_file = ole.get_data_filename(ch00, 0)
ocv = read_ocv(mpr_file)
print('OCV: {:.4f} V'.format(ocv))

# ole.check_measure_status(ch00)

# len(ole.server.MeasureStatus(0, 0))

# import os
# os.path.exists(ole.get_data_filename(0, 0, 0))