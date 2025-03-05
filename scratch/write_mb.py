import numpy as np

from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.techniques.mb import (
    MBSequence, MBConstantCurrent, MBGEIS, MBLoop, MBUrbanProfile, MBLimit, MBLimitAction, MBLimitType, MBLimitComparison, 
    MBRecordCriterion, MBRecordType, EISAmpUnit
)
from biocom.mps.common import EweVs, IRange, IVs, Bandwidth, BLDeviceModel, SampleType, get_i_range
from biocom.mps.write_utils import set_decimal_separator
import biocom.mps.config as cfg
from biocom.mps.write import write_techniques

from pathlib import Path

set_decimal_separator(comma=False)

# write_dir = Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM_SymIonBlock_100mg\olecom_test')
write_dir = Path('.')

profile = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\dummy_DC3\lapsin\sin_1.0e+00Hz_Neg.txt")
import pandas as pd
profile = pd.read_csv(profile, sep="\t")

# mb = MBUrbanProfileList(
#     [profile],
#     auto_rest=1
# )

v_limit = MBLimit(MBLimitType.EWE, MBLimitComparison.GT, 3.7, MBLimitAction.STOP)

i_dc = 1e-6

cc = MBConstantCurrent(
    i_dc, 
    limits=[
        MBLimit(MBLimitType.TIME, MBLimitComparison.GT, 10.0, MBLimitAction.NEXT),
        v_limit
    ],
    record_criteria=[
        MBRecordCriterion(MBRecordType.TIME, 1.0)
    ]
)

up = MBUrbanProfile(
    profile,
    limits=[v_limit],
    record_criteria=[MBRecordCriterion(MBRecordType.TIME, 1e-3)]
)

geis = MBGEIS(
    2e6, 100.0, 0.01 * np.sqrt(2), 
    EISAmpUnit.V,
    ppd=10,
    limits=[v_limit]
)

loop = MBLoop(0, 7)


mbseq = MBSequence([cc, up, geis, loop], i_range=get_i_range(i_dc))




seq = TechniqueSequence([mbseq])

config = cfg.set_defaults(
    BLDeviceModel.SP300,
    seq,
    SampleType.CORROSION
)

# print('\nSequence:\n--------------')
# print(seq.sequence_text())

# seq.write_params(write_dir.joinpath('PEIS_GEIS.mps'))


mps_file = write_dir.joinpath('MBSeq.mps')

# config.safety.no_start_on_overload = False
print(config.basic)
config.cell.comments = "here is my comment\nLine 2"

write_techniques(seq, config, mps_file)
