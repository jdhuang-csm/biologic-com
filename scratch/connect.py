import clr
import os
import numpy as np
from pathlib import Path


# Absolute path to dll
assembly_path = Path('C:\\Users\\jhuang2\\python\\biologic-com\\biocom\\dll\\Interop.EClabCOM.dll')

# Add the assembly reference
clr.AddReference(assembly_path.__str__())

# Now import EClabCOM
import EClabCOM

# Create an instance of EClabExe -> This will not wait till the program is opened
# So, either you open EC-Lab before executing the script or you add a sleep for 10s
# after this statement
eclabexe_instance = EClabCOM.EClabExe()

# Connect to device 1
device_id = 0
eclabexe_instance.ConnectDevice(device_id)
 
# Get the info about connected channels
channels = eclabexe_instance.GetDeviceChannelList(0)

channels
 
# Convert to an array that can be accessed via python
# The System.Int32[] is stored in channels[1] in channels[0] is a 1 stored.
npChannels = np.fromiter(channels[1], int)
 
# print Channels
print(npChannels)
 
# Get status of device 1 and Channel 0
status = eclabexe_instance.MeasureStatus(device_id, 0)
 
# Convert to array that can be accessed via python
# The System.Double[] is stored in status [1] in status [0] is a 1 stored.
# When the function failed, I saw that in status[0] is a 0.
npStatus = np.fromiter(status[1], float)
 
# print Status
print(npStatus)

# Get device type
dev_type = eclabexe_instance.GetDeviceType(device_id)
 
print(dev_type)

# Get software version
ci = eclabexe_instance.GetChannelInfos(device_id, 0)

dir(eclabexe_instance)


 
# Disconnect Device 1
eclabexe_instance.DisconnectDevice(device_id)