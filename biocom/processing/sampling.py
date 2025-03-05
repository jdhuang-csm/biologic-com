import numpy as np
from numpy import ndarray
import scipy.ndimage as ndi
import warnings
from typing import Optional, Union, List

from ..filters import nonuniform_gaussian_filter1d
from ..utils import nearest_value
from . import stats


# =======================
# Basic signal processing
# =======================
def find_steps(y, allow_consecutive=True, rthresh=20, athresh=1e-10):
    """
    Identify steps in signal
    :param ndarray y: signal
    :param bool allow_consecutive: if False, do not allow consecutive steps
    :param float rthresh: relative threshold for identifying steps
    :param float athresh: absolute threshold for step size
    :return: step indices
    """
    dy = np.diff(y)
    # Identify indices where diff exceeds threshold
    # athresh defaults to 1e-10 in case median diff is zero
    step_idx = np.where((np.abs(dy) >= np.median(np.abs(dy)) * rthresh) & (np.abs(dy) >= athresh))[0] + 1

    if not allow_consecutive:
        # eliminate consecutive steps - these arise due to finite rise time and do not represent 
        # distinct program steps
        idx_diff = np.diff(step_idx)
        idx_diff = np.concatenate(([2], idx_diff))
        step_idx = step_idx[idx_diff > 1]

    return step_idx


def split_steps(x, step_index):
    """
    Split x by step indices
    :param ndarray x: array to split
    :param ndarray step_index: step indices
    :return:
    """
    step_index = np.array(step_index)
    # Add start and end indices
    if step_index[0] > 0:
        step_index = np.insert(step_index, 0, 0)
    if step_index[-1] < len(x):
        step_index = np.append(step_index, len(x))

    return [x[start:end] for start, end in zip(step_index[:-1], step_index[1:])]


def get_step_values(x, step_index, agg: str = "median"):
    splits = split_steps(x, step_index)
    return [getattr(np, agg)(s) for s in splits]


def segment_step_values(x, step_index, rel_precision: float = 0.05):
    # Identify median signal values at each step
    x_vals = np.array(get_step_values(x, step_index))
    
    # Round signal values to 5 % of smallest step and get unique values
    abs_prec = rel_precision * np.min(np.abs(np.diff(x_vals)))
    x_vals_round = np.floor(np.abs(x_vals) / abs_prec) * abs_prec * np.sign(x_vals)
    x_unique = np.unique(x_vals_round)
    
    # Assign each step to the nearest unique value
    return nearest_value(x_unique, x_vals_round)
    


def step_times2index(times: ndarray, step_times: Union[list, ndarray]) -> ndarray:
    """Convert step times to array indices

    :param ndarray times: Sample times
    :param Union[list, ndarray] step_times: Times at which control steps
        were applied
    :return ndarray: Sample indices corresponding to steps
    """
    # Determine step index by getting measurement time closest to step time
    # Each step_index must start at or after step time - cannot start before
    def pos_delta(x, x0):
        out = np.empty(len(x))
        out[x < x0] = np.inf
        out[x >= x0] = x[x >= x0] - x0
        return out

    step_index = np.array([np.argmin(pos_delta(times, st)) for st in step_times])

    return step_index


def remove_short_samples(
        times: ndarray,
        data: ndarray,
        min_step: Optional[float] = None):
    if len(times) > 1:
        # Get time deltas
        dt = np.insert(np.diff(times), 0, np.inf)

        if min_step is None:
            # Set minimum step time to 90% of median sample period
            min_step = np.median(dt) * 0.9

        # Keep points that exceed the minimum step time
        mask = dt >= min_step

        return data[mask]
    return data

# =========================
# Downsampling & filtering
# ========================
def select_decimation_interval(times, step_index, t_sample, init_samples, decimation_factor, max_t_sample,
                               target_size):
    intervals = np.logspace(np.log10(2), np.log10(1000), 12).astype(int)
    sizes = [len(get_decimation_index(times, step_index, t_sample, init_samples,
                                      interval, decimation_factor, max_t_sample)
                 )
             for interval in intervals]
    if target_size > sizes[-1]:
        warnings.warn(f'Cannot achieve target size of {target_size} with selected decimation factor of '
                      f'{decimation_factor}. Decrease the decimation factor and/or decrease the maximum period')
    if target_size < sizes[0]:
        warnings.warn(f'Cannot achieve target size of {target_size} with selected decimation factor of '
                      f'{decimation_factor}. Increase the decimation factor and/or increase the maximum period'
                      )
    return int(np.interp(target_size, sizes, intervals))


def get_decimation_index(times, step_index, t_sample, init_samples, decimation_interval, decimation_factor,
                         max_t_sample):
    if init_samples is not None:
        # Get evenly spaced samples from period before first step
        init_index = np.unique(np.linspace(0, step_index[0] - 1, init_samples).round(0).astype(int))
        keep_indices = [init_index]
    else:
        # Treat initial data (prior to first step) as if it is a step
        if step_index[0] > 0:
            step_index = np.insert(step_index, 0, 0)
        keep_indices = []

    # Limit sample interval to max_t_sample
    if max_t_sample is None:
        max_sample_interval = np.inf
    else:
        max_sample_interval = int(max_t_sample / t_sample)

    # Build array of indices to keep
    # print("step_index:", step_index)
    for i, start_index in enumerate(step_index):
        # Decimate samples after each step
        if start_index == step_index[-1]:
            next_step_index = len(times)
        else:
            next_step_index = step_index[i + 1]

        # Keep first decimation_interval points without decimation
        undec_index = np.arange(start_index, min(start_index + decimation_interval + 1, next_step_index), dtype=int)

        keep_indices.append(undec_index)
        # sample_interval = 1
        last_index = undec_index[-1]
        j = 1
        while last_index < next_step_index - 1:
            # Increment sample_interval
            # sample_interval = min(int(sample_interval * decimation_factor), max_sample_interval)
            sample_interval = min(int(decimation_factor ** j), max_sample_interval)
            # print('sample_interval:', sample_interval)

            if sample_interval == max_sample_interval:
                # Sample interval has reached maximum. Continue through end of step
                interval_end_index = next_step_index #- 1
            else:
                # Continue with current sampling rate until decimation_interval points acquired
                interval_end_index = min(last_index + decimation_interval * sample_interval + 1,
                                         next_step_index)

            keep_index = np.arange(last_index + sample_interval, interval_end_index, sample_interval, dtype=int)

            if len(keep_index) == 0:
                # sample_interval too large - runs past end of step. Keep last sample
                keep_index = [interval_end_index - 1]

            # If this is the final interval, ensure that last point before next step is included
            if interval_end_index == next_step_index and keep_index[-1] < next_step_index - 1:
                keep_index = np.append(keep_index, next_step_index - 1)

            keep_indices.append(keep_index)

            # Increment last_index
            last_index = keep_index[-1]
            j += 1

    decimate_index = np.unique(np.concatenate(keep_indices))

    return decimate_index


def filter_chrono_signals(
        times, 
        signals: List[ndarray], 
        step_index: Union[List, ndarray], 
        decimate_index: Optional[ndarray] = None,
        sigma_factor: float = 0.01, 
        max_sigma: Optional[float] = None,
        remove_outliers: bool = False, 
        outlier_prior: float = 0.01, 
        outlier_thresh: float = 0.75, 
        median_prefilter: bool = False,
        first_step_steady: bool = False,
        **kw):

    signals_out = [s.copy() for s in signals]
    
    if remove_outliers:
        # First, remove obvious extreme values
        # ext_index = identify_extreme_values(y, qr_size=0.8)
        # print('extreme value indices:', np.where(ext_index))
        # y[ext_index] = ndimage.median_filter(y, size=31)[ext_index]

        # Find outliers with difference from filtered signal
        # Use median prefilter to avoid spread of outliers
        signals_filt = filter_chrono_signals(times, signals_out, step_index=step_index, decimate_index=decimate_index,
                                      sigma_factor=sigma_factor, max_sigma=max_sigma,
                                      remove_outliers=False,
                                      median_prefilter=True, **kw)

        outlier_flags = [
            flag_outliers(si, sfi, outlier_thresh, outlier_prior)
            for si, sfi in zip(signals_out, signals_filt)
        ]

        for i in range(len(signals_out)):
            print(f'Num outliers in signal {i}:', np.sum(outlier_flags[i]))
            # Replace outliers with filtered values
            signals_out[i][outlier_flags[i]] = signals_filt[i][outlier_flags[i]]

    t_steps = split_steps(times, step_index)
    t_sample = np.median(np.diff(times))
    
    if max_sigma is None:
        max_sigma = sigma_factor / t_sample
        
    # Get sigmas corresponding to decimation index
    if decimate_index is not None:
        decimate_sigma = sigma_from_decimate_index(signals[0], step_index, decimate_index)
        step_dec_sigmas = split_steps(decimate_sigma, step_index)
    else:
        step_dec_sigmas = None
            
    # Filter each signal
    for i in range(len(signals)):
        signal = signals_out[i]
        s_steps = split_steps(signal, step_index)

        s_filt = []
        n = 0
        for j, (t_step, s_step) in enumerate(zip(t_steps, s_steps)):
            if first_step_steady and j == 0:
                # Assume the initial step is at steady state and thus can be filtered with a uniform length scale
                sigmas = np.full(len(t_step), max_sigma)
            else:
                # Ideal sigma from inverse sqrt of maximum curvature of RC relaxation
                sigma_ideal = np.exp(1) * (t_step - (t_step[0] - t_sample)) / 2
                sigmas = sigma_factor * (sigma_ideal / t_sample)
                sigmas[sigmas > max_sigma] = max_sigma

            # Use decimation index to cap sigma
            if step_dec_sigmas is not None:
                sigmas = np.minimum(step_dec_sigmas[j], sigmas)

            if median_prefilter:
                s_step = ndi.median_filter(s_step, 3, mode='nearest')

            # if j == 0:
            dec_index = decimate_index[(decimate_index < n + len(t_step)) & (decimate_index >= n)]
            s_filt.append(nonuniform_gaussian_filter1d(s_step, sigmas, **kw))
            n += len(t_step)

        signals_out[i] = np.concatenate(s_filt)
        
    return signals_out


def sigma_from_decimate_index(y, step_index, decimate_index, truncate=4.0):
    sigmas = np.zeros(len(y)) #+ 0.25

    # Determine distance to nearest sample
    diff = np.diff(decimate_index)
    ldiff = np.insert(diff, 0, diff[0])
    rdiff = np.append(diff, diff[-1])
    # If the next sample to the right is the beginning of a new step,
    # don't consider its distance in the sigma calculation,
    # since the filter is bounded within each step.
    rdiff[np.isin(decimate_index, np.array(step_index) -1)] = 10000
    min_diff = np.minimum(ldiff, rdiff)

    # Set sigma such that truncate * sigma reaches halfway to nearest sample
    sigma_dec = min_diff / (2 * truncate)
    sigma_dec[min_diff < 2] = 0  # Don't filter undecimated regions
    sigmas[decimate_index] = sigma_dec

    return sigmas


def flag_outliers(y_raw, y_filt, thresh=0.75, p_prior=0.01):
    dev = y_filt - y_raw
    std = stats.robust_std(dev)
    sigma_out = np.maximum(np.abs(dev), 0.01 * std)
    p_out = stats.outlier_prob(dev, 0, std, sigma_out, p_prior)

    return p_out > thresh


