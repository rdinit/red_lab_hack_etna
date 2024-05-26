import functools
import warnings

import numpy as np
from joblib import Parallel, delayed
from numpy.lib.stride_tricks import sliding_window_view
from statsmodels.tsa.seasonal import STL

from etna_anomaly_detector.detectors.utils import auto_period

warnings.filterwarnings("ignore")


def sliding_window(data, window, stride=1):
    matrix = sliding_window_view(data[::-1], window)[::stride, ::-1]
    return matrix[::-1]


def sliding_window_decorator(func):
    @functools.wraps(func)
    def inner(x, *, window, stride=1, return_indices=True, workers=1, **kwargs):
        x_indexes = np.arange(x.size)
        indexes_matrix = sliding_window(x_indexes, window, stride)

        apply_func = functools.partial(func, x, **kwargs)

        parallel_res = Parallel(n_jobs=workers)(delayed(apply_func)(row) for row in indexes_matrix)
        res, all_scores = list(zip(*parallel_res))

        res = np.stack(res)
        all_scores = np.stack(all_scores)

        if return_indices:
            return res, all_scores, indexes_matrix

        else:
            return res, all_scores

    return inner


def _stl_decompose(series, stl_period=None, trend_only=False):
    if stl_period is not None:
        stl_res = STL(series, period=stl_period).fit()
        if trend_only:
            series = series - stl_res.trend

        else:
            series = stl_res.resid

    return series


@sliding_window_decorator
def iqr_method(x, idxs, stl_period=None, trend_only=False, iqr_scale=1.5, use_stl_period=False):
    series = x[idxs]

    if use_stl_period and stl_period is None:
        stl_period = auto_period(series)

        if stl_period >= len(stl_period) // 2:
            stl_period = stl_period // 2

    series = _stl_decompose(series, stl_period, trend_only)

    first = np.quantile(series, 0.25)
    third = np.quantile(series, 0.75)

    iqr = iqr_scale * (third - first)

    maxval = third + iqr
    minval = first - iqr

    anom_mask = (series > maxval) | (series < minval)  # reuse another
    scores = np.maximum(np.maximum(0, series - maxval), np.maximum(0, minval - series)) / (maxval - minval)

    return anom_mask, scores
