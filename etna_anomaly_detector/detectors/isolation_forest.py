import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import STL

from etna_anomaly_detector.detectors.utils import auto_period


def stl_components(series, period=None):
    stl = STL(series, period=period, robust=False)
    stl_res = stl.fit()

    components = pd.DataFrame({"trend": stl_res.trend, "season": stl_res.seasonal, "resid": stl_res.resid})
    return components


def _iforest_features(series):
    names = [
        "is_month_start",
        "is_month_end",
        "is_quarter_start",
        "is_quarter_end",
        "is_year_start",
        "is_year_end",
        "month",
        "day",
        "hour",
        "minute",
        "weekofyear",
        "week",
        "weekday",
        "dayofweek",
        "dayofyear",
        "quarter",
        "daysinmonth",
    ]

    features = {}

    # index features
    for name in names:
        features[name] = np.array(getattr(series.index, name))

    features = pd.DataFrame(features, index=series.index)
    return features


def hw_components(series, trend="add", seasonal="add", damped_trend=False, period=None):
    model = ExponentialSmoothing(
        endog=series, trend=trend, seasonal=seasonal, damped_trend=damped_trend, seasonal_periods=period
    )
    fit_result = model.fit()

    level = fit_result.level.values
    trend = fit_result.trend.values
    season = fit_result.season.values

    components = {
        "target_component_level": np.concatenate([[fit_result.params["initial_level"]], level[:-1]]),
    }

    if model.trend is not None:
        trend = np.concatenate([[fit_result.params["initial_trend"]], trend[:-1]])

        if model.damped_trend:
            trend *= fit_result.params["damping_trend"]

        components["target_component_trend"] = trend

    if model.seasonal is not None:
        seasonal_periods = model.seasonal_periods
        components["target_component_seasonality"] = np.concatenate(
            [fit_result.params["initial_seasons"], season[:-seasonal_periods]]
        )

    components = pd.DataFrame(data=components, index=series.index)

    residuals = series.values - np.sum(components.values, axis=1)
    return components, residuals


def isolation_forest(
    series, trend=None, seasonal=None, period=None, use_stl=False, use_hw=False, use_time=True, **kwargs
):
    if period is None:
        period = auto_period(series)

        if period >= len(series) // 2:
            period = period // 2

    if use_time:
        features = _iforest_features(series)
    else:
        features = pd.DataFrame({})

    if use_stl:
        comps = stl_components(series, period)
        features = pd.concat([features, comps], axis=1)

    elif use_hw:
        if period is None:
            seasonal = None

        comps, resids = hw_components(series, trend=trend, seasonal=seasonal, period=period)

        features = pd.concat([features, comps], axis=1)
        features["resids"] = resids

    else:
        features["target"] = series.values

    forest = IsolationForest(**kwargs)
    forest.fit(features)
    anom = forest.predict(features)
    scores = -forest.score_samples(features)

    return anom == -1, scores, np.arange(len(features), dtype=int)
