from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.techniques.gcpl import GCPLParameters, CurrentSpec
from biocom.mps.common import EweVs, IRange, IVs, Bandwidth, BLDeviceModel, SampleType
from biocom.mps.write_utils import set_decimal_separator
import biocom.mps.config as cfg
from biocom.mps.write import write_techniques

from pathlib import Path

set_decimal_separator(comma=False)

# write_dir = Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM_SymIonBlock_100mg\olecom_test')
write_dir = Path('.')

gcpl = GCPLParameters(
    CurrentSpec.CDN,
    [10, 10],
    
)



seq = TechniqueSequence([gcpl])

config = cfg.set_defaults(
    BLDeviceModel.SP300,
    seq,
    SampleType.CORROSION
)

print('\nSequence:\n--------------')
print(seq.sequence_text())

# seq.write_params(write_dir.joinpath('PEIS_GEIS.mps'))


mps_file = write_dir.joinpath('GCPL.mps')

# config.safety.no_start_on_overload = False
# print(config.basic)
config.cell.comments = "here is my comment\nLine 2"

write_techniques(seq, config, mps_file)
