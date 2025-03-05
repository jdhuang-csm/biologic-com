
import matplotlib.pyplot as plt
import time
import numpy as np
import asyncio
import pandas as pd
import os
from typing import List

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
    load_iac_z_test, process_iac_z_test
)
from biocom.processing.chrono import process_ivt_simple, ControlMode, downsample_data
from biocom.mpr import read_mpr

from pathlib import Path
from datetime import datetime

from collections import deque

from binder.kt53 import BinderKT53


"""
Requirements

1. Async run all channels with temperature logging
2. Log temperature at start and end of each iteration
3. Determine when temp is stable, then hold for x minutes
4. Write temperature log to file periodically (in case of crash)
"""
# Config 
t_long = 5.
v_ac = 0.01
max_iter_per_ramp = 100
iac_test_interval = 5

T_init = 25
temp_sequence = [35, 45, 55, 45, 35, 25, 15, 25]
temp_log_interval = 2.0
temp_hold_time = 1800.0

# EC-LAB server
ole = OLECOM(validate_return_codes=True, retries=1)


#set IP address of binder
HOST = "192.109.209.12"

    
set_decimal_separator(comma=True)

# Temperature log files
temp_log_dir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\temperature_logs")
ts = datetime.strftime(datetime.now(), "%y%m%d_%H.%M")
temp_log_file = temp_log_dir.joinpath(f"{ts}_TempLog.csv")
iter_log_file = temp_log_dir.joinpath(f"{ts}_IterLog.csv")
                    

# Setup biologic connection
device = BLDeviceModel.SP300

channels = [
    DeviceChannel(0, 0, device, "SP10_Ch1",
        data_path=Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM_SymIonBlock_100mg\T_dep\Ramp_25-55-15-25_10Csteps')
    ),
    DeviceChannel(0, 1, device, "SP10_Ch2",
        data_path=Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240702_NCM_SymIonBlock_50mg\T_dep\Ramp_25-55-15-25_10Csteps')
    ),
    DeviceChannel(1, 0, device, "SP11_Ch1",
        data_path=Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_NCM-SE-NCM_SymIonBlock\T_dep\Ramp_25-55-15-25_10Csteps')
    ),
    DeviceChannel(1, 1, device, "SP11_Ch2",
        data_path=Path(r'C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\240703_LPSCl_SymIonBlock_50mg\T_dep\Ramp_25-55-15-25_10Csteps')          
    ),
]

for channel in channels:
    if not os.path.exists(channel.data_path.parent):
        raise ValueError(f"Data path parent does not exist for {channel.name}: {channel.data_path}")
    if not os.path.exists(channel.data_path):
        os.makedirs(channel.data_path)

# Functions
async def wait_for_channel(dc: DeviceChannel, min_wait, channel_status: dict):
    start = time.monotonic()
    done = False
    while not done:
        await asyncio.sleep(0.5)
        elapsed = time.monotonic() - start
        done = ole.channel_is_done(dc) and elapsed > min_wait
        # print('Channel {} running after {:.1f} s: {}'.format(dc.name, elapsed, channel_running))
        
    channel_status[dc.key] = True
    print('Channel {} finished in {:.1f} s'.format(dc.name, time.monotonic() - start))
    return elapsed
    
    
# async def test_iac(dc: DeviceChannel, it, label, channel_status: dict):
#     # Run current test
#     # ca_mps_file = write_dir.joinpath(f'CA_IacTest_#{it}.mps')
#     print(f"IAC test for {dc.name}")
#     ca_mps_file = dc.data_path.joinpath(f'PEIS_IacTest_{label}_#{it}.mps')
    
#     # Wait for a moment to make sure the channel is ready
#     await asyncio.sleep(0.5)
#     # ca_mpr_file = run_iac_chrono_test(ole, dc, ca_mps_file, v_dc=0, v_ac=v_ac, 
#     #                        step_duration=t_long, dt=1e-2, v_vs=EweVs.EOC,
#     #                        bandwidth=Bandwidth.BW9)
    
#     print(f"{dc.name} blocking")
#     # time.sleep(2.0)
#     print(f"Run IAC test for {dc.name}")
#     ca_mpr_file = run_iac_z_test(ole, dc, ca_mps_file, v_dc=0, v_ac=v_ac, 
#                            f=1 / t_long, v_vs=EweVs.EOC,
#                            bandwidth=Bandwidth.BW9)
#     # time.sleep(2.0)
#     print(f"{dc.name} done blocking")
    
#     # Wait for test to finish
#     await wait_for_channel(dc, min_wait=t_long)
    
#     # Extract dc and ac currents
#     # iv = process_iac_chrono_test(ca_mpr_file, use_drt=True)
#     iv = process_iac_z_test(ca_mpr_file)
#     v_oc = iv.eval_v(0)
#     # Use 1/2 the desired voltage since the test frequency is 1/t instead of 1/2*pi*t
#     _, i_ac = iv.eval_iac(v_oc, v_ac * 0.5)
#     # Hard-code i_dc to zero since we want open circuit
#     i_dc = 0
    
#     # Store the current with the channel object
#     dc.i_dc = i_dc
#     dc.i_ac = i_ac
#     print('{} i_dc: {:.2e}'.format(dc.name, i_dc))
#     print('{} i_ac: {:.2e}'.format(dc.name, i_ac))
    
#     channel_status[dc.key] = True
    
#     return i_dc, i_ac



# async def run_hybrid(dc: DeviceChannel, i_dc, i_ac, it, label, channel_status: dict):
#     hy_mps_file = dc.data_path.joinpath(f'HybridGalv_{label}_#{it}.mps')

#     currents = [i_dc, i_dc + i_ac, i_dc - i_ac, i_dc]
#     durations = [t_long, t_long, t_long, t_long]

#     cp = CPParameters(
#         currents,
#         durations,
#         1e-3,
#         IVs.NONE,
#         v_limits=None,
#         dq_limits=None,
#         v_range_min=-1.,
#         v_range_max=1.,
#         record_average=False,
#         bandwidth=Bandwidth.BW9
#     )

#     eis = PEISParameters(
#         0.0, 
#         0.01,
#         EweVs.EOC,
#         5e6,
#         1e2,
#         10,
#         v_range_min=-1.,
#         v_range_max=1.,
#         i_range=IRange.AUTO,
#         bandwidth=Bandwidth.BW9
#     )

#     seq = TechniqueSequence([cp, eis])

#     config = cfg.set_defaults(device, seq, SampleType.CORROSION)
#     cfg.set_misc_options(turn_to_ocv=True, current_settings=config)

#     # Wait for a moment to give the channel time to finish
#     await asyncio.sleep(0.5)
#     ole.load_techniques(dc, seq, config, hy_mps_file)

#     ole.run_channel(dc, hy_mps_file)

#     await wait_for_channel(dc, min_wait=3 * t_long)
    
#     channel_status[dc.key] = True
    
    
    
    
def log_temperature(oven: BinderKT53, log: deque, t_init):
    # Log the temperature once
    elapsed = time.monotonic() - t_init
    pv = oven.get_temp_pv()
    log.append([elapsed, pv])
    return pv
    

def check_status(channels, channel_status: dict):
    # Check if all channels are done
    return all([channel_status.get(c.key) for c in channels])

def temp_is_stable(log: deque, sp: float, window: int = 10):    
    if len(log) < window:
        # Not enough points collected yet
        return False
    tt = np.array(log)[-window:]
    temps = tt[:, 1]
    slope = np.polyfit(tt[:, 0], tt[:, 1], deg=1)[0] * 60 # deg / minute
    abs_diffs = np.abs(temps - sp)
    print("sp:", sp)
    # print("temp log:", tt)
    print("slope:", slope)
    print("mean abs diff:", np.mean(abs_diffs))
    print("max abs diff:", np.max(abs_diffs))
    
    return all([
        np.mean(abs_diffs) <= 0.2,
        np.max(abs_diffs) <= 0.5,
        abs(slope) <= 0.5, 
    ])
    

async def run_temperature_log(oven: BinderKT53, log: deque, t_init, channels, channel_status, interval: float = 2.0):
    # Keep running until all channels are finished
    while not check_status(channels, channel_status):
        log_temperature(oven, log, t_init)
        await asyncio.sleep(interval)
        
        

async def test_iac_all(channels: List[DeviceChannel], it, label, oven: BinderKT53, log: deque, t_init, interval: float = 2.0
                       ):
    # Wait for a moment to make sure all channels are ready
    await asyncio.sleep(0.5)
    
    # Load settings for all channels
    mps_files = {}
    for channel in channels:
        print(f"Configuring IAC test for {channel.name}")
        mps_file = channel.data_path.joinpath(f'PEIS_IacTest_{label}_#{it}.mps')
        mps_files[channel.key] = mps_file
        
        # ca_mpr_file = run_iac_chrono_test(ole, dc, ca_mps_file, v_dc=0, v_ac=v_ac, 
        #                        step_duration=t_long, dt=1e-2, v_vs=EweVs.EOC,
        #                        bandwidth=Bandwidth.BW9)
        
        # print(f"{channel.name} blocking")
        # time.sleep(2.0)
        print(f"Load IAC test for {channel.name}")
        load_iac_z_test(ole, channel, mps_file, v_dc=0, v_ac=v_ac, 
                            f=1 / t_long, v_vs=EweVs.EOC,
                            bandwidth=Bandwidth.BW9)
        # time.sleep(2.0)
        # print(f"{channel.name} done blocking")
        
    # Launch all channels
    mpr_files = {}
    for channel in channels:
        print(f"Launching IAC test for {channel.name}")
        ole.run_channel(channel, mps_files[channel.key])
        mpr_files[channel.key] = ole.get_data_filename(channel, 0)
        
    # Wait for all tests to finish
    channel_status = {}
    await asyncio.gather(
        *[wait_for_channel(c, t_long, channel_status) for c in channels],
        run_temperature_log(oven, log, t_init, channels, channel_status, interval)  
    )
        
    # Extract dc and ac currents
    for channel in channels:
        # iv = process_iac_chrono_test(ca_mpr_file, use_drt=True)
        iv = process_iac_z_test(mpr_files[channel.key])
        v_oc = iv.eval_v(0)
        # Use 1/2 the desired voltage since the test frequency is 1/t instead of 1/2*pi*t
        _, i_ac = iv.eval_iac(v_oc, v_ac * 0.5)
        # Hard-code i_dc to zero since we want open circuit
        i_dc = 0
        
        # Store the current settings with the channel object
        channel.i_dc = i_dc
        channel.i_ac = i_ac
        print('{} i_dc: {:.2e}'.format(channel.name, i_dc))
        print('{} i_ac: {:.2e}'.format(channel.name, i_ac))
    
    
        

async def run_hybrid_all(channels: List[DeviceChannel], it, label, refresh_settings, oven: BinderKT53, log: deque, t_init, interval: float = 2.0):
    
    # Wait for a moment to ensure the channel is ready
    await asyncio.sleep(0.5)
    
    # Load settings for all channels
    mps_files = {}
    for channel in channels:
        print(f"Configuring Hybrid measurement for {channel.name}")

        mps_file = channel.data_path.joinpath(f'HybridGalv_{label}_#{it}.mps')
        mps_files[channel.name] = mps_file

        if refresh_settings:
            # Only re-load settings if something has changed
            i_dc = channel.i_dc
            i_ac = channel.i_ac        
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
            
            ole.load_techniques(channel, seq, config, mps_file)
    
    # Launch all channels
    for channel in channels:
        print(f"Launching Hybrid measurement for {channel.name}")
        ole.run_channel(channel, mps_files[channel.name])

    # Wait for all channels to finish
    channel_status = {}
    await asyncio.gather(
        *[wait_for_channel(c, 4 * t_long, channel_status) for c in channels],
        run_temperature_log(oven, log, t_init, channels, channel_status, interval)  
    )
    
    # # Downsample data
    # Best to do this as a downstream step to avoid runtime errors.
    # There is no benefit to doing this in real time since we aren't deleting the original mpr files.
    # for channel in channels:
    #     cp_file = ole.get_data_filename(channel, 0)
    #     mpr = read_mpr(cp_file, unscale=True)
    #     ds_data, _ = downsample_data(
    #         mpr.data["time/s"], mpr.data["I/A"], mpr.data["Ewe/V"],
    #         ControlMode.GALV, target_size=250, init_samples=25
    #     )
        

async def run_peis_all(channels: List[DeviceChannel], it, label, oven: BinderKT53, log: deque, t_init, interval: float = 2.0):
    
    # Wait for a moment to ensure the channel is ready
    await asyncio.sleep(0.5)
    
    # Load settings for all channels
    mps_files = {}
    for channel in channels:
        print(f"Configuring PEIS measurement for {channel.name}")

        mps_file = channel.data_path.joinpath(f'PEIS_{label}_#{it}.mps')
        mps_files[channel.name] = mps_file

        eis = PEISParameters(
            0.0, 
            0.01,
            EweVs.EOC,
            5e6,
            1 / (2 * np.pi * t_long),
            10,
            condition_time=5.0,
            v_range_min=-1.,
            v_range_max=1.,
            i_range=IRange.AUTO,
            bandwidth=Bandwidth.BW9
        )

        seq = TechniqueSequence([eis])

        config = cfg.set_defaults(device, seq, SampleType.CORROSION)
        cfg.set_misc_options(turn_to_ocv=True, current_settings=config)
        
        ole.load_techniques(channel, seq, config, mps_file)
    
    # Launch all channels
    for channel in channels:
        print(f"Launching PEIS measurement for {channel.name}")
        ole.run_channel(channel, mps_files[channel.name])

    # Wait for all channels to finish
    channel_status = {}
    await asyncio.gather(
        *[wait_for_channel(c, 4 * t_long, channel_status) for c in channels],
        run_temperature_log(oven, log, t_init, channels, channel_status, interval)  
    )
    
    # # Downsample data
    # Best to do this as a downstream step to avoid runtime errors.
    # There is no benefit to doing this in real time since we aren't deleting the original mpr files.
    # for channel in channels:
    #     cp_file = ole.get_data_filename(channel, 0)
    #     mpr = read_mpr(cp_file, unscale=True)
    #     ds_data, _ = downsample_data(
    #         mpr.data["time/s"], mpr.data["I/A"], mpr.data["Ewe/V"],
    #         ControlMode.GALV, target_size=250, init_samples=25
    #     )

    
    
if __name__ == "__main__":
    oven = BinderKT53(HOST)
    
    ole.launch_server()
    time.sleep(1.)

    cfg.set_versions('11.52')
    start_time = time.monotonic()

    # Temperature log by time    
    temp_log = deque()
    
    # Fixed temp logging args
    temp_args = (oven, temp_log, start_time, temp_log_interval)
    
    # Iteration temperatures
    iter_temps = deque()
    
    # Set fan to high to increase convection while ramping
    oven.set_fan_speed(75.0)
    
    try:
        for i, T_set in enumerate(temp_sequence):
            print(f"Sending setpoint {T_set} C to Binder")
            sp = oven.set_temp_sp(T_set)
            print(f"Set setpoint to {sp} C")
            
            sp_reached = False
            sp_stable_time = None
            
            label = f"{T_init}-{T_set}"
            for it in range(max_iter_per_ramp):
                print(f"Iteration {it}")
                
                iter_start = time.monotonic()
                # Test Iac only at intervals
                if it % iac_test_interval == 0:
                    print("Testing current...")
                    i_config = asyncio.run(test_iac_all(channels, it, label, *temp_args))
                    refresh = True
                else:
                    # Nothing changed - don't need to reload settings files
                    refresh = False
                    
                print("Running hybrid measurement...") 
                # Get the temperature at the beginning of the measurement
                pv_start = log_temperature(*temp_args[:-1])
                asyncio.run(run_hybrid_all(channels, it, label, refresh, *temp_args))
                
                # Get the temperature at the end of the measurement
                iter_end = time.monotonic()
                pv_end = log_temperature(*temp_args[:-1])
                
                # Record the start and end times/temps
                iter_temps.append([label, it, (iter_start - start_time) / 60.0, (iter_end - start_time) / 60.0,  pv_start, pv_end])
                
                # Check if temperature is stable
                # Set window to 1 minute
                sp_status = temp_is_stable(temp_log, T_set, window=int(60. / temp_log_interval))
                print("SP status:", sp_status)
                
                # Set the sp_stable_time only the first time that the temperature flag is set!
                if sp_status and not sp_reached:
                    sp_stable_time = time.monotonic()
                    print("Temperature stable at setpoint")
                    print("Holding temperature for {:.0f} minutes...".format(temp_hold_time / 60.0))
                    sp_reached = True
                    
                if sp_reached:
                    if time.monotonic() - sp_stable_time >= temp_hold_time:
                        break
                
            # Once the sample has equilibrated, take a conventional PEIS measurement
            # Treat the PEIS measurement as if it is one final iteration
            it += 1
            iter_start = time.monotonic()

            print("Running PEIS measurement...") 
            # Get the temperature at the beginning of the measurement
            pv_start = log_temperature(*temp_args[:-1])
            asyncio.run(run_peis_all(channels, it, label, *temp_args))
            
            # Get the temperature at the end of the measurement
            iter_end = time.monotonic()
            pv_end = log_temperature(*temp_args[:-1])
            
            # Record the start and end times/temps
            iter_temps.append([label, it, (iter_start - start_time) / 60.0, (iter_end - start_time) / 60.0,  pv_start, pv_end])
            
            T_init = T_set
    finally:
        # Return fan to idle  
        oven.set_temp_sp(25.0)      
        fan_sp = oven.set_fan_speed(25.0)
        print("fan_sp:", fan_sp)
        
        # Store location of log files in each data directory
        for channel in channels:
            with open(channel.data_path.joinpath("temp_log_location.txt"), "w") as f:
                f.write(f"{temp_log_file.__str__()}\n{iter_log_file.__str__()}")
        
        # Write logs to file
        if len(iter_temps) > 0:
            # at least 1 iteration complete
            iter_temp_df = pd.DataFrame(np.array(iter_temps), 
                                        columns=["label", "iteration", "start_time/min", "end_time/min", "start_T/C", "end_T/C"]
                                        )
            iter_temp_df.to_csv(iter_log_file, index_label="index", float_format="%.3f")
        
        temp_df = pd.DataFrame(np.array(temp_log), columns=["time/s", "T/C"])
        temp_df.to_csv(temp_log_file, index_label="index", float_format="%.1f")