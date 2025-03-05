from pathlib import Path
import os
from shutil import copy2
import pandas as pd
import numpy as np

from biocom.mpr import read_mpr
from biocom.processing.chrono import downsample_data, ControlMode
from biocom.processing.sampling import remove_short_samples

datadir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\Martin L")
exchange_dir = Path(r"J:\Messungen\IAACTEMP\AKZeier\AKZMESS-002\MK")

logdirname = "temperature_logs"
logdest = exchange_dir.joinpath(logdirname)


if not os.path.exists(logdest):
    os.makedirs(logdest)


def is_chrono_file(file):
    tag = file.name.split("_")[-2]
    return tag == "CP"
    
def tiv_from_mpr(mpr):
    return mpr.data["time/s"], mpr.data["I/A"], mpr.data["Ewe/V"]

def export_chrono(file):
    destfile = dest.joinpath(file.name.replace(".mpr", ".csv"))
    try:
        mpr = read_mpr(file, unscale=True)
        tiv = tiv_from_mpr(mpr)
        tiv_ds, _ = downsample_data(*tiv, ControlMode.GALV, target_size=250, init_samples=25, remove_outliers=False)
        df = pd.DataFrame(np.array(tiv_ds).T, columns=["time/s", "I/A", "Ewe/V"])
        df.to_csv(destfile, index_label="index")
        return True
    except Exception as err:
        print(f"Error processing file {file.name}: {err}")
        raise err
        return False
    
expdirnames = [
    "MLCR4_V3ClRich_1013mg",
    "MLSoLiStemp_V63+2%CNF_978mg",
    "MLJMF1_V13+2%CNF_1018mg",
    "MLSoLiS2_Vmix50%CB_976mg"
]
for expdirname in expdirnames:
    print(f"Transferring {expdirname}...")
    source = datadir.joinpath(expdirname)
    dest = exchange_dir.joinpath(expdirname)

    if not os.path.exists(dest):
        os.makedirs(dest)

    # Copy temp log location
    ll_files = list(source.glob("temp_log_location*.txt"))
    for ll_file in ll_files:
        copy2(ll_file, dest.joinpath(ll_file.name))

        # Copy the temperature log files
        with open(ll_file, "r") as f:
            log_locs = f.read()
        log_locs = log_locs.split("\n")
        for logf in log_locs:
            logf = Path(logf)
            copy2(logf, logdest.joinpath(logf.name))

    # Copy/export the data files
    eis_files = list(source.glob("OCV-PEIS_*.mpr"))
    charge_file = next(source.glob("Charge2_CP_*.mpr"))
    mpr_files = eis_files + [charge_file]
    
    num_files = len(mpr_files)
    n_chrono = 0
    n_other = 0
    n_err = 0
    for i, file in enumerate(mpr_files):
        # if is_chrono_file(file):
        #     stat = export_chrono(file)
        #     if stat: 
        #         n_chrono += 1
        #     else:
        #         n_err += 1
        # else:
        copy2(file, dest.joinpath(file.name))
        n_other += 1
            
        # Print progress at intervals
        if (i + 1) % 20 == 0:
            print(f"{i + 1}/{num_files}")
            
    print(f"Exported {n_chrono} chrono files and transferred {n_other} other mpr files with {n_err} errors.")
        

