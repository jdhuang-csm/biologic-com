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

import matplotlib.pyplot as plt

# datadir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang")
datadir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JZ")
exchange_dir = Path(r"J:\Messungen\IAACTEMP\AKZeier\AKZMESS-002\jdh\JZ")


file = datadir.joinpath("1110 10mg0.5SiN078 Test", "run1_Discharge", "Hybrid_TSeq1_25C_#0_02_CP_C01.mpr")

mpr = read_mpr(file)

mpr.data.dtype.fields

time = mpr.data["time/s"]
dt = np.diff(time)

dt = np.insert(dt, 0, 0)
index = np.where(dt > 10)[0]

splits = np.split(mpr.data, index)

split = splits[1]
fig, ax = plt.subplots()
ax.plot(split["time/s"], split["I/mA"], marker=".")
plt.show()


mask = mpr.data["time/s"] < 900
fig, ax = plt.subplots()
ax.hist(dt)
ax.set_ylim(0, 100)

ax.plot(mpr.data["time/s"][mask], mpr.data["half cycle"][mask])
# ax.set_xlim(0, 600)
plt.show()