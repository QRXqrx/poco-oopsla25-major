import math
import scipy.stats as stats

"""
Given a set of N seed files, sample n seed files and copy the sampled seed files 
into a target directory.
"""


def lookup_zscore_by_conf(confidence: float) -> float:
    # How to read Z-table: https://www.simplypsychology.org/z-table.html
    return stats.norm.ppf(1 - (1 - confidence) / 2)


def cal_sample_size(N: int, p: float = 0.5, e: float = .05, conf: float = .95) -> int:
    """
    Reference: 1992-Determining Sample Size

    Cochran-style sample size calculation. First calculate to representative
    sample size n0. Note that n0 is calculated under the assumption that the
    population size N is large enough, that is, approaches to +inf.

        n0 = (z^2 * p * (1-p)) / e^2

    where z is z-score, p is the degree of variability of w.r.t. the
    population which is assumed to 0.5 by default, e is the margin of
    error (or the level of precision). With finite population N, the
    actual sample size n w.r.t. to n0 is corrected as:

        n = n0 / (1 + (n0 - 1) / N)

    :param N: population size
    :param p: degree of variability, float in [0, 1], default is 0.5 (50%)
    :param e: margin or error, default is 0.05 (5%)
    :param conf: confidential interval, typical values are .90, .95, .99
    :return:
    """
    # Look up for z-score with the given confidence
    z = lookup_zscore_by_conf(confidence=conf)
    n0 = (z**2 * p * (1-p)) / e**2
    n = n0 / (1 + (n0 - 1) / N)
    return math.ceil(n)
