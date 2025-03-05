
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

ac_amp = 0.01
n_max = 4000
t_base = 200e-6

# Segment: chunk of time with fixed c, consisting of N periods
# Alternate sign of c between segments
n_periods_per_segment = 2
n_cycles = 4
n_segments = n_cycles * 2
n_periods = n_segments * n_periods_per_segment
c = 0.5

segment_len = int(n_max / n_segments)

writedir = Path(r"C:\Users\AKZMESS002\Documents\EC-Lab\Data\JakeHuang\dummy_DC3\lapsin")

for fi, f in enumerate([100, 25, 10]):
    omega = 2 * np.pi * f
    
    # c = -0.01

    f_nyquist = 2 * f
    t_nyquist = 1 / f_nyquist

    period = 1 / f
    print('period: {:.1e} s'.format(period))
    print('Max points per period: {:.0f}'.format(int(period / t_base)))

    # f_cutoff = min_n_periods / (n_max * t_base)
    # print('Min frequency: {:.1e}'.format(f_cutoff))
    
    times = np.linspace(0, n_periods * period, n_max)

    # if n_max * t_base < (n_segments / f):
    #     # Low frequency
    #     # Make time step as long as needed to reach min_n_periods
    #     times = np.linspace(0, n_segments / f, n_max)
    # else:
    #     # High frequency
    #     # Go for as many periods as allowed by n_max
    #     if t_base < t_nyquist:
    #         # Ensure that we hit an integer number of periods
    #         # so that the voltage returns to zero
    #         n_periods = np.ceil(n_max * t_base * f)
    #         times = np.linspace(0, n_periods * period, n_max)
    #     else:
    #         # Sub-harmonic sampling
    #         periods_per_sample = t_base / period
    #         periods_per_sample = np.ceil(periods_per_sample) + 0.6
    #         print('periods_per_sample: {:.3f}'.format(periods_per_sample))
    #         t_sample = period * periods_per_sample
            
    #         # n_periods = n_max * t_base * f
    #         # # rem = max(0.1, 1. / n_periods)
    #         # rem = 0.25
    #         # n_per_period = np.floor(period / t_base) + rem
    #         # # Can't go below timebase
    #         # n_per_period = min(period / t_base, n_per_period)
    #         # print('n_per_period:', n_per_period)
    #         # t_sample = period / n_per_period
            
    #         times = np.linspace(0, t_sample * n_max, n_max)
        
    t_base / period
    # t_sample
    # n_periods
    # n_per_period
    print('time step: {:.3e}'.format(np.mean(np.diff(times))))
    print('t_Nyquist: {:.3e}'.format(t_nyquist))

    y = np.zeros(len(times))
    for i in range(n_segments):
        sign = -np.sign(i % 2 - 0.5)
        ci = c * sign
        
        start = i * segment_len
        end = start + segment_len
        
        ti = times[start:end]
        ti = ti - ti[0]
            
        print('c: {:.3f}'.format(ci))
        
        scale_factor = 1
        if sign == -1:
            scale_factor *= np.exp(c * omega * ti[-1])
            # scale_factor = 0
        print("scale_factor:", scale_factor)
        
        y[start:end] = np.sin(ti * omega + np.pi) * np.exp(ci * omega * ti) * scale_factor
        
    # Finally rescale to get desired amplitude    
    y *= ac_amp / np.max(np.abs(y))
    
    if fi == 0:
        # Plot first frequency to check
        fig, ax = plt.subplots()
        ax.plot(times, y, ls='', marker='.')
        # ax.set_xlim(0, 10 / f)
        ax.axhline(0, c='k', lw=1)
        plt.show()


    df = pd.DataFrame(np.array([times, y]).T, columns=['Time', 'E/V']) #I/A
    df.to_csv(writedir.joinpath('sin_{:.1e}Hz_C={:.3g}_{}pps_{}Cycles_PiOffset.txt'.format(f, c, n_periods_per_segment, n_cycles)), 
              index=False, sep='\t', float_format='%.9f', encoding='ANSI')

    # times[-4:], y[-4:]