import numpy as np
from pathlib import Path

from ..mpr import read_mpr

def read_loop_file(file: Path):
    with open(file, "r") as f:
        txt = f.read()
        
    split_index = [int(t) for t in txt.split("\n")[1:-1]]
    return split_index
    
    
def path_to_loop_file(mpr_file: Path):
    return mpr_file.parent.joinpath(mpr_file.name.replace(".mpr", "_LOOP.txt"))
    
def split_cycles(mpr_file: Path, unscale=True):
    mpr = read_mpr(mpr_file, unscale=unscale)
    loop_file = path_to_loop_file(mpr_file)
    split_index = read_loop_file(loop_file)
    # First and last indices are unnecesary (0 and len(mpr.data))
    return np.split(mpr.data, split_index[1:-1])