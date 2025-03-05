import comtypes
from comtypes.client import CreateObject
import time
import os
import numpy as np
from pathlib import Path


# create OLE-COM instance. EC-Lab will start after that.
# You can either include a time.sleep() to give EC-Lab time (EC-Lab does not give any feedback when it
# has finished loading) or you can open EC-Lab before you execute the script.
prog_id = "EClabCOM.EClabExe"
ole_com = CreateObject(prog_id)
time.sleep(5)




datadir = Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM_SymIonBlock_100mg')
datadir = datadir.joinpath('olecom_test')
mps_file = datadir.joinpath('CP.mps')
write_file = datadir.joinpath(mps_file.name)

# Connect to the first device listed in EC-Lab.
# connection_result=1 if the device is connected, 0 else
device_id = 0
connection_result = ole_com.ConnectDevice(device_id)
print(connection_result)

ip = "192.109.209.10"
connection_result = ole_com.ConnectDeviceByIP(ip)
print(connection_result)

# Get the Measurement Status of Device 0 and Channel 0.
status = ole_com.MeasureStatus(device_id, 0)
print(status)

# Convert to array that can be accessed via python
# The System.Double[] is stored in status [1] in status [0] is a 1 stored.
# When the function failed, I saw that in status[0] is a 0.
npStatus = np.fromiter(status[1], float)
 
# print Status
print(npStatus)

 
# Get the info about connected channels
channels = ole_com.GetDeviceChannelList(device_id)

channels
type(channels)
 
# Convert to an array that can be accessed via python
# The System.Int32[] is stored in channels[1] in channels[0] is a 1 stored.
npChannels = np.fromiter(channels[1], int)
 
# print Channels
print(npChannels)
 
 


# Get device type
dev_type = ole_com.GetDeviceType(device_id)
 
print(dev_type)

# Get software version
ci = ole_com.GetChannelInfos(device_id, 0)

print(ci)
dir(ole_com)


# Load settings and run techniques
ole_com.LoadSettings(device_id, 0, mps_file.absolute().__str__())

ole_com.RunChannel(device_id, 0, write_file.absolute().__str__())

 
# Disconnect Device 1
ole_com.DisconnectDevice(device_id)

ole_com.GetDeviceType(1)