
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


for f in np.logspace(2, 0, 11):
    omega = 2 * np.pi * f
    ac_amp = 0.01
    # c = -0.01

    f_nyquist = 2 * f
    t_nyquist = 1 / f_nyquist

    n_max = 4000
    t_base = 200e-6
    min_n_periods = 10

    period = 1 / f
    print('period: {:.1e} s'.format(period))
    print('Max points per period: {:.0f}'.format(int(period / t_base)))

    f_cutoff = min_n_periods / (n_max * t_base)
    print('Min frequency: {:.1e}'.format(f_cutoff))

    if n_max * t_base < (min_n_periods / f):
        # Low frequency
        # Make time step as long as needed to reach min_n_periods
        times = np.linspace(0, min_n_periods / f, n_max)
    else:
        # High frequency
        # Go for as many periods as allowed by n_max
        if t_base < t_nyquist:
            times = np.linspace(0, n_max * t_base, n_max)
        else:
            # Sub-harmonic sampling
            periods_per_sample = t_base / period
            periods_per_sample = np.ceil(periods_per_sample) + 0.6
            print('periods_per_sample: {:.3f}'.format(periods_per_sample))
            t_sample = period * periods_per_sample
            
            # n_periods = n_max * t_base * f
            # # rem = max(0.1, 1. / n_periods)
            # rem = 0.25
            # n_per_period = np.floor(period / t_base) + rem
            # # Can't go below timebase
            # n_per_period = min(period / t_base, n_per_period)
            # print('n_per_period:', n_per_period)
            # t_sample = period / n_per_period
            
            times = np.linspace(0, t_sample * n_max, n_max)
        
    t_base / period
    # t_sample
    # n_periods
    # n_per_period
    print('time step: {:.3e}'.format(np.mean(np.diff(times))))
    print('t_Nyquist: {:.3e}'.format(t_nyquist))

    c = np.log(0.2) / (omega * times[-1])
    print('c: {:.3f}'.format(c))
    y = ac_amp * np.sin(times * omega) * np.exp(c * omega * times)

    fig, ax = plt.subplots()
    ax.plot(times, y, ls='', marker='.')
    ax.plot(times, ac_amp * np.exp(c * omega * times))
    ax.set_xlim(0, 10 / f)
    ax.axhline(0, c='k', lw=1)
    plt.show()


    df = pd.DataFrame(np.array([times, y]).T, columns=['Time', 'E/V']) #I/A
    df.to_csv(f'sin_{f}.txt', index=False, sep='\t', float_format='%.9f', encoding='ANSI')

    # times[-4:], y[-4:]