import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import os
import time

from biocom.mps.techniques.mb import MBUrbanProfileList
from biocom.mps.techniques.ocv import OCVParameters
from biocom.mps.techniques.sequence import TechniqueSequence
import biocom.mps.config as cfg
from biocom.mps.common import BLDeviceModel, SampleType, IRange, Filter, Bandwidth
from biocom.com.server import OLECOM, DeviceChannel
from biocom.mps.write_utils import set_decimal_separator


ac_amp = 0.05
n_max = 4000
t_base = 200e-6
# c_lap = 0.0  # c > 0
# n_periods_per_segment = 2
# n_cycles = 10
v_range_min = -1.
v_range_max = 1.
frequencies = np.logspace(3, 0, 19)
# frequencies = [100]


params = [
    # dict(c_lap=0.0, n_periods_per_segment=2, n_cycles=10, ocv_between_cycles = False),
    dict(c_lap=-0.5, n_periods_per_segment=3, n_cycles=10, rest_type="flat"),
    # dict(c_lap=-0.5, n_periods_per_segment=2, n_cycles=10, ocv_between_cycles = True),
    # dict(c_lap=1.0, n_periods_per_segment=1, n_cycles=20, ocv_between_cycles = False),
    # dict(c_lap=1.0, n_periods_per_segment=1, n_cycles=20, ocv_between_cycles = True),
    # dict(c_lap=1.0, n_periods_per_segment=2, n_cycles=10, ocv_between_cycles = False),
    # dict(c_lap=1.0, n_periods_per_segment=2, n_cycles=10, ocv_between_cycles = True),
]


# Launch EC-Lab server
server = OLECOM(validate_return_codes=True, retries=1)


# Configure decimal separator and version for EC-lab
set_decimal_separator(comma=True)
cfg.set_versions("11.61")


# Configure channels and data directories
device = BLDeviceModel.SP300

basedir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang")

# expdir = basedir.joinpath(r"240919_CC_SymZType\PC09_8020\lapsin_test")
# expdir = basedir.joinpath(r"dummy_DC3\lapsin\240923")


# if not os.path.exists(expdir):
#     os.makedirs(expdir)

# TODO: update device and datadir
# channel = DeviceChannel(1, 1, BLDeviceModel.SP300, "SP11_Ch2", expdir)


channels = [
    DeviceChannel(0, 0, device, "SP10_Ch1",
        data_path=basedir.joinpath(r'240918_LPSCl_SymEonBlock_FlatInLi\PC06_140mg\lapsin')
    ),
    DeviceChannel(0, 1, device, "SP10_Ch2",
        data_path=basedir.joinpath(r'240918_LPSCl_SymEonBlock_FlatInLi\PC07_140mg\lapsin')
    ),
    DeviceChannel(1, 0, device, "SP11_Ch1",
        data_path=basedir.joinpath(r"240919_CC_SymZType\PC09_8020\lapsin")
    ),
    DeviceChannel(1, 1, BLDeviceModel.SP300, "SP11_Ch2", 
        data_path=basedir.joinpath(r"dummy_DC3\lapsin\241010")
    )
]

channel = channels[3]


def prime6(upto=1000000):
    # From https://rebrained.com/?p=458
    primes = np.arange(3, upto+1, 2)
    isprime = np.ones((upto-1) // 2, dtype=bool)
    for factor in primes[:int(math.sqrt(upto)) // 2]:
        if isprime[(factor - 2) // 2]: 
            isprime[(factor * 3 - 2) // 2::factor] = 0
    return np.insert(primes[isprime], 0, 2)

# Generate irrational numbers via sqrt of primes
primes = prime6(200)

irrationals = []
for factor in [1, 2, 4, 8]:
    irrationals.append(factor / np.sqrt(primes))
irrationals = np.unique(np.concatenate(irrationals))
irrationals = irrationals[irrationals < 1]
    
#
def select_irrational(a, irrationals):
    return irrationals[irrationals >= a][0]

# def select_subharmonic_dt(f, t_base):
#     raw_periods_per_sample = t_base * f
#     print("raw pps:", raw_periods_per_sample)
#     irr = select_irrational(raw_periods_per_sample % 1, irrationals)
#     irr_pps = np.floor(raw_periods_per_sample) + irr
#     print("irrational pps:", irr_pps)
    
#     return irr_pps / f


def select_subharmonic_factor(f, t_base):
    raw_periods_per_sample = t_base * f
    print("raw pps:", raw_periods_per_sample)
    irr = select_irrational(raw_periods_per_sample % 1, irrationals)
    irr_pps = np.floor(raw_periods_per_sample) + irr
    print("irrational pps:", irr_pps)
    
    return irr_pps / raw_periods_per_sample


def make_signal(f, c_lap, n_periods_per_segment, n_cycles, rest_type):
    omega = 2 * np.pi * f
    
    f_nyquist = 2 * f
    t_nyquist = 1 / f_nyquist
    
    rest_options = ["ocv", "opposite", "flat"]
    if rest_type not in rest_options:
        raise ValueError(f"Invalid rest_type {rest_type}. Options: {rest_options}")

    # period = 1 / f
    # print('period: {:.1e} s'.format(period))
    
    # Segment: chunk of time with fixed c, consisting of N periods
    # Alternate sign of c between segments

    n_segments = n_cycles * 2
    n_periods = n_segments * n_periods_per_segment
    # segment_duration = n_periods_per_segment * period
    # print("segment duration", segment_duration)

        
    if n_max * t_base < (n_periods / f):
        # Low frequency:
        # The time per sample is longer than the timebase
        # Make time step as long as needed to reach min_n_periods
        print("Low-frequency case")
        # Make sample period an integer multiple of timebase
        dt = (n_periods / f ) / n_max
        dt = np.ceil(dt / t_base) * t_base
        times = np.linspace(0, (n_max - 1) * dt, n_max)
    else:
        # High frequency
        # Go for as many periods as allowed by n_max
        
        times = np.linspace(0, (n_max - 1) * t_base, n_max)
        
        if t_base < t_nyquist / 10:
            # Ensure that we hit an integer number of periods
            # so that the voltage returns to zero
            print("High-frequency standard case")
            # n_periods = np.ceil(n_max * t_base * f)
            # times = np.linspace(0, n_periods * period, n_max)
        else:
            print("Subharmonic")
            # Sub-harmonic sampling
            
            factor = select_subharmonic_factor(f, t_base)
            print("Subharmonic factor:", factor)
           
            # times = np.linspace(0, t_sample * n_max, n_max)
            
            # We can't adjust the sample period, so we have to adjust the frequency
            
            f = f / factor
            print("Adjusted frequency: {:.9e}".format(f))

            
    # Calculate after adjusting frequency as needed
    omega = 2 * np.pi * f
    
    f_nyquist = 2 * f
    t_nyquist = 1 / f_nyquist

    period = 1 / f
    print('period: {:.1e} s'.format(period))
    
    # Segment: chunk of time with fixed c, consisting of N periods
    # Alternate sign of c between segments

    segment_duration = n_periods_per_segment * period
    print("segment duration", segment_duration)
        
    # Recalculate n_segments based on time grid
    n_segments = int(np.ceil(times[-1] / (period * n_periods_per_segment)))
    print("n_segments:", n_segments)
    
    
    print('time step: {:.3e}'.format(np.mean(np.diff(times))))
    # print('t_Nyquist: {:.3e}'.format(t_nyquist))

    y = np.zeros(len(times))
    
    for i in range(n_segments + 1):
        if rest_type == "ocv" and i % 2 == 1:
            # Return to OCV (leave signal at 0)
            pass
        else:
            sign = -np.sign(i % 2 - 0.5)
            
            if sign == -1:
                if rest_type == "opposite":
                    # Grow or decay in opposite direction
                    ci = c_lap * sign
                elif rest_type == "flat":
                    # Regular sin wave
                    ci = 0
            else:
                ci = c_lap * sign
                
            mask = (times >= i * segment_duration) & (times < (i + 1) * segment_duration)
        
            ti = times[mask]
            
            if len(ti) > 0:
                # print(i, "time range", ti[0], ti[-1])
                # Offset times to start at 0
                # This doesn't matter for phase, only for exp decay/growth
                ti = ti - segment_duration * i
                    
                # print('c: {:.3f}'.format(ci))
                
                # scale_factor = np.exp(-ci * omega * ti[-1])
                
                scale_factor = 1
                if rest_type == "opposite" and sign == -1:
                    scale_factor = np.exp(-c_lap * omega * ti[-1])
                elif rest_type == "flat" and sign == -1:
                    # scale_factor == 1
                    # Make max flat sin amplitude match max amplitude in decaying region
                    scale_factor = np.max(np.abs(np.sin(ti * omega + np.pi) * np.exp(c_lap * omega * ti) * scale_factor))
                    # print("scale_factor:", scale_factor)
                
                y[mask] = np.sin(ti * omega + np.pi) * np.exp(ci * omega * ti) * scale_factor
        
    # Finally, rescale to get desired amplitude    
    y *= ac_amp / np.max(np.abs(y))    
    print("y max:", np.max(y))
    df = pd.DataFrame(np.array([times, y]).T, columns=['Time/s', 'E/V'])
    
    return f, df



if __name__ == "__main__":
    server.launch_server()
    
    if not os.path.exists(channel.data_path):
        os.makedirs(channel.data_path)
    
    for j, param in enumerate(params):
        rest_type = param["rest_type"]
        
        rest_label = f"{rest_type}BtwCycles"
            
        for i, freq in enumerate(frequencies):
            print("Frequency: {:.2e} Hz".format(freq))
            freq, profile = make_signal(freq, **param)
            # Record 10 points per step or by timebase, whichever is slower
            # record_dt = max(np.mean(np.diff(profile["Time/s"])) * 0.1, t_base)
            record_dt = np.mean(np.diff(profile["Time/s"]))
            print("record_dt: {:.6f} s".format(record_dt))
            
            if i == 0:
                # Plot first frequency to check
                fig, axes = plt.subplots(1, 2, figsize=(8, 3))
                
                for ax in axes:
                    ax.plot(profile["Time/s"], profile['E/V'], ls='-', marker='.')
                    # ax.set_xlim(0.075, 0.083)
                    ax.set_xlim(0, 20 / freq)
                    ax.axhline(0, c='k', lw=1)
                    
                axes[1].set_ylim(-0.01, 0.01)
                fig.tight_layout()
                
                plt.show()
                
            
            period = 1 / freq
            
            ocv = OCVParameters(duration=max(2, period), record_dt=0.1,
                                v_range_min=v_range_min, 
                                v_range_max=v_range_max)
            
            mb = MBUrbanProfileList(
                [profile],
                record_dt,
                auto_rest=1,
                v_range_min=v_range_min, 
                v_range_max=v_range_max,
                # TODO: set IRange
                i_range=IRange.u10,
                bandwidth=Bandwidth.BW9
            )


            seq = TechniqueSequence([ocv, mb])

            config = cfg.set_defaults(channel.model, seq, SampleType.CORROSION)
            config.hardware.filtering = Filter.k50
            
            mps_file = channel.data_path.joinpath("LapSin_f={:.6e}_c={:.2f}_Vac={}_{}pps_{}-Scaled.mps".format(
                freq, param["c_lap"], ac_amp, param["n_periods_per_segment"], rest_label))
            server.load_techniques(channel, seq, config, mps_file)

            mpr_file = mps_file.parent.joinpath(mps_file.name.replace(".mps", ".mpr"))
            server.run_channel(channel, mpr_file)
            
            time.sleep(1.0)
            server.wait_for_channel(channel, min_wait=2.0, timeout=10 + 2 * profile["Time/s"].max())
            time.sleep(0.5)
            
        if j < len(params) - 1:
            # Rest before starting next parameter set
            time.sleep(60.0)
        