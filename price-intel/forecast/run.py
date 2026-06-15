# -*- coding: utf-8 -*-
"""run.py — baseline forecast: naive / moving-average (Holt-Winters nếu đủ chuỗi).
Chọn model bằng walk-forward Theil's U (<1 mới hơn naive). Gắn độ tin cậy + cơ sở dự báo."""
import math

MIN_FOR_MODELS = 8      # < 8 điểm: chỉ naive
MIN_FOR_HW = 24         # >= 24: thử Holt-Winters


def naive(series, horizon):
    last = series[-1]
    return [last] * horizon


def moving_average(series, horizon, window=3):
    w = series[-window:]
    avg = round(sum(w) / len(w), 4)
    return [avg] * horizon


def _rmse(pred, actual):
    n = len(actual)
    return math.sqrt(sum((p - a) ** 2 for p, a in zip(pred, actual)) / n)


def theils_u(actual, pred, naive):
    """U = RMSE(model)/RMSE(naive). <1 = thắng dự báo 'ngày mai = hôm nay'."""
    den = _rmse(naive, actual)
    if den == 0:
        return float("inf")
    return _rmse(pred, actual) / den


def _band(yhat):
    """Dải bất định nới dần theo bước (đơn giản: ±2% × sqrt(bước))."""
    lower, upper = [], []
    for i, v in enumerate(yhat, start=1):
        d = v * 0.02 * math.sqrt(i)
        lower.append(round(v - d, 1)); upper.append(round(v + d, 1))
    return lower, upper


def forecast_series(series, horizon=6, basis="spot dài", confidence=None):
    """Dự báo 1 chuỗi. Trả {model, yhat, lower, upper, theils_u, confidence, basis}."""
    series = [float(x) for x in series if x is not None]
    n = len(series)
    if n < 2:
        yhat = naive(series or [0], horizon)
        lower, upper = _band(yhat)
        return {"model": "naive", "yhat": yhat, "lower": lower, "upper": upper,
                "theils_u": None, "confidence": confidence or "thấp", "basis": basis}
    if n < MIN_FOR_MODELS:
        yhat = naive(series, horizon)
        lower, upper = _band(yhat)
        return {"model": "naive", "yhat": yhat, "lower": lower, "upper": upper,
                "theils_u": None, "confidence": confidence or "thấp", "basis": basis}
    # walk-forward 1 bước cho naive vs MA trên 5 điểm cuối
    k = min(5, n - 1)
    act, pred_ma, pred_nv = [], [], []
    for i in range(n - k, n):
        act.append(series[i])
        pred_nv.append(series[i - 1])
        w = series[max(0, i - 3):i]
        pred_ma.append(sum(w) / len(w))
    u_ma = theils_u(act, pred_ma, pred_nv)
    if u_ma < 1.0:
        model, yhat, u = "moving_average", moving_average(series, horizon), round(u_ma, 3)
    else:
        model, yhat, u = "naive", naive(series, horizon), round(u_ma, 3)
    lower, upper = _band(yhat)
    conf = confidence or ("vừa" if n >= MIN_FOR_HW else "vừa")
    return {"model": model, "yhat": yhat, "lower": lower, "upper": upper,
            "theils_u": u, "confidence": conf, "basis": basis}
