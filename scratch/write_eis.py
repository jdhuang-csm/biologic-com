from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.techniques.eis import PEISParameters, GEISParameters, PointDensity
from biocom.mps.common import (
    EweVs, IRange, IVs, Bandwidth, BLDeviceModel,
    SampleType
    
)

from biocom.mps.write_utils import set_decimal_separator
from biocom.mps.write import write_techniques
from biocom.mps import config as cfg


from pathlib import Path

set_decimal_separator(comma=False)

# write_dir = Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM_SymIonBlock_100mg\olecom_test')
write_dir = Path('.')


peis = PEISParameters(
    dc_value=0.0, 
    ac_amp=0.01, 
    dc_vs=EweVs.EOC, 
    f_max=1e5, 
    f_min=1, 
    points=10, 
    point_density=PointDensity.PPD,
    i_range=IRange.AUTO,
    bandwidth=Bandwidth.BW7,
    v_range_max=10.
    )

# geis = GEISParameters(
#     dc_value=0.0, 
#     ac_amp=0.001, 
#     dc_vs=IVs.NONE, 
#     f_max=1e5, 
#     f_min=1, 
#     points=10, 
#     point_density=PointDensity.PPD,
#     i_range=IRange.m10
#     )


print('fi:', peis.fi_scaled, peis.fi_unit)
print('ff:', peis.ff_scaled, peis.ff_unit)

# print(params.param_map)

# print(peis._param_map)

print('\nPEIS:\n--------------')
print(peis.param_text(1))

# print('\nGEIS:\n--------------')
# print(geis.param_text())


seq = TechniqueSequence([peis])

config = cfg.set_defaults(
    BLDeviceModel.SP150,
    seq,
    SampleType.CORROSION
)

print('\nSequence:\n--------------')
print(seq.sequence_text())

# seq.write_params(write_dir.joinpath('PEIS_GEIS.mps'))


mps_file = write_dir.joinpath('PEIS.mps')

# config.safety.no_start_on_overload = False
print(config.basic)
config.cell.comments = "here is my comment\nLine 2"

write_techniques(seq, config, mps_file)