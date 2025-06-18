import numpy as np
from numpy import ndarray
from enum import Enum, StrEnum
from typing import Optional, Union, Tuple

from .sampling import (
    find_steps, split_steps, step_times2index, segment_step_values,
    remove_short_samples, select_decimation_interval,
    get_decimation_index, filter_chrono_signals
)

from .iv import LinearIV

try:
    from hybdrt.models import DRT
    _drt_available = True
    _drt = None
except ModuleNotFoundError:
    _drt_available = False


class ControlMode(StrEnum):
    GALV = "Galvanostatic"
    POT  = "Potentiostatic"
    

def get_io_signals(i_signal, v_signal, mode: ControlMode):
    if mode == ControlMode.GALV:
        s_in, s_out = i_signal, v_signal
    else:
        s_in, s_out = v_signal, i_signal
    return s_in, s_out


def get_dc_step_values(
        times, 
        i_signal, 
        v_signal,
        mode: ControlMode,
        step_times: Optional[Union[list, ndarray]] = None,
        window_fraction: float = 0.1,
        min_agg_points: int = 5,
        agg: str = 'median',
        use_longest_step: bool = True):
    
    s_in, s_out = get_io_signals(i_signal, v_signal, mode)
    
    # Identify steps in the input signal
    if step_times is None:
        step_index = find_steps(s_in, allow_consecutive=False)
    else:
        step_index = step_times2index(times, step_times)
        
    if use_longest_step:
        step_durations = np.array([ts[-1] - ts[0] for ts in split_steps(times, step_index)])
        # Get unique input signal values
        sin_rnd_vals = segment_step_values(s_in, step_index)
        sin_unique = np.unique(sin_rnd_vals)
        # Find the longest step for each input signal value
        long_step_index = []
        for si in sin_unique:
            index = np.where(sin_rnd_vals == si)[0]
            long_step_index.append(index[np.argmax(step_durations[index])])
    else:
        long_step_index = None
        
    def agg_window(x):
        # Aggregate points from the end of the data segment
        n_agg = max(min_agg_points, int(len(x) * window_fraction))
        return getattr(np, agg)(x[-n_agg:])
    
    # Estimate steady-state i and v values from the end of each step
    step_agg_vals = []
    for sig in (i_signal, v_signal):
        s_split = split_steps(sig, step_index)
        if long_step_index is not None:
            # Only use the longest step at each value
            s_split = [s_split[i] for i in long_step_index]
        step_agg_vals.append(np.array([agg_window(s) for s in s_split]))
        
    return step_agg_vals
    
def process_ivt_simple(
        times, 
        i_signal, 
        v_signal,
        mode: ControlMode,
        step_times: Optional[Union[list, ndarray]] = None,
        window_fraction: float = 0.1,
        min_agg_points: int = 5,
        agg: str = 'median',
        use_longest_step: bool = True
        ) -> LinearIV:
    
    step_agg_vals = get_dc_step_values(times, i_signal, v_signal, mode,
                       step_times, window_fraction, min_agg_points,
                       agg, use_longest_step
                       )
        
    # Linear fit of v vs. i
    pfit = np.polyfit(step_agg_vals[0], step_agg_vals[1], deg=1)
    dvdi = pfit[0]
    
    # Estimate midpoint (i, v) coordinates
    i_mid = getattr(np, agg)(i_signal)
    v_mid = np.polyval(pfit, [i_mid])[0]
    
    # Return: LinearIV instance 
    return LinearIV(i_mid, v_mid, dvdi)



def process_ivt_drt(times, 
        i_signal, 
        v_signal,
        mode: ControlMode,
        remove_short: bool = False,
        fit_kw = None,
        ) -> LinearIV:
    
    if not _drt_available:
        raise RuntimeError("hybrid-drt must be installed to call process_ivt_drt")
    
    global _drt
    if _drt is None:
        # Initialize DRT instance for data processing
        _drt = DRT()
        
    # Remove short time steps
    if remove_short:
        times, i_signal, v_signal = remove_short_samples(times, np.array([times, i_signal, v_signal]).T).T
    
    if fit_kw is None:
        fit_kw = {
            "downsample": True,
            "downsample_kw": {
                "method": "decimate",
                "target_size": 200,
                "prestep_samples": 10
            }
        }
    
    # Use basic ivt processing to get i_mid and v_mid
    iv = process_ivt_simple(times, i_signal, v_signal, mode)
    # print("Initial i_mid: {:.2e}".format(iv.i_mid))
    # print("Initial v_mid: {:.2e}".format(iv.v_mid))
    
    f_long = (2 * np.pi * (times[-1] - times[0])) ** -1
    if mode == ControlMode.POT:
        _drt.fit_chrono(times, v_signal, i_signal, nonneg=False, **fit_kw)
        z_tot = _drt.predict_z(np.array([f_long]))[0] ** -1
        iv.i_mid = _drt.fit_parameters["v_baseline"]
        # print("Updated i_mid: {:.2e}".format(iv.i_mid))
        
    else:
        _drt.fit_chrono(times, i_signal, v_signal, **fit_kw)
        z_tot = _drt.predict_z(np.array([f_long]))[0]
        iv.v_mid = _drt.fit_parameters["v_baseline"]
        # print("Updated v_mid: {:.2e}".format(iv.v_mid))
        
    # _drt.plot_results()
    # _drt.plot_chrono_fit(transform_time=False)
        
    iv.dvdi = np.abs(z_tot)
    # print("z_tot:", z_tot)
    # print("dvdi: {:.1e}".format(iv.dvdi))
    return iv


def downsample_data(
        times: ndarray, 
        i_signal: ndarray, 
        v_signal: ndarray,
        mode: ControlMode,
        target_size: int = 1000,
        init_samples: Union[int, None] = 25,
        stepwise: bool = True,
        step_index: Optional[ndarray] = None, 
        decimation_interval: int = 10, 
        decimation_factor: float = 2.0, 
        max_interval: Optional[float] = None,
        antialiased: bool = True, 
        remove_short: bool = False,
        remove_outliers: bool = True,
        outlier_prior: float = 0.01,
        outlier_thresh: float = 0.75,
        **filter_kw
        ) -> Tuple[Tuple[ndarray, ndarray, ndarray], ndarray]:

    # Remove short time steps
    if remove_short:
        times, i_signal, v_signal = remove_short_samples(times, np.array([times, i_signal, v_signal]).T).T
        
    if stepwise:
        # Restart sampling from start of each step
        if step_index is None:
            # Identify steps in input signal. Exclude consecutive steps
            s_in, _ = get_io_signals(i_signal, v_signal, mode)            
            step_index = find_steps(s_in, allow_consecutive=False)
    else:
        # Treat as a single step
        step_index = np.array([0], dtype=int)

    # Get sample period
    t_sample = np.median(np.diff(times))
    
    if target_size is not None:
        decimation_interval = -1
        while decimation_interval == -1:
            decimation_interval = select_decimation_interval(times, step_index, t_sample, init_samples,
                                                                decimation_factor, max_interval,
                                                                target_size)
    # print(decimation_interval)
    sample_index = get_decimation_index(times, step_index, t_sample, init_samples, decimation_interval,
                                        decimation_factor, max_interval)
    
    # else:
    #     # Get sample times closest to ideal times
    #     sample_index = np.array([[nearest_index(times, target_times[i])] for i in range(len(target_times))])
    #     sample_index = np.unique(sample_index)

    if antialiased:
        # Apply an antialiasing filter before downsampling
        if filter_kw is None:
            filter_kw = {}
            
        i_signal, v_signal = filter_chrono_signals(
            times, 
            (i_signal, v_signal), 
            step_index,
            decimate_index=sample_index, 
            remove_outliers=remove_outliers,
            outlier_prior=outlier_prior,
            outlier_thresh=outlier_thresh,
            **filter_kw)
        

    sample_times = times[sample_index].flatten()
    sample_i = i_signal[sample_index].flatten()
    sample_v = v_signal[sample_index].flatten()

    return (sample_times, sample_i, sample_v), sample_index

    

