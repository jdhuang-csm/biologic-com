import numpy as np
from scipy.stats import norm


def robust_std(x):
    """Estimate standard deviation from interquartile range"""
    q1 = np.percentile(x, 25)
    q3 = np.percentile(x, 75)

    return (q3 - q1) / 1.349


def outlier_prob(x, mu_in, sigma_in, sigma_out, p_prior):
    """
    Estimate outlier probability using a Bernoulli prior
    :param ndarray x: data
    :param ndarray mu_in: mean of inlier distribution
    :param ndarray sigma_in: standard deviation of inlier distribution
    :param ndarray sigma_out: standard deviation of outlier distribution
    :param float p_prior: prior probability of any point being an outlier
    :return:
    """
    pdf_in = norm.pdf(x, mu_in, sigma_in)
    pdf_out = norm.pdf(x, mu_in, sigma_out)
    p_out = p_prior * pdf_out / ((1 - p_prior) * pdf_in + p_prior * pdf_out)
    dev = np.abs(x - mu_in)
    # Don't consider data points with smaller deviations than sigma_in to be outliers
    p_out[dev <= sigma_in] = 0
    return p_out