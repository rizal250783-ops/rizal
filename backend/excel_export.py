"""Excel export for notes (openpyxl)."""
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

TEAL = "00A0A0"
GOLD = "F0B43C"


def export_notes_excel(notes: list) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Nota Restruktur"
    headers = ["Nomor Nota", "Nama Nasabah", "CIF", "Area", "Region", "Segmen", "Status",
               "Nilai Kewenangan Pemutus", "Total OS Pokok", "Total OS Margin", "Total Penalty",
               "Total Kewajiban", "Pemutus", "Tanggal Approved"]
    ws.append(headers)
    thin = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=TEAL)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border
    for n in notes:
        cust = n.get("customer", {})
        facs = n.get("facilities", [])
        cif = facs[0].get("cif", "") if facs else ""
        segmen = ", ".join(sorted({f.get("segmen", "") for f in facs if f.get("segmen")}))
        ws.append([
            n.get("nomor_nota", ""), cust.get("nama", ""), cif, n.get("area", ""), n.get("region", ""),
            segmen, n.get("status", ""), n.get("nilai_kewenangan_pemutus", 0),
            n.get("total_os_pokok", 0), n.get("total_os_margin", 0), n.get("total_penalty", 0),
            n.get("total_kewajiban", 0), n.get("final_approver_nama", "") or "-",
            n.get("approved_date", "") or "-",
        ])
    widths = [24, 24, 14, 20, 20, 14, 22, 22, 18, 18, 16, 18, 24, 16]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i) if i <= 26 else "A"].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.border = border
            if c.column in (8, 9, 10, 11, 12):
                c.number_format = '#,##0'
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
