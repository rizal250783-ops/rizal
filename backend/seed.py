"""Seed demo data AO-360 (bagian 78-81)."""
import os
from datetime import datetime, timezone

CURRENT_PERIOD = datetime.now(timezone.utc).strftime("%Y-%m")


async def run(db, hash_password):
    if await db.users.count_documents({}) > 0:
        return

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@hajimiskin.co.id")
    admin_pw = os.environ.get("ADMIN_PASSWORD", "Admin12345")

    await db.branches.update_one({"_id": "main"},
        {"$set": {"name": "PT BPRS Haji Miskin", "kode": "HM-01", "is_main": True}}, upsert=True)
    await db.system_settings.update_one({"_id": "system"},
        {"$set": {"active_period": CURRENT_PERIOD, "session_timeout_minutes": 60}}, upsert=True)

    def u(name, email, role, pw="Password123", req=False):
        return {"name": name, "email": email.lower(), "role": role,
                "password_hash": hash_password(pw), "is_active": True,
                "requires_password_reset": req, "failed_login_attempts": 0,
                "locked_until": None, "branch": "PT BPRS Haji Miskin",
                "employee_id": None, "phone": None,
                "created_at": datetime.now(timezone.utc).isoformat()}

    users = [
        u("HENDRI KAMAL", "hendri.kamal@hajimiskin.co.id", "direktur", "Direktur123"),
        u("Administrator", admin_email, "admin", admin_pw),
        u("Rizky Pratama", "rizky.lending@hajimiskin.co.id", "ao_lending"),
        u("Dewi Anggraini", "dewi.lending@hajimiskin.co.id", "ao_lending"),
        u("Fajar Nugroho", "fajar.lending@hajimiskin.co.id", "ao_lending"),
        u("Siti Rahmawati", "siti.lending@hajimiskin.co.id", "ao_lending"),
        u("Budi Santoso", "budi.funding@hajimiskin.co.id", "ao_funding"),
        u("Maya Sari", "maya.funding@hajimiskin.co.id", "ao_funding"),
        u("Andi Wijaya", "andi.funding@hajimiskin.co.id", "ao_funding"),
        u("Lestari Putri", "lestari.funding@hajimiskin.co.id", "ao_funding"),
        u("Hendra Gunawan", "hendra.remedial@hajimiskin.co.id", "pic_remedial"),
        u("Ratna Dewi", "ratna.remedial@hajimiskin.co.id", "pic_remedial"),
    ]
    res = await db.users.insert_many(users)
    ids = [str(x) for x in res.inserted_ids]
    # index by role order
    lending_ids = ids[2:6]
    funding_ids = ids[6:10]
    remedial_ids = ids[10:12]

    # ---- Targets & Achievements ----
    M = 1_000_000
    lending_data = [
        (1_500*M, 1_650*M, 500*M, 600*M),   # ach 110% / 120% -> score 113 (bagian 79)
        (1_200*M, 1_080*M, 400*M, 360*M),   # 90 / 90
        (2_000*M, 1_500*M, 600*M, 420*M),   # 75 / 70
        (1_000*M, 700*M,   300*M, 180*M),   # 70 / 60
    ]
    for i, aid in enumerate(lending_ids):
        tb, rb, tf, rf = lending_data[i]
        await db.targets.insert_one({"ao_id": aid, "period": CURRENT_PERIOD,
            "target_booking": tb, "target_funding": tf, "target_recovery_wo": 0,
            "target_npf_ratio": 0, "target_npf_absolute": 0})
        await db.achievements.insert_one({"ao_id": aid, "period": CURRENT_PERIOD,
            "realisasi_booking": rb, "realisasi_funding": rf, "realisasi_recovery_wo": 0})

    funding_data = [
        (2_000*M, 2_300*M),  # 115% (bagian 80)
        (1_800*M, 1_620*M),  # 90%
        (2_500*M, 3_000*M),  # 120%
        (1_500*M, 900*M),    # 60%
    ]
    for i, aid in enumerate(funding_ids):
        tf, rf = funding_data[i]
        await db.targets.insert_one({"ao_id": aid, "period": CURRENT_PERIOD,
            "target_booking": 0, "target_funding": tf, "target_recovery_wo": 0,
            "target_npf_ratio": 0, "target_npf_absolute": 0})
        await db.achievements.insert_one({"ao_id": aid, "period": CURRENT_PERIOD,
            "realisasi_booking": 0, "realisasi_funding": rf, "realisasi_recovery_wo": 0})

    remedial_data = [
        (500*M, 600*M, 3.0, 3_000*M),  # recovery 120%, target npf 3% (bagian 81)
        (400*M, 320*M, 3.0, 3_000*M),  # recovery 80%
    ]
    for i, aid in enumerate(remedial_ids):
        tr, rr, npfr, npfa = remedial_data[i]
        await db.targets.insert_one({"ao_id": aid, "period": CURRENT_PERIOD,
            "target_booking": 0, "target_funding": 0, "target_recovery_wo": tr,
            "target_npf_ratio": npfr, "target_npf_absolute": npfa})
        await db.achievements.insert_one({"ao_id": aid, "period": CURRENT_PERIOD,
            "realisasi_booking": 0, "realisasi_funding": 0, "realisasi_recovery_wo": rr})

    # ---- Portfolio (kolek 1-5) ----
    produk = ["Murabahah", "Musyarakah", "Mudharabah", "Ijarah"]
    portfolios = []
    n = 1
    # Total outstanding ~ set so NPF ~2.7% (bagian 81): kol3-5 small vs total
    kolek_plan = [(1, 20, 225*M), (2, 6, 67*M), (3, 2, 30*M), (4, 1, 40*M), (5, 1, 35*M)]
    for kol, count, avg in kolek_plan:
        for c in range(count):
            aid = lending_ids[n % 4]
            portfolios.append({
                "nomor_kontrak": f"HM-{CURRENT_PERIOD.replace('-','')}-{n:04d}",
                "nama_nasabah": f"Nasabah {n:03d}",
                "produk": produk[n % 4],
                "plafond": avg * 1.2,
                "outstanding_pokok": avg,
                "tanggal_akad": "2024-01-15",
                "tanggal_jatuh_tempo": "2027-01-15",
                "kolektibilitas": kol,
                "dpd": 0 if kol == 1 else (30 if kol == 2 else (kol - 1) * 90),
                "ao_id": aid,
                "created_at": datetime.now(timezone.utc).isoformat()})
            n += 1
    await db.loan_portfolio.insert_many(portfolios)

    # ---- default performance weights ----
    now = datetime.now(timezone.utc).isoformat()
    await db.performance_settings.insert_many([
        {"type": "weight", "role": "ao_lending", "weights": {"lending": 70, "funding": 30},
         "version": 1, "created_at": now, "created_by": "system", "old_weights": None},
        {"type": "weight", "role": "ao_funding", "weights": {"funding": 100},
         "version": 1, "created_at": now, "created_by": "system", "old_weights": None},
        {"type": "weight", "role": "pic_remedial", "weights": {"recovery": 70, "npf": 30},
         "version": 1, "created_at": now, "created_by": "system", "old_weights": None},
        {"type": "parameter", "parameter_key": "npf_score_cap", "parameter_value": 150.0,
         "version": 1, "created_at": now, "created_by": "system"},
        {"type": "parameter", "parameter_key": "npf_status_threshold", "parameter_value": 1.0,
         "version": 1, "created_at": now, "created_by": "system"},
    ])
