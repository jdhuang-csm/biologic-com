
import matplotlib.pyplot as plt
import time
import numpy as np
from biocom.com.server import OLECOM, DeviceChannel
from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.techniques.chrono import CAParameters, CPParameters
from biocom.mps.techniques.ocv import OCVParameters
from biocom.mps.techniques.eis import PEISParameters, GEISParameters
from biocom.mps.common import EweVs, IRange, IVs, Bandwidth, BLDeviceModel, SampleType
from biocom.mps.write_utils import set_decimal_separator
import biocom.mps.config as cfg
from biocom.mps.write import write_techniques

from biocom.meastools.ocv import run_ocv, read_ocv
from biocom.meastools.galv import (
    run_iac_chrono_test, read_iac_chrono, process_iac_chrono_test,
    run_iac_z_test, process_iac_z_test
)
from biocom.processing.chrono import process_ivt_simple, ControlMode
from biocom.mpr import read_mpr

from pathlib import Path


import os 
import sys
import socket

# Config 
t_long = 5
v_ac = 0.01
n_iter_per_ramp = 200
iac_test_interval = 3

T_init = 15 
temp_sequence = [45, 25]

#set IP address and port of binder
HOST, PORT = "192.109.209.12", 9000

def set_temp(T_set):
    # Convert to K
    T_K = float(T_set) + 273.17
    msg = f"CANIDWriteValue:114000C0:{T_K}\r\n"
    # Create a socket (SOCK_STREAM means a TCP socket)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(bytes(msg, "utf-8"))
        # Receive data from the server and shut down
        received = str(sock.recv(1024), "utf-8")
        print("Received:", received)
    
    
set_decimal_separator(comma=True)


# write_dir = Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM_SymIonBlock_100mg\olecom_test')
write_dir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_LPSCl_SymIonBlock_50mg\T_dep\Ramp_15-45-25")
# write_dir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\dummy_DC3")

# Setup biologic connection
device = BLDeviceModel.SP300
channel = DeviceChannel(1, 0, device)

ole = OLECOM(validate_return_codes=True)

ole.launch_server()
time.sleep(1)

cfg.set_versions('11.52')



# Functions
def wait_for_channel(dc, min_wait):
    start = time.monotonic()
    done = False
    while not done:
        time.sleep(0.5)
        elapsed = time.monotonic() - start
        channel_running = ole.channel_is_running(dc)
        done = not channel_running and elapsed > min_wait
        print('Channel running after {:.1f} s: {}'.format(elapsed, channel_running))
        
    print('Finished in {:.1f} s'.format(time.monotonic() - start))
    
    
def test_iac(dc, it, label):
    # Run current test
    # ca_mps_file = write_dir.joinpath(f'CA_IacTest_#{it}.mps')
    ca_mps_file = write_dir.joinpath(f'PEIS_IacTest_{label}_#{it}.mps')
    
    time.sleep(0.5)
    # ca_mpr_file = run_iac_chrono_test(ole, dc, ca_mps_file, v_dc=0, v_ac=v_ac, 
    #                        step_duration=t_long, dt=1e-2, v_vs=EweVs.EOC,
    #                        bandwidth=Bandwidth.BW9)
    
    ca_mpr_file = run_iac_z_test(ole, dc, ca_mps_file, v_dc=0, v_ac=v_ac, 
                           f=1 / t_long, v_vs=EweVs.EOC,
                           bandwidth=Bandwidth.BW9)
    
    # Wait for test to finish
    wait_for_channel(dc, min_wait=t_long)
    
    # Extract dc and ac currents
    # iv = process_iac_chrono_test(ca_mpr_file, use_drt=True)
    iv = process_iac_z_test(ca_mpr_file)
    v_oc = iv.eval_v(0)
    # Use 1/2 the desired voltage since the test frequency is 1/t instead of 1/2*pi*t
    _, i_ac = iv.eval_iac(v_oc, v_ac * 0.5)
    # Hard-code i_dc to zero since we want open circuit
    i_dc = 0
    
    # TEMP: hard-code i_ac
    # TODO: improve i_ac estimation
    # i_ac_0 = 27e-9
    # i_ac_1 = 7e-9
    # i_ac = i_ac_0 + (i_ac_1 - i_ac_0) * it / n_iter
    # i_ac = 7e-9
    print('i_dc: {:.2e}'.format(i_dc))
    print('i_ac: {:.2e}'.format(i_ac))
    
    return i_dc, i_ac


def run_hybrid(dc, it, i_dc, i_ac, label):
    hy_mps_file = write_dir.joinpath(f'HybridGalv_Triple_{label}_#{it}.mps')

    currents = [i_dc, i_dc + i_ac, i_dc - i_ac, i_dc]
    durations = [t_long, t_long, t_long, t_long]

    cp = CPParameters(
        currents,
        durations,
        1e-3,
        IVs.NONE,
        v_limits=None,
        dq_limits=None,
        v_range_min=-1.,
        v_range_max=1.,
        record_average=False,
        bandwidth=Bandwidth.BW9
    )

    eis = PEISParameters(
        0.0, 
        0.01,
        EweVs.EOC,
        5e6,
        1e2,
        10,
        v_range_min=-1.,
        v_range_max=1.,
        i_range=IRange.AUTO,
        bandwidth=Bandwidth.BW9
    )

    seq = TechniqueSequence([cp, eis])

    config = cfg.set_defaults(device, seq, SampleType.CORROSION)
    cfg.set_misc_options(turn_to_ocv=True, current_settings=config)

    # Wait for a moment to give the channel time to finish
    time.sleep(0.5)
    ole.load_techniques(dc, seq, config, hy_mps_file)

    ole.run_channel(dc, hy_mps_file)

    wait_for_channel(dc, min_wait=3 * t_long)
    
    
for i, T_set in enumerate(temp_sequence):
    print(f"Sending setpoint {T_set} C to Binder")
    set_temp(T_set)
    
    label = f"{T_init}-{T_set}"
    for it in range(n_iter_per_ramp):
        print(f"Iteration {it}")
        # Test Iac only at intervals
        if it % iac_test_interval == 0:
            print("Testing current...")
            i_dc, i_ac = test_iac(channel, it, label)
            
        print("Running hybrid measurement...") 
        run_hybrid(channel, it, i_dc, i_ac, label)
        
    T_init = T_set
        
        