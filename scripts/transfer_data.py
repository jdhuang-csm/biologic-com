from pathlib import Path
import os
from shutil import copy2
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Union

from biocom.mpr import read_mpr
from biocom.processing.chrono import downsample_data, ControlMode
from biocom.processing.sampling import remove_short_samples
from biocom.processing import loop

# datadir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang")
datadir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang")
exchange_dir = Path(r"J:\Messungen\IAACTEMP\AKZeier\AKZMESS-002\jdh")
# exchange_dir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\TEST")

logdirname = "temperature_logs"
logdest = exchange_dir.joinpath(logdirname)


if not os.path.exists(logdest):
    os.makedirs(logdest)


def is_hychrono_file(file, exclude_patterns=[]):
    if file.name.split("_")[0][:6] == "Hybrid":
        if any([file.name.find(p) > -1 for p in exclude_patterns]):
            return False
        tag = file.name.split("_")[-2]
        return tag in ("CP", "CA")
    else:
        return False
    
def tiv_from_mpr(data):
    v_field = "<Ewe>/V" if "<Ewe>/V" in data.dtype.fields.keys() else "Ewe/V"
    i_field = "<I>/A" if "<I>/A" in data.dtype.fields.keys() else "I/A"
    return data["time/s"], data[i_field], data[v_field]

def split_cycles(mpr_file, dt_thresh=10.0):
    if os.path.exists(loop.path_to_loop_file(mpr_file)):
        data = loop.split_cycles(mpr_file, unscale=True)
        return data
    else:
        mpr = read_mpr(mpr_file, unscale=True)
        if "cycle number" in mpr.data.dtype.fields.keys():
            cycles = np.unique(mpr.data["cycle number"])
            data = [mpr.data[mpr.data["cycle number"] == n] for n in cycles]
            return data
        elif "half cycle" in mpr.data.dtype.fields.keys():
            # can't use half cycle directly due to odd stepping behavior, use time instead
            dt = np.diff(mpr.data["time/s"])
            dt = np.insert(dt, 0, 0)
            split_index = np.where(dt > dt_thresh)[0]
            return np.split(mpr.data, split_index)
        else:
            # Single cycle
            return [mpr.data]
        

def export_chrono(file, dest, max_size=500):
    destfile = dest.joinpath(file.name.replace(".mpr", ".csv"))
    try:
        # mpr = read_mpr(file, unscale=True)
        # print(mpr.data.dtype.fields.keys())
        cycle_data = split_cycles(file)        
        
        if len(cycle_data) > 1:
            print(f"Found {len(cycle_data)} cycles in file {file}")
            def get_dest_file(n):
                return dest.joinpath(file.name.replace(".mpr", f"_Cycle{n}.csv"))
        else:
             def get_dest_file(n):
                return dest.joinpath(file.name.replace(".mpr", ".csv"))   
        
        for n, data in enumerate(cycle_data):
            tiv = tiv_from_mpr(data)
            if len(tiv[0]) > max_size:
                tiv_ds, _ = downsample_data(*tiv, ControlMode.GALV, target_size=300, init_samples=25, remove_outliers=False)
            else:
                tiv_ds = tiv
            df = pd.DataFrame(np.array(tiv_ds).T, columns=["time/s", "I/A", "Ewe/V"])
            destfile = get_dest_file(n)
            df.to_csv(destfile, index_label="index")
        return True
        
    except Exception as err:
        print(f"Error processing file {file.name}: {err}")
        raise err
        return False
    
expdirnames = [
    # r"240820_CCDecomp_SymIonBlock\PCGW04_50mg_300C-1h",
    # r"240820_CCDecomp_SymIonBlock\PCGW04_75mg_300C-1h",
    # r"240820_CCDecomp_SymIonBlock\PCGW05_50mg_300C-24h",
    # r"240820_CCDecomp_SymIonBlock\PCGW05_75mg_300C-24h",
    # r"240821_CCDecomp_SymEonBlock\PCGW04_75mg_300C-1h",
    # r"240821_CCDecomp_SymEonBlock\PCGW05_75mg_300C-24h",
    # r"240821_NCM_SymEonBlock",
    # r"240821_SE-NCM-SE",
    # r"240824_CC_SymEonBlock\PC04_25mg",
    # r"240824_CC_SymEonBlock\PC06_50mg",
    # r"240824_CC_SymEonBlock\PC07_75mg",
    # r"240702_NCM_SymIonBlock_50mg\T_dep\240820",
    # r"240703_NCM_SymIonBlock_100mg\T_dep\240820",
    # r"240905_CCMixTest_SymIonBlock",
    # "240906_CCRatioTest_SymIonBlock",
    # "240909_CCMixTest_SymEonBlock",
    # "240909_CCRatioTest_SymEonBlock",
    # "240909_LPSCl_SymIonBlock",
    # "240912_LPSCl_SymEonBlock",
    # "240917_LPSCl_SymEonBlock",
    # "240918_LPSCl_SymEonBlock_FlatInLi",
    # "240918_LPSCl_SymIonBlock",
    "240918_NCM-LPSCl_8020_Half",
    # "240919_CC_SymZType",
    # "240924_3E_SymEonBlock",
    # "241007_CC_SymIonBlock",
    # "241007_LPSCl_SymIonBlock",
    # "241007_NCM_SymIonBlock",
    # "241009_CC80_SymIonBlock"
    # "dummy_DC3",
    # "0810 10mg0.5SiN078 Test",
    # "1110 10mg0.5SiN078 Test",
    
]


after_time = datetime(2024, 10, 24, 0)
# after_time = None
exclude_patterns_from_hy = [] #["_01_CP_"]

def should_copy(file: Path):
    if after_time is None:
        return True
    
    mtime = os.path.getmtime(file)
    return datetime.fromtimestamp(mtime) >= after_time
    
    


def transfer_tree(dir_tuple):
    # Recursive
    print(f"Processing directory {dir_tuple}...")
    source = datadir.joinpath(*dir_tuple)
    dest = exchange_dir.joinpath(*dir_tuple)

    if not os.path.exists(dest):
        os.makedirs(dest)
            
    # Copy notes file if present
    if os.path.exists(source.joinpath("notes.txt")):
        print("Found notes file:", source.joinpath("notes.txt"))
        copy2(source.joinpath("notes.txt"), dest.joinpath("notes.txt"))
    
    # Copy temp log locations
    ll_files = list(source.glob("temp_log_location*.txt"))
    for ll_file in ll_files:
        copy2(ll_file, dest.joinpath(ll_file.name))

        # Copy the temperature log files
        with open(ll_file, "r") as f:
            log_locs = f.read()
        log_locs = log_locs.split("\n")
        for logf in log_locs:
            logf = Path(logf)
            try:
                copy2(logf, logdest.joinpath(logf.name))
            except FileNotFoundError:
                print(f"No temperature log file named {logf.name}")

    # Copy/export the data files
    mpr_files = list(source.glob("*.mpr"))
    # mpr_files = [f for f in mpr_files if f.name.find("TSeq6") < 0]
    # channel_str = mpr_files[0].name.split("_")[-1]
    num_files = len(mpr_files)
    n_chrono = 0
    n_other = 0
    n_err = 0
    n_old = 0
    for i, file in enumerate(mpr_files):
        if should_copy(file):
            if is_hychrono_file(file, exclude_patterns_from_hy):
                stat = export_chrono(file, dest)
                if stat: 
                    n_chrono += 1
                else:
                    n_err += 1
            else:
                copy2(file, dest.joinpath(file.name))
                
                # Check for a loop file and copy if it exists
                loop_file = loop.path_to_loop_file(file)
                if os.path.exists(loop_file):
                    copy2(loop_file, dest.joinpath(loop_file.name))
                    
                n_other += 1
        else:
            n_old += 1
            
        # Print progress at intervals
        if (i + 1) % 20 == 0:
            print(f"{i + 1}/{num_files}")
            
    print(f"Exported {n_chrono} chrono files and transferred {n_other} other mpr files with {n_err} errors. Ignored {n_old} old files")
    
    subdirs = next(os.walk(datadir.joinpath(*dir_tuple)))[1]
    for subdir in subdirs:
        transfer_tree(dir_tuple + (subdir, ))
    
    
for expdirname in expdirnames:
    print(f"Transferring {expdirname}...")
    transfer_tree((expdirname,))
    
# for expdirname in expdirnames:
#     print(f"Transferring {expdirname}...")
    
#     subdirs = next(os.walk(datadir.joinpath(expdirname)))[1]
    
#     for subdir in [""] + subdirs:
#         if subdir == "":
#             print(f"Processing top level...")
#         else:
#             print(f"Processing subdir {subdir}...")
#         source = datadir.joinpath(expdirname, subdir)
#         dest = exchange_dir.joinpath(expdirname, subdir)

#         if not os.path.exists(dest):
#             os.makedirs(dest)
                
#         # Copy notes file if present
#         if os.path.exists(source.joinpath("notes.txt")):
#             print("Found notes file:", source.joinpath("notes.txt"))
#             copy2(source.joinpath("notes.txt"), dest.joinpath("notes.txt"))
        
#         # Copy temp log locations
#         ll_files = list(source.glob("temp_log_location*.txt"))
#         for ll_file in ll_files:
#             copy2(ll_file, dest.joinpath(ll_file.name))

#             # Copy the temperature log files
#             with open(ll_file, "r") as f:
#                 log_locs = f.read()
#             log_locs = log_locs.split("\n")
#             for logf in log_locs:
#                 logf = Path(logf)
#                 try:
#                     copy2(logf, logdest.joinpath(logf.name))
#                 except FileNotFoundError:
#                     print(f"No temperature log file named {logf.name}")

#         # Copy/export the data files
#         mpr_files = list(source.glob("*.mpr"))
#         # mpr_files = [f for f in mpr_files if f.name.find("TSeq6") < 0]
#         # channel_str = mpr_files[0].name.split("_")[-1]
#         num_files = len(mpr_files)
#         n_chrono = 0
#         n_other = 0
#         n_err = 0
#         for i, file in enumerate(mpr_files):
#             if is_hychrono_file(file):
#                 stat = export_chrono(file, dest)
#                 if stat: 
#                     n_chrono += 1
#                 else:
#                     n_err += 1
#             else:
#                 copy2(file, dest.joinpath(file.name))
#                 n_other += 1
                
#             # Print progress at intervals
#             if (i + 1) % 20 == 0:
#                 print(f"{i + 1}/{num_files}")
                
#         print(f"Exported {n_chrono} chrono files and transferred {n_other} other mpr files with {n_err} errors.")
        

