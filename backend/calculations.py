"""AO-360 Calculation Engine (bagian 51).
Semua perhitungan achievement/score/NPF/ranking dilakukan di sini,
bukan di frontend. Menerapkan aturan pembagian nol (22a) & formula revisi.
"""
from typing import Optional, List, Dict, Any

# ---- Flag hasil achievement ----
FLAG_OK = "OK"
FLAG_NA = "NA"                 # target 0 & realisasi 0
FLAG_NA_NO_TARGET = "NA_NO_TARGET"  # target 0 & realisasi > 0


def _num(x) -> float:
    try:
        return float(x) if x is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def hitung_achievement(target, realisasi) -> Dict[str, Any]:
    """Aturan 22a untuk semua formula Achievement."""
    t = _num(target)
    r = _num(realisasi)
    if t == 0 and r == 0:
        return {"value": None, "flag": FLAG_NA, "target": t, "realisasi": r,
                "label": "N/A", "note": "Tidak ada target & realisasi"}
    if t == 0 and r > 0:
        return {"value": None, "flag": FLAG_NA_NO_TARGET, "target": t, "realisasi": r,
                "label": "N/A (tidak ada target)", "note": "Realisasi tercatat namun tanpa target"}
    val = round(r / t * 100, 2)
    return {"value": val, "flag": FLAG_OK, "target": t, "realisasi": r,
            "label": f"{val}%", "note": None}


def status_performa(score: Optional[float]) -> str:
    """Bagian 26."""
    if score is None:
        return "N/A"
    if score >= 100:
        return "Excellent"
    if score >= 85:
        return "Good"
    if score >= 70:
        return "Need Attention"
    return "Critical"


def _weighted(components: List[Dict[str, Any]]) -> Dict[str, Any]:
    """components: list of {value: float|None, weight: fraction 0..1, name: str}.
    Normalisasi bobot bila ada komponen N/A (bagian 24)."""
    valid = [c for c in components if c.get("value") is not None]
    if not valid:
        return {"value": None, "partial": False, "note": "Semua komponen N/A"}
    total_w = sum(c["weight"] for c in valid)
    if total_w == 0:
        return {"value": None, "partial": False, "note": "Total bobot 0"}
    score = sum(c["value"] * c["weight"] for c in valid) / total_w
    partial = len(valid) < len(components)
    missing = [c["name"] for c in components if c.get("value") is None]
    note = None
    if partial:
        note = f"Dihitung parsial — komponen {', '.join(missing)} tidak memiliki target."
    return {"value": round(score, 2), "partial": partial, "note": note}


def hitung_performance_score_lending(ach_lending: Dict, ach_funding: Dict,
                                     w_lending: float, w_funding: float) -> Dict[str, Any]:
    """Bagian 24. w_* dalam bentuk persen (mis. 70)."""
    res = _weighted([
        {"value": ach_lending.get("value"), "weight": w_lending / 100.0, "name": "Lending"},
        {"value": ach_funding.get("value"), "weight": w_funding / 100.0, "name": "Funding"},
    ])
    res["status"] = status_performa(res["value"])
    return res


def hitung_performance_score_funding(ach_funding: Dict, w_funding: float = 100.0) -> Dict[str, Any]:
    """Bagian 34/56."""
    res = _weighted([
        {"value": ach_funding.get("value"), "weight": w_funding / 100.0, "name": "Funding"},
    ])
    res["status"] = status_performa(res["value"])
    return res


def hitung_npf(out_kol_345: float, out_total: float, target_npf_ratio: float,
               npf_score_cap: float = 150.0, status_threshold: float = 1.0) -> Dict[str, Any]:
    """Bagian 40, 40a, 41a. NPF Ratio + NPF Score + Status."""
    ot = _num(out_total)
    k = _num(out_kol_345)
    tr = _num(target_npf_ratio)

    if ot == 0:
        return {"npf_ratio": None, "npf_score": None, "status": "N/A",
                "label": "N/A", "note": "Total outstanding portfolio = 0"}

    ratio = round(k / ot * 100, 2)

    # NPF Score (41a)
    if ratio == 0:
        score = npf_score_cap
    else:
        raw = (tr / ratio) * 100 if ratio > 0 else npf_score_cap
        score = min(raw, npf_score_cap)
        score = max(score, 0.0)
    score = round(score, 2)

    # Status (40a)
    if ratio <= tr:
        status = "Sehat"
    elif ratio <= tr + status_threshold:
        status = "Perhatian"
    else:
        status = "Critical"

    return {"npf_ratio": ratio, "npf_score": score, "status": status,
            "label": f"{ratio}%", "target_npf_ratio": tr, "note": None}


def hitung_performance_score_remedial(ach_recovery: Dict, npf_result: Dict,
                                      w_recovery: float, w_npf: float) -> Dict[str, Any]:
    """Bagian 41/57."""
    res = _weighted([
        {"value": ach_recovery.get("value"), "weight": w_recovery / 100.0, "name": "Recovery WO"},
        {"value": npf_result.get("npf_score"), "weight": w_npf / 100.0, "name": "NPF Position"},
    ])
    res["status"] = status_performa(res["value"])
    return res


def hitung_ranking(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Tie breaker (63): 1) achievement tertinggi, 2) realisasi terbesar,
    3) performance score periode sebelumnya. N/A di bawah, terpisah.
    entries item butuh: performance_score, achievement_value, realisasi, prev_score.
    """
    valid = [e for e in entries if e.get("performance_score") is not None]
    na = [e for e in entries if e.get("performance_score") is None]

    valid.sort(key=lambda e: (
        -(e.get("performance_score") or 0),
        -(e.get("achievement_value") or 0),
        -(e.get("realisasi") or 0),
        -(e.get("prev_score") or 0),
    ))
    for i, e in enumerate(valid):
        e["rank"] = i + 1
    for e in na:
        e["rank"] = None
    return valid + na
