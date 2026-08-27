"""Decision engine: pemutus routing based on limit + RAC escalation."""
from constants import RCG_CAP

ORDER = ["ACRM", "RCRM", "RCG", "ABOVE_RCG"]

STAGE_STATUS = {
    ("ACRM", "review"): "Menunggu Review ACRM",
    ("ACRM", "decide"): "Menunggu Pemutus ACRM",
    ("RCRM", "review"): "Menunggu Review RCRM",
    ("RCRM", "decide"): "Menunggu Pemutus RCRM",
    ("RCG", "decide"): "Menunggu Pemutus RCG",
    ("RA", "ra"): "Menunggu Risk Assessment",
    ("ESCALATION", "blocked"): "Memerlukan Eskalasi di Atas RCG",
}


def compute_normal_approver(nilai: float, acrm_limit: float, rcrm_limit: float) -> str:
    if acrm_limit and acrm_limit > 0 and nilai <= acrm_limit:
        return "ACRM"
    if rcrm_limit and rcrm_limit > 0 and nilai <= rcrm_limit:
        return "RCRM"
    if nilai <= RCG_CAP:
        return "RCG"
    return "ABOVE_RCG"


def compute_final_approver(normal: str, rac_ok: bool) -> str:
    if rac_ok:
        return normal
    idx = ORDER.index(normal)
    return ORDER[min(idx + 1, len(ORDER) - 1)]


def build_stages(final: str, ra_required: bool):
    """Return list of [level, action] stages from RCO submission to final decision."""
    stages = []
    if final in ("RCRM", "RCG", "ABOVE_RCG"):
        stages.append(["ACRM", "review"])
    if final in ("RCG", "ABOVE_RCG"):
        stages.append(["RCRM", "review"])
    if final == "ABOVE_RCG":
        stages.append(["ESCALATION", "blocked"])
        return stages
    if ra_required:
        stages.append(["RA", "ra"])
    stages.append([final, "decide"])
    return stages


def status_for_stage(stage) -> str:
    return STAGE_STATUS.get((stage[0], stage[1]), "Menunggu Proses")


def route_note(nilai: float, acrm_limit: float, rcrm_limit: float, rac_ok: bool):
    normal = compute_normal_approver(nilai, acrm_limit, rcrm_limit)
    ra_required = not rac_ok
    final = compute_final_approver(normal, rac_ok)
    stages = build_stages(final, ra_required)
    return {
        "normal_approver_level": normal,
        "final_approver_level": final,
        "ra_required": ra_required,
        "stages": stages,
    }
