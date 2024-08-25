from typing import Dict
from venv import logger

# from matplotlib import pyplot as plt
import requests

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from copy import deepcopy
from dataclasses import dataclass, field, asdict
from math import exp
from urllib.parse import quote_plus
from utils.loadcdx import load_cdx, DailyRecord, PeriodicSamples

MAXCDXPAGES = 2000
WBM = "https://web.archive.org/web"
CRLF = "\n"
CDXAPI = "https://web.archive.org/cdx/search/cdx"


def ymd(d):
    y, d = divmod(d, 365)
    m, d = divmod(d, 30)
    if y or m > 6:
        if d > 15:
            m += 1
        d = 0
    if m == 12:
        y += 1
        m = 0
    t = {"y": y, "m": m, "d": d}
    return "".join([s for k, v in t.items() if v for s in (str(v), k)])


@st.cache(max_entries=65536, show_spinner=False)
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


@st.cache(ttl=3600)
def get_resp_headers(url):
    res = requests.head(url, allow_redirects=True)
    rh = res.history + [res]
    return [
        f"HTTP/1.1 {r.status_code} {r.reason}{CRLF}{CRLF.join(': '.join(i) for i in r.headers.items())}{CRLF}"
        for r in rh
    ]


def load_cdx_pages(url):
    ses = requests.Session()
    prog = st.progress(0)
    page = 0
    while page < MAXCDXPAGES:
        pageurl = f"{url}&page={page}"
        r = ses.get(pageurl, stream=True)
        if not r.ok:
            prog.empty()
            raise ValueError(
                f"CDX API returned `{r.status_code}` status code for `{url}`"
            )
        r.raw.decode_content = True
        for line in r.raw:
            yield line
        page += 1
        maxp = int(r.headers.get("x-cdx-num-pages", 1))
        prog.progress(min(page / maxp, 1.0))
        if page >= maxp:
            prog.empty()
            break


@st.cache(ttl=3600, persist=True, show_spinner=False, suppress_st_warning=True)
def load_cdx(url):
    digest_status = {}
    date_record = {}
    psc = PeriodicSamples()
    STPR = {"2xx": 4, "4xx": 3, "5xx": 2, "3xx": 1}
    SWS = 1000
    sw = ["~"] * SWS
    cp = -1
    dr = None
    pt = ""
    pc = "~"
    ps = "~"
    rs = us = uw = 0
    for l in load_cdx_pages(
        f"{CDXAPI}?fl=timestamp,statuscode,digest&url={quote_plus(url)}"
    ):
        ts, s, d = l.decode().split()
        psc(ts)
        t = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
        s = f"{s[:1]}xx" if "200" <= s <= "599" else s
        if s == "-":
            s = digest_status.get(d, "~")
        else:
            digest_status[d] = s
        d = d[:8]
        if t != pt:
            if pt:
                pc = dr.digest
                dr.chaos = us / rs
                dr.chaosn = uw / min(SWS, rs)
                date_record[pt] = dr
            dr = DailyRecord(t)
            cp = -1
            pt = t
        dr.incr(s)
        pr = STPR.get(s, 0)
        if pr > cp:
            dr.specimen = s
            dr.datetime = ts
            dr.digest = d
            dr.content = "Unchanged" if d == pc else "Changed"
            cp = pr
        wp = rs % SWS
        rs += 1
        if s != ps:
            ps = s
            us += 1
            uw += 1
        if sw[wp] != sw[wp - SWS + 1]:
            uw -= 1
        sw[wp] = s
    if pt:
        dr.chaos = us / rs
        dr.chaosn = uw / min(SWS, rs)
        date_record[pt] = dr
    return (date_record, psc.sample)


@st.cache(ttl=3600)
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


def analyze_trends(url: str) -> Dict[str, float]:
    fill, policy = 0, "identical"
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

    d, _, _ = load_data(url, fill, policy, sigparams)

    # Chart for Resilience
    st.sidebar.subheader("Resilience Over Time")
    st.sidebar.line_chart(d.set_index("Day")["Resilience"])

    # Chart for Fixity
    st.sidebar.subheader("Fixity Over Time")
    st.sidebar.line_chart(d.set_index("Day")["Fixity"])

    # Chart for Chaos
    st.sidebar.subheader("Chaos Over Time")
    chaos_df = d.set_index("Day")[["Chaos", "Chaosn"]]
    chaos_df.columns = ["All", "Last 1000"]
    st.sidebar.line_chart(chaos_df)

    # st.sidebar.header("Trend Graphs")
    # plot_metrics(d, "Chaos", "Chaos Trend Over Time")
    # plot_metrics(d, "Fixity", "Fixity Trend Over Time")

    return {
        "captures": int(d["All"].sum()),
        "span": len(d),
        "gaps": int((d["All"] == 0).sum()),
        "resilience": float(d["Resilience"].iloc[-1]),
        "resilience_trend": (
            float(d["Resilience"].iloc[-1] - d["Resilience"].iloc[-2])
            if len(d) > 1
            else 0
        ),
        "fixity": float(d["Fixity"].iloc[-1]),
        "fixity_trend": (
            float(d["Fixity"].iloc[-1] - d["Fixity"].iloc[-2]) if len(d) > 1 else 0
        ),
        "chaos": float(d["Chaos"].iloc[-1]),
        "chaos_trend": (
            float(d["Chaos"].iloc[-1] - d["Chaos"].iloc[-2]) if len(d) > 1 else 0
        ),
        "status_distribution": d[["2xx", "3xx", "4xx", "5xx"]].sum().to_dict(),
    }


# def plot_metrics(data: pd.DataFrame, metric: str, title: str):
#     plt.figure(figsize=(10, 4))
#     plt.plot(data["Datetime"], data[metric], marker="o")
#     plt.title(title)
#     plt.xlabel("Date")
#     plt.ylabel(metric.capitalize())
#     plt.grid(True)
#     st.pyplot(plt)


def interpret_trend(metric: str, value: float, trend: float) -> str:
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

    level = "high" if value > 0.7 else "medium" if value > 0.3 else "low"
    trend_desc = "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable"

    return f"{interpretations[metric][level]} The trend is {trend_desc}."


def get_trend_analysis(url: str) -> str:
    logger.info(f"Analyzing trends for {url}")
    summary = analyze_trends(url)

    # # Plotting the Chaos and Fixity graphs in the sidebar
    # st.sidebar.header("Trend Graphs")
    # plot_metrics(d, "Chaos", "Chaos Trend Over Time")
    # plot_metrics(d, "Fixity", "Fixity Trend Over Time")

    return f"""
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
    
    These metrics are for the understanding of LLM only. Try to simplify the explanation for the end-user. You'll have to explain in layman terms what these metrics me an for the website's health and stability. Don't include the technical terms like fixity, chaos in the trend analysis result as user might not know of these.
    """
