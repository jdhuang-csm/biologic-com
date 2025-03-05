
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
t_long = 5
v_ac = 0.01
max_iter_per_temp = 200
iac_test_interval = 5

temp_sequence = [45, 35, 25, 15, 5, 25]
temp_log_interval = 5.0
temp_hold_time = 3600.0
temp_timeout = 3600.0

v_range_min = 0.0
v_range_max = 5.0

# Manually configured files
discharge_mps_file = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\discharge1.mps")
charge_mps_file = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\charge2.mps")

if not os.path.exists(discharge_mps_file):
    raise ValueError("can't find discharge file")

if not os.path.exists(charge_mps_file):
    raise ValueError("can't find charge file")

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

userdir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\Martin L")


channels = [
    DeviceChannel(0, 0, device, "SP10_Ch1",
        data_path=userdir.joinpath(r"MLSoLiStemp_V63+2%CNF_978mg")
    ),
    DeviceChannel(0, 1, device, "SP10_Ch2",
        data_path=userdir.joinpath(r"MLCR4_V3ClRich_1013mg")
    ),
    DeviceChannel(1, 0, device, "SP11_Ch1",
        data_path=userdir.joinpath(r'MLJMF1_V13+2%CNF_1018mg')
    ),
    DeviceChannel(1, 1, device, "SP11_Ch2",
        data_path=userdir.joinpath(r'MLSoLiS2_Vmix50%CB_976mg')
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
    print("sp:", sp, "pv:", temps[-1])
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
    
    # Wait to ensure that data files are written
    asyncio.sleep(0.2)
        
    # Extract dc and ac currents
    for channel in channels:
        # iv = process_iac_chrono_test(ca_mpr_file, use_drt=True)
        try:
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
        except Exception as err:
            # Could not read or process mpr file
            # Reuse the previous settings
            print(f"Could not process Iac test for {channel.name}. Reusing last current config")
            print("Reason for failure:", err)
    
    
async def run_mps_all(channels: List[DeviceChannel], mps_files: dict, label, oven: BinderKT53, log: deque, t_init, interval: float = 2.0):
    # Wait for a moment to ensure the channel is ready
    await asyncio.sleep(0.5)
    
    # Load settings for all channels
    for channel in channels:
        mps_file = mps_files[channel.key]
        print(f"Loading file {mps_file} for {channel.name}")

        ole.load_settings(channel, mps_file)
    
    # Launch all channels
    for channel in channels:
        output_file = channel.data_path.joinpath(f"{label}_CP.mpr")
        print(f"Launching mps measurement for {channel.name}")
        ole.run_channel(channel, output_file)

    # Wait for all channels to finish
    channel_status = {}
    await asyncio.gather(
        *[wait_for_channel(c, 30, channel_status) for c in channels],
        run_temperature_log(oven, log, t_init, channels, channel_status, interval)  
    )
    

async def run_hybrid_all(channels: List[DeviceChannel], it, label, refresh_settings, oven: BinderKT53, log: deque, t_init, interval: float = 2.0):
    
    # Wait for a moment to ensure the channel is ready
    await asyncio.sleep(0.5)
    
    # Load settings for all channels
    mps_files = {}
    for channel in channels:
        print(f"Configuring Hybrid measurement for {channel.name}")

        mps_file = channel.data_path.joinpath(f'Hybrid_{label}_#{it}.mps')
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
                v_range_min=v_range_min,
                v_range_max=v_range_max,
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
                v_range_min=v_range_min,
                v_range_max=v_range_max,
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
        

async def run_peis_all(channels: List[DeviceChannel], ocv_duration, it, label, oven: BinderKT53, log: deque, t_init, interval: float = 2.0):
    
    # Wait for a moment to ensure the channel is ready
    await asyncio.sleep(0.5)
    
    # Load settings for all channels
    mps_files = {}
    for channel in channels:
        print(f"Configuring PEIS measurement for {channel.name}")

        mps_file = channel.data_path.joinpath(f'OCV-PEIS_{label}_#{it}.mps')
        mps_files[channel.name] = mps_file

        ocv = OCVParameters(
            ocv_duration,
            1.0,
            v_range_min=v_range_min,
            v_range_max=v_range_max
        )
        
        eis = PEISParameters(
            0.0, 
            0.01,
            EweVs.EOC,
            5e6,
            0.1,
            10,
            condition_time=5.0,
            v_range_min=v_range_min,
            v_range_max=v_range_max,
            i_range=IRange.AUTO,
            bandwidth=Bandwidth.BW9
        )

        seq = TechniqueSequence([ocv, eis])

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

def run_temp_sweep(stage, temp_sequence, iter_temps, oven: BinderKT53, log: deque, t_init, interval: float = 2.0):
    for i, T_set in enumerate(temp_sequence):
        print(f"Sending setpoint {T_set} C to Binder")
        sp = oven.set_temp_sp(T_set)
        print(f"Set setpoint to {sp} C")
        
        sp_reached = False
        sp_stable_time = None
        
        temp_start_time = time.monotonic()
        
        # First wait to reach SP
        while not sp_reached:
            # Check if temperature is stable
            # Set window to 1 minute
            log_temperature(oven, log, t_init)
            sp_reached = temp_is_stable(log, T_set, window=int(60. / interval))
            print("SP status:", sp_reached)
            
            # Record the time at which sp was reached
            if sp_reached:
                sp_stable_time = time.monotonic()
                sp_reached = True
                
            elapsed = time.monotonic() - temp_start_time
            if elapsed >= temp_timeout:
                # Timeout and record time
                print("SP {} not reached after {} minutes; starting measurements".format(T_set, elapsed / 60.0))
                sp_stable_time = time.monotonic()
                break
                
            time.sleep(temp_log_interval)
            
        
        print("Temperature stable at setpoint")
        print("Holding temperature for {:.0f} minutes...".format(temp_hold_time / 60.0))
        
        label = f"{stage}_TSeq{i + 1}_{T_set}C"
        for it in range(max_iter_per_temp):
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
            iter_temps.append([label, it, (iter_start - t_init) / 60.0, (iter_end - t_init) / 60.0,  pv_start, pv_end])
            
            
            # Break after holding for specified time 
            if time.monotonic() - sp_stable_time >= temp_hold_time:
                break
            
        # Once the sample has equilibrated, take a conventional PEIS measurement
        # Treat the PEIS measurement as if it is one final iteration
        it += 1
        iter_start = time.monotonic()

        print("Running PEIS measurement...") 
        # Get the temperature at the beginning of the measurement
        pv_start = log_temperature(*temp_args[:-1])
        asyncio.run(run_peis_all(channels, 30.0, it, label, *temp_args))
        
        # Get the temperature at the end of the measurement
        iter_end = time.monotonic()
        pv_end = log_temperature(*temp_args[:-1])
        
        # Record the start and end times/temps
        iter_temps.append([label, it, (iter_start - t_init) / 60.0, (iter_end - t_init) / 60.0,  pv_start, pv_end])
    
    
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
        # Test code only for running from mps file
        # test_file = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\Martin L\MLCR4_V3ClRich_1013mg\OCV-PEIS_init.mps")
        # asyncio.run(run_mps_all(channels, {c.key: test_file for c in channels}, "TEST", *temp_args))
        
        # First, run OCV and PEIS
        # asyncio.run(run_peis_all(channels, 30.0, 0, "0Initial_TSeq0_25C", *temp_args))
        
        # Then run temp sweep 
        # run_temp_sweep("0Initial", temp_sequence, iter_temps, *temp_args)
        
        # 1. discharge
        # discharge_mps_files = {c.key: discharge_mps_file for c in channels}
        # asyncio.run(run_mps_all(channels, discharge_mps_files, "Discharge1", *temp_args))
        
        # Post-discharge measurements
        # First OCV for 10 minutes then EIS, all at room temp
        # asyncio.run(run_peis_all(channels, 600.00, 0, "1Post-Discharge_Tseq0_25C", *temp_args))
        # Then temp sweep
        temp_seq_retry = [15, 5, 25]
        run_temp_sweep("1.1Post-Discharge", temp_seq_retry, iter_temps, *temp_args)
        
        # 2. charge
        charge_mps_files = {c.key: charge_mps_file for c in channels}
        asyncio.run(run_mps_all(channels, charge_mps_files, "Charge2", *temp_args))
        
        # Post-charge measurements
        # First OCV for 10 minutes then EIS, all at room temp
        asyncio.run(run_peis_all(channels, 600.00, 0, "2Post-Charge_Tseq0_25C", *temp_args))
        # Then temp sweep
        run_temp_sweep("2Post-Charge", temp_sequence, iter_temps, *temp_args)
        
        
    finally:
        # Return fan to idle 
        temp_sp = oven.set_temp_sp(25.0)      
        fan_sp = oven.set_fan_speed(25.0)
        print("temp_sp:", temp_sp)
        print("fan_sp:", fan_sp)
        
        # Store location of log files in each data directory
        for channel in channels:
            with open(channel.data_path.joinpath("temp_log_location_3.txt"), "w") as f:
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