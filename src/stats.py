"""Small statistics helpers: mean, standard deviation, 95% confidence interval, percentiles."""
import math
import statistics

# Student's t critical values for a two-sided 95% interval, by degrees of freedom (n - 1).
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
       10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 19: 2.093, 24: 2.064, 29: 2.045}


def t95(df):
    if df >= 30:
        return 1.96                                 # large samples: normal approximation
    return T95[max(d for d in T95 if d <= df)]      # conservative: nearest smaller df in the table


def summary(values):
    """Returns (mean, sd, ci95_half_width). For one value sd and ci are 0."""
    n = len(values)
    mean = statistics.fmean(values)
    if n < 2:
        return mean, 0.0, 0.0
    sd = statistics.stdev(values)
    return mean, sd, t95(n - 1) * sd / math.sqrt(n)


def percentile(values, q):
    """q-th percentile (0-100) with linear interpolation."""
    s = sorted(values)
    k = (len(s) - 1) * q / 100
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)