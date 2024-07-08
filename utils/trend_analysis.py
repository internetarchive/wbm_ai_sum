import pandas as pd
import numpy as np
from math import exp
import streamlit as st
from dataclasses import dataclass, field
from copy import deepcopy
from utils.loadcdx import load_cdx, DailyRecord

WBM = "https://web.archive.org/web"


@st.cache_data(max_entries=65536, show_spinner=False)
def _sigmoid_inverse(x, shift, slope):
    return 1 + exp(shift - x / slope)


def sigmoid(x, shift=5, slope=1, spread=1):
    return spread / _sigmoid_inverse(x, shift, slope)


def fill_identical(f, lk, lv, rk, rv, gap):
    if lv != rv:
        return
    for day in pd.date_range(lk, rk, inclusive="neither"):
        t = day.strftime("%Y-%m-%d")
        f[t] = DailyRecord(t, specimen=lv)


def fill_closest(f, lk, lv, rk, rv, gap):
    mid = gap / 2
    for i, day in enumerate(pd.date_range(lk, rk, inclusive="neither")):
        t = day.strftime("%Y-%m-%d")
        f[t] = DailyRecord(t, specimen=lv) if i < mid else DailyRecord(t, specimen=rv)


def fill_forward(f, lk, lv, rk, rv, gap):
    for day in pd.date_range(lk, rk, inclusive="neither"):
        t = day.strftime("%Y-%m-%d")
        f[t] = DailyRecord(t, specimen=lv)


def fill_backward(f, lk, lv, rk, rv, gap):
    for day in pd.date_range(lk, rk, inclusive="neither"):
        t = day.strftime("%Y-%m-%d")
        f[t] = DailyRecord(t, specimen=rv)


fillpolicies = {
    "identical": fill_identical,
    "closest": fill_closest,
    "forward": fill_forward,
    "backward": fill_backward,
}


def filler(drs, fill, policy):
    f = {}
    kv = iter(drs.items())
    pk, pv = next(kv)
    pv = pv.specimen
    pk = pd.to_datetime(pk)
    for k, v in kv:
        v = v.specimen
        k = pd.to_datetime(k)
        gap = (k - pk).days - 1
        if gap and (fill == -1 or gap <= fill):
            fillpolicies[policy](f, pk, pv, k, v, gap)
        pk, pv = k, v
    return f


def load_data(url, fill, policy, sigparams):
    date_record, psc = deepcopy(load_cdx(url))
    if not date_record:
        raise ValueError(f"Empty or malformed CDX API response for `{url}`")
    if fill != 0:
        date_record.update(filler(date_record, fill, policy))
    res = []
    ps = "~"
    pc = "Unknown"
    pch = pchn = 0.0
    base = basec = scale = scalec = h = hc = 0.5
    x = xc = 0
    for day in pd.date_range(next(iter(date_record)), pd.to_datetime("today")):
        t = day.strftime("%Y-%m-%d")
        dr = date_record.get(t, DailyRecord(t))
        if dr.chaos:
            pch = dr.chaos
            pchn = dr.chaosn
        else:
            dr.chaos = pch
            dr.chaosn = pchn
        s = dr.specimen
        p = sigparams.get(s)
        if s != ps:
            base = h
            scale = base if p[2] < 0 else 1 - base
            ps = s
            x = 0
        x += 1
        h = base + scale * sigmoid(x, *p)
        dr.resilience = h
        c = dr.content
        cp = sigparams.get(c)
        if c != pc:
            basec = hc
            scalec = basec if cp[2] < 0 else 1 - basec
            pc = c
            xc = 0
        xc += 1
        hc = basec + scalec * sigmoid(xc, *cp)
        dr.fixity = hc
        res.append(dr)
    resdf = pd.DataFrame(res)
    resdf.columns = [c[1:] if c[0] == "_" else c.title() for c in resdf.columns]
    resdf["URIM"] = resdf["Datetime"].apply(
        lambda x: f"{WBM}/{x}/{url}" if x != "~" else "#"
    )
    trs = {
        "2xx": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0},
        "3xx": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0},
        "4xx": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0},
        "5xx": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0},
    }
    rs = iter(res)
    pr = next(rs)
    for r in rs:
        try:
            trs[r.specimen][pr.specimen] += 1
            pr = r
        except KeyError as e:
            continue
    trsdf = (
        pd.DataFrame(trs)
        .reset_index()
        .rename(columns={"index": "Source"})
        .melt(
            id_vars=["Source"],
            value_vars=["2xx", "3xx", "4xx", "5xx"],
            var_name="Target",
            value_name="Count",
        )
    )
    pscdf = (
        pd.DataFrame.from_dict(psc, orient="index", columns=["Samples"])
        .reset_index()
        .rename(columns={"index": "Period"})
    )
    return (resdf, trsdf, pscdf)


def analyze_trends(url):
    # Default values for fill, policy, and sigparams
    fill = 0
    policy = "identical"
    sigparams = {
        "2xx": (4, 1.0, 1.0),
        "3xx": (5, 10.0, -0.5),
        "4xx": (5, 1.0, -1.0),
        "5xx": (5, 1.0, -1.0),
        "~": (10, 20.0, -0.5),
        "Changed": (6, 1.0, -1.0),
        "Unchanged": (4, 1.0, 1.0),
        "Unknown": (10, 30.0, -0.5),
    }

    d, t, p = load_data(url, fill, policy, sigparams)

    # Calculate trend metrics
    resilience_trend = (
        d["Resilience"].iloc[-1] - d["Resilience"].iloc[-2] if len(d) > 1 else 0
    )
    fixity_trend = d["Fixity"].iloc[-1] - d["Fixity"].iloc[-2] if len(d) > 1 else 0
    chaos_trend = d["Chaos"].iloc[-1] - d["Chaos"].iloc[-2] if len(d) > 1 else 0

    # Prepare summary
    summary = {
        "captures": int(d["All"].sum()),
        "span": len(d),
        "gaps": int((d["All"] == 0).sum()),
        "resilience": float(d["Resilience"].iloc[-1]),
        "resilience_trend": float(resilience_trend),
        "fixity": float(d["Fixity"].iloc[-1]),
        "fixity_trend": float(fixity_trend),
        "chaos": float(d["Chaos"].iloc[-1]),
        "chaos_trend": float(chaos_trend),
        "status_distribution": d[["2xx", "3xx", "4xx", "5xx"]].sum().to_dict(),
    }

    return summary


def interpret_trend(metric, value, trend):
    interpretations = {
        "resilience": {
            "high": "The webpage is highly resilient, indicating good archival preservation.",
            "medium": "The webpage has moderate resilience, suggesting room for improvement in archival preservation.",
            "low": "The webpage has low resilience, indicating potential issues with archival preservation.",
        },
        "fixity": {
            "high": "The webpage content is highly stable over time.",
            "medium": "The webpage content shows moderate stability over time.",
            "low": "The webpage content is frequently changing or unstable.",
        },
        "chaos": {
            "high": "The webpage shows high variability in its HTTP status codes, indicating potential instability.",
            "medium": "The webpage shows moderate variability in its HTTP status codes.",
            "low": "The webpage shows low variability in its HTTP status codes, indicating stability.",
        },
    }

    if value > 0.7:
        level = "high"
    elif value > 0.3:
        level = "medium"
    else:
        level = "low"

    trend_desc = "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable"

    return f"{interpretations[metric][level]} The trend is {trend_desc}."


def get_trend_analysis(url):
    summary = analyze_trends(url)

    analysis = f"""
    Trend Analysis for {url}:

    1. Captures: {summary['captures']} total captures over {summary['span']} days, with {summary['gaps']} gaps.

    2. Resilience: {summary['resilience']:.5f} (Trend: {summary['resilience_trend']:.5f})
    {interpret_trend('resilience', summary['resilience'], summary['resilience_trend'])}

    3. Fixity: {summary['fixity']:.5f} (Trend: {summary['fixity_trend']:.5f})
    {interpret_trend('fixity', summary['fixity'], summary['fixity_trend'])}

    4. Chaos: {summary['chaos']:.5f} (Trend: {summary['chaos_trend']:.5f})
    {interpret_trend('chaos', summary['chaos'], summary['chaos_trend'])}

    5. Status Distribution:
    - 2xx: {summary['status_distribution']['2xx']}
    - 3xx: {summary['status_distribution']['3xx']}
    - 4xx: {summary['status_distribution']['4xx']}
    - 5xx: {summary['status_distribution']['5xx']}
    """

    return analysis
