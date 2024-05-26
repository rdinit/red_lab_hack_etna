import numpy as np
from scipy.signal import periodogram


def auto_period(series_):
    f, p = periodogram(series_)
    return int(np.floor(1 / f[np.argmax(p)]))
