import streamlit as st
import requests
from urllib.parse import quote_plus
from dataclasses import dataclass, field

CDXAPI = "https://web.archive.org/cdx/search/cdx"
MAXCDXPAGES = 2000


@dataclass
class DailyRecord:
    day: str
    datetime: str = "~"
    _2xx: int = 0
    _3xx: int = 0
    _4xx: int = 0
    _5xx: int = 0
    all: int = field(init=False)
    specimen: str = "~"
    filled: bool = field(init=False)
    resilience: float = 0.0
    digest: str = "~"
    content: str = "Unknown"
    fixity: float = 0.0
    chaos: float = 0.0
    chaosn: float = 0.0

    @property
    def all(self) -> int:
        return self._2xx + self._3xx + self._4xx + self._5xx

    @all.setter
    def all(self, _):
        pass

    @property
    def specimen(self) -> str:
        if self._specimen != "~":
            return self._specimen
        for k in ("_2xx", "_4xx", "_5xx", "_3xx"):
            if getattr(self, k):
                return k[1:]
        return self._specimen

    @specimen.setter
    def specimen(self, v):
        self._specimen = v if isinstance(v, str) else "~"

    @property
    def filled(self) -> bool:
        return self.specimen != "~" and not self.all

    @filled.setter
    def filled(self, _):
        pass

    def incr(self, status, count=1):
        k = "_" + status
        try:
            setattr(self, k, getattr(self, k) + count)
        except AttributeError as e:
            pass


class PeriodicSamples:
    PERIODS = {"Second": 14, "Minute": 12, "Hour": 10, "Day": 8, "Month": 6, "Year": 4}

    def __init__(self):
        self.count = 0
        self.sample = {p: 0 for p in self.PERIODS}
        self._prev = {p: "~" for p in self.PERIODS}

    def __call__(self, dt):
        self.count += 1
        for k, v in self.PERIODS.items():
            if dt[:v] == self._prev[k]:
                break
            self._prev[k] = dt[:v]
            self.sample[k] += 1

    def __str__(self):
        return "\t".join([str(self.count)] + [str(v) for v in self.sample.values()])


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


@st.cache_data(persist=True, show_spinner=False)
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
