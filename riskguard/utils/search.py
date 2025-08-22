# riskguard/utils/search.py
from functools import lru_cache
from typing import List, Dict
import requests
from ..config import FALLBACK_SYMBOLS

def _label(sym, name="", exch=""):
    return f"{sym} — {name} [{exch}]" if (name or exch) else sym

def search_symbols_online(q: str) -> List[Dict]:
    url = "https://query1.finance.yahoo.com/v1/finance/search"
    r = requests.get(url, params={"q": q, "quotesCount": 20, "newsCount": 0}, timeout=5)
    r.raise_for_status()
    data = r.json() if r.text else {}
    out = []
    for it in (data.get("quotes") or [])[:20]:
        sym = it.get("symbol")
        if not sym:
            continue
        out.append({"label": _label(sym, it.get("shortname") or it.get("longname") or "", it.get("exchDisp") or ""), "value": sym})
    return out

@lru_cache(maxsize=512)
def search_symbols(q: str) -> List[Dict]:
    q = (q or "").strip()
    if not q:
        return [{"label": s, "value": s} for s in FALLBACK_SYMBOLS[:12]]
    try:
        return search_symbols_online(q)
    except Exception:
        matches = [s for s in FALLBACK_SYMBOLS if q.lower() in s.lower()]
        return [{"label": m, "value": m} for m in (matches[:12] or FALLBACK_SYMBOLS[:12])]
