# This script will:
# 1. Create an mps settings file for OCV followed by PEIS
# 2. Load the mps file to the specified channel
# 3. Start the measurement
# 4. Monitor the measurement and report when it is complete
from pathlib import Path

from biocom.mps.techniques.eis import PEISParameters
from biocom.mps.techniques.ocv import OCVParameters
from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.common import EweVs, Bandwidth, BLDeviceModel, SampleType
from biocom.com.server import DeviceChannel, OLECOM
from biocom.mps.config import set_versions, set_defaults

# Directory in which to write files
datadir = Path("./")


if __name__ == "__main__":
    
    # Set the software and firmware version to match your instance of EC-Lab
    set_versions("11.61")
    
    # Make TechniqueParameters instances to configure the measurements
    
    ocv_params = OCVParameters(
        10.0, # Duratin (s)
        1.0, # Sample period (s)
    )
    
    peis_params = PEISParameters(
        0.0, # DC voltage (V)
        0.01, # AC amplitude (V),
        dc_vs=EweVs.EOC, # DC voltage relative to EOC (open circuit),
        f_max=1e6, # Maximum frequency (Hz)
        f_min=1, # Minimum frequency (Hz)
        points=10, # points per decade,
        average=2, # Number of cycles per frequency to average,
        v_range_max=10,
        v_range_min=-10,
        bandwidth=Bandwidth.BW7
    )
    
    # Combine the techniques in a sequence
    sequence = TechniqueSequence([ocv_params, peis_params])
    
    # Filename in which to write mps file
    mps_file = datadir.joinpath("OCV-PEIS.mps")
    
    # # Write the settings to an mps file (optional, mostly for testing - the mps file will be created below by server.load_techniques)
    # sequence.write_params(mps_file)

    # Create a server instance to communicate with EC-Lab
    server = OLECOM()

    # Create a DeviceChannel object to indicate which deivce/channel to commmunicate with
    channel = DeviceChannel(
        0, # Device ID
        0, # Channel ID
        BLDeviceModel.SP150, # Model
        name="SP150_Channel1" # User-defined name for convenience
    )
    
    
    # Connect to EC-Lab. An EC-Lab instance needs to be running already before you run this script!
    server.launch_server()
    
    # Create a configuration for running the measurement
    # This contains the parameters that you would find in the "Safety/Adv. Settings" and "Cell Characteristics"
    # sections of EC-Lab
    config = set_defaults(channel.model, sequence, SampleType.CORROSION)
    
    
    # Create the mps file and load it to the channel
    server.load_techniques(channel, sequence, config, mps_file)
    
    # Launch the measurement
    # mpr file pattern in which to save data
    mpr_file = mps_file.parent.joinpath(mps_file.name.replace(".mps", ".mpr"))
    server.run_channel(channel, mpr_file)
    
    result = server.wait_for_channel(
        channel, 
        min_wait=10.0, # Minimum wait time (s) to avoid weird statuses near measurement start
        # Timeout (s) - after this time, the function will return a TIMEOUT status 
        # if the measurement has not yet finished
        timeout=3600,
        interval=5.0 # Interval (s): check the channel status every 5 seconds
        )
    
    print(f"Channel finished with result {result.name}")
    
    