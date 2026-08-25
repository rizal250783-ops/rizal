import os
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

BULAN_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


class EmailNotConfigured(Exception):
    pass


class EmailDeliveryError(Exception):
    pass


def _rupiah(v):
    try:
        return "Rp" + f"{int(v):,}".replace(",", ".")
    except Exception:
        return "Rp0"


def _tanggal(v):
    if not v:
        return "-"
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return f"{d.day} {BULAN_ID[d.month - 1]} {d.year}"
    except Exception:
        return str(v)


def _bulan(v):
    if not v:
        return "-"
    try:
        y, m = str(v).split("-")
        return f"{BULAN_ID[int(m) - 1]} {y}"
    except Exception:
        return str(v)


def send_email(to: str, subject: str, html: str):
    api_key = os.environ.get("SENDGRID_API_KEY", "").strip()
    sender = os.environ.get("SENDER_EMAIL", "").strip()
    if not api_key or not sender:
        raise EmailNotConfigured(
            "SendGrid belum dikonfigurasi. Tambahkan SENDGRID_API_KEY dan SENDER_EMAIL (email pengirim terverifikasi) di backend/.env."
        )
    message = Mail(from_email=sender, to_emails=to, subject=subject, html_content=html)
    try:
        sg = SendGridAPIClient(api_key)
        resp = sg.send(message)
        if resp.status_code not in (200, 201, 202):
            raise EmailDeliveryError(f"SendGrid mengembalikan status {resp.status_code}")
        return True
    except EmailDeliveryError:
        raise
    except Exception as e:
        raise EmailDeliveryError(f"Gagal mengirim email: {e}")


def reminder_html(items, periode):
    rows = "".join(
        f"""<tr>
            <td style="padding:10px 14px;border-bottom:1px solid #eef1f5;">{it['nama']}</td>
            <td style="padding:10px 14px;border-bottom:1px solid #eef1f5;">{it['lokasi']} — Kamar {it['nomor_kamar']}</td>
            <td style="padding:10px 14px;border-bottom:1px solid #eef1f5;">{_tanggal(it.get('tanggal_jatuh_tempo'))}</td>
            <td style="padding:10px 14px;border-bottom:1px solid #eef1f5;text-align:right;font-weight:700;color:#9f1239;">{_rupiah(it['jumlah'])}</td>
        </tr>"""
        for it in items
    )
    total = sum(int(it["jumlah"]) for it in items)
    return f"""<!DOCTYPE html>
<html><body style="margin:0;background:#f8fafc;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
  <div style="max-width:640px;margin:0 auto;background:#ffffff;">
    <div style="background:#0A192F;padding:22px 24px;">
      <div style="font-size:22px;font-weight:800;color:#ffffff;">ROSADAH KOST</div>
      <div style="font-size:12px;color:#D4AF37;letter-spacing:2px;">Nyaman • Aman • Bersih</div>
    </div>
    <div style="height:4px;background:#D4AF37;"></div>
    <div style="padding:24px;">
      <h2 style="margin:0 0 6px;color:#0A192F;">Pengingat Tunggakan Pembayaran</h2>
      <p style="color:#475569;margin:0 0 18px;">Periode {_bulan(periode)}. Berikut daftar penghuni yang belum melunasi pembayaran:</p>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="background:#f1f5f9;color:#475569;text-align:left;">
            <th style="padding:10px 14px;">Nama</th>
            <th style="padding:10px 14px;">Lokasi / Kamar</th>
            <th style="padding:10px 14px;">Jatuh Tempo</th>
            <th style="padding:10px 14px;text-align:right;">Tagihan</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <div style="margin-top:18px;padding:14px 18px;background:#fff1f2;border-radius:10px;display:flex;justify-content:space-between;">
        <span style="color:#9f1239;font-weight:700;">Total Tunggakan</span>
        <span style="color:#9f1239;font-weight:800;font-size:18px;float:right;">{_rupiah(total)}</span>
      </div>
      <p style="color:#94a3b8;font-size:12px;margin-top:24px;">Email ini dikirim otomatis oleh aplikasi ROSADAH KOST.</p>
    </div>
  </div>
</body></html>"""
